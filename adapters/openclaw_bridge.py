"""
OpenClaw Bridge - Shadow Mode

只读 shadow 接入 Memory Kernel，不影响主链决策、不污染主状态。

Core Principles:
1. Read-Only - 只读，不正式注入主流程
2. No Pollution - 不改主回复/主状态/truth source
3. Candidate Isolation - 不允许 candidate 进入正式召回
4. Single Path - 单 canary agent / 单 workspace / 单入口链路
5. Fail-Open - bridge 失败必须 fail-open，不影响主链

Author: Memory Kernel
Created: 2026-03-16
Version: 1.0.0
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from pathlib import Path
import time
import traceback

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from contract.memory.types import (
    MemoryRecord,
    MemoryScope,
    TruthKnowledgeRetrieval,
)
from core.memory.memory_recall import RecallEngine, RecallConfig, RecallResult
from core.memory.memory_budget import BudgetManager, BudgetConfig


@dataclass
class BridgeRequest:
    """
    Bridge 请求
    
    用户查询和上下文信息。
    """
    query: str  # 用户查询
    context: Optional[str] = None  # 上下文
    task_type: Optional[str] = None  # 任务类型（可选）
    max_suggestions: int = 5  # 最大建议数
    timeout_ms: int = 1000  # 超时时间（毫秒）


@dataclass
class RecallSuggestion:
    """
    召回建议
    
    单条建议的结构化输出。
    """
    record_id: str  # 记录 ID
    title: str  # 标题
    content_preview: str  # 内容预览（截断）
    relevance_score: float  # 相关性分数
    source: str  # 来源文件
    scope: str  # 作用域
    tkr_layer: str  # Truth/Knowledge/Retrieval 层
    
    # 元数据
    use_count: int = 0  # 使用次数
    created_at: Optional[datetime] = None  # 创建时间


@dataclass
class BridgeTrace:
    """
    Bridge 追踪信息
    
    用于监控和调试。
    """
    request_id: str  # 请求 ID
    start_time: datetime  # 开始时间
    end_time: Optional[datetime] = None  # 结束时间
    duration_ms: float = 0.0  # 耗时（毫秒）
    
    # 处理信息
    task_type_detected: Optional[str] = None  # 检测到的任务类型
    budget_used: int = 0  # 使用的预算
    candidates_found: int = 0  # 找到的候选数
    suggestions_returned: int = 0  # 返回的建议数
    
    # 状态
    success: bool = True  # 是否成功
    error: Optional[str] = None  # 错误信息


@dataclass
class BridgeResponse:
    """
    Bridge 响应
    
    包含召回建议和追踪信息。
    """
    success: bool  # 是否成功
    suggestions: List[RecallSuggestion] = field(default_factory=list)  # 建议列表
    trace: Optional[BridgeTrace] = None  # 追踪信息
    error: Optional[str] = None  # 错误信息


class OpenClawBridge:
    """
    OpenClaw Bridge - Shadow Mode
    
    只读接入 Memory Kernel，返回召回建议但不注入主流程。
    """
    
    def __init__(
        self,
        recall_engine: Optional[RecallEngine] = None,
        budget_manager: Optional[BudgetManager] = None,
        approved_records: Optional[List[MemoryRecord]] = None,
        max_content_preview: int = 200,  # 内容预览最大长度
    ):
        """
        初始化 Bridge
        
        Args:
            recall_engine: 召回引擎（可选，默认创建 shadow 模式）
            budget_manager: 预算管理器（可选）
            approved_records: approved 记录列表（可选）
            max_content_preview: 内容预览最大长度
        """
        # Shadow 模式配置
        config = RecallConfig(
            mode="shadow",  # shadow 模式
            top_k=10,
            include_candidates=False,  # 不包含候选
            fail_open=True,
            enable_trace=True,
        )
        
        self._recall_engine = recall_engine or RecallEngine(config=config)
        self._budget_manager = budget_manager or BudgetManager(BudgetConfig())
        
        # 加载 approved 记录
        if approved_records:
            self._recall_engine.load_approved_records(approved_records)
        
        self._max_content_preview = max_content_preview
        
        # 统计信息
        self._request_count = 0
        self._error_count = 0
        self._total_duration_ms = 0.0
    
    def load_approved_records(self, records: List[MemoryRecord]):
        """
        加载 approved 记录
        
        Args:
            records: 记录列表
        """
        self._recall_engine.load_approved_records(records)
    
    def recall(self, request: BridgeRequest) -> BridgeResponse:
        """
        执行召回
        
        Shadow 模式：只读、不注入主流程、fail-open。
        
        Args:
            request: Bridge 请求
            
        Returns:
            BridgeResponse: 包含建议和追踪信息
        """
        request_id = f"bridge_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{self._request_count}"
        start_time = datetime.now(timezone.utc)
        
        trace = BridgeTrace(
            request_id=request_id,
            start_time=start_time,
        )
        
        try:
            # 检查超时
            if request.timeout_ms <= 0:
                raise ValueError("timeout_ms must be positive")
            
            # 检测任务类型
            task_type = request.task_type or self._detect_task_type(request.query)
            trace.task_type_detected = task_type
            
            # 执行召回
            result = self._recall_engine.recall(
                query=request.query,
                top_k=request.max_suggestions,
            )
            
            # 检查预算
            total_content = sum(len(r.content) for r in result.records)
            if self._budget_manager:
                budget_check = self._budget_manager.check_budget(total_content)
                trace.budget_used = total_content
                
                if not budget_check:
                    # 预算超出，截断
                    result.records = self._truncate_by_budget(
                        result.records,
                        self._budget_manager.remaining()
                    )
            
            # 转换为建议
            suggestions = []
            for record in result.records:
                suggestion = RecallSuggestion(
                    record_id=record.id,
                    title=record.title,
                    content_preview=self._truncate_content(record.content),
                    relevance_score=getattr(record, 'score', 1.0),
                    source=record.source_file,
                    scope=record.scope.value,
                    tkr_layer=record.tkr_layer.value,
                    use_count=record.use_count,
                    created_at=record.created_at,
                )
                suggestions.append(suggestion)
            
            # 更新追踪
            trace.candidates_found = len(result.records)
            trace.suggestions_returned = len(suggestions)
            trace.success = True
            
            # 更新统计
            self._request_count += 1
            
            return BridgeResponse(
                success=True,
                suggestions=suggestions,
                trace=trace,
            )
            
        except Exception as e:
            # Fail-open: 记录错误但返回空建议
            trace.success = False
            trace.error = str(e)
            
            self._error_count += 1
            
            return BridgeResponse(
                success=False,
                suggestions=[],
                trace=trace,
                error=str(e),
            )
        
        finally:
            # 计算耗时
            end_time = datetime.now(timezone.utc)
            trace.end_time = end_time
            trace.duration_ms = (end_time - start_time).total_seconds() * 1000
            self._total_duration_ms += trace.duration_ms
    
    def _detect_task_type(self, query: str) -> str:
        """
        检测任务类型
        
        Args:
            query: 用户查询
            
        Returns:
            任务类型字符串
        """
        query_lower = query.lower()
        
        # 任务类型关键词
        task_patterns = {
            "coding": ["code", "implement", "fix", "refactor", "debug", "编写", "实现", "修复", "重构"],
            "review": ["review", "check", "audit", "审核", "检查"],
            "docs": ["docs", "document", "readme", "文档", "说明"],
            "test": ["test", "testing", "测试"],
            "deploy": ["deploy", "release", "publish", "部署", "发布"],
            "config": ["config", "settings", "配置", "设置"],
            "analysis": ["analyze", "analysis", "分析"],
        }
        
        for task_type, keywords in task_patterns.items():
            for keyword in keywords:
                if keyword in query_lower:
                    return task_type
        
        return "general"
    
    def _truncate_content(self, content: str) -> str:
        """
        截断内容为预览
        
        Args:
            content: 原始内容
            
        Returns:
            截断后的预览
        """
        if len(content) <= self._max_content_preview:
            return content
        
        return content[:self._max_content_preview - 3] + "..."
    
    def _truncate_by_budget(
        self,
        records: List[MemoryRecord],
        budget: int
    ) -> List[MemoryRecord]:
        """
        按预算截断记录列表
        
        Args:
            records: 记录列表
            budget: 剩余预算
            
        Returns:
            截断后的记录列表
        """
        result = []
        used = 0
        
        for record in records:
            content_len = len(record.content)
            if used + content_len <= budget:
                result.append(record)
                used += content_len
            else:
                break
        
        return result
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            统计字典
        """
        return {
            "request_count": self._request_count,
            "error_count": self._error_count,
            "error_rate": self._error_count / max(1, self._request_count),
            "total_duration_ms": self._total_duration_ms,
            "avg_duration_ms": self._total_duration_ms / max(1, self._request_count),
        }


def create_bridge(
    approved_records: Optional[List[MemoryRecord]] = None,
    max_content_preview: int = 200,
) -> OpenClawBridge:
    """
    创建 Bridge 实例
    
    Args:
        approved_records: approved 记录列表
        max_content_preview: 内容预览最大长度
        
    Returns:
        OpenClawBridge 实例
    """
    return OpenClawBridge(
        approved_records=approved_records,
        max_content_preview=max_content_preview,
    )
