"""
Memory Runtime - Unified Memory Layer

提供所有 Agent 的持久化记忆与记忆恢复能力。

模块职责：
- session_bootstrap: 新会话启动时的记忆加载入口
- memory_loader: 加载长期记忆、handoff、execution_state
- memory_writer: 写回记忆、状态、handoff
- instruction_rules_resolver: 解析长期指令规则
- handoff_manager: 管理会话交接状态
- execution_state_manager: 管理运行时执行状态
- evidence_logger: 记录记忆操作证据链

Author: Memory Runtime
Created: 2026-03-17
Version: 1.0.0
"""

# 核心加载/写入接口
from memory_runtime.memory_loader import (
    MemoryLoader,
    LoadConfig,
    LoadResult,
)
from memory_runtime.memory_writer import (
    MemoryWriter,
    WriteConfig,
    WriteResult,
)

# 会话管理
from memory_runtime.session_bootstrap import (
    SessionBootstrap,
    BootstrapConfig,
    BootstrapResult,
)
from memory_runtime.handoff_manager import (
    HandoffManager,
    HandoffConfig,
)
from memory_runtime.execution_state_manager import (
    ExecutionStateManager,
    ExecutionStateConfig,
)

# 规则解析
from memory_runtime.instruction_rules_resolver import (
    InstructionRulesResolver,
    RuleConfig,
    RuleSet,
)

# 证据链
from memory_runtime.evidence_logger import (
    EvidenceLogger,
    EvidenceConfig,
    EvidenceRecord,
)

__all__ = [
    # Loader
    "MemoryLoader",
    "LoadConfig",
    "LoadResult",
    # Writer
    "MemoryWriter",
    "WriteConfig",
    "WriteResult",
    # Bootstrap
    "SessionBootstrap",
    "BootstrapConfig",
    "BootstrapResult",
    # Handoff
    "HandoffManager",
    "HandoffConfig",
    # Execution State
    "ExecutionStateManager",
    "ExecutionStateConfig",
    # Rules
    "InstructionRulesResolver",
    "RuleConfig",
    "RuleSet",
    # Evidence
    "EvidenceLogger",
    "EvidenceConfig",
    "EvidenceRecord",
]
