"""
Recall Trace Tests

测试 M5a 召回追踪功能。

Author: Memory Kernel
Created: 2026-03-15
Version: 1.0.0
"""

import pytest
from datetime import datetime, timezone
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.memory.recall_trace import (
    TraceStage,
    RecallTrace,
    RecallTraceBuilder,
    TruthQuote,
    create_trace_builder,
)


# ============== TraceStage Tests ==============

class TestTraceStage:
    """测试追踪阶段"""
    
    def test_stage_creation(self):
        """测试阶段创建"""
        stage = TraceStage(
            name="search_approved",
            input_count=100,
            output_count=10,
            timing_ms=5.5,
        )
        
        assert stage.name == "search_approved"
        assert stage.input_count == 100
        assert stage.output_count == 10
        assert stage.timing_ms == 5.5
    
    def test_stage_with_details(self):
        """测试带详细信息的阶段"""
        stage = TraceStage(
            name="filter",
            input_count=100,
            output_count=50,
            timing_ms=2.0,
            details={"filter_type": "scope"},
        )
        
        assert stage.details["filter_type"] == "scope"


# ============== RecallTrace Tests ==============

class TestRecallTrace:
    """测试召回追踪"""
    
    def test_trace_creation(self):
        """测试追踪创建"""
        trace = RecallTrace(
            query="test query",
            mode="production",
        )
        
        assert trace.query == "test query"
        assert trace.mode == "production"
        assert len(trace.stages) == 0
    
    def test_add_stage(self):
        """测试添加阶段"""
        trace = RecallTrace(query="test", mode="production")
        
        trace.add_stage(
            name="search",
            input_count=100,
            output_count=10,
            timing_ms=5.0,
        )
        
        assert len(trace.stages) == 1
        assert trace.stages[0].name == "search"
    
    def test_add_error(self):
        """测试添加错误"""
        trace = RecallTrace(query="test", mode="production")
        
        trace.add_error("Something went wrong")
        
        assert len(trace.errors) == 1
        assert "wrong" in trace.errors[0]
    
    def test_add_warning(self):
        """测试添加警告"""
        trace = RecallTrace(query="test", mode="production")
        
        trace.add_warning("This is a warning")
        
        assert len(trace.warnings) == 1
    
    def test_add_approved_record(self):
        """测试添加 approved 记录"""
        trace = RecallTrace(query="test", mode="production")
        
        trace.add_approved_record("mem_001")
        
        assert len(trace.approved_records) == 1
        assert "mem_001" in trace.approved_records
    
    def test_add_candidate_record(self):
        """测试添加 candidate 记录"""
        trace = RecallTrace(query="test", mode="shadow")
        
        trace.add_candidate_record("cand_001")
        
        assert len(trace.candidate_records) == 1
        assert "cand_001" in trace.candidate_records
    
    def test_add_truth_quote(self):
        """测试添加 Truth 引用"""
        trace = RecallTrace(query="test", mode="production")
        
        trace.add_truth_quote(
            record_id="mem_truth_001",
            exact_quote="This is an exact quote from the original content",
            source_ref={"path": "memory/truth.md"},
        )
        
        assert len(trace.truth_quotes) == 1
        assert trace.truth_quotes[0]["record_id"] == "mem_truth_001"
    
    def test_to_dict(self):
        """测试转换为字典"""
        trace = RecallTrace(
            query="test",
            mode="production",
            total_scanned=100,
            returned_count=10,
        )
        
        trace_dict = trace.to_dict()
        
        assert trace_dict["query"] == "test"
        assert trace_dict["total_scanned"] == 100
        assert "timestamp" in trace_dict
    
    def test_is_success(self):
        """测试成功状态"""
        trace = RecallTrace(query="test", mode="production")
        
        assert trace.is_success() is True
        
        trace.add_error("Error")
        
        assert trace.is_success() is False
    
    def test_has_candidates(self):
        """测试是否有候选"""
        trace = RecallTrace(query="test", mode="production")
        
        assert trace.has_candidates() is False
        
        trace.add_candidate_record("cand_001")
        
        assert trace.has_candidates() is True
    
    def test_has_truth_quotes(self):
        """测试是否有 Truth 引用"""
        trace = RecallTrace(query="test", mode="production")
        
        assert trace.has_truth_quotes() is False
        
        trace.add_truth_quote(
            record_id="mem_001",
            exact_quote="quote",
            source_ref={"path": "test.md"},
        )
        
        assert trace.has_truth_quotes() is True


# ============== TruthQuote Tests ==============

class TestTruthQuote:
    """测试 Truth 引用"""
    
    def test_quote_creation(self):
        """测试引用创建"""
        quote = TruthQuote(
            record_id="mem_001",
            exact_quote="This is the exact quote",
            source_ref={"path": "memory/test.md"},
        )
        
        assert quote.record_id == "mem_001"
        assert quote.verified is False
    
    def test_quote_verify_success(self):
        """测试引用验证成功"""
        quote = TruthQuote(
            record_id="mem_001",
            exact_quote="exact quote",
            source_ref={"path": "test.md"},
        )
        
        original = "This is the exact quote from the original content"
        
        result = quote.verify(original)
        
        assert result is True
        assert quote.verified is True
    
    def test_quote_verify_failure(self):
        """测试引用验证失败"""
        quote = TruthQuote(
            record_id="mem_001",
            exact_quote="not in original",
            source_ref={"path": "test.md"},
        )
        
        original = "This is the original content"
        
        result = quote.verify(original)
        
        assert result is False
        assert quote.verified is False
    
    def test_quote_to_dict(self):
        """测试引用转字典"""
        quote = TruthQuote(
            record_id="mem_001",
            exact_quote="quote",
            source_ref={"path": "test.md"},
            verified=True,
        )
        
        quote_dict = quote.to_dict()
        
        assert quote_dict["record_id"] == "mem_001"
        assert quote_dict["verified"] is True


