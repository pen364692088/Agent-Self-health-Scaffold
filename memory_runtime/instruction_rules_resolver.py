"""
Instruction Rules Resolver - Long-term Instruction Rules Resolution

解析长期指令规则，支持跨会话的执行约束。

Author: Memory Runtime
Created: 2026-03-17
Version: 1.0.0
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Set
from pathlib import Path
import yaml
from datetime import datetime, timezone
import re


@dataclass
class RuleConfig:
    """
    规则配置
    """
    agent_id: str = "default"
    memory_root: Optional[Path] = None
    include_global: bool = True


@dataclass
class Rule:
    """
    单条规则
    """
    id: str
    category: str  # boundary/action/permission/constraint
    description: str
    priority: int = 0
    enabled: bool = True
    conditions: Dict[str, Any] = field(default_factory=dict)
    actions: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RuleSet:
    """
    规则集合
    """
    agent_id: str
    rules: List[Rule]
    loaded_at: str
    source: str
    
    def get_rules_by_category(self, category: str) -> List[Rule]:
        """按类别获取规则"""
        return [r for r in self.rules if r.category == category and r.enabled]
    
    def get_enabled_rules(self) -> List[Rule]:
        """获取所有启用的规则"""
        return [r for r in self.rules if r.enabled]
    
    def check_constraint(self, action: str, context: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        检查约束
        
        Args:
            action: 动作名称
            context: 上下文
        
        Returns:
            (是否允许, 阻塞原因)
        """
        for rule in self.get_rules_by_category("constraint"):
            if self._matches_condition(rule, action, context):
                if rule.actions.get("block"):
                    return False, rule.description
        
        return True, None
    
    def _matches_condition(self, rule: Rule, action: str, context: Dict[str, Any]) -> bool:
        """检查条件是否匹配"""
        conditions = rule.conditions
        
        if not conditions:
            return True
        
        # 检查动作匹配
        if "actions" in conditions:
            if action not in conditions["actions"]:
                return False
        
        # 检查上下文匹配
        if "context" in conditions:
            for key, value in conditions["context"].items():
                if context.get(key) != value:
                    return False
        
        return True


