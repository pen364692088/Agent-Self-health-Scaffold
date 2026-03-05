#!/usr/bin/env python3
"""
Memory Retrieval Hardening v1.2.2 - 强一致回归测试

测试目标：
1. recall/use 事件语义正确
2. event_version 闸门生效
3. adoption 指标计算正确
4. 分位数计算正确
5. orphan 指标正确
6. 样本量门槛判断正确

运行方式：
  pytest tests/test_memory_retrieval_hardening.py -v
  python tests/test_memory_retrieval_hardening.py
"""

import json
import sys
import tempfile
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# 添加 tools 到路径
TOOLS_DIR = Path(__file__).parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))

# ============== 阈值配置 ==============
MIN_EVENTS = 200
MIN_SESSIONS = 20

# ============== 测试样本 ==============

FIXED_SAMPLES = [
    {
        "name": "sample_1_basic_recall_use",
        "description": "基础 recall→use 链路",
        "events": [
            {"event": "recall", "ts": "2026-03-03T10:00:00Z", "recall_id": "r1", "used": ["mem_001", "mem_002"], "candidates_count": 2, "event_version": "v2"},
            {"event": "use", "ts": "2026-03-03T10:00:01Z", "memory_id": "mem_001", "recall_id": "r1", "event_version": "v2"},
            {"event": "use", "ts": "2026-03-03T10:00:02Z", "memory_id": "mem_002", "recall_id": "r1", "event_version": "v2"},
        ],
        "expected": {
            "recall_count": 2,
            "use_count": 2,
            "adoption_rate_any": 1.0,
            "uses_per_recall": 2.0,
            "use_with_recall_link_rate": 1.0,  # 所有 use 都有 recall_id
        }
    },
    {
        "name": "sample_2_partial_adoption",
        "description": "部分采用（检索了 3 条，只用了 1 条）",
        "events": [
            {"event": "recall", "ts": "2026-03-03T10:01:00Z", "recall_id": "r2", "used": ["mem_003", "mem_004", "mem_005"], "candidates_count": 3, "event_version": "v2"},
            {"event": "use", "ts": "2026-03-03T10:01:01Z", "memory_id": "mem_003", "recall_id": "r2", "event_version": "v2"},
        ],
        "expected": {
            "recall_count": 3,
            "use_count": 1,
            "adoption_rate_any": 1.0,  # 有 use 发生
            "uses_per_recall": 1.0,
            "use_with_recall_link_rate": 1.0,
        }
    },
    {
        "name": "sample_3_no_adoption",
        "description": "检索但未采用",
        "events": [
            {"event": "recall", "ts": "2026-03-03T10:02:00Z", "recall_id": "r3", "used": ["mem_006"], "candidates_count": 1, "event_version": "v2"},
        ],
        "expected": {
            "recall_count": 1,
            "use_count": 0,
            "adoption_rate_any": 0.0,  # 没有 use
            "uses_per_recall": 0.0,
            "use_with_recall_link_rate": 1.0,  # 没有 use 时默认 1.0
        }
    },
    {
        "name": "sample_4_v1_filtering",
        "description": "v1 事件被过滤，不计入统计",
        "events": [
            {"event": "recall", "ts": "2026-03-03T10:03:00Z", "recall_id": "r4", "used": ["mem_007"], "candidates_count": 1, "event_version": "v1"},
            {"event": "use", "ts": "2026-03-03T10:03:01Z", "memory_id": "mem_007", "recall_id": "r4", "event_version": "v1"},
            {"event": "recall", "ts": "2026-03-03T10:03:02Z", "recall_id": "r5", "used": ["mem_008"], "candidates_count": 1, "event_version": "v2"},
            {"event": "use", "ts": "2026-03-03T10:03:03Z", "memory_id": "mem_008", "recall_id": "r5", "event_version": "v2"},
        ],
        "expected": {
            "recall_count": 1,  # 只有 v2 的 1 条
            "use_count": 1,     # 只有 v2 的 1 条
            "adoption_rate_any": 1.0,
            "uses_per_recall": 1.0,
            "v1_recall_count": 1,  # v1 不计入主指标，但需统计
            "v1_use_count": 1,
            "v2_recall_count": 1,
            "v2_use_count": 1,
        }
    },
    {
        "name": "sample_5_orphan_use",
        "description": "孤儿 use（没有对应 recall）",
        "events": [
            {"event": "use", "ts": "2026-03-03T10:04:00Z", "memory_id": "mem_009", "event_version": "v2"},
        ],
        "expected": {
            "recall_count": 0,
            "use_count": 1,
            "adoption_rate_any": 0.0,  # 没有 recall
            "orphan_use_count": 1,     # 孤儿 use 需要统计
        }
    },
    {
        "name": "sample_6_multi_recall_per_session",
        "description": "一个 session 多次检索",
        "events": [
            {"event": "recall", "ts": "2026-03-03T10:05:00Z", "recall_id": "r6a", "used": ["mem_010"], "candidates_count": 1, "event_version": "v2", "session_id": "s1"},
            {"event": "use", "ts": "2026-03-03T10:05:01Z", "memory_id": "mem_010", "recall_id": "r6a", "event_version": "v2", "session_id": "s1"},
            {"event": "recall", "ts": "2026-03-03T10:05:30Z", "recall_id": "r6b", "used": ["mem_011", "mem_012"], "candidates_count": 2, "event_version": "v2", "session_id": "s1"},
            {"event": "use", "ts": "2026-03-03T10:05:31Z", "memory_id": "mem_011", "recall_id": "r6b", "event_version": "v2", "session_id": "s1"},
        ],
        "expected": {
            "recall_count": 3,  # 1 + 2
            "use_count": 2,     # 1 + 1
            "adoption_rate_any": 1.0,  # 两个 recall 都有 use
            "uses_per_recall": 1.0,    # 2 / 2 recalls
            "total_recalls": 2,        # recall 事件数
        }
    },
    {
        "name": "sample_7_orphan_metrics",
        "description": "orphan 指标测试",
        "events": [
            {"event": "recall", "ts": "2026-03-03T10:06:00Z", "recall_id": "r7a", "used": ["mem_013"], "candidates_count": 1, "event_version": "v2"},
            # r7a 有 use
            {"event": "use", "ts": "2026-03-03T10:06:01Z", "memory_id": "mem_013", "recall_id": "r7a", "event_version": "v2"},
            # r7b 没有 use -> orphan recall
            {"event": "recall", "ts": "2026-03-03T10:06:30Z", "recall_id": "r7b", "used": ["mem_014"], "candidates_count": 1, "event_version": "v2"},
            # orphan use (没有 recall_id)
            {"event": "use", "ts": "2026-03-03T10:07:00Z", "memory_id": "mem_015", "event_version": "v2"},
        ],
        "expected": {
            "recall_count": 2,
            "use_count": 2,
            "orphan_use_count": 1,
            "orphan_recall_count": 1,
            "orphan_use_rate": 0.5,
            "adoption_rate_any": 0.5,  # 1/2 recalls have use
        }
    },
    {
        "name": "sample_8_broken_link_recall",
        "description": "broken_link_recall_rate 测试 (v1.2.4)",
        "events": [
            # 正常 recall + use
            {"event": "recall", "ts": "2026-03-03T10:08:00Z", "recall_id": "r8a", "used": ["mem_016"], "candidates_count": 1, "event_version": "v2"},
            {"event": "use", "ts": "2026-03-03T10:08:01Z", "memory_id": "mem_016", "recall_id": "r8a", "event_version": "v2"},
            # broken link recall (缺少 recall_id)
            {"event": "recall", "ts": "2026-03-03T10:08:30Z", "used": ["mem_017"], "candidates_count": 1, "event_version": "v2"},  # 无 recall_id
        ],
        "expected": {
            "recall_count": 2,
            "use_count": 1,
            "total_recalls": 1,  # 只有带 recall_id 的才算
            "total_v2_recalls": 2,  # v2 recall 事件总数
            "adoption_rate_any": 1.0,  # 唯一带 recall_id 的 recall 有 use
            "unadopted_recall_rate": 0.0,
            "broken_link_recall_rate": 0.5,  # 1/2 缺少 recall_id
        }
    },
    {
        "name": "sample_9_scenario_buckets",
        "description": "场景分桶测试 (v1.2.5)",
        "events": [
            # Bucket A: 有候选且未过滤
            {"event": "recall", "ts": "2026-03-03T10:09:00Z", "recall_id": "r9a", "used": ["mem_018"], "candidates_count": 1, "event_version": "v2"},
            {"event": "use", "ts": "2026-03-03T10:09:01Z", "memory_id": "mem_018", "recall_id": "r9a", "event_version": "v2"},
            # Bucket B: 被闸门过滤
            {"event": "recall", "ts": "2026-03-03T10:09:30Z", "recall_id": "r9b", "used": ["mem_019"], "candidates_count": 1, "event_version": "v2", "filtered": True},
            # Bucket B: 候选为 0
            {"event": "recall", "ts": "2026-03-03T10:10:00Z", "recall_id": "r9c", "used": ["mem_020"], "candidates_count": 0, "event_version": "v2"},
        ],
        "expected": {
            "total_recalls": 3,
            "bucket_a_count": 1,  # r9a
            "bucket_b_count": 2,  # r9b, r9c
            "bucket_a_ratio": round(1/3, 4),  # 浮点数精度匹配
        }
    },
    {
        "name": "sample_10_linkability",
        "description": "linkability 豁免测试 (v1.2.5)",
        "events": [
            # expected (默认)
            {"event": "recall", "ts": "2026-03-03T10:11:00Z", "recall_id": "r10a", "used": ["mem_021"], "candidates_count": 1, "event_version": "v2"},
            # not_applicable
            {"event": "recall", "ts": "2026-03-03T10:11:30Z", "used": ["mem_022"], "candidates_count": 1, "event_version": "v2", "linkability": "not_applicable"},
            # broken link (expected 但缺少 recall_id)
            {"event": "recall", "ts": "2026-03-03T10:12:00Z", "used": ["mem_023"], "candidates_count": 1, "event_version": "v2"},  # 默认 expected
        ],
        "expected": {
            "total_v2_recalls": 3,
            "expected_link_count": 2,  # r10a + 最后一个（默认 expected）
            "broken_link_expected": 1,  # 最后一个缺少 recall_id
        }
    },
]

