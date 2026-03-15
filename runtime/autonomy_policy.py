"""
Autonomy Policy Layer - 自治策略层 (v3-E)

让系统拥有"默认自动推进"的能力，同时明确什么不能自动做。

核心概念:
- Allowed Actions: 默认可自治的动作
- Forbidden Actions: 必须阻断的动作
- Approval-Required Actions: 需要人工确认的动作
- Risk Levels: low/medium/high/critical
- Safe-Stop Conditions: 安全停止条件
- Policy Evidence Log: 策略决策日志

与 risk_gate.py 的关系:
- AutonomyPolicy 使用 RiskGate 进行风险评估
- 在 RiskGate 基础上叠加策略规则
- 不修改 RiskGate 的核心逻辑
"""

import json
import yaml
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Callable
from dataclasses import dataclass, asdict, field
from enum import Enum
import threading
import functools

# 导入 RiskGate
from runtime.risk_gate import (
    RiskGate, 
    RiskLevel, 
    RiskAction,
    Operation,
    RiskAssessment
)


class AutonomyDecision(str, Enum):
    """自治决策"""
    ALLOW_AUTO = "allow_auto"           # 允许自动执行
    ALLOW_WITH_LOG = "allow_with_log"   # 允许执行但需记录
    REQUIRE_APPROVAL = "require_approval"  # 需要审批
    BLOCK = "block"                     # 阻断
    SAFE_STOP = "safe_stop"             # 安全停止


class ActionType(str, Enum):
    """动作类型"""
    # === 默认可自治的动作 ===
    READ_DOCUMENT = "read_document"
    RUN_TEST = "run_test"
    SMALL_CODE_FIX = "small_code_fix"
    WRITE_REPORT = "write_report"
    TASK_SPLIT = "task_split"
    TASK_SCHEDULE = "task_schedule"
    RETRY = "retry"
    RECLAIM = "reclaim"
    ROLLBACK = "rollback"
    
    # === 需要审批的动作 ===
    LARGE_CODE_CHANGE = "large_code_change"
    EXTERNAL_API_CALL = "external_api_call"
    NEW_FEATURE_IMPLEMENT = "new_feature_implement"
    DEPLOY_OPERATION = "deploy_operation"
    
    # === 必须阻断的动作 ===
    MASS_DELETE = "mass_delete"
    MODIFY_GATE_RULES = "modify_gate_rules"
    DESTROY_BASELINE = "destroy_baseline"
    EXTERNAL_DESTRUCTIVE = "external_destructive"
    CREDENTIAL_OPERATION = "credential_operation"
    PAYMENT_OPERATION = "payment_operation"
    ACCOUNT_OPERATION = "account_operation"


@dataclass
class PolicyRule:
    """策略规则"""
    action_type: str
    category: str  # allowed, forbidden, approval_required
    risk_threshold: str  # low, medium, high, critical
    description: str
    conditions: Dict[str, Any] = field(default_factory=dict)
    exemptions: List[str] = field(default_factory=list)


@dataclass
class SafeStopCondition:
    """安全停止条件"""
    name: str
    description: str
    check_function: str  # 可调用的检查函数名
    severity: str  # info, warning, error, critical
    auto_recoverable: bool = False


