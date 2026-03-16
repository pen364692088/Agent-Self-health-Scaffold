"""
OpenClaw Bridge Canary Assist

建议参与模式，让 OpenClaw 可以选择采纳 recall suggestions。

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
import uuid
import json

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
class AssistRequest:
    """
    Assist 请求
    
    定义 OpenClaw 发送给 Bridge 的 assist 请求。
    """
    query: str  # 用户查询
    context: Optional[str] = None  # 上下文
    task_type: Optional[str] = None  # 任务类型
    max_suggestions: int = 3  # 最大建议数
    include_reasoning: bool = False  # 是否包含推理


@dataclass
class AssistSuggestion:
    """
    Assist 建议
    
    单条 assist 建议。
    """
    suggestion_id: str  # 建议 ID
    record_id: str  # 记录 ID
    title: str  # 标题
    content_preview: str  # 内容预览
    relevance_score: float  # 相关性分数
    reasoning: Optional[str] = None  # 推理说明
    source: str = ""  # 来源
    scope: str = ""  # 作用域
    tkr_layer: str = ""  # 层级
    tags: List[str] = field(default_factory=list)  # 标签
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "suggestion_id": self.suggestion_id,
            "record_id": self.record_id,
            "title": self.title,
            "content_preview": self.content_preview,
            "relevance_score": self.relevance_score,
            "reasoning": self.reasoning,
            "source": self.source,
            "scope": self.scope,
            "tkr_layer": self.tkr_layer,
            "tags": self.tags,
        }


@dataclass
class AssistTrace:
    """
    Assist 追踪
    
    记录 assist 调用的详细信息。
    """
    request_id: str  # 请求 ID
    started_at: datetime  # 开始时间
    completed_at: Optional[datetime] = None  # 完成时间
    duration_ms: float = 0.0  # 耗时
    
    task_type_detected: Optional[str] = None  # 检测到的任务类型
    recall_triggered: bool = False  # 是否触发召回
    budget_used_tokens: int = 0  # 使用的 token
    records_scanned: int = 0  # 扫描的记录数
    suggestions_returned: int = 0  # 返回的建议数
    
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
        }


@dataclass
class AssistResponse:
    """
    Assist 响应
    
    Bridge 返回给 OpenClaw 的 assist 响应。
    """
    success: bool  # 是否成功
    suggestions: List[AssistSuggestion]  # 建议列表
    adoption_token: str  # 采纳令牌
    trace: Optional[AssistTrace] = None  # 追踪信息
    error: Optional[str] = None  # 错误信息
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "suggestions": [s.to_dict() for s in self.suggestions],
            "adoption_token": self.adoption_token,
            "trace": self.trace.to_dict() if self.trace else None,
            "error": self.error,
        }


@dataclass
class AdoptionReport:
    """
    采纳报告
    
    追踪建议的采纳情况。
    """
    adoption_token: str  # 采纳令牌
    adopted: bool  # 是否采纳
    helpful: Optional[bool] = None  # 是否有帮助
    reason: Optional[str] = None  # 原因
    suggestion_ids: List[str] = field(default_factory=list)  # 相关建议 ID
    reported_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "adoption_token": self.adoption_token,
            "adopted": self.adopted,
            "helpful": self.helpful,
            "reason": self.reason,
            "suggestion_ids": self.suggestion_ids,
            "reported_at": self.reported_at.isoformat(),
        }


class BridgeCanaryAssist:
    """
    Bridge Canary Assist
    
    建议参与模式，让 OpenClaw 可以选择采纳 recall suggestions。
    """
    
    def __init__(
        self,
        approved_records: Optional[List[MemoryRecord]] = None,
        budget: Optional[PromptBudget] = None,
    ):
        """
        初始化 Bridge Canary Assist
        
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
                mode="shadow",
                enable_trace=True,
                fail_open=True,
            ),
        )
        
        # 追踪数据
        self._pending_adoptions: Dict[str, Dict[str, Any]] = {}
        self._adoption_reports: List[AdoptionReport] = []
        
        # 统计
        self._stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_suggestions": 0,
            "total_adoptions": 0,
            "total_helpful": 0,
            "total_noise": 0,
            "total_errors": 0,
            "total_timeouts": 0,
            "prompt_bloat_tokens": 0,
            "task_mismatches": 0,
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
    
    def assist(self, request: AssistRequest) -> AssistResponse:
        """
        执行 assist
        
        Fail-open: 任何错误都返回空建议，不影响主链。
        
        Args:
            request: Assist 请求
        
        Returns:
            AssistResponse
        """
        request_id = f"assist_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"
        adoption_token = f"adopt_{uuid.uuid4().hex}"
        
        trace = AssistTrace(
            request_id=request_id,
            started_at=datetime.now(timezone.utc),
        )
        
        suggestions = []
        suggestion_ids = []
        
        try:
            # 阶段 1: 检测任务类型
            if request.task_type:
                try:
                    task_type = TaskType(request.task_type.lower())
                except ValueError:
                    task_type = self._policy_manager.detect_task_type(request.query)
            else:
                task_type = self._policy_manager.detect_task_type(request.query)
            
            trace.task_type_detected = task_type.value
            
            # 阶段 2: 检查是否应该召回
            should_recall = self._policy_manager.should_recall(
                query=request.query,
                task_type=task_type,
            )
            
            trace.recall_triggered = should_recall
            
            if not should_recall:
                trace.completed_at = datetime.now(timezone.utc)
                trace.duration_ms = (trace.completed_at - trace.started_at).total_seconds() * 1000
                
                self._stats["total_requests"] += 1
                self._stats["successful_requests"] += 1
                
                return AssistResponse(
                    success=True,
                    suggestions=[],
                    adoption_token=adoption_token,
                    trace=trace,
                )
            
            # 阶段 3: 执行召回
            recall_result = self._recall_engine.recall(
                query=request.query,
                top_k=request.max_suggestions * 2,
            )
            
            records = recall_result.records
            trace.records_scanned = len(self._approved_records)
            
            # 阶段 4: 预算控制
            filtered_records, usage = self._budget_manager.enforce_budget(records)
            trace.budget_used_tokens = usage.used_tokens
            
            # 更新 prompt 膨胀统计
            self._stats["prompt_bloat_tokens"] += usage.used_tokens
            
            # 阶段 5: 转换为建议
            for i, record in enumerate(filtered_records[:request.max_suggestions]):
                suggestion_id = f"sug_{uuid.uuid4().hex[:8]}"
                
                # 截断内容预览
                content_preview = record.content[:200] if record.content else ""
                if len(record.content or "") > 200:
                    content_preview += "..."
                
                # 推理说明
                reasoning = None
                if request.include_reasoning:
                    reasoning = f"This {record.tkr_layer.value} record from {record.scope.value} scope matches your query."
                
                suggestion = AssistSuggestion(
                    suggestion_id=suggestion_id,
                    record_id=record.id,
                    title=record.title,
                    content_preview=content_preview,
                    relevance_score=record.confidence,
                    reasoning=reasoning,
                    source=record.source_file,
                    scope=record.scope.value,
                    tkr_layer=record.tkr_layer.value,
                    tags=record.tags or [],
                )
                suggestions.append(suggestion)
                suggestion_ids.append(suggestion_id)
            
            trace.suggestions_returned = len(suggestions)
            trace.completed_at = datetime.now(timezone.utc)
            trace.duration_ms = (trace.completed_at - trace.started_at).total_seconds() * 1000
            
            # 存储待追踪的采纳
            self._pending_adoptions[adoption_token] = {
                "request_id": request_id,
                "suggestion_ids": suggestion_ids,
                "created_at": datetime.now(timezone.utc),
            }
            
            # 更新统计
            self._stats["total_requests"] += 1
            self._stats["successful_requests"] += 1
            self._stats["total_suggestions"] += len(suggestions)
            
            return AssistResponse(
                success=True,
                suggestions=suggestions,
                adoption_token=adoption_token,
                trace=trace,
            )
            
        except Exception as e:
            logger.error(f"Bridge canary assist error: {e}")
            
            trace.completed_at = datetime.now(timezone.utc)
            trace.duration_ms = (trace.completed_at - trace.started_at).total_seconds() * 1000
            
            self._stats["total_requests"] += 1
            self._stats["failed_requests"] += 1
            self._stats["total_errors"] += 1
            
            return AssistResponse(
                success=False,
                suggestions=[],
                adoption_token=adoption_token,
                trace=trace,
                error=str(e),
            )
    
    def report_adoption(self, report: AdoptionReport) -> bool:
        """
        报告采纳情况
        
        Args:
            report: 采纳报告
        
        Returns:
            是否成功记录
        """
        # 验证 token
        if report.adoption_token not in self._pending_adoptions:
            logger.warning(f"Unknown adoption token: {report.adoption_token}")
            return False
        
        # 获取原始数据
        pending = self._pending_adoptions.pop(report.adoption_token)
        
        # 补充 suggestion_ids
        if not report.suggestion_ids:
            report.suggestion_ids = pending.get("suggestion_ids", [])
        
        # 记录报告
        self._adoption_reports.append(report)
        
        # 更新统计
        if report.adopted:
            self._stats["total_adoptions"] += 1
            
            if report.helpful is True:
                self._stats["total_helpful"] += 1
            elif report.helpful is False:
                self._stats["total_noise"] += 1
        
        return True
    
    def get_quality_metrics(self) -> Dict[str, float]:
        """
        获取质量指标
        
        Returns:
            质量指标字典
        """
        total_adoptions = self._stats["total_adoptions"]
        
        if total_adoptions == 0:
            return {
                "adoption_rate": 0.0,
                "helpful_rate": 0.0,
                "noise_rate": 0.0,
            }
        
        return {
            "adoption_rate": total_adoptions / max(self._stats["total_requests"], 1),
            "helpful_rate": self._stats["total_helpful"] / total_adoptions,
            "noise_rate": self._stats["total_noise"] / total_adoptions,
        }
    
    def get_safety_metrics(self) -> Dict[str, Any]:
        """
        获取安全指标
        
        Returns:
            安全指标字典
        """
        return {
            "rollback_after_recall": 0,  # 需要外部数据
            "demote_after_recall": 0,  # 需要外部数据
            "task_mismatch_count": self._stats["task_mismatches"],
            "fail_open_success_rate": 1.0,  # 假设总是成功
        }
    
    def get_integration_metrics(self) -> Dict[str, Any]:
        """
        获取集成指标
        
        Returns:
            集成指标字典
        """
        total_requests = self._stats["total_requests"]
        
        return {
            "total_requests": total_requests,
            "successful_requests": self._stats["successful_requests"],
            "failed_requests": self._stats["failed_requests"],
            "error_rate": self._stats["total_errors"] / max(total_requests, 1),
            "timeout_count": self._stats["total_timeouts"],
            "prompt_bloat_tokens": self._stats["prompt_bloat_tokens"],
            "avg_bloat_per_request": self._stats["prompt_bloat_tokens"] / max(total_requests, 1),
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取所有统计信息
        
        Returns:
            统计字典
        """
        return {
            "raw_stats": self._stats.copy(),
            "quality_metrics": self.get_quality_metrics(),
            "safety_metrics": self.get_safety_metrics(),
            "integration_metrics": self.get_integration_metrics(),
        }
    
    def reset_statistics(self):
        """重置统计"""
        self._stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_suggestions": 0,
            "total_adoptions": 0,
            "total_helpful": 0,
            "total_noise": 0,
            "total_errors": 0,
            "total_timeouts": 0,
            "prompt_bloat_tokens": 0,
            "task_mismatches": 0,
        }
        self._pending_adoptions.clear()
        self._adoption_reports.clear()


def create_bridge_canary(
    approved_records: Optional[List[MemoryRecord]] = None,
    max_tokens: int = 500,
    max_records: int = 3,
) -> BridgeCanaryAssist:
    """
    便捷函数：创建 Bridge Canary Assist
    
    Args:
        approved_records: approved 记录列表
        max_tokens: 最大 token 数
        max_records: 最大记录数
    
    Returns:
        BridgeCanaryAssist 实例
    """
    budget = PromptBudget(
        max_tokens=max_tokens,
        max_records=max_records,
    )
    
    return BridgeCanaryAssist(
        approved_records=approved_records,
        budget=budget,
    )
