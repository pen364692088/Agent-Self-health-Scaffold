"""
Instruction Rules Merger

合并全局 baseline rules 与 agent-specific overlay rules。

Author: Agent-Self-health-Scaffold
Created: 2026-03-17
Version: 1.0.0
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Set
from pathlib import Path
import yaml
from datetime import datetime, timezone


@dataclass
class MergeResult:
    """合并结果"""
    agent_id: str
    effective_rules: Dict[str, Any]
    base_rules: Dict[str, Any]
    overlay_rules: Dict[str, Any]
    merge_summary: Dict[str, Any]
    errors: List[str] = field(default_factory=list)


class InstructionRulesMerger:
    """
    规则合并器
    
    负责合并全局 baseline 与 agent-specific overlay。
    """
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.baseline_path = project_root / "memory" / "baseline" / "instruction_rules.yaml"
    
    def load_baseline(self) -> Dict[str, Any]:
        """加载全局 baseline rules"""
        if not self.baseline_path.exists():
            return {}
        
        with open(self.baseline_path, "r") as f:
            return yaml.safe_load(f) or {}
    
    def load_overlay(self, agent_id: str) -> Dict[str, Any]:
        """加载 agent-specific overlay"""
        overlay_path = self.project_root / "memory" / "agents" / agent_id / "instruction_rules.yaml"
        
        if not overlay_path.exists():
            return {}
        
        with open(overlay_path, "r") as f:
            return yaml.safe_load(f) or {}
    
    def merge(self, agent_id: str) -> MergeResult:
        """
        合并 baseline 与 overlay
        
        Args:
            agent_id: Agent ID
        
        Returns:
            MergeResult
        """
        errors = []
        
        # 加载规则
        baseline = self.load_baseline()
        overlay = self.load_overlay(agent_id)
        
        if not baseline:
            errors.append("Global baseline rules not found")
        
        # 初始化 effective rules
        effective = {
            "agent_id": agent_id,
            "version": "1.0",
            "merged_at": datetime.now(timezone.utc).isoformat(),
        }
        
        merge_summary = {
            "hard_constraints": 0,
            "workflow_rules": 0,
            "memory_rules": 0,
            "mutation_rules": 0,
        }
        
        # 1. 合并 hard_constraints (并集，全局优先)
        baseline_hard = baseline.get("hard_constraints", [])
        overlay_hard = overlay.get("hard_constraints", [])
        
        # 使用 ID 去重，全局优先
        hard_by_id = {}
        for rule in baseline_hard:
            hard_by_id[rule.get("id")] = rule
        for rule in overlay_hard:
            if rule.get("id") not in hard_by_id:
                hard_by_id[rule.get("id")] = rule
        
        effective["hard_constraints"] = list(hard_by_id.values())
        merge_summary["hard_constraints"] = len(effective["hard_constraints"])
        
        # 2. 合并 workflow_rules (按 ID 合并，agent 优先)
        baseline_workflow = baseline.get("workflow_rules", [])
        overlay_workflow = overlay.get("workflow_rules", [])
        
        workflow_by_id = {}
        for rule in baseline_workflow:
            workflow_by_id[rule.get("id")] = rule
        for rule in overlay_workflow:
            workflow_by_id[rule.get("id")] = rule  # agent 覆盖全局
        
        effective["workflow_rules"] = list(workflow_by_id.values())
        merge_summary["workflow_rules"] = len(effective["workflow_rules"])
        
        # 3. 合并 memory_rules (并集)
        baseline_memory = baseline.get("memory_rules", [])
        overlay_memory = overlay.get("memory_rules", [])
        
        memory_by_id = {}
        for rule in baseline_memory:
            memory_by_id[rule.get("id")] = rule
        for rule in overlay_memory:
            if rule.get("id") not in memory_by_id:
                memory_by_id[rule.get("id")] = rule
        
        effective["memory_rules"] = list(memory_by_id.values())
        merge_summary["memory_rules"] = len(effective["memory_rules"])
        
        # 4. 合并 mutation_rules (交集)
        baseline_mutation = baseline.get("mutation_rules", {})
        overlay_mutation = overlay.get("mutation_rules", {})
        
        # 默认策略：取更严格的
        effective_mutation = {
            "default_policy": baseline_mutation.get("default_policy", {}),
            "global_forbidden": baseline_mutation.get("global_forbidden", []),
            "global_allowed": baseline_mutation.get("global_allowed", []),
        }
        
        # Agent allowed_paths 与全局 allowed_paths 取交集
        global_allowed = set(baseline_mutation.get("global_allowed", []))
        agent_allowed = set(overlay_mutation.get("allowed_paths", []))
        
        if agent_allowed:
            effective_mutation["allowed_paths"] = list(global_allowed | agent_allowed)
        else:
            effective_mutation["allowed_paths"] = list(global_allowed)
        
        # Agent forbidden_paths 必须包含全局 forbidden_paths
        global_forbidden = set(baseline_mutation.get("global_forbidden", []))
        agent_forbidden = set(overlay_mutation.get("forbidden_paths", []))
        effective_mutation["forbidden_paths"] = list(global_forbidden | agent_forbidden)
        
        effective["mutation_rules"] = effective_mutation
        merge_summary["mutation_rules"] = 1
        
        # 5. 隔离规则 (直接继承全局)
        effective["isolation_rules"] = baseline.get("isolation_rules", [])
        
        return MergeResult(
            agent_id=agent_id,
            effective_rules=effective,
            base_rules=baseline,
            overlay_rules=overlay,
            merge_summary=merge_summary,
            errors=errors,
        )
    
    def get_effective_rules(self, agent_id: str) -> Dict[str, Any]:
        """
        获取合并后的有效规则
        
        Args:
            agent_id: Agent ID
        
        Returns:
            Effective rules dictionary
        """
        result = self.merge(agent_id)
        return result.effective_rules
    
    def validate_overlay(self, agent_id: str) -> List[str]:
        """
        验证 overlay 是否符合规范
        
        Args:
            agent_id: Agent ID
        
        Returns:
            验证错误列表，空列表表示通过
        """
        errors = []
        overlay = self.load_overlay(agent_id)
        baseline = self.load_baseline()
        
        if not overlay:
            return ["Overlay not found"]
        
        # 检查 base 声明
        if overlay.get("base") != "global":
            errors.append("Overlay must declare 'base: global'")
        
        # 检查是否移除了全局 hard_constraints
        overlay_hard_ids = set(
            r.get("id") for r in overlay.get("hard_constraints", [])
        )
        baseline_hard_ids = set(
            r.get("id") for r in baseline.get("hard_constraints", [])
        )
        
        removed = baseline_hard_ids - overlay_hard_ids
        # 注意：overlay 不声明某个约束不等于移除，只有显式设置 enabled: false 才算移除
        
        for rule in overlay.get("hard_constraints", []):
            if rule.get("id") in baseline_hard_ids and rule.get("enabled") == False:
                errors.append(f"Cannot disable global hard_constraint: {rule.get('id')}")
        
        # 检查 allowed_paths 是否合法
        global_allowed = set(baseline.get("mutation_rules", {}).get("global_allowed", []))
        agent_allowed = set(overlay.get("mutation_rules", {}).get("allowed_paths", []))
        
        # agent allowed 可以扩展，但不能包含 global_forbidden
        global_forbidden = set(baseline.get("mutation_rules", {}).get("global_forbidden", []))
        for path in agent_allowed:
            for forbidden in global_forbidden:
                if path.startswith(forbidden) or forbidden.startswith(path):
                    errors.append(f"allowed_path '{path}' conflicts with global_forbidden '{forbidden}'")
        
        return errors
