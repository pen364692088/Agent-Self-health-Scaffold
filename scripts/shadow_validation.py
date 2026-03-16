#!/usr/bin/env python3
"""
Memory Kernel Shadow Validation Script

验证 M4a + M5a 的边界是否成立。

Author: Memory Kernel
Created: 2026-03-15
Version: 1.0.0
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from contract.memory.types import (
    MemoryRecord,
    MemoryScope,
    MemoryTier,
    MemorySourceKind,
    MemoryContentType,
    TruthKnowledgeRetrieval,
)
from core.memory.memory_capture import (
    CaptureEngine,
    CaptureWhitelist,
    CaptureReason,
    SourceRef,
    CaptureMetadata,
)
from core.memory.memory_candidate_store import CandidateStore
from core.memory.memory_recall import (
    RecallEngine,
    RecallConfig,
)
from core.memory.memory_search import MemorySearchEngine


@dataclass
class CaptureMetrics:
    """捕获指标"""
    total_candidates: int = 0
    noise_filtered: int = 0
    noise_filter_rate: float = 0.0
    duplicates: int = 0
    dedup_rate: float = 0.0
    whitelist_rejected: int = 0
    promotion_suggested: int = 0
    promotion_approved: int = 0
    promotion_rate: float = 0.0
    authority_leaked: int = 0  # candidate 越权数


@dataclass
class RecallMetrics:
    """召回指标"""
    total_queries: int = 0
    approved_hits: int = 0
    approved_hit_rate: float = 0.0
    candidate_visible_shadow: int = 0
    candidate_leaked_production: int = 0  # candidate 在 production 模式泄露
    scope_filtered: int = 0
    truth_quotes: int = 0
    truth_correct: int = 0
    truth_correct_rate: float = 0.0
    fail_open_triggered: int = 0
    main_chain_affected: bool = False


class ShadowValidator:
    """Shadow 验证器"""
    
    def __init__(self):
        self.capture_metrics = CaptureMetrics()
        self.recall_metrics = RecallMetrics()
        self.capture_engine = CaptureEngine()
        self.candidate_store = CandidateStore()
        self.approved_records: List[MemoryRecord] = []
        self.errors: List[str] = []
    
    def setup_approved_records(self):
        """设置 approved 记录"""
        now = datetime.now(timezone.utc)
        
        self.approved_records = [
            MemoryRecord(
                id="mem_approved_001",
                source_file="memory/approved/rule1.md",
                source_kind=MemorySourceKind.DECISION_LOG,
                content_type=MemoryContentType.RULE,
                scope=MemoryScope.GLOBAL,
                tkr_layer=TruthKnowledgeRetrieval.KNOWLEDGE,
                title="API Versioning Rule",
                content="All API endpoints must be versioned with /vN prefix",
                tags=["api", "versioning"],
                created_at=now - timedelta(days=1),
            ),
            MemoryRecord(
                id="mem_approved_002",
                source_file="memory/approved/truth1.md",
                source_kind=MemorySourceKind.RULE,
                content_type=MemoryContentType.RULE,
                scope=MemoryScope.GLOBAL,
                tkr_layer=TruthKnowledgeRetrieval.TRUTH,
                title="Configuration Path",
                content="All configuration files are located in ~/.openclaw/ directory",
                tags=["config"],
                created_at=now - timedelta(days=2),
            ),
            MemoryRecord(
                id="mem_approved_003",
                source_file="memory/approved/fact1.md",
                source_kind=MemorySourceKind.TECHNICAL_NOTE,
                content_type=MemoryContentType.FACT,
                scope=MemoryScope.PROJECTS,
                scope_qualifier="openemotion",
                tkr_layer=TruthKnowledgeRetrieval.RETRIEVAL,
                title="OpenEmotion Architecture",
                content="OpenEmotion uses transformer model for emotion recognition",
                tags=["openemotion", "architecture"],
                created_at=now - timedelta(days=3),
            ),
        ]
    
    def validate_capture(self) -> Dict[str, Any]:
        """验证捕获"""
        print("=" * 60)
        print("CAPTURE VALIDATION")
        print("=" * 60)
        
        test_cases = [
            # (title, content, metadata, expected_result, category)
            ("Valid Capture", "This is a valid memory capture test content.", self._create_metadata(0.9, 0.8), True, "valid"),
            ("Noise - Empty", "", self._create_metadata(0.9, 0.8), False, "noise"),
            ("Noise - Short", "Hi", self._create_metadata(0.9, 0.8), False, "noise"),
            ("Noise - Whitespace", "   \n\t  ", self._create_metadata(0.9, 0.8), False, "noise"),
            ("Low Confidence", "Valid content but low confidence.", self._create_metadata(0.3, 0.8), False, "whitelist"),
            ("Low Importance", "Valid content but low importance.", self._create_metadata(0.9, 0.2), False, "whitelist"),
            ("Duplicate 1", "This is duplicate content.", self._create_metadata(0.9, 0.8), True, "valid"),
            ("Duplicate 2", "This is duplicate content.", self._create_metadata(0.9, 0.8), False, "duplicate"),
        ]
        
        results = []
        
        for title, content, metadata, expected, category in test_cases:
            candidate = self.capture_engine.capture(title, content, metadata)
            success = (candidate is not None) == expected
            
            results.append({
                "title": title,
                "category": category,
                "expected": expected,
                "actual": candidate is not None,
                "success": success,
            })
            
            if candidate:
                self.candidate_store.add(candidate)
                self.capture_metrics.total_candidates += 1
            else:
                if category == "noise":
                    self.capture_metrics.noise_filtered += 1
                elif category == "whitelist":
                    self.capture_metrics.whitelist_rejected += 1
                elif category == "duplicate":
                    self.capture_metrics.duplicates += 1
        
        # 计算指标
        total_tests = len(test_cases)
        noise_tests = sum(1 for t in test_cases if t[4] == "noise")
        dup_tests = sum(1 for t in test_cases if t[4] == "duplicate")
        
        if noise_tests > 0:
            self.capture_metrics.noise_filter_rate = self.capture_metrics.noise_filtered / noise_tests
        
        if dup_tests > 0:
            self.capture_metrics.dedup_rate = self.capture_metrics.duplicates / dup_tests
        
        # 验证 candidate 不越权
        promoted_memories = self.candidate_store.list_promoted_memories()
        self.capture_metrics.authority_leaked = len(promoted_memories)  # 应该是 0
        
        # 打印结果
        print(f"\nTotal Candidates: {self.capture_metrics.total_candidates}")
        print(f"Noise Filtered: {self.capture_metrics.noise_filtered}")
        print(f"Noise Filter Rate: {self.capture_metrics.noise_filter_rate:.1%}")
        print(f"Duplicates: {self.capture_metrics.duplicates}")
        print(f"Dedup Rate: {self.capture_metrics.dedup_rate:.1%}")
        print(f"Whitelist Rejected: {self.capture_metrics.whitelist_rejected}")
        print(f"Authority Leaked: {self.capture_metrics.authority_leaked}")
        
        # 验证通过条件
        passed = self.capture_metrics.authority_leaked == 0
        print(f"\nCAPTURE VALIDATION: {'✅ PASSED' if passed else '❌ FAILED'}")
        
        return {
            "passed": passed,
            "metrics": asdict(self.capture_metrics),
            "results": results,
        }
    
    def validate_recall(self) -> Dict[str, Any]:
        """验证召回"""
        print("\n" + "=" * 60)
        print("RECALL VALIDATION")
        print("=" * 60)
        
        # 初始化召回引擎
        recall_engine = RecallEngine(
            approved_records=self.approved_records,
            config=RecallConfig(mode="production", enable_trace=True),
        )
        
        test_queries = [
            ("API versioning", "approved"),
            ("configuration", "approved"),
            ("openemotion", "approved"),
            ("nonexistent query xyz", "miss"),
        ]
        
        results = []
        
        for query, expected_type in test_queries:
            result = recall_engine.recall(query=query)
            
            hit = len(result.records) > 0
            success = (expected_type == "approved" and hit) or (expected_type == "miss" and not hit)
            
            results.append({
                "query": query,
                "expected": expected_type,
                "hit": hit,
                "records_count": len(result.records),
                "success": success,
            })
            
            self.recall_metrics.total_queries += 1
            if hit:
                self.recall_metrics.approved_hits += 1
        
        # 计算命中率
        if self.recall_metrics.total_queries > 0:
            self.recall_metrics.approved_hit_rate = self.recall_metrics.approved_hits / self.recall_metrics.total_queries
        
        # 验证 candidate 不可见（production 模式）
        print("\n--- Testing candidate visibility ---")
        
        # 添加 candidate 记录
        candidate_record = MemoryRecord(
            id="mem_candidate_test",
            source_file="memory/candidate/test.md",
            source_kind=MemorySourceKind.SESSION_LOG,
            content_type=MemoryContentType.FACT,
            scope=MemoryScope.GLOBAL,
            tkr_layer=TruthKnowledgeRetrieval.RETRIEVAL,
            title="Test Candidate",
            content="This is a candidate record for testing",
            tags=["candidate", "test"],
        )
        
        recall_engine.load_candidate_records([candidate_record])
        
        # Production 模式 - candidate 不应该被召回
        result_prod = recall_engine.recall(query="candidate")
        self.recall_metrics.candidate_leaked_production = len(result_prod.records)
        
        print(f"Production mode - candidate leaked: {self.recall_metrics.candidate_leaked_production}")
        
        # Shadow 模式 - candidate 应该可见（在 trace 中）
        recall_engine.set_mode("shadow")
        recall_engine._config.include_candidates = True
        result_shadow = recall_engine.recall(query="candidate")
        
        if result_shadow.trace:
            self.recall_metrics.candidate_visible_shadow = len(result_shadow.trace.candidate_records)
        
        print(f"Shadow mode - candidate visible: {self.recall_metrics.candidate_visible_shadow}")
        
        # 验证 Truth 精确引用
        print("\n--- Testing Truth quotes ---")
        
        truth_result = recall_engine.recall_with_truth_quote(query="configuration")
        
        self.recall_metrics.truth_quotes = len(truth_result.truth_quotes)
        self.recall_metrics.truth_correct = sum(1 for q in truth_result.truth_quotes if q.verified)
        
        if self.recall_metrics.truth_quotes > 0:
            self.recall_metrics.truth_correct_rate = self.recall_metrics.truth_correct / self.recall_metrics.truth_quotes
        
        print(f"Truth quotes: {self.recall_metrics.truth_quotes}")
        print(f"Truth correct: {self.recall_metrics.truth_correct}")
        print(f"Truth correct rate: {self.recall_metrics.truth_correct_rate:.1%}")
        
        # 打印结果
        print(f"\nTotal Queries: {self.recall_metrics.total_queries}")
        print(f"Approved Hits: {self.recall_metrics.approved_hits}")
        print(f"Hit Rate: {self.recall_metrics.approved_hit_rate:.1%}")
        print(f"Candidate Leaked (Production): {self.recall_metrics.candidate_leaked_production}")
        print(f"Truth Correct Rate: {self.recall_metrics.truth_correct_rate:.1%}")
        
        # 验证通过条件
        passed = (
            self.recall_metrics.candidate_leaked_production == 0 and
            self.recall_metrics.truth_correct_rate >= 1.0
        )
        print(f"\nRECALL VALIDATION: {'✅ PASSED' if passed else '❌ FAILED'}")
        
        return {
            "passed": passed,
            "metrics": asdict(self.recall_metrics),
            "results": results,
        }
    
    def validate_fail_open(self) -> Dict[str, Any]:
        """验证 fail-open"""
        print("\n" + "=" * 60)
        print("FAIL-OPEN VALIDATION")
        print("=" * 60)
        
        # 测试 fail-open - 强制触发错误
        engine = RecallEngine(
            config=RecallConfig(fail_open=True, enable_trace=True),
        )
        
        # 手动破坏搜索引擎来触发错误
        original_engine = engine._search_engine
        engine._search_engine = None  # 强制 None 来触发错误
        
        try:
            result = engine.recall(query="test")
            # fail-open 应该捕获异常并返回空结果
            self.recall_metrics.fail_open_triggered = 1 if len(result.errors) > 0 else 0
            self.recall_metrics.main_chain_affected = False  # 主链继续，没有抛异常
        except Exception as e:
            # 如果抛异常了，说明 fail-open 没有生效
            self.recall_metrics.fail_open_triggered = 0
            self.recall_metrics.main_chain_affected = True
            result = type('obj', (object,), {'errors': [str(e)], 'records': []})()
        finally:
            # 恢复
            engine._search_engine = original_engine
        
        print(f"Fail-open triggered: {self.recall_metrics.fail_open_triggered > 0}")
        print(f"Main chain affected: {self.recall_metrics.main_chain_affected}")
        if hasattr(result, 'errors') and result.errors:
            print(f"Errors: {result.errors}")
        
        # 验证通过条件 - fail_open 触发错误但主链继续
        passed = not self.recall_metrics.main_chain_affected
        print(f"\nFAIL-OPEN VALIDATION: {'✅ PASSED' if passed else '❌ FAILED'}")
        
        return {
            "passed": passed,
            "metrics": {
                "fail_open_triggered": self.recall_metrics.fail_open_triggered,
                "main_chain_affected": self.recall_metrics.main_chain_affected,
            },
        }
    
    def _create_metadata(self, confidence: float, importance: float) -> CaptureMetadata:
        """创建捕获元数据"""
        return CaptureMetadata(
            capture_reason=CaptureReason(
                reason="Shadow validation test",
                category="auto",
            ),
            source_ref=SourceRef(path="validation/shadow_test.md"),
            scope=MemoryScope.GLOBAL,
            importance=importance,
            confidence=confidence,
            authority_level="medium",
        )
    
    def run_full_validation(self) -> Dict[str, Any]:
        """运行完整验证"""
        print("Starting Memory Kernel Shadow Validation...")
        print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
        
        # 设置 approved 记录
        self.setup_approved_records()
        
        # 运行验证
        capture_result = self.validate_capture()
        recall_result = self.validate_recall()
        fail_open_result = self.validate_fail_open()
        
        # 汇总结果
        all_passed = (
            capture_result["passed"] and
            recall_result["passed"] and
            fail_open_result["passed"]
        )
        
        summary = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "overall_passed": all_passed,
            "capture": capture_result,
            "recall": recall_result,
            "fail_open": fail_open_result,
        }
        
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"Capture: {'✅ PASSED' if capture_result['passed'] else '❌ FAILED'}")
        print(f"Recall: {'✅ PASSED' if recall_result['passed'] else '❌ FAILED'}")
        print(f"Fail-Open: {'✅ PASSED' if fail_open_result['passed'] else '❌ FAILED'}")
        print(f"\nOVERALL: {'✅ ALL PASSED' if all_passed else '❌ SOME FAILED'}")
        
        return summary


def main():
    validator = ShadowValidator()
    summary = validator.run_full_validation()
    
    # 保存结果
    output_path = Path(__file__).parent.parent.parent / "artifacts" / "memory" / "shadow_validation_results.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\nResults saved to: {output_path}")
    
    return 0 if summary["overall_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
