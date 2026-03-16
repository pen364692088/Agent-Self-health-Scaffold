"""
OpenClaw Bridge Shadow

只读 shadow 接入 Memory Kernel，不影响主链。

Author: Memory Kernel
Created: 2026-03-16
Version: 1.0.0
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from pathlib import Path
import time
import logging

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from contract.memory.types import (
    MemoryRecord,
    MemoryScope,
    TruthKnowledgeRetrieval,
)
from core.memory.memory_recall import RecallEngine, RecallConfig
from core.memory.memory_recall_policy import (
    RecallPolicyManager,
    TaskType,
)
from core.memory.memory_budget import BudgetManager, PromptBudget


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class BridgeRequest:
    """
    Bridge 请求
    
    定义 OpenClaw 发送给 Bridge 的请求。
    """
    query: str  # 用户查询
    context: Optional[str] = None  # 上下文
    task_type: Optional[str] = None  # 任务类型（可选）
    max_suggestions: int = 5  # 最大建议数
    timeout_ms: int = 1000  # 超时时间（毫秒）
    approved_ids: Optional[set] = None  # approved 记录 ID 集合


@dataclass
class RecallSuggestion:
    """
    召回建议
    
    单条召回建议。
    """
    record_id: str  # 记录 ID
    title: str  # 标题
    content_preview: str  # 内容预览（已截断）
    relevance_score: float  # 相关性分数
    source: str  # 来源
    scope: str  # 作用域
    tkr_layer: str  # 层级
    tags: List[str] = field(default_factory=list)  # 标签
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "record_id": self.record_id,
            "title": self.title,
            "content_preview": self.content_preview,
            "relevance_score": self.relevance_score,
            "source": self.source,
            "scope": self.scope,
            "tkr_layer": self.tkr_layer,
            "tags": self.tags,
        }


@dataclass
class BridgeTrace:
    """
    Bridge 追踪
    
    记录 Bridge 调用的详细信息。
    """
    request_id: str  # 请求 ID
    started_at: datetime  # 开始时间
    completed_at: Optional[datetime] = None  # 完成时间
    duration_ms: float = 0.0  # 耗时（毫秒）
    
    task_type_detected: Optional[str] = None  # 检测到的任务类型
    recall_triggered: bool = False  # 是否触发召回
    budget_used_tokens: int = 0  # 使用的 token 预算
    records_scanned: int = 0  # 扫描的记录数
    suggestions_returned: int = 0  # 返回的建议数
    
    stages: List[Dict[str, Any]] = field(default_factory=list)  # 阶段信息
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "request_id": self.request_id,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_ms": self.duration_ms,
            "task_type_detected": self.task_type_detected,
            "recall_triggered": self.recall_triggered,
            "budget_used_tokens": self.budget_used_tokens,
            "records_scanned": self.records_scanned,
            "suggestions_returned": self.suggestions_returned,
            "stages": self.stages,
        }


@dataclass
class BridgeResponse:
    """
    Bridge 响应
    
    Bridge 返回给 OpenClaw 的响应。
    """
    success: bool  # 是否成功
    suggestions: List[RecallSuggestion]  # 召回建议
    trace: Optional[BridgeTrace] = None  # 追踪信息
    error: Optional[str] = None  # 错误信息
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "suggestions": [s.to_dict() for s in self.suggestions],
            "trace": self.trace.to_dict() if self.trace else None,
            "error": self.error,
        }


class OpenClawBridge:
    """
    OpenClaw Bridge
    
    只读 shadow 接入 Memory Kernel。
    """
    
    def __init__(
        self,
        approved_records: Optional[List[MemoryRecord]] = None,
        budget: Optional[PromptBudget] = None,
    ):
        """
        初始化 Bridge
        
        Args:
            approved_records: approved 记录列表
            budget: 预算配置
        """
        self._approved_records = approved_records or []
        self._approved_ids = {r.id for r in self._approved_records}
        
        # 初始化组件
        self._policy_manager = RecallPolicyManager()
        self._policy_manager.set_approved_ids(self._approved_ids)
        
        self._budget_manager = BudgetManager(budget=budget)
        
        self._recall_engine = RecallEngine(
            approved_records=self._approved_records,
            config=RecallConfig(
                mode="shadow",  # Shadow 模式
                enable_trace=True,
                fail_open=True,
            ),
        )
        
        # 统计
        self._stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_suggestions": 0,
            "total_errors": 0,
        }
    
    def load_approved_records(self, records: List[MemoryRecord]):
        """
        加载 approved 记录
        
        Args:
            records: 记录列表
        """
        self._approved_records = records
        self._approved_ids = {r.id for r in records}
        self._policy_manager.set_approved_ids(self._approved_ids)
        self._recall_engine.load_approved_records(records)
    
    def recall(self, request: BridgeRequest) -> BridgeResponse:
        """
        执行召回
        
        Fail-open: 任何错误都返回空建议，不影响主链。
        
        Args:
            request: Bridge 请求
        
        Returns:
            BridgeResponse
        """
        request_id = f"bridge_{datetime.now().strftime('%Y%m%d%H%M%S')}_{hash(request.query) % 10000:04d}"
        
        trace = BridgeTrace(
            request_id=request_id,
            started_at=datetime.now(timezone.utc),
        )
        
        suggestions = []
        
        try:
            # 阶段 1: 检测任务类型
            stage_start = time.time()
            
            if request.task_type:
                try:
                    task_type = TaskType(request.task_type.lower())
                except ValueError:
                    task_type = self._policy_manager.detect_task_type(request.query)
            else:
                task_type = self._policy_manager.detect_task_type(request.query)
            
            trace.task_type_detected = task_type.value
            trace.stages.append({
                "name": "detect_task_type",
                "duration_ms": (time.time() - stage_start) * 1000,
            })
            
            # 阶段 2: 检查是否应该召回
            stage_start = time.time()
            
            should_recall = self._policy_manager.should_recall(
                query=request.query,
                task_type=task_type,
            )
            
            trace.recall_triggered = should_recall
            trace.stages.append({
                "name": "check_policy",
                "duration_ms": (time.time() - stage_start) * 1000,
            })
            
            if not should_recall:
                # 不触发召回
                trace.completed_at = datetime.now(timezone.utc)
                trace.duration_ms = (trace.completed_at - trace.started_at).total_seconds() * 1000
                
                self._stats["total_requests"] += 1
                self._stats["successful_requests"] += 1
                
                return BridgeResponse(
                    success=True,
                    suggestions=[],
                    trace=trace,
                )
            
            # 阶段 3: 执行召回
            stage_start = time.time()
            
            recall_result = self._recall_engine.recall(
                query=request.query,
                top_k=request.max_suggestions * 2,  # 多召回一些，后面过滤
            )
            
            records = recall_result.records
            trace.records_scanned = len(self._approved_records)
            trace.stages.append({
                "name": "recall",
                "duration_ms": (time.time() - stage_start) * 1000,
            })
            
            # 阶段 4: 预算控制
            stage_start = time.time()
            
            filtered_records, usage = self._budget_manager.enforce_budget(records)
            trace.budget_used_tokens = usage.used_tokens
            trace.stages.append({
                "name": "budget_control",
                "duration_ms": (time.time() - stage_start) * 1000,
            })
            
            # 阶段 5: 转换为建议
            stage_start = time.time()
            
            for record in filtered_records[:request.max_suggestions]:
                # 截断内容预览
                content_preview = record.content[:200] if record.content else ""
                if len(record.content or "") > 200:
                    content_preview += "..."
                
                suggestion = RecallSuggestion(
                    record_id=record.id,
                    title=record.title,
                    content_preview=content_preview,
                    relevance_score=record.confidence,
                    source=record.source_file,
                    scope=record.scope.value,
                    tkr_layer=record.tkr_layer.value,
                    tags=record.tags or [],
                )
                suggestions.append(suggestion)
            
            trace.suggestions_returned = len(suggestions)
            trace.stages.append({
                "name": "convert_suggestions",
                "duration_ms": (time.time() - stage_start) * 1000,
            })
            
            # 完成
            trace.completed_at = datetime.now(timezone.utc)
            trace.duration_ms = (trace.completed_at - trace.started_at).total_seconds() * 1000
            
            # 更新统计
            self._stats["total_requests"] += 1
            self._stats["successful_requests"] += 1
            self._stats["total_suggestions"] += len(suggestions)
            
            return BridgeResponse(
                success=True,
                suggestions=suggestions,
                trace=trace,
            )
            
        except Exception as e:
            # Fail-open: 记录错误，返回空建议
            logger.error(f"Bridge recall error: {e}")
            
            trace.completed_at = datetime.now(timezone.utc)
            trace.duration_ms = (trace.completed_at - trace.started_at).total_seconds() * 1000
            
            self._stats["total_requests"] += 1
            self._stats["failed_requests"] += 1
            self._stats["total_errors"] += 1
            
            return BridgeResponse(
                success=False,
                suggestions=[],
                trace=trace,
                error=str(e),
            )
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            统计字典
        """
        return self._stats.copy()
    
    def reset_statistics(self):
        """重置统计"""
        self._stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_suggestions": 0,
            "total_errors": 0,
        }


def create_bridge(
    approved_records: Optional[List[MemoryRecord]] = None,
    max_tokens: int = 500,
    max_records: int = 5,
) -> OpenClawBridge:
    """
    便捷函数：创建 Bridge
    
    Args:
        approved_records: approved 记录列表
        max_tokens: 最大 token 数
        max_records: 最大记录数
    
    Returns:
        OpenClawBridge 实例
    """
    budget = PromptBudget(
        max_tokens=max_tokens,
        max_records=max_records,
    )
    
    return OpenClawBridge(
        approved_records=approved_records,
        budget=budget,
    )