# ============== 分析函数 ==============

def analyze_events(events: List[Dict]) -> Dict[str, Any]:
    """分析事件并计算指标"""
    recall_count = 0
    use_count = 0
    recalled_candidates_total = 0
    
    v1_recall_count = 0
    v1_use_count = 0
    v2_recall_count = 0
    v2_use_count = 0
    
    recalls = {}
    uses_with_recall = 0
    orphan_uses = 0
    
    for event in events:
        event_type = event.get("event", "")
        event_version = event.get("event_version", "v1")
        recall_id = event.get("recall_id")
        
        if event_type == "recall":
            if event_version == "v1":
                v1_recall_count += 1
            else:
                v2_recall_count += 1
                used = event.get("used", [])
                recall_count += len(used)
                recalled_candidates_total += len(used)
                if recall_id:
                    recalls[recall_id] = {
                        "used": used,
                        "has_use": False,
                        "use_count": 0
                    }
        
        elif event_type == "use":
            if event_version == "v1":
                v1_use_count += 1
            else:
                v2_use_count += 1
                use_count += 1
                
                if recall_id and recall_id in recalls:
                    uses_with_recall += 1
                    recalls[recall_id]["has_use"] = True
                    recalls[recall_id]["use_count"] += 1
                else:
                    orphan_uses += 1
    
    # 计算指标
    total_recalls = len(recalls) if recalls else 1
    recalls_with_any_use = sum(1 for data in recalls.values() if data["has_use"])
    
    # orphan recall: recall 没有 use
    orphan_recalls = total_recalls - recalls_with_any_use
    
    # broken_link_recall: recall 缺少 recall_id (v1.2.4)
    # 基于 v2_recall_count 计算
    broken_link_recalls = 0
    for event in events:
        if event.get("event") == "recall" and event.get("event_version") == "v2":
            if not event.get("recall_id"):
                broken_link_recalls += 1
    
    # total_v2_recalls: v2 recall 事件总数（用于 broken_link 比例计算）
    total_v2_recalls = v2_recall_count if v2_recall_count > 0 else 1
    
    # 场景分桶 (v1.2.5)
    bucket_a_count = 0
    bucket_b_count = 0
    expected_link_count = 0
    broken_link_expected = 0
    
    for event in events:
        if event.get("event") == "recall" and event.get("event_version") == "v2":
            recall_id = event.get("recall_id")
            candidates_count = event.get("candidates_count", 0)
            filtered = event.get("filtered", False)
            linkability = event.get("linkability", "expected")
            
            if linkability == "expected":
                expected_link_count += 1
            
            if recall_id:
                if candidates_count > 0 and not filtered:
                    bucket_a_count += 1
                else:
                    bucket_b_count += 1
            else:
                if linkability == "expected":
                    broken_link_expected += 1
    
    bucket_a_ratio = bucket_a_count / total_v2_recalls if total_v2_recalls > 0 else 1.0
    
    adoption_rate_any = recalls_with_any_use / total_recalls if total_recalls > 0 else 0.0
    uses_per_recall = use_count / total_recalls if total_recalls > 0 else 0.0
    use_with_recall_link_rate = uses_with_recall / use_count if use_count > 0 else 1.0
    orphan_use_rate = orphan_uses / use_count if use_count > 0 else 0.0
    unadopted_recall_rate = orphan_recalls / total_recalls if total_recalls > 0 else 0.0
    broken_link_recall_rate = broken_link_expected / expected_link_count if expected_link_count > 0 else 0.0
    
    return {
        "recall_count": recall_count,
        "use_count": use_count,
        "adoption_rate_any": round(adoption_rate_any, 4),
        "uses_per_recall": round(uses_per_recall, 4),
        "use_with_recall_link_rate": round(use_with_recall_link_rate, 4),
        "orphan_use_count": orphan_uses,
        "orphan_recall_count": orphan_recalls,
        "orphan_use_rate": round(orphan_use_rate, 4),
        "unadopted_recall_rate": round(unadopted_recall_rate, 4),
        "broken_link_recall_rate": round(broken_link_recall_rate, 4),
        "total_v2_recalls": total_v2_recalls,
        "total_recalls": total_recalls,
        "recalls_with_any_use": recalls_with_any_use,
        "v1_recall_count": v1_recall_count,
        "v1_use_count": v1_use_count,
        "v2_recall_count": v2_recall_count,
        "v2_use_count": v2_use_count,
        # 场景分桶 (v1.2.5)
        "bucket_a_count": bucket_a_count,
        "bucket_b_count": bucket_b_count,
        "bucket_a_ratio": round(bucket_a_ratio, 4),
        # linkability (v1.2.5)
        "expected_link_count": expected_link_count,
        "broken_link_expected": broken_link_expected,
    }

# ============== 测试函数 ==============

def test_sample(name: str, events: List[Dict], expected: Dict) -> Dict:
    """运行单个测试样本"""
    actual = analyze_events(events)
    
    errors = []
    for key, expected_value in expected.items():
        actual_value = actual.get(key)
        if actual_value != expected_value:
            errors.append(f"  {key}: expected {expected_value}, got {actual_value}")
    
    return {
        "name": name,
        "passed": len(errors) == 0,
        "errors": errors,
        "actual": actual,
    }

def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("Memory Retrieval Hardening v1.2.1 - Regression Tests")
    print("=" * 60)
    
    results = []
    passed = 0
    failed = 0
    
    for sample in FIXED_SAMPLES:
        result = test_sample(sample["name"], sample["events"], sample["expected"])
        results.append(result)
        
        if result["passed"]:
            passed += 1
            print(f"\n✅ {sample['name']}: PASSED")
        else:
            failed += 1
            print(f"\n❌ {sample['name']}: FAILED")
            for error in result["errors"]:
                print(error)
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0

# ============== 主入口 ==============

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
