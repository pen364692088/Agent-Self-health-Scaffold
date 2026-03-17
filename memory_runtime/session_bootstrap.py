"""
Session Bootstrap - Session Startup Memory Recovery

新会话启动时的记忆恢复入口。

Author: Memory Runtime
Created: 2026-03-17
Version: 1.0.0
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from pathlib import Path
from datetime import datetime, timezone


@dataclass
class BootstrapConfig:
    """
    Bootstrap 配置
    """
    agent_id: str = "default"
    memory_root: Optional[Path] = None
    load_instruction_rules: bool = True
    load_long_term_memory: bool = True
    load_handoff: bool = True
    load_execution_state: bool = True
    query: Optional[str] = None


@dataclass
class BootstrapResult:
    """
    Bootstrap 结果
    """
    success: bool
    agent_id: str
    instruction_rules: Optional[Dict[str, Any]] = None
    long_term_memory: List[Dict[str, Any]] = field(default_factory=list)
    handoff_state: Optional[Dict[str, Any]] = None
    execution_state: Optional[Dict[str, Any]] = None
    bootstrap_time: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    errors: List[str] = field(default_factory=list)
    
    def to_summary(self) -> str:
        """生成摘要"""
        lines = [f"## Bootstrap Summary ({self.agent_id})"]
        lines.append(f"Time: {self.bootstrap_time}")
        lines.append(f"Status: {'✅ Success' if self.success else '❌ Failed'}")
        
        if self.instruction_rules:
            rule_count = self.instruction_rules.get("rule_count", 0)
            lines.append(f"Rules: {rule_count} loaded")
        
        if self.long_term_memory:
            lines.append(f"Memory: {len(self.long_term_memory)} records")
        
        if self.handoff_state:
            lines.append("Handoff: ✅ Recovered")
        else:
            lines.append("Handoff: No state")
        
        if self.execution_state:
            lines.append(f"Execution: {self.execution_state.get('status', 'unknown')}")
        
        if self.errors:
            lines.append(f"\nErrors: {len(self.errors)}")
            for err in self.errors[:3]:
                lines.append(f"- {err}")
        
        return "\n".join(lines)


class SessionBootstrap:
    """
    会话启动引导
    
    负责：
    - 按顺序加载所有记忆
    - 生成启动摘要
    - 验证加载结果
    """
    
    def __init__(self, config: Optional[BootstrapConfig] = None, **kwargs):
        # 支持直接传参
        if config is None:
            config = BootstrapConfig(
                agent_id=kwargs.get("agent_id", "default"),
                memory_root=kwargs.get("memory_root"),
            )
        self.config = config
    
    def run(self) -> BootstrapResult:
        """
        执行启动引导
        
        加载顺序（强制）：
        1. instruction_rules → 确保后续恢复和执行受长期红线约束
        2. long_term_memory → 补背景
        3. handoff_state → 恢复工作交接点
        4. execution_state → 恢复临时运行位置
        
        Returns:
            BootstrapResult
        """
        result = BootstrapResult(
            success=True,
            agent_id=self.config.agent_id,
        )
        
        # 1. 指令规则（优先）
        if self.config.load_instruction_rules:
            try:
                from memory_runtime.instruction_rules_resolver import InstructionRulesResolver
                
                resolver = InstructionRulesResolver(
                    agent_id=self.config.agent_id,
                    memory_root=self.config.memory_root,
                )
                result.instruction_rules = resolver.load_rules()
                
            except Exception as e:
                result.errors.append(f"Failed to load instruction rules: {e}")
        
        # 2. 长期记忆
        if self.config.load_long_term_memory:
            try:
                from memory_runtime.memory_loader import MemoryLoader, LoadConfig
                
                loader = MemoryLoader(LoadConfig(
                    agent_id=self.config.agent_id,
                    memory_root=self.config.memory_root,
                    include_handoff=False,
                    include_execution_state=False,
                    include_instruction_rules=False,
                ))
                load_result = loader.load_all(self.config.query)
                result.long_term_memory = load_result.long_term_memory
                
            except Exception as e:
                result.errors.append(f"Failed to load long-term memory: {e}")
        
        # 3. Handoff 状态
        if self.config.load_handoff:
            try:
                from memory_runtime.handoff_manager import HandoffManager
                
                manager = HandoffManager(
                    agent_id=self.config.agent_id,
                    memory_root=self.config.memory_root,
                )
                result.handoff_state = manager.load()
                
            except Exception as e:
                result.errors.append(f"Failed to load handoff state: {e}")
        
        # 4. 执行状态
        if self.config.load_execution_state:
            try:
                from memory_runtime.execution_state_manager import ExecutionStateManager
                
                manager = ExecutionStateManager(
                    agent_id=self.config.agent_id,
                    memory_root=self.config.memory_root,
                )
                result.execution_state = manager.load()
                
            except Exception as e:
                result.errors.append(f"Failed to load execution state: {e}")
        
        # 确定成功状态
        # 指令规则加载失败视为严重错误
        if result.errors and not result.instruction_rules:
            result.success = False
        
        return result
    
    def quick_bootstrap(self) -> str:
        """
        快速启动引导
        
        Returns:
            启动摘要
        """
        result = self.run()
        return result.to_summary()


# 便捷函数
def bootstrap(
    agent_id: str = "default",
    query: Optional[str] = None,
    **kwargs
) -> BootstrapResult:
    """
    便捷的启动引导函数
    
    Args:
        agent_id: Agent ID
        query: 可选的查询字符串
        **kwargs: 其他 BootstrapConfig 参数
    
    Returns:
        BootstrapResult
    """
    config = BootstrapConfig(agent_id=agent_id, query=query, **kwargs)
    bootstrap = SessionBootstrap(config)
    return bootstrap.run()
