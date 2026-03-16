"""
Memory Budget

控制召回的 token 预算，防止超出限制。

Author: Memory Kernel
Created: 2026-03-16
Version: 1.0.0
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from contract.memory.types import MemoryRecord


@dataclass
class PromptBudget:
    """
    Prompt 预算
    
    定义召回的 token 预算限制。
    """
    max_tokens: int = 1000  # 最大 token 数
    max_records: int = 10  # 最大记录数
    max_content_length: int = 500  # 单条记录最大字符数
    max_total_length: int = 5000  # 总最大字符数
    
    # 预算分配
    truth_budget_ratio: float = 0.5  # Truth 层预算比例
    knowledge_budget_ratio: float = 0.3  # Knowledge 层预算比例
    retrieval_budget_ratio: float = 0.2  # Retrieval 层预算比例
    
    def estimate_tokens(self, text: str) -> int:
        """
        估算 token 数
        
        使用简单的字符/4 近似估算。
        
        Args:
            text: 文本
        
        Returns:
            token 估算数
        """
        # 简单估算：约 4 字符 = 1 token
        return len(text) // 4 + 1
    
    def is_within_budget(
        self,
        total_tokens: int,
        record_count: int,
    ) -> bool:
        """
        检查是否在预算内
        
        Args:
            total_tokens: 总 token 数
            record_count: 记录数
        
        Returns:
            是否在预算内
        """
        return (
            total_tokens <= self.max_tokens and
            record_count <= self.max_records
        )


@dataclass
class BudgetUsage:
    """
    预算使用情况
    
    记录预算的使用详情。
    """
    budget: PromptBudget
    used_tokens: int = 0
    used_records: int = 0
    truncated: int = 0  # 截断的记录数
    rejected: int = 0  # 拒绝的记录数
    
    records_included: List[str] = field(default_factory=list)
    records_truncated: List[str] = field(default_factory=list)
    records_rejected: List[str] = field(default_factory=list)
    
    def usage_ratio(self) -> float:
        """使用比例"""
        return self.used_tokens / self.budget.max_tokens if self.budget.max_tokens > 0 else 0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "max_tokens": self.budget.max_tokens,
            "used_tokens": self.used_tokens,
            "usage_ratio": self.usage_ratio(),
            "used_records": self.used_records,
            "max_records": self.budget.max_records,
            "truncated": self.truncated,
            "rejected": self.rejected,
        }


class BudgetManager:
    """
    预算管理器
    
    管理召回的 token 预算。
    """
    
    def __init__(
        self,
        budget: Optional[PromptBudget] = None,
    ):
        """
        初始化预算管理器
        
        Args:
            budget: 预算配置
        """
        self.budget = budget or PromptBudget()
    
    def enforce_budget(
        self,
        records: List[MemoryRecord],
    ) -> tuple[List[MemoryRecord], BudgetUsage]:
        """
        执行预算限制
        
        Args:
            records: 记录列表
        
        Returns:
            (filtered_records, usage)
        """
        usage = BudgetUsage(budget=self.budget)
        filtered = []
        total_length = 0
        
        for record in records:
            # 检查记录数限制
            if len(filtered) >= self.budget.max_records:
                usage.rejected += 1
                usage.records_rejected.append(record.id)
                continue
            
            # 获取内容
            content = record.content or ""
            
            # 检查单条记录长度
            if len(content) > self.budget.max_content_length:
                # 截断
                content = content[:self.budget.max_content_length] + "..."
                usage.truncated += 1
                usage.records_truncated.append(record.id)
            
            # 估算 token
            tokens = self.budget.estimate_tokens(content)
            
            # 检查总 token 限制
            if usage.used_tokens + tokens > self.budget.max_tokens:
                usage.rejected += 1
                usage.records_rejected.append(record.id)
                continue
            
            # 检查总长度限制
            if total_length + len(content) > self.budget.max_total_length:
                usage.rejected += 1
                usage.records_rejected.append(record.id)
                continue
            
            # 更新统计
            usage.used_tokens += tokens
            usage.used_records += 1
            total_length += len(content)
            usage.records_included.append(record.id)
            
            # 添加到结果
            filtered.append(record)
        
        return filtered, usage
    
    def allocate_by_layer(
        self,
        records: List[MemoryRecord],
    ) -> Dict[str, List[MemoryRecord]]:
        """
        按层级分配预算
        
        Args:
            records: 记录列表
        
        Returns:
            按层级分配的记录字典
        """
        from contract.memory.types import TruthKnowledgeRetrieval
        
        # 分组
        by_layer: Dict[str, List[MemoryRecord]] = {
            "truth": [],
            "knowledge": [],
            "retrieval": [],
        }
        
        for record in records:
            if record.tkr_layer == TruthKnowledgeRetrieval.TRUTH:
                by_layer["truth"].append(record)
            elif record.tkr_layer == TruthKnowledgeRetrieval.KNOWLEDGE:
                by_layer["knowledge"].append(record)
            else:
                by_layer["retrieval"].append(record)
        
        # 按预算比例分配
        result: Dict[str, List[MemoryRecord]] = {
            "truth": [],
            "knowledge": [],
            "retrieval": [],
        }
        
        truth_budget = int(self.budget.max_tokens * self.budget.truth_budget_ratio)
        knowledge_budget = int(self.budget.max_tokens * self.budget.knowledge_budget_ratio)
        retrieval_budget = int(self.budget.max_tokens * self.budget.retrieval_budget_ratio)
        
        # Truth 层
        used = 0
        for record in by_layer["truth"]:
            tokens = self.budget.estimate_tokens(record.content or "")
            if used + tokens <= truth_budget:
                result["truth"].append(record)
                used += tokens
        
        # Knowledge 层
        used = 0
        for record in by_layer["knowledge"]:
            tokens = self.budget.estimate_tokens(record.content or "")
            if used + tokens <= knowledge_budget:
                result["knowledge"].append(record)
                used += tokens
        
        # Retrieval 层
        used = 0
        for record in by_layer["retrieval"]:
            tokens = self.budget.estimate_tokens(record.content or "")
            if used + tokens <= retrieval_budget:
                result["retrieval"].append(record)
                used += tokens
        
        return result
    
    def get_budget_summary(self) -> Dict[str, Any]:
        """
        获取预算摘要
        
        Returns:
            摘要字典
        """
        return {
            "max_tokens": self.budget.max_tokens,
            "max_records": self.budget.max_records,
            "max_content_length": self.budget.max_content_length,
            "max_total_length": self.budget.max_total_length,
            "layer_ratios": {
                "truth": self.budget.truth_budget_ratio,
                "knowledge": self.budget.knowledge_budget_ratio,
                "retrieval": self.budget.retrieval_budget_ratio,
            },
        }


def create_budget_manager(
    max_tokens: int = 1000,
    max_records: int = 10,
) -> BudgetManager:
    """
    便捷函数：创建预算管理器
    
    Args:
        max_tokens: 最大 token 数
        max_records: 最大记录数
    
    Returns:
        BudgetManager 实例
    """
    budget = PromptBudget(
        max_tokens=max_tokens,
        max_records=max_records,
    )
    
    return BudgetManager(budget=budget)