@dataclass
class PolicyEvidence:
    """策略决策证据"""
    evidence_id: str
    timestamp: str
    action_type: str
    operation_summary: str
    decision: str
    risk_level: str
    matched_rules: List[str]
    safe_stop_triggered: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AutonomyPolicy:
    """
    自治策略层
    
    决策流程:
    1. 检查是否匹配 forbidden actions → BLOCK
    2. 检查是否触发 safe-stop conditions → SAFE_STOP
    3. 使用 RiskGate 进行风险评估
    4. 检查是否匹配 approval-required actions → REQUIRE_APPROVAL
    5. 检查是否匹配 allowed actions → ALLOW_AUTO / ALLOW_WITH_LOG
    6. 默认策略 (根据配置)
    """
    
    # === 默认可自治的动作 ===
    DEFAULT_ALLOWED_ACTIONS: Set[str] = {
        ActionType.READ_DOCUMENT.value,
        ActionType.RUN_TEST.value,
        ActionType.SMALL_CODE_FIX.value,
        ActionType.WRITE_REPORT.value,
        ActionType.TASK_SPLIT.value,
        ActionType.TASK_SCHEDULE.value,
        ActionType.RETRY.value,
        ActionType.RECLAIM.value,
        ActionType.ROLLBACK.value,
    }
    
    # === 必须阻断的动作 ===
    DEFAULT_FORBIDDEN_ACTIONS: Set[str] = {
        ActionType.MASS_DELETE.value,
        ActionType.MODIFY_GATE_RULES.value,
        ActionType.DESTROY_BASELINE.value,
        ActionType.EXTERNAL_DESTRUCTIVE.value,
        ActionType.CREDENTIAL_OPERATION.value,
        ActionType.PAYMENT_OPERATION.value,
        ActionType.ACCOUNT_OPERATION.value,
    }
    
    # === 需要审批的动作 ===
    DEFAULT_APPROVAL_REQUIRED_ACTIONS: Set[str] = {
        ActionType.LARGE_CODE_CHANGE.value,
        ActionType.EXTERNAL_API_CALL.value,
        ActionType.NEW_FEATURE_IMPLEMENT.value,
        ActionType.DEPLOY_OPERATION.value,
    }
    
    # === 风险等级阈值 ===
    RISK_DECISION_MAP = {
        RiskLevel.LOW.value: AutonomyDecision.ALLOW_AUTO,
        RiskLevel.MEDIUM.value: AutonomyDecision.ALLOW_WITH_LOG,
        RiskLevel.HIGH.value: AutonomyDecision.REQUIRE_APPROVAL,
        RiskLevel.CRITICAL.value: AutonomyDecision.BLOCK,
    }
    
    def __init__(
        self,
        config_path: Optional[str] = None,
        risk_gate: Optional[RiskGate] = None,
        evidence_log_path: Optional[str] = None,
        policy_override: Optional[Dict[str, Any]] = None,
    ):
        """
        初始化自治策略层
        
        Args:
            config_path: 策略配置文件路径
            risk_gate: RiskGate 实例 (可选，会自动创建)
            evidence_log_path: 策略证据日志路径
            policy_override: 策略覆盖配置
        """
        self.config_path = config_path
        self.risk_gate = risk_gate or RiskGate()
        self.evidence_log_path = Path(evidence_log_path) if evidence_log_path else None
        
        # 可配置的策略
        self.allowed_actions: Set[str] = set(self.DEFAULT_ALLOWED_ACTIONS)
        self.forbidden_actions: Set[str] = set(self.DEFAULT_FORBIDDEN_ACTIONS)
        self.approval_required_actions: Set[str] = set(self.DEFAULT_APPROVAL_REQUIRED_ACTIONS)
        
        # 自定义规则
        self.custom_rules: Dict[str, PolicyRule] = {}
        
        # 安全停止条件
        self.safe_stop_conditions: Dict[str, SafeStopCondition] = {}
        self._register_default_safe_stop_conditions()
        
        # 策略证据日志
        self.evidence_log: List[PolicyEvidence] = []
        self._evidence_lock = threading.Lock()
        
        # 模式
        self.mode = "guarded-auto"  # shadow, guarded-auto, full-auto
        
        # 运行时状态
        self._safe_stop_triggered: Optional[str] = None
        self._consecutive_blocks = 0
        self._max_consecutive_blocks = 3
        
        # 加载配置
        if config_path:
            self._load_config(config_path)
        
        if policy_override:
            self._apply_override(policy_override)
    
    def _register_default_safe_stop_conditions(self):
        """注册默认安全停止条件"""
        default_conditions = [
            SafeStopCondition(
                name="consecutive_blocks_exceeded",
                description="连续被阻断的操作超过阈值",
                check_function="_check_consecutive_blocks",
                severity="critical",
                auto_recoverable=False
            ),
            SafeStopCondition(
                name="risk_gate_unavailable",
                description="RiskGate 不可用",
                check_function="_check_risk_gate_available",
                severity="error",
                auto_recoverable=True
            ),
            SafeStopCondition(
                name="baseline_integrity_violation",
                description="基线完整性被破坏",
                check_function="_check_baseline_integrity",
                severity="critical",
                auto_recoverable=False
            ),
            SafeStopCondition(
                name="policy_config_corrupted",
                description="策略配置损坏",
                check_function="_check_policy_config_valid",
                severity="error",
                auto_recoverable=True
            ),
            SafeStopCondition(
                name="evidence_log_full",
                description="证据日志达到容量上限",
                check_function="_check_evidence_log_capacity",
                severity="warning",
                auto_recoverable=True
            ),
        ]
        
        for condition in default_conditions:
            self.safe_stop_conditions[condition.name] = condition
    
    def _load_config(self, config_path: str):
        """加载配置文件"""
        path = Path(config_path)
        if not path.exists():
            return
        
        with open(path, 'r') as f:
            config = yaml.safe_load(f)
        
        if not config:
            return
        
        # 加载允许的动作
        if "allowed_actions" in config:
            self.allowed_actions = set(config["allowed_actions"])
        
        # 加载禁止的动作
        if "forbidden_actions" in config:
            self.forbidden_actions = set(config["forbidden_actions"])
        
        # 加载需要审批的动作
        if "approval_required_actions" in config:
            self.approval_required_actions = set(config["approval_required_actions"])
        
        # 加载模式
        if "mode" in config:
            self.mode = config["mode"]
        
        # 加载自定义规则
        if "custom_rules" in config:
            for rule_data in config["custom_rules"]:
                rule = PolicyRule(**rule_data)
                self.custom_rules[rule.action_type] = rule
        
        # 加载安全停止条件
        if "safe_stop_conditions" in config:
            for cond_data in config["safe_stop_conditions"]:
                condition = SafeStopCondition(**cond_data)
                self.safe_stop_conditions[condition.name] = condition
    
    def _apply_override(self, override: Dict[str, Any]):
        """应用策略覆盖"""
        if "add_allowed" in override:
            self.allowed_actions.update(override["add_allowed"])
        
        if "remove_allowed" in override:
            self.allowed_actions.difference_update(override["remove_allowed"])
        
        if "add_forbidden" in override:
            self.forbidden_actions.update(override["add_forbidden"])
        
        if "remove_forbidden" in override:
            self.forbidden_actions.difference_update(override["remove_forbidden"])
        
        if "mode" in override:
            self.mode = override["mode"]
    
    def decide(
        self,
        action_type: str,
        operation: Optional[Operation] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> PolicyEvidence:
        """
        决策是否允许自动执行
        
        Args:
            action_type: 动作类型
            operation: 操作描述 (用于风险评估)
            context: 上下文信息
            
        Returns:
            PolicyEvidence: 策略决策证据
        """
        context = context or {}
        evidence_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        matched_rules = []
        
        # 1. 检查安全停止条件
        safe_stop_triggered = self._check_safe_stop_conditions()
        if safe_stop_triggered:
            evidence = PolicyEvidence(
                evidence_id=evidence_id,
                timestamp=timestamp,
                action_type=action_type,
                operation_summary=operation.description if operation else action_type,
                decision=AutonomyDecision.SAFE_STOP.value,
                risk_level=RiskLevel.CRITICAL.value,
                matched_rules=["safe_stop:" + safe_stop_triggered],
                safe_stop_triggered=safe_stop_triggered,
                context=context
            )
            self._record_evidence(evidence)
            return evidence
        
        # 2. 检查禁止的动作
        if action_type in self.forbidden_actions:
            self._consecutive_blocks += 1
            matched_rules.append(f"forbidden:{action_type}")
            
            evidence = PolicyEvidence(
                evidence_id=evidence_id,
                timestamp=timestamp,
                action_type=action_type,
                operation_summary=operation.description if operation else action_type,
                decision=AutonomyDecision.BLOCK.value,
                risk_level=RiskLevel.CRITICAL.value,
                matched_rules=matched_rules,
                context=context
            )
            self._record_evidence(evidence)
            return evidence
        
        # 3. 进行风险评估
        risk_assessment = None
        risk_level = RiskLevel.LOW.value
        
        if operation:
            risk_assessment = self.risk_gate.assess(operation, context)
            risk_level = risk_assessment.risk_level
            matched_rules.append(f"risk_assessment:{risk_level}")
        
        # 4. 检查需要审批的动作
        if action_type in self.approval_required_actions:
            matched_rules.append(f"approval_required:{action_type}")
            
            # 即使需要审批，也要看风险等级
            if risk_level == RiskLevel.CRITICAL.value:
                decision = AutonomyDecision.BLOCK
                self._consecutive_blocks += 1
            else:
                decision = AutonomyDecision.REQUIRE_APPROVAL
                self._consecutive_blocks = 0  # 重置计数
            
            evidence = PolicyEvidence(
                evidence_id=evidence_id,
                timestamp=timestamp,
                action_type=action_type,
                operation_summary=operation.description if operation else action_type,
                decision=decision.value,
                risk_level=risk_level,
                matched_rules=matched_rules,
                context=context
            )
            self._record_evidence(evidence)
            return evidence
        
        # 5. 检查允许的动作
        if action_type in self.allowed_actions:
            matched_rules.append(f"allowed:{action_type}")
            
            # 即使允许，也要根据风险等级决定
            if risk_level == RiskLevel.CRITICAL.value:
                decision = AutonomyDecision.BLOCK
                self._consecutive_blocks += 1
            elif risk_level == RiskLevel.HIGH.value:
                decision = AutonomyDecision.REQUIRE_APPROVAL
                self._consecutive_blocks = 0
            elif risk_level == RiskLevel.MEDIUM.value:
                decision = AutonomyDecision.ALLOW_WITH_LOG
                self._consecutive_blocks = 0
            else:
                decision = AutonomyDecision.ALLOW_AUTO
                self._consecutive_blocks = 0
            
            evidence = PolicyEvidence(
                evidence_id=evidence_id,
                timestamp=timestamp,
                action_type=action_type,
                operation_summary=operation.description if operation else action_type,
                decision=decision.value,
                risk_level=risk_level,
                matched_rules=matched_rules,
                context=context
            )
            self._record_evidence(evidence)
            return evidence
        
        # 6. 检查自定义规则
        if action_type in self.custom_rules:
            rule = self.custom_rules[action_type]
            matched_rules.append(f"custom_rule:{action_type}")
            
            if rule.category == "forbidden":
                decision = AutonomyDecision.BLOCK
                self._consecutive_blocks += 1
            elif rule.category == "approval_required":
                decision = AutonomyDecision.REQUIRE_APPROVAL
                self._consecutive_blocks = 0
            else:
                decision = AutonomyDecision.ALLOW_AUTO
                self._consecutive_blocks = 0
            
            evidence = PolicyEvidence(
                evidence_id=evidence_id,
                timestamp=timestamp,
                action_type=action_type,
                operation_summary=operation.description if operation else action_type,
                decision=decision.value,
                risk_level=rule.risk_threshold,
                matched_rules=matched_rules,
                context=context
            )
            self._record_evidence(evidence)
            return evidence
        
        # 7. 默认策略
        # 根据模式决定默认行为
        if self.mode == "shadow":
            decision = AutonomyDecision.ALLOW_WITH_LOG
        elif self.mode == "guarded-auto":
            decision = AutonomyDecision.REQUIRE_APPROVAL
        else:  # full-auto
            decision = AutonomyDecision.ALLOW_AUTO
        
        matched_rules.append(f"default:{self.mode}")
        
        evidence = PolicyEvidence(
            evidence_id=evidence_id,
            timestamp=timestamp,
            action_type=action_type,
            operation_summary=operation.description if operation else action_type,
            decision=decision.value,
            risk_level=risk_level,
            matched_rules=matched_rules,
            context=context
        )
        self._record_evidence(evidence)
        return evidence
    
    def _check_safe_stop_conditions(self) -> Optional[str]:
        """检查安全停止条件"""
        for name, condition in self.safe_stop_conditions.items():
            check_func = getattr(self, condition.check_function, None)
            if check_func and check_func():
                self._safe_stop_triggered = name
                return name
        return None
    
    def _check_consecutive_blocks(self) -> bool:
        """检查连续阻断"""
        return self._consecutive_blocks >= self._max_consecutive_blocks
    
    def _check_risk_gate_available(self) -> bool:
        """检查 RiskGate 可用性"""
        return self.risk_gate is None
    
    def _check_baseline_integrity(self) -> bool:
        """检查基线完整性 (需要外部实现)"""
        # 这个方法应该由外部实现覆盖
        # 默认返回 False (不触发)
        return False
    
    def _check_policy_config_valid(self) -> bool:
        """检查策略配置有效性"""
        if not self.config_path:
            return False
        
        path = Path(self.config_path)
        if not path.exists():
            return False
        
        try:
            with open(path, 'r') as f:
                yaml.safe_load(f)
            return False
        except:
            return True
    
    def _check_evidence_log_capacity(self) -> bool:
        """检查证据日志容量"""
        return len(self.evidence_log) >= 10000
    
    def _record_evidence(self, evidence: PolicyEvidence):
        """记录策略证据"""
        with self._evidence_lock:
            self.evidence_log.append(evidence)
            
            # 持久化到文件
            if self.evidence_log_path:
                with open(self.evidence_log_path, 'a') as f:
                    f.write(json.dumps(evidence.to_dict()) + "\n")
    
    def is_allowed_auto(self, action_type: str, operation: Optional[Operation] = None) -> bool:
        """快速检查是否允许自动执行"""
        evidence = self.decide(action_type, operation)
        return evidence.decision in [
            AutonomyDecision.ALLOW_AUTO.value,
            AutonomyDecision.ALLOW_WITH_LOG.value
        ]
    
    def add_allowed_action(self, action_type: str):
        """添加允许的动作"""
        self.allowed_actions.add(action_type)
        self.forbidden_actions.discard(action_type)
        self.approval_required_actions.discard(action_type)
    
    def add_forbidden_action(self, action_type: str):
        """添加禁止的动作"""
        self.forbidden_actions.add(action_type)
        self.allowed_actions.discard(action_type)
        self.approval_required_actions.discard(action_type)
    
    def add_approval_required_action(self, action_type: str):
        """添加需要审批的动作"""
        self.approval_required_actions.add(action_type)
        self.allowed_actions.discard(action_type)
        self.forbidden_actions.discard(action_type)
    
    def clear_safe_stop(self):
        """清除安全停止状态"""
        self._safe_stop_triggered = None
        self._consecutive_blocks = 0
    
    def get_policy_summary(self) -> Dict[str, Any]:
        """获取策略摘要"""
        return {
            "mode": self.mode,
            "allowed_actions_count": len(self.allowed_actions),
            "forbidden_actions_count": len(self.forbidden_actions),
            "approval_required_count": len(self.approval_required_actions),
            "custom_rules_count": len(self.custom_rules),
            "safe_stop_conditions_count": len(self.safe_stop_conditions),
            "safe_stop_triggered": self._safe_stop_triggered,
            "consecutive_blocks": self._consecutive_blocks,
            "evidence_log_size": len(self.evidence_log),
        }
    
    def export_policy(self) -> Dict[str, Any]:
        """导出策略配置"""
        return {
            "mode": self.mode,
            "allowed_actions": list(self.allowed_actions),
            "forbidden_actions": list(self.forbidden_actions),
            "approval_required_actions": list(self.approval_required_actions),
            "custom_rules": [
                asdict(rule) for rule in self.custom_rules.values()
            ],
            "safe_stop_conditions": [
                asdict(cond) for cond in self.safe_stop_conditions.values()
            ],
        }


class AutonomyPolicyContext:
    """
    自治策略上下文管理器
    
    用于临时修改策略配置，执行完毕后恢复
    """
    
    def __init__(self, policy: AutonomyPolicy, override: Dict[str, Any]):
        self.policy = policy
        self.override = override
        self._original_state = None
    
    def __enter__(self):
        # 保存原始状态
        self._original_state = {
            "allowed_actions": set(self.policy.allowed_actions),
            "forbidden_actions": set(self.policy.forbidden_actions),
            "approval_required_actions": set(self.policy.approval_required_actions),
            "mode": self.policy.mode,
        }
        
        # 应用覆盖
        self.policy._apply_override(self.override)
        return self.policy
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # 恢复原始状态
        self.policy.allowed_actions = self._original_state["allowed_actions"]
        self.policy.forbidden_actions = self._original_state["forbidden_actions"]
        self.policy.approval_required_actions = self._original_state["approval_required_actions"]
        self.policy.mode = self._original_state["mode"]
        return False


# === 便捷函数 ===

def create_default_policy(
    config_path: Optional[str] = None,
    evidence_log_path: Optional[str] = None
) -> AutonomyPolicy:
    """创建默认策略实例"""
    return AutonomyPolicy(
        config_path=config_path,
        evidence_log_path=evidence_log_path
    )


def quick_decide(
    action_type: str,
    command: Optional[str] = None,
    mode: str = "guarded-auto"
) -> AutonomyDecision:
    """快速决策函数"""
    policy = AutonomyPolicy()
    policy.mode = mode
    
    operation = None
    if command:
        operation = Operation(
            type="shell_command",
            description=command,
            command=command
        )
    
    evidence = policy.decide(action_type, operation)
    return AutonomyDecision(evidence.decision)
