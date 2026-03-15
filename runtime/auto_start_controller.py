"""
Auto Start Controller - 自动启动控制器

决定当前运行模式、是否自动建任务、是否自动推进。
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict, field
from enum import Enum


class RunMode(str, Enum):
    """运行模式"""
    SHADOW = "shadow"
    GUARDED_AUTO = "guarded-auto"
    FULL_AUTO = "full-auto"


class DecisionType(str, Enum):
    """决策类型"""
    DIRECT_REPLY = "DIRECT_REPLY"
    CREATE_TASK = "CREATE_TASK"
    CONTINUE_TASK = "CONTINUE_TASK"
    CONTROL = "CONTROL"
    SAFE_MODE = "SAFE_MODE"
    MANUAL_MODE = "MANUAL_MODE"
    BLOCKED = "BLOCKED"


@dataclass
class AutoStartDecision:
    """自动启动决策"""
    decision_id: str
    timestamp: str
    message_event_id: str
    decision_type: str
    reason: str
    mode: str
    risk_level: Optional[str] = None
    classification: Optional[Dict[str, Any]] = None
    action: Dict[str, Any] = field(default_factory=dict)
    checks: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class FeatureFlags:
    """Feature Flags 管理"""
    
    DEFAULT_FLAGS = {
        "telegram.main_flow_enabled": True,
        "telegram.auto_start_mode": "guarded-auto",
        "telegram.high_risk_requires_approval": True,
        "telegram.allow_background_resume": True,
        "telegram.kill_switch_enabled": False
    }
    
    def __init__(self, config_path: str = None):
        self.config_path = Path(config_path) if config_path else None
        self._flags = self._load_flags()
    
    def _load_flags(self) -> Dict[str, Any]:
        flags = self.DEFAULT_FLAGS.copy()
        
        if self.config_path and self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    flags.update(config.get("telegram", {}))
            except (json.JSONDecodeError, IOError):
                pass
        
        # 环境变量覆盖
        import os
        for key in flags.keys():
            env_key = key.upper().replace(".", "_").replace("-", "_")
            env_value = os.environ.get(env_key)
            if env_value is not None:
                if env_value.lower() in ("true", "1", "yes"):
                    flags[key] = True
                elif env_value.lower() in ("false", "0", "no"):
                    flags[key] = False
                else:
                    flags[key] = env_value
        
        return flags
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取 feature flag 值"""
        return self._flags.get(key, default)
    
    def set(self, key: str, value: Any):
        """设置 feature flag 值"""
        self._flags[key] = value
    
    def is_kill_switch_enabled(self) -> bool:
        """检查 kill switch 是否启用"""
        return self._flags.get("telegram.kill_switch_enabled", False)
    
    def is_main_flow_enabled(self) -> bool:
        """检查主流程是否启用"""
        return self._flags.get("telegram.main_flow_enabled", True)
    
    def get_mode(self) -> str:
        """获取当前运行模式"""
        return self._flags.get("telegram.auto_start_mode", "guarded-auto")
    
    def set_mode(self, mode: str):
        """设置运行模式"""
        if mode in [m.value for m in RunMode]:
            self._flags["telegram.auto_start_mode"] = mode
        else:
            raise ValueError(f"Invalid mode: {mode}")


class DecisionLogger:
    """决策日志记录器"""
    
    def __init__(self, log_path: str = ".decision_log.jsonl"):
        self.log_path = Path(log_path)
    
    def log(self, decision: AutoStartDecision):
        """记录决策"""
        with open(self.log_path, 'a') as f:
            f.write(json.dumps(decision.to_dict()) + "\n")


