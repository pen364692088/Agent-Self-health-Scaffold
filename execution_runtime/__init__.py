"""
Execution Runtime - Unified Execution Layer

提供所有 Agent 的可靠任务执行能力。

模块职责：
- task_runtime: 任务生命周期管理
- preflight: 执行前检查（memory、repo、state）
- mutation_guard: 变更约束与审计
- canonical_guard: 仓库/路径/状态源验证
- retry: 重试策略管理
- receipt: 执行凭证与审计

Author: Execution Runtime
Created: 2026-03-17
Version: 1.0.0
"""

# 核心执行接口
from execution_runtime.task_runtime import (
    TaskRuntime,
    TaskConfig,
    TaskResult,
)
from execution_runtime.preflight import (
    PreflightChecker,
    PreflightConfig,
    PreflightResult,
)
from execution_runtime.mutation_guard import (
    MutationGuard,
    MutationConfig,
    MutationResult,
)
from execution_runtime.canonical_guard import (
    CanonicalGuard,
    CanonicalConfig,
    CanonicalResult,
)
from execution_runtime.retry import (
    RetryManager,
    RetryConfig,
    RetryResult,
)
from execution_runtime.receipt import (
    ReceiptManager,
    ReceiptConfig,
    ExecutionReceipt,
)

__all__ = [
    # Task Runtime
    "TaskRuntime",
    "TaskConfig",
    "TaskResult",
    # Preflight
    "PreflightChecker",
    "PreflightConfig",
    "PreflightResult",
    # Mutation Guard
    "MutationGuard",
    "MutationConfig",
    "MutationResult",
    # Canonical Guard
    "CanonicalGuard",
    "CanonicalConfig",
    "CanonicalResult",
    # Retry
    "RetryManager",
    "RetryConfig",
    "RetryResult",
    # Receipt
    "ReceiptManager",
    "ReceiptConfig",
    "ExecutionReceipt",
]
