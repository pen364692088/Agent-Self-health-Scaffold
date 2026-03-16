"""
OpenClaw Bridge Mainline Limited

有限主链 assist，仅限指定任务类型和入口。

Author: Memory Kernel
Created: 2026-03-16
Version: 1.0.0
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Set
from datetime import datetime, timezone, timedelta
from pathlib import Path
import time
import logging
import uuid

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


# Allowed task types for mainline assist
ALLOWED_TASK_TYPES: Set[str] = {
    "coding",
    "decision",
    "question",
}

# Task type budgets
TASK_TYPE_BUDGETS: Dict[str, int] = {
    "coding": 800,
    "decision": 600,
    "question": 400,
}


@dataclass
class MainlineAssistRequest:
    """
    Mainline Assist 请求
    
    定义主链 assist 请求。
    """
    query: str  # 用户查询
    session_id: str  # 会话 ID（用于限流）
    task_type: str  # 任务类型
    max_suggestions: int = 3  # 最大建议数
    format: str = "block"  # 输出格式: block, list, markdown


@dataclass
class MainlineSuggestion:
    """
    Mainline 建议
    
    单条 mainline 建议。
    """
    suggestion_id: str
    record_id: str
    title: str
    content_preview: str
    relevance_score: float
    tkr_layer: str
    scope: str
    source: str
    
    def to_markdown(self, index: int) -> str:
        """转换为 markdown 格式"""
        return f"{index}. [{self.title}] ({self.tkr_layer.capitalize()} | {self.scope.capitalize()})\n   {self.content_preview}\n   Relevance: {self.relevance_score:.2f}"


@dataclass
class MainlineMetrics:
    """
    Mainline 指标
    
    追踪 mainline assist 的指标。
    """
    session_requests: int = 0  # 会话请求数
    session_tokens_used: int = 0  # 会话 token 使用
    total_requests: int = 0  # 总请求数
    allowed_requests: int = 0  # 允许的请求数
    denied_requests: int = 0  # 拒绝的请求数
    rate_limit_hits: int = 0  # 限流触发次数
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "session_requests": self.session_requests,
            "session_tokens_used": self.session_tokens_used,
            "total_requests": self.total_requests,
            "allowed_requests": self.allowed_requests,
            "denied_requests": self.denied_requests,
            "rate_limit_hits": self.rate_limit_hits,
        }


@dataclass
class MainlineAssistResponse:
    """
    Mainline Assist 响应
    
    Bridge 返回给主链的响应。
    """
    success: bool  # 是否成功
    allowed: bool  # 是否允许 assist
    suggestion_block: Optional[str] = None  # 格式化的建议块
    suggestions: List[MainlineSuggestion] = field(default_factory=list)
    metrics: Optional[MainlineMetrics] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "allowed": self.allowed,
            "suggestion_block": self.suggestion_block,
            "suggestions": [
                {
                    "suggestion_id": s.suggestion_id,
                    "title": s.title,
                    "relevance_score": s.relevance_score,
                }
                for s in self.suggestions
            ],
            "metrics": self.metrics.to_dict() if self.metrics else None,
            "error": self.error,
        }


@dataclass
class SessionState:
    """
    会话状态
    
    追踪单个会话的使用情况。
    """
    session_id: str
    request_count: int = 0
    tokens_used: int = 0
    last_request: Optional[datetime] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class BridgeMainlineLimited:
    """
    Bridge Mainline Limited
    
    有限主链 assist，仅限指定任务类型和入口。
    """
    
    def __init__(
        self,
        approved_records: Optional[List[MemoryRecord]] = None,
        max_requests_per_session: int = 10,
        max_tokens_per_session: int = 5000,
    ):
        """
        初始化 Bridge Mainline Limited
        
        Args:
            approved_records: approved 记录列表
            max_requests_per_session: 每会话最大请求数
            max_tokens_per_session: 每会话最大 token 数
        """
        self._approved_records = approved_records or []
        self._approved_ids = {r.id for r in self._approved_records}
        
        self._max_requests_per_session = max_requests_per_session
        self._max_tokens_per_session = max_tokens_per_session
        
        # 初始化组件
        self._policy_manager = RecallPolicyManager()
        self._policy_manager.set_approved_ids(self._approved_ids)
        
        self._recall_engine = RecallEngine(
            approved_records=self._approved_records,
            config=RecallConfig(
                mode="shadow",
                enable_trace=True,
                fail_open=True,
            ),
        )
        
        # 会话状态
        self._session_states: Dict[str, SessionState] = {}
        
        # 全局指标
        self._global_metrics = MainlineMetrics()
        
        # 统计
        self._stats = {
            "total_requests": 0,
            "allowed_requests": 0,
            "denied_requests": 0,
            "task_type_denied": 0,
            "rate_limit_denied": 0,
            "total_suggestions": 0,
            "total_adoptions": 0,
            "quality_improvements": 0,
            "noise_reports": 0,
            "fail_open_count": 0,
            "errors": 0,
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
    
    def _get_or_create_session(self, session_id: str) -> SessionState:
        """
        获取或创建会话状态
        
        Args:
            session_id: 会话 ID
        
        Returns:
            SessionState
        """
        if session_id not in self._session_states:
            self._session_states[session_id] = SessionState(session_id=session_id)
        return self._session_states[session_id]
    
    def _check_rate_limit(self, session: SessionState) -> tuple[bool, str]:
        """
        检查限流
        
        Args:
            session: 会话状态
        
        Returns:
            (allowed, reason)
        """
        # 检查请求数
        if session.request_count >= self._max_requests_per_session:
            return False, f"Max requests ({self._max_requests_per_session}) reached"
        
        # 检查 token 数
        if session.tokens_used >= self._max_tokens_per_session:
            return False, f"Max tokens ({self._max_tokens_per_session}) reached"
        
        return True, ""
    
    def _is_task_type_allowed(self, task_type: str) -> bool:
        """
        检查任务类型是否允许
        
        Args:
            task_type: 任务类型
        
        Returns:
            是否允许
        """
        return task_type.lower() in ALLOWED_TASK_TYPES
    
    def _get_budget_for_task(self, task_type: str) -> int:
        """
        获取任务类型的预算
        
        Args:
            task_type: 任务类型
        
        Returns:
            token 预算
        """
        return TASK_TYPE_BUDGETS.get(task_type.lower(), 0)
    
    def _format_suggestion_block(
        self,
        suggestions: List[MainlineSuggestion],
    ) -> str:
        """
        格式化建议块
        
        Args:
            suggestions: 建议列表
        
        Returns:
            格式化的建议块
        """
        if not suggestions:
            return ""
        
        lines = [
            "---",
            "📚 Memory Suggestions (Limited Mainline)",
            ""
        ]
        
        for i, s in enumerate(suggestions, 1):
            lines.append(s.to_markdown(i))
            lines.append("")
        
        lines.extend([
            "---",
            "Note: These are suggestions from the memory kernel. Use at your discretion.",
        ])
        
        return "\n".join(lines)
    
    def assist(self, request: MainlineAssistRequest) -> MainlineAssistResponse:
        """
        执行 mainline assist
        
        Fail-open: 任何错误都返回空建议，不影响主链。
        
        Args:
            request: Mainline assist 请求
        
        Returns:
            MainlineAssistResponse
        """
        self._stats["total_requests"] += 1
        self._global_metrics.total_requests += 1
        
        # 创建指标
        metrics = MainlineMetrics()
        metrics.total_requests = self._global_metrics.total_requests
        
        suggestions = []
        suggestion_block = None
        
        try:
            # 1. 检查任务类型
            if not self._is_task_type_allowed(request.task_type):
                self._stats["denied_requests"] += 1
                self._stats["task_type_denied"] += 1
                self._global_metrics.denied_requests += 1
                metrics.denied_requests = self._global_metrics.denied_requests
                
                return MainlineAssistResponse(
                    success=True,
                    allowed=False,
                    suggestion_block=None,
                    suggestions=[],
                    metrics=metrics,
                    error=f"Task type '{request.task_type}' not allowed for mainline assist",
                )
            
            # 2. 获取会话状态
            session = self._get_or_create_session(request.session_id)
            
            # 3. 检查限流
            allowed, reason = self._check_rate_limit(session)
            if not allowed:
                self._stats["denied_requests"] += 1
                self._stats["rate_limit_denied"] += 1
                self._global_metrics.denied_requests += 1
                self._global_metrics.rate_limit_hits += 1
                metrics.denied_requests = self._global_metrics.denied_requests
                metrics.rate_limit_hits = self._global_metrics.rate_limit_hits
                
                return MainlineAssistResponse(
                    success=True,
                    allowed=False,
                    suggestion_block=None,
                    suggestions=[],
                    metrics=metrics,
                    error=f"Rate limit exceeded: {reason}",
                )
            
            # 4. 获取预算
            budget_tokens = self._get_budget_for_task(request.task_type)
            
            # 5. 执行召回
            recall_result = self._recall_engine.recall(
                query=request.query,
                top_k=request.max_suggestions * 2,
            )
            
            records = recall_result.records
            
            # 6. 预算控制
            budget = PromptBudget(max_tokens=budget_tokens, max_records=request.max_suggestions)
            budget_manager = BudgetManager(budget=budget)
            
            filtered_records, usage = budget_manager.enforce_budget(records)
            
            # 7. 更新会话状态
            session.request_count += 1
            session.tokens_used += usage.used_tokens
            session.last_request = datetime.now(timezone.utc)
            
            # 8. 更新指标
            self._stats["allowed_requests"] += 1
            self._global_metrics.allowed_requests += 1
            metrics.session_requests = session.request_count
            metrics.session_tokens_used = session.tokens_used
            metrics.allowed_requests = self._global_metrics.allowed_requests
            
            # 9. 转换为建议
            for record in filtered_records:
                suggestion_id = f"mainline_{uuid.uuid4().hex[:8]}"
                
                content_preview = record.content[:150] if record.content else ""
                if len(record.content or "") > 150:
                    content_preview += "..."
                
                suggestion = MainlineSuggestion(
                    suggestion_id=suggestion_id,
                    record_id=record.id,
                    title=record.title,
                    content_preview=content_preview,
                    relevance_score=record.confidence,
                    tkr_layer=record.tkr_layer.value,
                    scope=record.scope.value,
                    source=record.source_file,
                )
                suggestions.append(suggestion)
            
            # 10. 格式化建议块
            if suggestions and request.format == "block":
                suggestion_block = self._format_suggestion_block(suggestions)
            
            self._stats["total_suggestions"] += len(suggestions)
            
            return MainlineAssistResponse(
                success=True,
                allowed=True,
                suggestion_block=suggestion_block,
                suggestions=suggestions,
                metrics=metrics,
            )
            
        except Exception as e:
            logger.error(f"Bridge mainline assist error: {e}")
            
            self._stats["fail_open_count"] += 1
            self._stats["errors"] += 1
            
            return MainlineAssistResponse(
                success=True,  # Fail-open: 返回成功但无建议
                allowed=True,  # 允许但无内容
                suggestion_block=None,
                suggestions=[],
                metrics=metrics,
                error=str(e),
            )
    
    def report_adoption(
        self,
        suggestion_ids: List[str],
        adopted: bool,
        helpful: Optional[bool] = None,
        quality_improved: Optional[bool] = None,
    ):
        """
        报告采纳情况
        
        Args:
            suggestion_ids: 建议 ID 列表
            adopted: 是否采纳
            helpful: 是否有帮助
            quality_improved: 质量是否提升
        """
        if adopted:
            self._stats["total_adoptions"] += 1
            
            if helpful is True:
                pass  # Positive signal
            elif helpful is False:
                self._stats["noise_reports"] += 1
            
            if quality_improved is True:
                self._stats["quality_improvements"] += 1
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            统计字典
        """
        total_allowed = self._stats["allowed_requests"]
        total_adoptions = self._stats["total_adoptions"]
        
        adoption_rate = total_adoptions / max(total_allowed, 1)
        noise_rate = self._stats["noise_reports"] / max(total_adoptions, 1)
        quality_improvement_rate = self._stats["quality_improvements"] / max(total_adoptions, 1)
        
        return {
            "raw_stats": self._stats.copy(),
            "quality_metrics": {
                "adoption_rate": adoption_rate,
                "quality_improvement_rate": quality_improvement_rate,
                "noise_rate": noise_rate,
            },
            "safety_metrics": {
                "fail_open_success_rate": 1.0,  # Always succeeds
                "rate_limit_effective": self._stats["rate_limit_denied"] > 0,
            },
            "integration_metrics": {
                "total_requests": self._stats["total_requests"],
                "allowed_requests": total_allowed,
                "denied_requests": self._stats["denied_requests"],
                "task_type_denied": self._stats["task_type_denied"],
                "rate_limit_denied": self._stats["rate_limit_denied"],
            },
            "active_sessions": len(self._session_states),
        }
    
    def reset_session(self, session_id: str):
        """
        重置会话状态
        
        Args:
            session_id: 会话 ID
        """
        if session_id in self._session_states:
            del self._session_states[session_id]
    
    def reset_all_sessions(self):
        """重置所有会话状态"""
        self._session_states.clear()


def create_bridge_mainline(
    approved_records: Optional[List[MemoryRecord]] = None,
    max_requests_per_session: int = 10,
    max_tokens_per_session: int = 5000,
) -> BridgeMainlineLimited:
    """
    便捷函数：创建 Bridge Mainline Limited
    
    Args:
        approved_records: approved 记录列表
        max_requests_per_session: 每会话最大请求数
        max_tokens_per_session: 每会话最大 token 数
    
    Returns:
        BridgeMainlineLimited 实例
    """
    return BridgeMainlineLimited(
        approved_records=approved_records,
        max_requests_per_session=max_requests_per_session,
        max_tokens_per_session=max_tokens_per_session,
    )
