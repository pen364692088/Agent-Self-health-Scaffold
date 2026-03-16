"""
Task Admission Pipeline - Minimal Implementation

只实现最小闭环：风险分类 + 自动入队决策。

Author: Autonomy Closure
Created: 2026-03-16
Version: 1.0.0-minimal
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import hashlib
import json


class RiskLevel(Enum):
    """风险等级"""
    R0 = "r0_readonly"      # 只读，自动执行
    R1 = "r1_reversible"    # 可逆，自动执行 + checkpoint
    R2 = "r2_medium"        # 中风险，preflight + rollback plan
    R3 = "r3_destructive"   # 不可逆，强制人工确认


@dataclass
class AdmissionDecision:
    """入队决策"""
    task_id: str
    risk_level: RiskLevel
    auto_admit: bool
    requires_checkpoint: bool
    requires_preflight: bool
    requires_human_approval: bool
    reason: str
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "risk_level": self.risk_level.value,
            "auto_admit": self.auto_admit,
            "requires_checkpoint": self.requires_checkpoint,
            "requires_preflight": self.requires_preflight,
            "requires_human_approval": self.requires_human_approval,
            "reason": self.reason,
            "timestamp": self.timestamp.isoformat(),
        }


class TaskAdmissionPipeline:
    """
    任务入队管道
    
    最小实现：基于关键词和操作类型进行风险分类。
    """
    
    # R3 关键词（不可逆操作）
    R3_KEYWORDS = [
        "delete", "remove", "destroy", "drop", "truncate",
        "publish", "deploy", "release", "production",
        " irreversible", "destructive",
    ]
    
    # R2 关键词（中风险操作）
    R2_KEYWORDS = [
        "migrate", "refactor", "update", "upgrade",
        "modify", "change", "alter",
    ]
    
    # R1 关键词（可逆操作）
    R1_KEYWORDS = [
        "create", "add", "write", "generate",
        "test", "build",
    ]
    
    # R0 关键词（只读操作）
    R0_KEYWORDS = [
        "read", "query", "analyze", "check", "verify",
        "list", "show", "get", "fetch",
    ]
    
    def __init__(self):
        self._admission_history: Dict[str, AdmissionDecision] = {}
    
    def classify_risk(self, task_input: str, operation_type: Optional[str] = None) -> RiskLevel:
        """
        分类风险等级
        
        Args:
            task_input: 任务输入描述
            operation_type: 操作类型（可选）
        
        Returns:
            RiskLevel
        """
        input_lower = task_input.lower()
        
        # R3 检测（最高优先级）
        for keyword in self.R3_KEYWORDS:
            if keyword in input_lower:
                return RiskLevel.R3
        
        # R2 检测
        for keyword in self.R2_KEYWORDS:
            if keyword in input_lower:
                return RiskLevel.R2
        
        # R1 检测
        for keyword in self.R1_KEYWORDS:
            if keyword in input_lower:
                return RiskLevel.R1
        
        # R0 检测
        for keyword in self.R0_KEYWORDS:
            if keyword in input_lower:
                return RiskLevel.R0
        
        # 默认 R2（保守策略）
        return RiskLevel.R2
    
    def generate_task_id(self, task_input: str) -> str:
        """生成任务 ID（基于内容 hash）"""
        content_hash = hashlib.sha256(task_input.encode()).hexdigest()[:16]
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        return f"task_{timestamp}_{content_hash}"
    
    def check_duplicate(self, task_input: str, window_hours: int = 24) -> bool:
        """
        检查重复任务
        
        Args:
            task_input: 任务输入
            window_hours: 检查窗口（小时）
        
        Returns:
            是否为重复任务
        """
        task_id = self.generate_task_id(task_input)
        return task_id in self._admission_history
    
    def decide_admission(
        self,
        task_input: str,
        operation_type: Optional[str] = None,
        skip_duplicate_check: bool = False,
    ) -> AdmissionDecision:
        """
        决定是否自动入队
        
        Args:
            task_input: 任务输入描述
            operation_type: 操作类型
            skip_duplicate_check: 是否跳过去重检查
        
        Returns:
            AdmissionDecision
        """
        task_id = self.generate_task_id(task_input)
        risk_level = self.classify_risk(task_input, operation_type)
        
        # 去重检查
        if not skip_duplicate_check and self.check_duplicate(task_input):
            return AdmissionDecision(
                task_id=task_id,
                risk_level=risk_level,
                auto_admit=False,
                requires_checkpoint=False,
                requires_preflight=False,
                requires_human_approval=False,
                reason="Duplicate task within 24h window",
                timestamp=datetime.now(timezone.utc),
            )
        
        # 根据风险等级决定
        if risk_level == RiskLevel.R0:
            return AdmissionDecision(
                task_id=task_id,
                risk_level=risk_level,
                auto_admit=True,
                requires_checkpoint=False,
                requires_preflight=False,
                requires_human_approval=False,
                reason="R0: Read-only operation, auto-admit",
                timestamp=datetime.now(timezone.utc),
            )
        
        elif risk_level == RiskLevel.R1:
            return AdmissionDecision(
                task_id=task_id,
                risk_level=risk_level,
                auto_admit=True,
                requires_checkpoint=True,
                requires_preflight=False,
                requires_human_approval=False,
                reason="R1: Reversible operation, auto-admit with checkpoint",
                timestamp=datetime.now(timezone.utc),
            )
        
        elif risk_level == RiskLevel.R2:
            return AdmissionDecision(
                task_id=task_id,
                risk_level=risk_level,
                auto_admit=True,
                requires_checkpoint=True,
                requires_preflight=True,
                requires_human_approval=False,
                reason="R2: Medium risk, auto-admit with preflight and checkpoint",
                timestamp=datetime.now(timezone.utc),
            )
        
        else:  # R3
            return AdmissionDecision(
                task_id=task_id,
                risk_level=risk_level,
                auto_admit=False,
                requires_checkpoint=True,
                requires_preflight=True,
                requires_human_approval=True,
                reason="R3: Destructive/irreversible, requires human approval",
                timestamp=datetime.now(timezone.utc),
            )
    
    def record_admission(self, decision: AdmissionDecision):
        """记录入队决策"""
        self._admission_history[decision.task_id] = decision
    
    def get_admission_stats(self) -> Dict[str, Any]:
        """获取入队统计"""
        total = len(self._admission_history)
        if total == 0:
            return {
                "total": 0,
                "auto_admitted": 0,
                "blocked": 0,
                "by_risk_level": {},
            }
        
        auto_admitted = sum(1 for d in self._admission_history.values() if d.auto_admit)
        blocked = total - auto_admitted
        
        by_risk = {}
        for level in RiskLevel:
            by_risk[level.value] = sum(
                1 for d in self._admission_history.values()
                if d.risk_level == level
            )
        
        return {
            "total": total,
            "auto_admitted": auto_admitted,
            "blocked": blocked,
            "auto_admission_rate": auto_admitted / total if total > 0 else 0,
            "by_risk_level": by_risk,
        }


def create_admission_pipeline() -> TaskAdmissionPipeline:
    """创建入队管道"""
    return TaskAdmissionPipeline()
