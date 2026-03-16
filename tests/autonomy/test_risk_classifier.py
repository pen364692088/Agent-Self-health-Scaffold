"""
Risk Classifier Tests

Author: Autonomy Closure
Created: 2026-03-16
"""

import pytest
from core.governor.risk_classifier import (
    RiskClassifier,
    RiskLevel,
    RiskAssessment,
    create_risk_classifier,
)


class TestRiskClassification:
    """测试风险分类"""
    
    def test_r0_readonly(self):
        """测试 R0 只读"""
        classifier = create_risk_classifier()
        
        assessment = classifier.classify("read the config file")
        assert assessment.level == RiskLevel.R0_READONLY
        assert assessment.requires_approval is False
    
    def test_r1_reversible(self):
        """测试 R1 可逆"""
        classifier = create_risk_classifier()
        
        assessment = classifier.classify("create a new file")
        assert assessment.level == RiskLevel.R1_REVERSIBLE
        assert assessment.requires_approval is False
    
    def test_r2_medium(self):
        """测试 R2 中风险"""
        classifier = create_risk_classifier()
        
        assessment = classifier.classify("migrate the database")
        assert assessment.level == RiskLevel.R2_MEDIUM
        assert assessment.requires_approval is False
    
    def test_r3_destructive(self):
        """测试 R3 不可逆"""
        classifier = create_risk_classifier()
        
        assessment = classifier.classify("delete the production database")
        assert assessment.level == RiskLevel.R3_DESTRUCTIVE
        assert assessment.requires_approval is True
    
    def test_r3_deploy(self):
        """测试 R3 发布"""
        classifier = create_risk_classifier()
        
        assessment = classifier.classify("deploy to production")
        assert assessment.level == RiskLevel.R3_DESTRUCTIVE
        assert assessment.requires_approval is True


class TestActionAllowed:
    """测试动作是否允许"""
    
    def test_r0_allowed(self):
        """测试 R0 允许"""
        classifier = create_risk_classifier()
        
        allowed, reason = classifier.is_action_allowed("read file")
        assert allowed is True
    
    def test_r3_blocked(self):
        """测试 R3 阻断"""
        classifier = create_risk_classifier()
        
        allowed, reason = classifier.is_action_allowed("delete production data")
        assert allowed is False
        assert "requires human approval" in reason
    
    def test_r3_approved(self):
        """测试 R3 已批准"""
        classifier = create_risk_classifier()
        
        allowed, reason = classifier.is_action_allowed(
            "delete production data",
            approved_r3=True,
        )
        assert allowed is True
        assert "approved" in reason


class TestRiskStats:
    """测试风险统计"""
    
    def test_stats_empty(self):
        """测试空统计"""
        classifier = create_risk_classifier()
        stats = classifier.get_stats()
        
        assert stats["total"] == 0
    
    def test_stats_with_records(self):
        """测试有记录的统计"""
        classifier = create_risk_classifier()
        
        for action in ["read", "create", "delete"]:
            classifier.classify(action)
        
        stats = classifier.get_stats()
        
        assert stats["total"] == 3
        assert stats["approval_required_count"] == 1


class TestAssessmentToDict:
    """测试评估结果转字典"""
    
    def test_to_dict(self):
        """测试转字典"""
        classifier = create_risk_classifier()
        assessment = classifier.classify("test action")
        
        data = assessment.to_dict()
        
        assert "level" in data
        assert "confidence" in data
        assert "requires_approval" in data
        assert "timestamp" in data
