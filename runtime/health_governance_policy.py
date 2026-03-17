#!/usr/bin/env python3
"""
Health Governance Policy

健康状态治理策略：
- healthy: 正常继续
- warning_once: 继续但标记风险
- warning_repeated: 升级观察，限制高风险动作
- critical_once: 阻断，触发恢复
- critical_repeated: 隔离，切换到 manual_enable_only

升级规则：
- 连续 N 次 warning → warning_repeated
- 连续 M 次 critical → quarantine
- recovery 成功并稳定 K 次 → 允许恢复

Author: Runtime
Created: 2026-03-17
Version: 1.0.0
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from pathlib import Path
from enum import Enum
from datetime import datetime, timezone
import json


class HealthGovernanceStatus(str, Enum):
    """健康治理状态"""
    HEALTHY = "healthy"
    WARNING_ONCE = "warning_once"
    WARNING_REPEATED = "warning_repeated"
    CRITICAL_ONCE = "critical_once"
    CRITICAL_REPEATED = "critical_repeated"


class GovernanceAction(str, Enum):
    """治理动作"""
    CONTINUE_WITH_EVIDENCE = "continue_with_evidence"
    CONTINUE_WITH_MONITORING = "continue_with_monitoring"
    CONTINUE_WITH_ESCALATION = "continue_with_escalation"
    BLOCK_AND_RECOVER = "block_and_recover"
    QUARANTINE_OR_MANUAL_MODE = "quarantine_or_manual_mode"


@dataclass
class GovernanceDecision:
    """治理决策"""
    status: HealthGovernanceStatus
    action: GovernanceAction
    allow_continue: bool
    requires_intervention: bool
    should_quarantine: bool
    message: str
    recommended_actions: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)


class HealthGovernancePolicy:
    """
    健康治理策略
    
    根据 Agent 的健康历史做出治理决策。
    """
    
    # 阈值配置
    WARNING_THRESHOLD = 2  # 连续 N 次 warning → warning_repeated
    CRITICAL_THRESHOLD = 2  # 连续 M 次 critical → quarantine
    RECOVERY_THRESHOLD = 5  # 成功 K 次 → 允许恢复
    
    # 状态定义
    STATUS_DEFINITIONS = {
        HealthGovernanceStatus.HEALTHY: {
            "action": GovernanceAction.CONTINUE_WITH_EVIDENCE,
            "allow_continue": True,
            "requires_intervention": False,
            "should_quarantine": False,
            "message": "系统健康，正常继续执行",
            "recommended_actions": [
                "记录本次执行的 evidence",
                "更新执行状态",
            ],
        },
        HealthGovernanceStatus.WARNING_ONCE: {
            "action": GovernanceAction.CONTINUE_WITH_MONITORING,
            "allow_continue": True,
            "requires_intervention": False,
            "should_quarantine": False,
            "message": "存在风险，继续运行但需监控",
            "recommended_actions": [
                "强制记录风险到日志",
                "标记风险项",
                "建议下次检查前恢复",
            ],
        },
        HealthGovernanceStatus.WARNING_REPEATED: {
            "action": GovernanceAction.CONTINUE_WITH_ESCALATION,
            "allow_continue": True,
            "requires_intervention": False,
            "should_quarantine": False,
            "message": "连续 warning，升级为重点观察对象",
            "recommended_actions": [
                "限制高风险动作",
                "加强监控频率",
                "准备降级方案",
            ],
        },
        HealthGovernanceStatus.CRITICAL_ONCE: {
            "action": GovernanceAction.BLOCK_AND_RECOVER,
            "allow_continue": False,
            "requires_intervention": True,
            "should_quarantine": False,
            "message": "严重问题，阻断当前高风险动作",
            "recommended_actions": [
                "立即阻断高风险动作",
                "触发 recovery 流程",
                "通知需要人工干预",
            ],
        },
        HealthGovernanceStatus.CRITICAL_REPEATED: {
            "action": GovernanceAction.QUARANTINE_OR_MANUAL_MODE,
            "allow_continue": False,
            "requires_intervention": True,
            "should_quarantine": True,
            "message": "连续 critical，隔离并切换到手动模式",
            "recommended_actions": [
                "取消默认接管",
                "切换为 manual_enable_only",
                "待修复后再恢复",
            ],
        },
    }
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.history_dir = project_root / "logs" / "health_history"
        self.history_dir.mkdir(parents=True, exist_ok=True)
    
    def decide(
        self,
        agent_id: str,
        current_health: str,
        history: Optional[List[str]] = None,
    ) -> GovernanceDecision:
        """
        做出治理决策
        
        Args:
            agent_id: Agent ID
            current_health: 当前健康状态 (healthy/warning/critical)
            history: 历史健康状态列表
        
        Returns:
            GovernanceDecision
        """
        # 获取历史
        if history is None:
            history = self._load_history(agent_id)
        
        # 确定治理状态
        governance_status = self._determine_status(current_health, history)
        
        # 获取状态定义
        definition = self.STATUS_DEFINITIONS[governance_status]
        
        # 构建决策
        decision = GovernanceDecision(
            status=governance_status,
            action=definition["action"],
            allow_continue=definition["allow_continue"],
            requires_intervention=definition["requires_intervention"],
            should_quarantine=definition["should_quarantine"],
            message=definition["message"],
            recommended_actions=definition["recommended_actions"],
            context={
                "agent_id": agent_id,
                "current_health": current_health,
                "history_length": len(history),
            },
        )
        
        # 记录决策
        self._record_decision(agent_id, decision)
        
        return decision
    
    def _determine_status(
        self,
        current_health: str,
        history: List[str],
    ) -> HealthGovernanceStatus:
        """确定治理状态"""
        if current_health == "healthy":
            return HealthGovernanceStatus.HEALTHY
        
        elif current_health == "warning":
            # 检查是否连续 warning
            recent_warnings = self._count_consecutive(history, "warning")
            
            if recent_warnings >= self.WARNING_THRESHOLD:
                return HealthGovernanceStatus.WARNING_REPEATED
            else:
                return HealthGovernanceStatus.WARNING_ONCE
        
        elif current_health == "critical":
            # 检查是否连续 critical
            recent_criticals = self._count_consecutive(history, "critical")
            
            if recent_criticals >= self.CRITICAL_THRESHOLD:
                return HealthGovernanceStatus.CRITICAL_REPEATED
            else:
                return HealthGovernanceStatus.CRITICAL_ONCE
        
        # 未知状态，视为 critical
        return HealthGovernanceStatus.CRITICAL_ONCE
    
    def _count_consecutive(self, history: List[str], target: str) -> int:
        """计算连续出现次数"""
        count = 0
        for status in reversed(history):
            if status == target:
                count += 1
            else:
                break
        return count
    
    def _load_history(self, agent_id: str) -> List[str]:
        """加载历史健康状态"""
        history_file = self.history_dir / f"{agent_id}_history.json"
        
        if not history_file.exists():
            return []
        
        try:
            with open(history_file, "r") as f:
                data = json.load(f)
            return data.get("history", [])
        except Exception:
            return []
    
    def _record_decision(self, agent_id: str, decision: GovernanceDecision) -> None:
        """记录治理决策"""
        history_file = self.history_dir / f"{agent_id}_history.json"
        
        # 加载现有历史
        try:
            with open(history_file, "r") as f:
                data = json.load(f)
            history = data.get("history", [])
        except Exception:
            history = []
        
        # 添加新记录
        history.append(decision.context.get("current_health", "unknown"))
        
        # 只保留最近 100 条
        if len(history) > 100:
            history = history[-100:]
        
        # 保存
        data = {
            "agent_id": agent_id,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "history": history,
            "last_decision": {
                "status": decision.status.value,
                "action": decision.action.value,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        }
        
        with open(history_file, "w") as f:
            json.dump(data, f, indent=2)
    
    def record_recovery(self, agent_id: str) -> bool:
        """
        记录恢复成功
        
        Returns:
            是否达到恢复阈值
        """
        history = self._load_history(agent_id)
        
        # 添加健康记录
        history.append("healthy")
        
        # 检查是否连续健康
        recent_healthy = self._count_consecutive(history, "healthy")
        
        # 保存
        history_file = self.history_dir / f"{agent_id}_history.json"
        data = {
            "agent_id": agent_id,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "history": history,
        }
        
        with open(history_file, "w") as f:
            json.dump(data, f, indent=2)
        
        return recent_healthy >= self.RECOVERY_THRESHOLD
    
    def should_allow_recovery(self, agent_id: str) -> bool:
        """判断是否允许恢复"""
        history = self._load_history(agent_id)
        recent_healthy = self._count_consecutive(history, "healthy")
        return recent_healthy >= self.RECOVERY_THRESHOLD