class AutoStartController:
    """自动启动控制器"""
    
    def __init__(
        self,
        config_path: str = None,
        decision_log_path: str = None
    ):
        self.feature_flags = FeatureFlags(config_path)
        self.decision_logger = DecisionLogger(decision_log_path or ".decision_log.jsonl")
    
    def decide(
        self,
        event: Dict[str, Any],
        route_decision: Dict[str, Any],
        risk_assessment: Optional[Dict[str, Any]] = None
    ) -> AutoStartDecision:
        """
        做出自动启动决策
        
        Args:
            event: MessageEvent 字典
            route_decision: 路由决策字典
            risk_assessment: 风险评估（可选）
            
        Returns:
            AutoStartDecision 自动启动决策
        """
        decision_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat() + "Z"
        message_event_id = event.get("event_id", "")
        
        # 检查各项条件
        checks = {
            "kill_switch_enabled": self.feature_flags.is_kill_switch_enabled(),
            "main_flow_enabled": self.feature_flags.is_main_flow_enabled(),
            "idempotency_check": "not_checked",  # 由 ingress 处理
            "authorization_check": "not_required"
        }
        
        route_type = route_decision.get("type", "chat")
        mode = self.feature_flags.get_mode()
        risk_level = risk_assessment.get("risk_level") if risk_assessment else None
        
        # 1. Kill Switch 检查
        if checks["kill_switch_enabled"]:
            decision = AutoStartDecision(
                decision_id=decision_id,
                timestamp=timestamp,
                message_event_id=message_event_id,
                decision_type=DecisionType.SAFE_MODE.value,
                reason="Kill switch is enabled",
                mode=mode,
                checks=checks,
                action={
                    "type": "safe_mode_response",
                    "reply_message": "⚠️ 系统处于安全模式，自动推进已暂停。\n\n你可以使用 /status 查看状态，或等待管理员恢复。"
                }
            )
            self.decision_logger.log(decision)
            return decision
        
        # 2. 主流程检查
        if not checks["main_flow_enabled"]:
            decision = AutoStartDecision(
                decision_id=decision_id,
                timestamp=timestamp,
                message_event_id=message_event_id,
                decision_type=DecisionType.MANUAL_MODE.value,
                reason="Main flow is disabled",
                mode=mode,
                checks=checks,
                action={
                    "type": "manual_mode_response",
                    "reply_message": "系统处于手动模式，任务执行已暂停。"
                }
            )
            self.decision_logger.log(decision)
            return decision
        
        # 3. 控制命令直接放行
        if route_type == "control":
            decision = AutoStartDecision(
                decision_id=decision_id,
                timestamp=timestamp,
                message_event_id=message_event_id,
                decision_type=DecisionType.CONTROL.value,
                reason="Control command",
                mode=mode,
                checks=checks,
                action={
                    "type": "control_routing",
                    "command": route_decision.get("command")
                }
            )
            self.decision_logger.log(decision)
            return decision
        
        # 4. 普通聊天直接回复
        if route_type == "chat":
            decision = AutoStartDecision(
                decision_id=decision_id,
                timestamp=timestamp,
                message_event_id=message_event_id,
                decision_type=DecisionType.DIRECT_REPLY.value,
                reason="Chat message, no task needed",
                mode=mode,
                risk_level=risk_level,
                checks=checks,
                action={
                    "type": "direct_reply"
                }
            )
            self.decision_logger.log(decision)
            return decision
        
        # 5. 审批响应
        if route_type == "approval":
            decision = AutoStartDecision(
                decision_id=decision_id,
                timestamp=timestamp,
                message_event_id=message_event_id,
                decision_type=DecisionType.CONTROL.value,
                reason="Approval response",
                mode=mode,
                checks=checks,
                action={
                    "type": "approval_handling",
                    "task_id": route_decision.get("task_id"),
                    "command": route_decision.get("command")
                }
            )
            self.decision_logger.log(decision)
            return decision
        
        # 6. 任务类型（新任务或继续任务）
        task_id = route_decision.get("task_id")
        objective = route_decision.get("objective")
        
        decision_type = DecisionType.CREATE_TASK if route_type == "new_task" else DecisionType.CONTINUE_TASK
        
        # 根据模式和风险评估决定动作
        if mode == RunMode.SHADOW.value:
            # Shadow 模式：只观测，不执行
            action = {
                "type": "observe_only",
                "task_id": task_id,
                "objective": objective,
                "reply_message": f"📝 已记录你的请求（shadow 模式观测中）\n\n任务 ID: {task_id}\n\n使用 /status 查看详情"
            }
        
        elif mode == RunMode.GUARDED_AUTO.value:
            # Guarded-Auto 模式：低风险自动执行，高风险需确认
            if risk_level in ["high", "critical"]:
                action = {
                    "type": "pause_for_approval",
                    "task_id": task_id,
                    "objective": objective,
                    "requires_approval": True,
                    "reply_message": f"⚠️ 检测到高风险操作\n\n需要你的确认才能继续。\n\n任务 ID: {task_id}\n使用 /approve 确认或 /reject 拒绝"
                }
            else:
                action = {
                    "type": "auto_proceed",
                    "task_id": task_id,
                    "objective": objective,
                    "requires_approval": False,
                    "reply_message": f"✅ 已创建任务并开始执行\n\n任务 ID: {task_id}\n\n使用 /status 查看进度"
                }
        
        else:  # FULL_AUTO
            # Full-Auto 模式：全自动执行
            action = {
                "type": "auto_proceed",
                "task_id": task_id,
                "objective": objective,
                "requires_approval": False,
                "reply_message": f"✅ 已创建任务并开始执行\n\n任务 ID: {task_id}"
            }
        
        decision = AutoStartDecision(
            decision_id=decision_id,
            timestamp=timestamp,
            message_event_id=message_event_id,
            decision_type=decision_type.value,
            reason=f"Route type: {route_type}, Mode: {mode}",
            mode=mode,
            risk_level=risk_level,
            classification={
                "type": route_type,
                "confidence": route_decision.get("confidence", 1.0),
                "task_id": task_id
            },
            action=action,
            checks=checks
        )
        
        self.decision_logger.log(decision)
        return decision
    
    def set_mode(self, mode: str) -> Dict[str, Any]:
        """切换运行模式"""
        try:
            old_mode = self.feature_flags.get_mode()
            self.feature_flags.set_mode(mode)
            new_mode = self.feature_flags.get_mode()
            
            return {
                "success": True,
                "old_mode": old_mode,
                "new_mode": new_mode,
                "message": f"模式已从 {old_mode} 切换到 {new_mode}"
            }
        except ValueError as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def enable_kill_switch(self) -> Dict[str, Any]:
        """启用 Kill Switch"""
        self.feature_flags.set("telegram.kill_switch_enabled", True)
        return {
            "success": True,
            "kill_switch_enabled": True,
            "message": "⚠️ Kill Switch 已启用，所有自动推进已暂停"
        }
    
    def disable_kill_switch(self) -> Dict[str, Any]:
        """禁用 Kill Switch"""
        self.feature_flags.set("telegram.kill_switch_enabled", False)
        return {
            "success": True,
            "kill_switch_enabled": False,
            "message": "✅ Kill Switch 已禁用，自动推进已恢复"
        }
    
    def get_status(self) -> Dict[str, Any]:
        """获取当前状态"""
        return {
            "mode": self.feature_flags.get_mode(),
            "main_flow_enabled": self.feature_flags.is_main_flow_enabled(),
            "kill_switch_enabled": self.feature_flags.is_kill_switch_enabled(),
            "high_risk_requires_approval": self.feature_flags.get("telegram.high_risk_requires_approval"),
            "allow_background_resume": self.feature_flags.get("telegram.allow_background_resume")
        }


# 便捷函数
def create_auto_start_decision(
    event: Dict[str, Any],
    route_decision: Dict[str, Any],
    risk_assessment: Optional[Dict[str, Any]] = None
) -> AutoStartDecision:
    """便捷函数：创建自动启动决策"""
    controller = AutoStartController()
    return controller.decide(event, route_decision, risk_assessment)