class InstructionRulesResolver:
    """
    指令规则解析器
    
    负责：
    - 加载指令规则
    - 解析规则
    - 检查约束
    """
    
    # 全局规则模板
    GLOBAL_RULES = [
        {
            "id": "canonical-repo",
            "category": "boundary",
            "description": "所有文件操作必须在 canonical repo 内",
            "priority": 100,
            "conditions": {
                "actions": ["write", "edit", "delete"]
            },
            "actions": {
                "check": "canonical_repo"
            }
        },
        {
            "id": "no-duplicate-create",
            "category": "constraint",
            "description": "禁止重复创建已存在的资源",
            "priority": 90,
            "conditions": {
                "actions": ["create"]
            },
            "actions": {
                "check": "existence"
            }
        },
        {
            "id": "mutation-preflight",
            "category": "action",
            "description": "变更操作前必须执行 preflight 检查",
            "priority": 80,
            "conditions": {
                "actions": ["mutate", "update", "delete"]
            },
            "actions": {
                "require": "preflight"
            }
        },
        {
            "id": "git-protection",
            "category": "permission",
            "description": "git 操作前必须检查权限",
            "priority": 70,
            "conditions": {
                "actions": ["git_push", "git_rebase", "git_merge"]
            },
            "actions": {
                "require": "git_permission"
            }
        },
        {
            "id": "evidence-required",
            "category": "constraint",
            "description": "关键操作必须留下证据",
            "priority": 60,
            "conditions": {
                "actions": ["write", "mutate", "git_push"]
            },
            "actions": {
                "require": "evidence"
            }
        },
    ]
    
    def __init__(self, config: Optional[RuleConfig] = None, **kwargs):
        # 支持直接传参
        if config is None:
            config = RuleConfig(
                agent_id=kwargs.get("agent_id", "default"),
                memory_root=kwargs.get("memory_root"),
            )
        self.config = config
    
    def _get_memory_root(self) -> Path:
        """获取记忆根目录"""
        if self.config.memory_root:
            return self.config.memory_root
        
        # 默认路径
        return Path.home() / ".openclaw" / "agents" / self.config.agent_id / "memory"
    
    def _get_rules_file(self) -> Path:
        """获取规则文件路径"""
        return self._get_memory_root() / "instruction_rules.yaml"
    
    def _ensure_memory_dir(self) -> Path:
        """确保记忆目录存在"""
        root = self._get_memory_root()
        root.mkdir(parents=True, exist_ok=True)
        return root
    
    def load_rules(self) -> Optional[Dict[str, Any]]:
        """
        加载规则
        
        Returns:
            规则字典
        """
        rules_file = self._get_rules_file()
        
        # 加载私有规则
        private_rules = []
        if rules_file.exists():
            try:
                with open(rules_file) as f:
                    data = yaml.safe_load(f) or {}
                    private_rules = data.get("rules", [])
            except Exception:
                pass
        
        # 合并全局规则
        all_rules = []
        
        if self.config.include_global:
            all_rules.extend(self.GLOBAL_RULES)
        
        all_rules.extend(private_rules)
        
        # 构建 RuleSet
        rule_objects = []
        for r in all_rules:
            rule_objects.append(Rule(
                id=r.get("id", "unknown"),
                category=r.get("category", "constraint"),
                description=r.get("description", ""),
                priority=r.get("priority", 0),
                enabled=r.get("enabled", True),
                conditions=r.get("conditions", {}),
                actions=r.get("actions", {}),
            ))
        
        # 按优先级排序
        rule_objects.sort(key=lambda r: r.priority, reverse=True)
        
        return {
            "agent_id": self.config.agent_id,
            "rules": [{"id": r.id, "category": r.category, "description": r.description} for r in rule_objects],
            "rule_count": len(rule_objects),
            "loaded_at": datetime.now(timezone.utc).isoformat(),
            "source": str(rules_file) if rules_file.exists() else "global",
        }
    
    def load_rule_set(self) -> RuleSet:
        """
        加载 RuleSet 对象
        
        Returns:
            RuleSet
        """
        rules_file = self._get_rules_file()
        
        # 加载私有规则
        private_rules = []
        if rules_file.exists():
            try:
                with open(rules_file) as f:
                    data = yaml.safe_load(f) or {}
                    private_rules = data.get("rules", [])
            except Exception:
                pass
        
        # 合并全局规则
        all_rules = []
        
        if self.config.include_global:
            all_rules.extend(self.GLOBAL_RULES)
        
        all_rules.extend(private_rules)
        
        # 构建 RuleSet
        rule_objects = []
        for r in all_rules:
            rule_objects.append(Rule(
                id=r.get("id", "unknown"),
                category=r.get("category", "constraint"),
                description=r.get("description", ""),
                priority=r.get("priority", 0),
                enabled=r.get("enabled", True),
                conditions=r.get("conditions", {}),
                actions=r.get("actions", {}),
            ))
        
        # 按优先级排序
        rule_objects.sort(key=lambda r: r.priority, reverse=True)
        
        return RuleSet(
            agent_id=self.config.agent_id,
            rules=rule_objects,
            loaded_at=datetime.now(timezone.utc).isoformat(),
            source=str(rules_file) if rules_file.exists() else "global",
        )
    
    def add_rule(self, rule: Dict[str, Any]) -> bool:
        """
        添加规则
        
        Args:
            rule: 规则字典
        
        Returns:
            是否添加成功
        """
        try:
            self._ensure_memory_dir()
            rules_file = self._get_rules_file()
            
            # 读取现有规则
            existing = {"rules": []}
            if rules_file.exists():
                with open(rules_file) as f:
                    existing = yaml.safe_load(f) or {"rules": []}
            
            # 添加新规则
            existing["rules"].append(rule)
            
            # 写回
            with open(rules_file, "w") as f:
                yaml.dump(existing, f)
            
            return True
            
        except Exception:
            return False
    
    def remove_rule(self, rule_id: str) -> bool:
        """
        移除规则
        
        Args:
            rule_id: 规则 ID
        
        Returns:
            是否移除成功
        """
        try:
            rules_file = self._get_rules_file()
            
            if not rules_file.exists():
                return False
            
            with open(rules_file) as f:
                data = yaml.safe_load(f) or {"rules": []}
            
            # 过滤掉指定规则
            data["rules"] = [r for r in data.get("rules", []) if r.get("id") != rule_id]
            
            with open(rules_file, "w") as f:
                yaml.dump(data, f)
            
            return True
            
        except Exception:
            return False
