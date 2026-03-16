"""
Risk Classifier - Minimal Implementation

R0-R3 风险分类器。

Author: Autonomy Closure
Created: 2026-03-16
Version: 1.0.0-minimal
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, List, Dict, Any, Set
from datetime import datetime, timezone


class RiskLevel(Enum):
    """风险等级"""
    R0_READONLY = "r0_readonly"
    R1_REVERSIBLE = "r1_reversible"
    R2_MEDIUM = "r2_medium"
    R3_DESTRUCTIVE = "r3_destructive"


@dataclass
class RiskAssessment:
    """风险评估结果"""
    level: RiskLevel
    confidence: float
    matched_keywords: List[str]
    requires_approval: bool
    approval_reason: Optional[str]
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "level": self.level.value,
            "confidence": self.confidence,
            "matched_keywords": self.matched_keywords,
            "requires_approval": self.requires_approval,
            "approval_reason": self.approval_reason,
            "timestamp": self.timestamp.isoformat(),
        }


class RiskClassifier:
    """
    风险分类器
    
    基于 RISK_BLOCKER_GOVERNOR.md 中定义的 R0-R3 分类规则。
    """
    
    # R3: Destructive / 不可逆
    R3_PATTERNS: Set[str] = {
        "delete", "remove", "destroy", "drop", "truncate",
        "publish", "deploy", "release", "production", "prod",
        "irreversible", "destructive", "permanent",
        "database delete", "schema change",
        "external api", "webhook", "payment",
    }
    
    # R2: 中风险
    R2_PATTERNS: Set[str] = {
        "migrate", "refactor", "update", "upgrade",
        "modify", "change", "alter", "transform",
        "multi-file", "batch", "bulk",
    }
    
    # R1: 可逆
    R1_PATTERNS: Set[str] = {
        "create", "add", "write", "generate",
        "test", "build", "install",
        "local", "temporary", "backup",
    }
    
    # R0: 只读
    R0_PATTERNS: Set[str] = {
        "read", "query", "analyze", "check", "verify",
        "list", "show", "get", "fetch", "search",
        "report", "summary", "status",
    }
    
    def __init__(self):
        self._assessment_history: List[RiskAssessment] = []
    
    def classify(
        self,
        action: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> RiskAssessment:
        """
        分类风险等级
        
        Args:
            action: 动作描述
            context: 额外上下文
        
        Returns:
            RiskAssessment
        """
        action_lower = action.lower()
        matched_r3 = []
        matched_r2 = []
        matched_r1 = []
        matched_r0 = []
        
        # 检测 R3
        for pattern in self.R3_PATTERNS:
            if pattern in action_lower:
                matched_r3.append(pattern)
        
        # 检测 R2
        for pattern in self.R2_PATTERNS:
            if pattern in action_lower:
                matched_r2.append(pattern)
        
        # 检测 R1
        for pattern in self.R1_PATTERNS:
            if pattern in action_lower:
                matched_r1.append(pattern)
        
        # 检测 R0
        for pattern in self.R0_PATTERNS:
            if pattern in action_lower:
                matched_r0.append(pattern)
        
        # 确定风险等级（优先级：R3 > R2 > R1 > R0）
        if matched_r3:
            level = RiskLevel.R3_DESTRUCTIVE
            matched = matched_r3
            confidence = len(matched_r3) / max(len(self.R3_PATTERNS), 1)
        elif matched_r2:
            level = RiskLevel.R2_MEDIUM
            matched = matched_r2
            confidence = len(matched_r2) / max(len(self.R2_PATTERNS), 1)
        elif matched_r1:
            level = RiskLevel.R1_REVERSIBLE
            matched = matched_r1
            confidence = len(matched_r1) / max(len(self.R1_PATTERNS), 1)
        elif matched_r0:
            level = RiskLevel.R0_READONLY
            matched = matched_r0
            confidence = len(matched_r0) / max(len(self.R0_PATTERNS), 1)
        else:
            # 未知操作，默认 R2（保守）
            level = RiskLevel.R2_MEDIUM
            matched = []
            confidence = 0.0
        
        # 是否需要审批
        requires_approval = level == RiskLevel.R3_DESTRUCTIVE
        approval_reason = None
        if requires_approval:
            approval_reason = f"R3 action detected: {', '.join(matched)}"
        
        assessment = RiskAssessment(
            level=level,
            confidence=min(confidence, 1.0),
            matched_keywords=matched,
            requires_approval=requires_approval,
            approval_reason=approval_reason,
            timestamp=datetime.now(timezone.utc),
        )
        
        self._assessment_history.append(assessment)
        return assessment
    
    def is_action_allowed(
        self,
        action: str,
        approved_r3: bool = False,
    ) -> tuple[bool, str]:
        """
        检查动作是否允许
        
        Args:
            action: 动作描述
            approved_r3: R3 是否已获批准
        
        Returns:
            (allowed, reason)
        """
        assessment = self.classify(action)
        
        if assessment.level == RiskLevel.R3_DESTRUCTIVE:
            if approved_r3:
                return True, "R3 action approved"
            else:
                return False, "R3 action requires human approval"
        
        return True, f"Action allowed: {assessment.level.value}"
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计"""
        total = len(self._assessment_history)
        if total == 0:
            return {"total": 0, "by_level": {}}
        
        by_level = {}
        for level in RiskLevel:
            by_level[level.value] = sum(
                1 for a in self._assessment_history
                if a.level == level
            )
        
        return {
            "total": total,
            "by_level": by_level,
            "approval_required_count": sum(
                1 for a in self._assessment_history
                if a.requires_approval
            ),
        }


def create_risk_classifier() -> RiskClassifier:
    """创建风险分类器"""
    return RiskClassifier()
