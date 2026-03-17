#!/usr/bin/env python3
"""
Agent Enablement State

Agent 启用状态分层：
- default_enabled: 默认接管，已验证稳定
- pilot_enabled: 灰度试点，受控运行
- manual_enable_only: 仅手动启用
- quarantine: 隔离状态，禁止自动运行

状态机：
manual_enable_only ↔ pilot_enabled ↔ default_enabled
                                         ↓
                                    quarantine

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
import yaml


class EnablementTier(str, Enum):
    """启用层级"""
    DEFAULT_ENABLED = "default_enabled"
    PILOT_ENABLED = "pilot_enabled"
    MANUAL_ENABLE_ONLY = "manual_enable_only"
    QUARANTINE = "quarantine"


@dataclass
class EnablementRecord:
    """启用记录"""
    agent_id: str
    tier: EnablementTier
    previous_tier: Optional[EnablementTier] = None
    reason: str = ""
    timestamp: str = ""
    evidence: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "tier": self.tier.value,
            "previous_tier": self.previous_tier.value if self.previous_tier else None,
            "reason": self.reason,
            "timestamp": self.timestamp,
            "evidence": self.evidence,
        }


class EnablementState:
    """
    Agent 启用状态管理
    
    管理所有 Agent 的启用层级和状态转换。
    """
    
    # 层级定义
    TIER_DEFINITIONS = {
        EnablementTier.DEFAULT_ENABLED: {
            "description": "默认接管，已通过多轮验证",
            "auto_execute": True,
            "requires_intervention": False,
            "conditions": [
                "冷启动稳定",
                "规则遵循稳定",
                "写回稳定",
                "warning/critical 口径稳定",
            ],
        },
        EnablementTier.PILOT_ENABLED: {
            "description": "灰度试点，受控条件下运行",
            "auto_execute": True,
            "requires_intervention": False,
            "conditions": [
                "已接入底座能力",
                "已通过基础验证",
                "需持续观察指标",
            ],
        },
        EnablementTier.MANUAL_ENABLE_ONLY: {
            "description": "仅手动启用，高风险或新接入",
            "auto_execute": False,
            "requires_intervention": True,
            "conditions": [
                "高风险 Agent",
                "新接入未验证",
                "规则尚未稳定",
            ],
        },
        EnablementTier.QUARANTINE: {
            "description": "隔离状态，禁止自动运行",
            "auto_execute": False,
            "requires_intervention": True,
            "conditions": [
                "连续 critical",
                "严重治理失败",
                "待修复后恢复",
            ],
        },
    }
    
    # 允许的状态转换
    ALLOWED_TRANSITIONS = {
        EnablementTier.MANUAL_ENABLE_ONLY: [EnablementTier.PILOT_ENABLED],
        EnablementTier.PILOT_ENABLED: [EnablementTier.DEFAULT_ENABLED, EnablementTier.MANUAL_ENABLE_ONLY],
        EnablementTier.DEFAULT_ENABLED: [EnablementTier.PILOT_ENABLED, EnablementTier.QUARANTINE],
        EnablementTier.QUARANTINE: [EnablementTier.MANUAL_ENABLE_ONLY],
    }
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.state_file = project_root / "config" / "enablement_state.yaml"
        self.history_dir = project_root / "logs" / "enablement_history"
        
        # 加载当前状态
        self.states: Dict[str, EnablementTier] = {}
        self._load_states()
    
    def _load_states(self) -> None:
        """加载启用状态"""
        if self.state_file.exists():
            with open(self.state_file, "r") as f:
                data = yaml.safe_load(f) or {}
            
            for agent_id, tier_str in data.get("agents", {}).items():
                try:
                    self.states[agent_id] = EnablementTier(tier_str)
                except ValueError:
                    self.states[agent_id] = EnablementTier.MANUAL_ENABLE_ONLY
    
    def _save_states(self) -> None:
        """保存启用状态"""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "version": "1.0",
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "agents": {
                agent_id: tier.value
                for agent_id, tier in self.states.items()
            },
        }
        
        with open(self.state_file, "w") as f:
            yaml.dump(data, f)
    
    def _record_transition(self, record: EnablementRecord) -> None:
        """记录状态转换"""
        self.history_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        history_file = self.history_dir / f"{record.agent_id}_{timestamp}.json"
        
        with open(history_file, "w") as f:
            json.dump(record.to_dict(), f, indent=2)
    
    def get_tier(self, agent_id: str) -> EnablementTier:
        """获取 Agent 启用层级"""
        return self.states.get(agent_id, EnablementTier.MANUAL_ENABLE_ONLY)
    
    def is_auto_execute(self, agent_id: str) -> bool:
        """检查 Agent 是否允许自动执行"""
        tier = self.get_tier(agent_id)
        return self.TIER_DEFINITIONS[tier]["auto_execute"]
    
    def set_tier(
        self,
        agent_id: str,
        new_tier: EnablementTier,
        reason: str,
        evidence: Optional[List[str]] = None,
    ) -> bool:
        """
        设置 Agent 启用层级
        
        Args:
            agent_id: Agent ID
            new_tier: 新层级
            reason: 原因
            evidence: 证据列表
        
        Returns:
            是否成功
        """
        current_tier = self.get_tier(agent_id)
        
        # 检查是否允许转换
        if new_tier not in self.ALLOWED_TRANSITIONS.get(current_tier, []):
            # 特殊情况：初始设置
            if current_tier == EnablementTier.MANUAL_ENABLE_ONLY and agent_id not in self.states:
                pass  # 允许初始设置
            else:
                return False
        
        # 记录转换
        record = EnablementRecord(
            agent_id=agent_id,
            tier=new_tier,
            previous_tier=current_tier,
            reason=reason,
            timestamp=datetime.now(timezone.utc).isoformat(),
            evidence=evidence or [],
        )
        
        # 更新状态
        self.states[agent_id] = new_tier
        self._save_states()
        self._record_transition(record)
        
        return True
    
    def rollout(self, agent_id: str, target_tier: EnablementTier, reason: str) -> bool:
        """
        推进 Agent 到更高层级
        
        Args:
            agent_id: Agent ID
            target_tier: 目标层级
            reason: 原因
        
        Returns:
            是否成功
        """
        return self.set_tier(agent_id, target_tier, reason)
    
    def rollback(self, agent_id: str, reason: str) -> bool:
        """
        回退 Agent 到更低层级
        
        Args:
            agent_id: Agent ID
            reason: 原因
        
        Returns:
            是否成功
        """
        current_tier = self.get_tier(agent_id)
        
        if current_tier == EnablementTier.DEFAULT_ENABLED:
            return self.set_tier(agent_id, EnablementTier.PILOT_ENABLED, reason)
        elif current_tier == EnablementTier.PILOT_ENABLED:
            return self.set_tier(agent_id, EnablementTier.MANUAL_ENABLE_ONLY, reason)
        
        return False
    
    def quarantine(self, agent_id: str, reason: str, evidence: Optional[List[str]] = None) -> bool:
        """
        隔离 Agent
        
        Args:
            agent_id: Agent ID
            reason: 原因
            evidence: 证据列表
        
        Returns:
            是否成功
        """
        current_tier = self.get_tier(agent_id)
        
        if current_tier == EnablementTier.DEFAULT_ENABLED:
            return self.set_tier(
                agent_id,
                EnablementTier.QUARANTINE,
                f"QUARANTINE: {reason}",
                evidence,
            )
        
        return False
    
    def recover(self, agent_id: str, reason: str) -> bool:
        """
        从隔离状态恢复
        
        Args:
            agent_id: Agent ID
            reason: 原因
        
        Returns:
            是否成功
        """
        current_tier = self.get_tier(agent_id)
        
        if current_tier == EnablementTier.QUARANTINE:
            return self.set_tier(
                agent_id,
                EnablementTier.MANUAL_ENABLE_ONLY,
                f"RECOVERY: {reason}",
            )
        
        return False
    
    def get_all_states(self) -> Dict[str, str]:
        """获取所有 Agent 状态"""
        return {
            agent_id: tier.value
            for agent_id, tier in self.states.items()
        }
    
    def get_tier_summary(self) -> Dict[str, List[str]]:
        """按层级汇总"""
        summary = {tier.value: [] for tier in EnablementTier}
        
        for agent_id, tier in self.states.items():
            summary[tier.value].append(agent_id)
        
        return summary
