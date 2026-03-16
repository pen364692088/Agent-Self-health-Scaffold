"""
Task Admission Pipeline Tests

Author: Autonomy Closure
Created: 2026-03-16
"""

import pytest
from core.admission.task_admission import (
    TaskAdmissionPipeline,
    RiskLevel,
    AdmissionDecision,
    create_admission_pipeline,
)


class TestRiskClassification:
    """测试风险分类"""
    
    def test_r0_readonly(self):
        """测试 R0 只读操作"""
        pipeline = create_admission_pipeline()
        
        # 只读操作
        decision = pipeline.decide_admission("read the configuration file")
        assert decision.risk_level == RiskLevel.R0
        assert decision.auto_admit is True
        assert decision.requires_checkpoint is False
    
    def test_r1_reversible(self):
        """测试 R1 可逆操作"""
        pipeline = create_admission_pipeline()
        
        # 可逆操作
        decision = pipeline.decide_admission("create a new test file")
        assert decision.risk_level == RiskLevel.R1
        assert decision.auto_admit is True
        assert decision.requires_checkpoint is True
    
    def test_r2_medium(self):
        """测试 R2 中风险操作"""
        pipeline = create_admission_pipeline()
        
        # 中风险操作
        decision = pipeline.decide_admission("migrate the database schema")
        assert decision.risk_level == RiskLevel.R2
        assert decision.auto_admit is True
        assert decision.requires_preflight is True
    
    def test_r3_destructive(self):
        """测试 R3 不可逆操作"""
        pipeline = create_admission_pipeline()
        
        # 不可逆操作
        decision = pipeline.decide_admission("delete the production database")
        assert decision.risk_level == RiskLevel.R3
        assert decision.auto_admit is False
        assert decision.requires_human_approval is True


class TestDeduplication:
    """测试去重"""
    
    def test_duplicate_detection(self):
        """测试重复检测"""
        pipeline = create_admission_pipeline()
        
        # 第一次入队
        decision1 = pipeline.decide_admission("test task")
        assert decision1.auto_admit is True
        
        # 记录入队
        pipeline.record_admission(decision1)
        
        # 第二次入队（重复）
        decision2 = pipeline.decide_admission("test task")
        assert decision2.auto_admit is False
        assert "Duplicate" in decision2.reason
    
    def test_skip_duplicate_check(self):
        """测试跳过去重检查"""
        pipeline = create_admission_pipeline()
        
        decision1 = pipeline.decide_admission("test task")
        pipeline.record_admission(decision1)
        
        # 跳过去重检查
        decision2 = pipeline.decide_admission(
            "test task",
            skip_duplicate_check=True,
        )
        assert decision2.auto_admit is True


class TestAdmissionStats:
    """测试入队统计"""
    
    def test_stats_empty(self):
        """测试空统计"""
        pipeline = create_admission_pipeline()
        stats = pipeline.get_admission_stats()
        
        assert stats["total"] == 0
    
    def test_stats_with_records(self):
        """测试有记录的统计"""
        pipeline = create_admission_pipeline()
        
        # 入队几个任务
        for task in ["read file", "create file", "delete file"]:
            decision = pipeline.decide_admission(task)
            pipeline.record_admission(decision)
        
        stats = pipeline.get_admission_stats()
        
        assert stats["total"] == 3
        assert stats["auto_admitted"] == 2  # read, create
        assert stats["blocked"] == 1  # delete


class TestAdmissionDecision:
    """测试入队决策"""
    
    def test_decision_to_dict(self):
        """测试决策转字典"""
        pipeline = create_admission_pipeline()
        decision = pipeline.decide_admission("test task")
        
        data = decision.to_dict()
        
        assert "task_id" in data
        assert "risk_level" in data
        assert "auto_admit" in data
        assert "timestamp" in data
