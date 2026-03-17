"""
Memory Loader - Unified Loading Interface

封装 core/memory/memory_recall.py 和 memory_service.py，提供统一的记忆加载接口。

Author: Memory Runtime
Created: 2026-03-17
Version: 1.0.0
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from pathlib import Path
import sys

# 添加项目根目录到 path
sys.path.insert(0, str(Path(__file__).parent.parent))

# 导入核心实现
from core.memory.memory_recall import (
    RecallConfig,
    RecallResult,
    RecallEngine,
)
from core.memory.memory_service import (
    MemoryService,
    ServiceConfig,
)
from core.memory.memory_search import (
    MemorySearchEngine,
    SearchParams,
)


@dataclass
class LoadConfig:
    """
    加载配置
    
    定义记忆加载行为。
    """
    agent_id: str = "default"
    memory_root: Optional[Path] = None
    scopes: List[str] = field(default_factory=lambda: ["global"])
    top_k: int = 10
    include_handoff: bool = True
    include_execution_state: bool = True
    include_instruction_rules: bool = True
    fail_open: bool = True
    enable_trace: bool = True


@dataclass
class LoadResult:
    """
    加载结果
    
    包含加载的记忆和状态。
    """
    success: bool
    long_term_memory: List[Dict[str, Any]] = field(default_factory=list)
    handoff_state: Optional[Dict[str, Any]] = None
    execution_state: Optional[Dict[str, Any]] = None
    instruction_rules: Optional[Dict[str, Any]] = None
    trace_id: Optional[str] = None
    error: Optional[str] = None


class MemoryLoader:
    """
    记忆加载器
    
    统一的记忆加载入口，整合：
    - 长期记忆加载 (core/memory/memory_recall.py)
    - Handoff 状态加载
    - Execution 状态加载
    - 指令规则加载
    """
    
    def __init__(self, config: Optional[LoadConfig] = None):
        self.config = config or LoadConfig()
        self._service: Optional[MemoryService] = None
        self._recall_engine: Optional[RecallEngine] = None
    
    def _ensure_service(self) -> MemoryService:
        """延迟初始化 MemoryService"""
        if self._service is None:
            service_config = ServiceConfig(
                default_top_k=self.config.top_k,
                enable_trace=self.config.enable_trace,
            )
            self._service = MemoryService(config=service_config)
        return self._service
    
    def load_long_term_memory(self, query: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        加载长期记忆
        
        Args:
            query: 可选的查询字符串
        
        Returns:
            记忆记录列表
        """
        service = self._ensure_service()
        
        # 构建搜索参数
        params = SearchParams(
            query=query or "",
            scopes=self.config.scopes,
            top_k=self.config.top_k,
        )
        
        # 执行搜索
        result = service.search(params)
        
        return [r.to_dict() for r in result.records]
    
    def load_handoff_state(self) -> Optional[Dict[str, Any]]:
        """
        加载 handoff 状态
        
        Returns:
            Handoff 状态字典
        """
        from memory_runtime.handoff_manager import HandoffManager
        
        manager = HandoffManager(
            agent_id=self.config.agent_id,
            memory_root=self.config.memory_root,
        )
        
        return manager.load()
    
    def load_execution_state(self) -> Optional[Dict[str, Any]]:
        """
        加载执行状态
        
        Returns:
            执行状态字典
        """
        from memory_runtime.execution_state_manager import ExecutionStateManager
        
        manager = ExecutionStateManager(
            agent_id=self.config.agent_id,
            memory_root=self.config.memory_root,
        )
        
        return manager.load()
    
    def load_instruction_rules(self) -> Optional[Dict[str, Any]]:
        """
        加载指令规则
        
        Returns:
            指令规则字典
        """
        from memory_runtime.instruction_rules_resolver import InstructionRulesResolver
        
        resolver = InstructionRulesResolver(
            agent_id=self.config.agent_id,
            memory_root=self.config.memory_root,
        )
        
        return resolver.load_rules()
    
    def load_all(self, query: Optional[str] = None) -> LoadResult:
        """
        加载所有记忆
        
        按顺序加载：
        1. instruction_rules (先读规则)
        2. long_term_memory (补背景)
        3. handoff_state (恢复工作交接点)
        4. execution_state (恢复临时运行位置)
        
        Args:
            query: 可选的查询字符串
        
        Returns:
            LoadResult 包含所有加载的记忆
        """
        result = LoadResult(success=True)
        
        try:
            # 1. 指令规则（优先）
            if self.config.include_instruction_rules:
                result.instruction_rules = self.load_instruction_rules()
            
            # 2. 长期记忆
            result.long_term_memory = self.load_long_term_memory(query)
            
            # 3. Handoff 状态
            if self.config.include_handoff:
                result.handoff_state = self.load_handoff_state()
            
            # 4. 执行状态
            if self.config.include_execution_state:
                result.execution_state = self.load_execution_state()
                
        except Exception as e:
            result.success = False
            result.error = str(e)
            
            if not self.config.fail_open:
                raise
        
        return result


# 便捷函数
def load_memory(
    agent_id: str = "default",
    query: Optional[str] = None,
    **kwargs
) -> LoadResult:
    """
    便捷的记忆加载函数
    
    Args:
        agent_id: Agent ID
        query: 可选的查询字符串
        **kwargs: 其他 LoadConfig 参数
    
    Returns:
        LoadResult
    """
    config = LoadConfig(agent_id=agent_id, **kwargs)
    loader = MemoryLoader(config)
    return loader.load_all(query)
