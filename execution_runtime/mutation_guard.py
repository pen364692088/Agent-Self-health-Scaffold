"""
Mutation Guard - Mutation Constraint and Audit

变更约束与审计，封装 runtime/mutation_gate.py。

Author: Execution Runtime
Created: 2026-03-17
Version: 1.0.0
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Set
from pathlib import Path
import sys
import hashlib
from datetime import datetime, timezone
from enum import Enum

# 添加项目根目录到 path
sys.path.insert(0, str(Path(__file__).parent.parent))


class MutationType(str, Enum):
    """变更类型"""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    MOVE = "move"
    COPY = "copy"


class MutationDecision(str, Enum):
    """变更决策"""
    ALLOW = "allow"
    BLOCK = "block"
    WARN = "warn"
    REQUIRE_APPROVAL = "require_approval"


@dataclass
class MutationConfig:
    """
    Mutation Guard 配置
    """
    agent_id: str = "default"
    allow_create: bool = True
    allow_update: bool = True
    allow_delete: bool = False
    require_evidence: bool = True
    protected_paths: List[Path] = field(default_factory=list)
    protected_patterns: List[str] = field(default_factory=lambda: ["*.env", "*.key", "*.secret"])


@dataclass
class MutationResult:
    """
    Mutation 检查结果
    """
    decision: MutationDecision
    mutation_type: MutationType
    target: Path
    reason: Optional[str] = None
    evidence_id: Optional[str] = None
    warnings: List[str] = field(default_factory=list)


class MutationGuard:
    """
    变更守卫
    
    负责：
    - 变更约束检查
    - 保护路径检查
    - 变更审计
    - 证据记录
    """
    
    def __init__(self, config: Optional[MutationConfig] = None):
        self.config = config or MutationConfig()
        self._mutations: List[Dict[str, Any]] = []
    
    def check(
        self,
        mutation_type: MutationType,
        target: Path,
        content: Optional[str] = None,
    ) -> MutationResult:
        """
        检查变更
        
        Args:
            mutation_type: 变更类型
            target: 目标路径
            content: 变更内容
        
        Returns:
            MutationResult
        """
        warnings = []
        
        # 1. 检查类型权限
        if mutation_type == MutationType.CREATE and not self.config.allow_create:
            return MutationResult(
                decision=MutationDecision.BLOCK,
                mutation_type=mutation_type,
                target=target,
                reason="CREATE not allowed",
            )
        
        if mutation_type == MutationType.UPDATE and not self.config.allow_update:
            return MutationResult(
                decision=MutationDecision.BLOCK,
                mutation_type=mutation_type,
                target=target,
                reason="UPDATE not allowed",
            )
        
        if mutation_type == MutationType.DELETE and not self.config.allow_delete:
            return MutationResult(
                decision=MutationDecision.BLOCK,
                mutation_type=mutation_type,
                target=target,
                reason="DELETE not allowed",
            )
        
        # 2. 检查保护路径
        for protected in self.config.protected_paths:
            if target.resolve().is_relative_to(protected.resolve()):
                return MutationResult(
                    decision=MutationDecision.BLOCK,
                    mutation_type=mutation_type,
                    target=target,
                    reason=f"Protected path: {protected}",
                )
        
        # 3. 检查保护模式
        for pattern in self.config.protected_patterns:
            if target.match(pattern):
                warnings.append(f"Matches protected pattern: {pattern}")
        
        # 4. 检查指令规则
        from memory_runtime.instruction_rules_resolver import InstructionRulesResolver
        
        resolver = InstructionRulesResolver(agent_id=self.config.agent_id)
        rule_set = resolver.load_rule_set()
        
        allowed, reason = rule_set.check_constraint(
            action=mutation_type.value,
            context={"target": str(target)},
        )
        
        if not allowed:
            return MutationResult(
                decision=MutationDecision.BLOCK,
                mutation_type=mutation_type,
                target=target,
                reason=reason,
            )
        
        # 5. 记录证据
        evidence_id = None
        if self.config.require_evidence:
            evidence_id = self._record_evidence(mutation_type, target, content)
        
        # 6. 记录变更
        self._mutations.append({
            "type": mutation_type.value,
            "target": str(target),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "evidence_id": evidence_id,
        })
        
        return MutationResult(
            decision=MutationDecision.ALLOW,
            mutation_type=mutation_type,
            target=target,
            evidence_id=evidence_id,
            warnings=warnings,
        )
    
    def _record_evidence(
        self,
        mutation_type: MutationType,
        target: Path,
        content: Optional[str],
    ) -> str:
        """记录证据"""
        from memory_runtime.evidence_logger import EvidenceLogger
        
        logger = EvidenceLogger(agent_id=self.config.agent_id)
        
        content_hash = hashlib.sha256((content or "").encode()).hexdigest()[:16]
        
        record = logger.log_write(
            target=str(target),
            content_hash=content_hash,
            category=mutation_type.value,
        )
        
        return record.evidence_id
    
    def get_mutations(self) -> List[Dict[str, Any]]:
        """获取变更历史"""
        return self._mutations.copy()
    
    def clear_history(self):
        """清除变更历史"""
        self._mutations.clear()
    
    def check_create(self, target: Path, content: Optional[str] = None) -> MutationResult:
        """检查创建"""
        return self.check(MutationType.CREATE, target, content)
    
    def check_update(self, target: Path, content: Optional[str] = None) -> MutationResult:
        """检查更新"""
        return self.check(MutationType.UPDATE, target, content)
    
    def check_delete(self, target: Path) -> MutationResult:
        """检查删除"""
        return self.check(MutationType.DELETE, target)


# 便捷函数
def check_mutation(
    mutation_type: str,
    target: Path,
    agent_id: str = "default",
    **kwargs
) -> MutationResult:
    """
    便捷的变更检查函数
    
    Args:
        mutation_type: 变更类型
        target: 目标路径
        agent_id: Agent ID
        **kwargs: 其他 MutationConfig 参数
    
    Returns:
        MutationResult
    """
    config = MutationConfig(agent_id=agent_id, **kwargs)
    guard = MutationGuard(config)
    
    mt = MutationType(mutation_type)
    return guard.check(mt, target)