# ============== RecallTraceBuilder Tests ==============

class TestRecallTraceBuilder:
    """测试追踪构建器"""
    
    def test_builder_creation(self):
        """测试构建器创建"""
        builder = create_trace_builder("test query")
        
        assert builder is not None
    
    def test_builder_with_mode(self):
        """测试带模式的构建器"""
        builder = create_trace_builder("test", mode="shadow")
        
        trace = builder.build()
        
        assert trace.mode == "shadow"
    
    def test_builder_timing(self):
        """测试构建器计时"""
        builder = create_trace_builder("test")
        
        builder.start()
        time.sleep(0.01)  # 10ms
        builder.stop()
        
        trace = builder.build()
        
        assert trace.timing_ms > 0
    
    def test_builder_setters(self):
        """测试构建器设置方法"""
        builder = create_trace_builder("test")
        
        builder.set_total_scanned(100)
        builder.set_approved_count(80)
        builder.set_candidate_count(20)
        builder.set_filtered_count(50)
        builder.set_top_k(10)
        builder.set_returned_count(10)
        
        trace = builder.build()
        
        assert trace.total_scanned == 100
        assert trace.approved_count == 80
        assert trace.candidate_count == 20
        assert trace.filtered_count == 50
        assert trace.top_k == 10
        assert trace.returned_count == 10
    
    def test_builder_add_stage(self):
        """测试构建器添加阶段"""
        builder = create_trace_builder("test")
        
        builder.add_stage(
            name="search",
            input_count=100,
            output_count=10,
            timing_ms=5.0,
            details={"key": "value"},
        )
        
        trace = builder.build()
        
        assert len(trace.stages) == 1
        assert trace.stages[0].name == "search"
    
    def test_builder_add_error(self):
        """测试构建器添加错误"""
        builder = create_trace_builder("test")
        
        builder.add_error("Test error")
        
        trace = builder.build()
        
        assert len(trace.errors) == 1
        assert trace.is_success() is False
    
    def test_builder_full_workflow(self):
        """测试构建器完整流程"""
        builder = create_trace_builder("memory kernel")
        
        builder.start()
        
        builder.set_total_scanned(100)
        builder.set_approved_count(100)
        
        builder.add_stage(
            name="search_approved",
            input_count=100,
            output_count=15,
            timing_ms=3.5,
        )
        
        builder.add_approved_record("mem_001")
        builder.add_approved_record("mem_002")
        
        builder.set_filtered_count(15)
        builder.set_returned_count(10)
        
        builder.stop()
        
        trace = builder.build()
        
        assert trace.query == "memory kernel"
        assert trace.total_scanned == 100
        assert len(trace.stages) == 1
        assert len(trace.approved_records) == 2
        assert trace.is_success() is True


# ============== Integration Tests ==============

class TestIntegration:
    """集成测试"""
    
    def test_full_trace_workflow(self):
        """测试完整追踪流程"""
        # 1. 创建构建器
        builder = create_trace_builder("test query", mode="shadow")
        
        # 2. 开始计时
        builder.start()
        
        # 3. 模拟召回过程
        builder.set_total_scanned(100)
        builder.set_approved_count(80)
        builder.set_candidate_count(20)
        
        # 4. 搜索阶段
        builder.add_stage(
            name="search_approved",
            input_count=80,
            output_count=10,
            timing_ms=2.5,
        )
        
        # 5. 添加结果
        for i in range(10):
            builder.add_approved_record(f"mem_{i:03d}")
        
        # 6. Shadow 模式下的候选
        builder.add_stage(
            name="search_candidates",
            input_count=20,
            output_count=3,
            timing_ms=1.0,
            details={"mode": "shadow"},
        )
        
        for i in range(3):
            builder.add_candidate_record(f"cand_{i:03d}")
        
        # 7. 添加 Truth 引用
        builder.add_truth_quote(
            record_id="mem_000",
            exact_quote="This is an exact quote",
            source_ref={"path": "memory/truth.md"},
        )
        
        # 8. 设置返回数量
        builder.set_filtered_count(13)
        builder.set_returned_count(10)
        
        # 9. 停止计时
        builder.stop()
        
        # 10. 构建追踪
        trace = builder.build()
        
        # 验证
        assert trace.mode == "shadow"
        assert trace.total_scanned == 100
        assert len(trace.stages) == 2
        assert len(trace.approved_records) == 10
        assert len(trace.candidate_records) == 3
        assert trace.has_candidates()
        assert trace.has_truth_quotes()
        assert trace.is_success()
    
    def test_trace_with_errors(self):
        """测试带错误的追踪"""
        builder = create_trace_builder("test")
        
        builder.start()
        builder.add_error("Something went wrong")
        builder.add_warning("This is a warning")
        builder.stop()
        
        trace = builder.build()
        
        assert trace.is_success() is False
        assert len(trace.warnings) == 1
