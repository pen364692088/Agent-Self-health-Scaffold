#!/usr/bin/env python3
"""
Health Action Matrix

健康状态 → 治理动作矩阵。

状态分级与动作定义：
- healthy: 正常继续，记录 evidence
- warning: 允许继续，但强制记录、标记风险、建议恢复或下次检查
- critical: 阻断当前高风险动作，触发 recovery / require intervention

Author: Runtime
Created: 2026-03-17
Version: 1.0.0
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum
from pathlib import Path
from datetime import datetime, timezone
import json


class HealthAction(str, Enum):
    """治理动作"""
    # Healthy
    CONTINUE_WITH_EVIDENCE = "continue_with_evidence"
    
    # Warning
    CONTINUE_WITH_MONITORING = "continue_with_monitoring"
    LOG_RISK = "log_risk"
    SCHEDULE_RECOVERY = "schedule_recovery"
    
    # Critical
    BLOCK_AND_RECOVER = "block_and_recover"
    REQUIRE_INTERVENTION = "require_intervention"
    EMERGENCY_SHUTDOWN = "emergency_shutdown"


class ActionSeverity(str, Enum):
    """动作严重程度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ActionDecision:
    """治理动作决策"""
    action: HealthAction
    severity: ActionSeverity
    allow_continue: bool
    require_intervention: bool
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    recommended_actions: List[str] = field(default_factory=list)


class HealthActionMatrix:
    """
    健康状态治理动作矩阵
    
    根据健康状态产出可执行的治理动作结论。
    """
    
    # 健康状态 → 动作矩阵
    MATRIX = {
        "healthy": {
            "action": HealthAction.CONTINUE_WITH_EVIDENCE,
            "severity": ActionSeverity.LOW,
            "allow_continue": True,
            "require_intervention": False,
            "message": "系统健康，正常继续执行",
            "recommended_actions": [
                "记录本次执行的 evidence",
                "更新执行状态",
            ],
        },
        "warning": {
            "action": HealthAction.CONTINUE_WITH_MONITORING,
            "severity": ActionSeverity.MEDIUM,
            "allow_continue": True,
            "require_intervention": False,
            "message": "存在风险，允许继续但需监控",
            "recommended_actions": [
                "强制记录风险到日志",
                "标记风险项",
                "建议下次检查前恢复",
                "如连续多次 warning，升级为 critical",
            ],
        },
        "critical": {
            "action": HealthAction.BLOCK_AND_RECOVER,
            "severity": ActionSeverity.CRITICAL,
            "allow_continue": False,
            "require_intervention": True,
            "message": "严重问题，阻断高风险动作",
            "recommended_actions": [
                "立即阻断当前高风险动作",
                "触发 recovery 流程",
                "通知需要人工干预",
                "记录完整错误上下文",
            ],
        },
    }
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
    
    def decide(self, health_status: str, context: Optional[Dict] = None) -> ActionDecision:
        """
        根据健康状态做出治理动作决策
        
        Args:
            health_status: 健康状态 (healthy/warning/critical)
            context: 上下文信息
        
        Returns:
            ActionDecision
        """
        matrix_entry = self.MATRIX.get(health_status)
        
        if not matrix_entry:
            # 未知状态，视为 critical
            matrix_entry = self.MATRIX["critical"]
            health_status = "critical"
        
        decision = ActionDecision(
            action=matrix_entry["action"],
            severity=matrix_entry["severity"],
            allow_continue=matrix_entry["allow_continue"],
            require_intervention=matrix_entry["require_intervention"],
            message=matrix_entry["message"],
            details={
                "health_status": health_status,
                "context": context or {},
            },
            recommended_actions=matrix_entry["recommended_actions"],
        )
        
        return decision
    
    def execute(self, decision: ActionDecision, agent_id: str) -> Dict[str, Any]:
        """
        执行治理动作
        
        Args:
            decision: 治理动作决策
            agent_id: Agent ID
        
        Returns:
            执行结果
        """
        result = {
            "agent_id": agent_id,
            "action": decision.action.value,
            "severity": decision.severity.value,
            "allow_continue": decision.allow_continue,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "executed": False,
            "log_path": None,
        }
        
        # 记录治理动作
        action_log = self._log_action(agent_id, decision)
        result["executed"] = action_log["success"]
        result["log_path"] = action_log.get("path")
        
        # 如果需要干预，创建干预请求
        if decision.require_intervention:
            intervention = self._create_intervention_request(agent_id, decision)
            result["intervention_id"] = intervention.get("id")
        
        return result
    
    def _log_action(self, agent_id: str, decision: ActionDecision) -> Dict[str, Any]:
        """记录治理动作到日志"""
        try:
            logs_dir = self.project_root / "logs" / "health_actions"
            logs_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            log_path = logs_dir / f"{agent_id}_{timestamp}.json"
            
            log_entry = {
                "agent_id": agent_id,
                "action": decision.action.value,
                "severity": decision.severity.value,
                "message": decision.message,
                "details": decision.details,
                "recommended_actions": decision.recommended_actions,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            
            with open(log_path, "w") as f:
                json.dump(log_entry, f, indent=2)
            
            return {"success": True, "path": str(log_path)}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _create_intervention_request(self, agent_id: str, decision: ActionDecision) -> Dict[str, Any]:
        """创建干预请求"""
        try:
            interventions_dir = self.project_root / "interventions"
            interventions_dir.mkdir(exist_ok=True)
            
            intervention_id = f"{agent_id}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
            intervention_path = interventions_dir / f"{intervention_id}.json"
            
            intervention = {
                "id": intervention_id,
                "agent_id": agent_id,
                "severity": decision.severity.value,
                "message": decision.message,
                "details": decision.details,
                "recommended_actions": decision.recommended_actions,
                "status": "pending",
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            
            with open(intervention_path, "w") as f:
                json.dump(intervention, f, indent=2)
            
            return {"success": True, "id": intervention_id, "path": str(intervention_path)}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def should_block(self, health_status: str) -> bool:
        """判断是否应该阻断"""
        decision = self.decide(health_status)
        return not decision.allow_continue
    
    def get_action_summary(self, health_status: str) -> str:
        """获取动作摘要"""
        decision = self.decide(health_status)
        
        lines = [
            f"Health Status: {health_status.upper()}",
            f"Action: {decision.action.value}",
            f"Severity: {decision.severity.value}",
            f"Allow Continue: {decision.allow_continue}",
            "",
            f"Message: {decision.message}",
            "",
            "Recommended Actions:",
        ]
        
        for action in decision.recommended_actions:
            lines.append(f"  - {action}")
        
        return "\n".join(lines)
