#!/usr/bin/env python3
"""
Revalidate calibration set with V2 evaluator
"""

import json
import sys
from pathlib import Path
from datetime import datetime

WORKSPACE = Path("/home/moonlight/.openclaw/workspace")
CALIBRATION_SET = WORKSPACE / "artifacts" / "context_compression" / "resume_readiness" / "CALIBRATION_SET.jsonl"
OUTPUT_DIR = WORKSPACE / "artifacts" / "context_compression" / "calibration"

sys.path.insert(0, str(WORKSPACE / "tools"))
from resume_readiness_evaluator_v2 import compute_readiness_v2


def revalidate():
    """重新验证 calibration 样本"""
    results = []
    
    with open(CALIBRATION_SET) as f:
        samples = [json.loads(line) for line in f]
    
    for sample in samples:
        sample_id = sample["sample_id"]
        content_summary = sample.get("content_summary", [])
        content = "\n".join(content_summary) if content_summary else ""
        
        # V2 评估
        v2_result = compute_readiness_v2(content)
        
        # 原始数据
        v1_score = sample.get("machine_readiness", 0)
        human_score = sample.get("human_readiness", 0)
        human_reason = sample.get("human_reason", "")
        
        # 计算一致性
        v2_agreement = abs(v2_result["readiness"] - human_score) < 0.25
        v1_agreement = sample.get("agreement") == "yes"
        
        results.append({
            "sample_id": sample_id,
            "v1_score": v1_score,
            "v2_score": round(v2_result["readiness"], 2),
            "human_score": human_score,
            "human_reason": human_reason,
            "v2_gates": v2_result["gates"],
            "v2_signals": v2_result["signals"],
            "v1_agreement": v1_agreement,
            "v2_agreement": v2_agreement
        })
    
    return results


def main():
    results = revalidate()
    
    # 统计
    total = len(results)
    v1_agreements = sum(1 for r in results if r["v1_agreement"])
    v2_agreements = sum(1 for r in results if r["v2_agreement"])
    
    v1_rate = v1_agreements / total if total else 0
    v2_rate = v2_agreements / total if total else 0
    
    # 保存详细结果
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_DIR / "REVALIDATION_RESULTS.json", "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "total_samples": total,
            "v1_agreement_rate": round(v1_rate, 2),
            "v2_agreement_rate": round(v2_rate, 2),
            "improvement": round(v2_rate - v1_rate, 2),
            "samples": results
        }, f, indent=2, ensure_ascii=False)
    
    # 输出摘要
    print("=" * 60)
    print("Revalidation Results: V1 vs V2")
    print("=" * 60)
    print(f"\nTotal samples: {total}")
    print(f"\nV1 Agreement Rate: {v1_rate:.0%} ({v1_agreements}/{total})")
    print(f"V2 Agreement Rate: {v2_rate:.0%} ({v2_agreements}/{total})")
    print(f"Improvement: {(v2_rate - v1_rate):.0%}")
    
    # 分析改进情况
    improved = sum(1 for r in results if r["v2_agreement"] and not r["v1_agreement"])
    regressed = sum(1 for r in results if r["v1_agreement"] and not r["v2_agreement"])
    
    print(f"\nImproved: {improved} samples")
    print(f"Regressed: {regressed} samples")
    
    # 显示一些具体案例
    print("\n--- Sample Changes ---")
    for r in results[:10]:
        status = "✅" if r["v2_agreement"] else "❌"
        change = ""
        if r["v2_agreement"] and not r["v1_agreement"]:
            change = " (FIXED)"
        elif not r["v2_agreement"] and r["v1_agreement"]:
            change = " (REGRESSED)"
        print(f"{status} {r['sample_id'][:40]}: V1={r['v1_score']:.2f}, V2={r['v2_score']:.2f}, Human={r['human_score']:.2f}{change}")
    
    # 生成报告
    report = f"""# Revalidation Summary

**Date**: {datetime.now().isoformat()}

---

## Results

| Metric | V1 | V2 | Change |
|--------|----|----|--------|
| Agreement Rate | {v1_rate:.0%} | {v2_rate:.0%} | {(v2_rate - v1_rate):+.0%} |
| Agreements | {v1_agreements} | {v2_agreements} | +{v2_agreements - v1_agreements} |
| Disagreements | {total - v1_agreements} | {total - v2_agreements} | {(total - v2_agreements) - (total - v1_agreements):+d} |

---

## Improvement Analysis

- Fixed (V1 wrong → V2 right): {improved}
- Regressed (V1 right → V2 wrong): {regressed}
- Net improvement: {improved - regressed}

---

## Gate Analysis

"""
    
    # Gate 统计
    gate_passed = sum(1 for r in results if r["v2_gates"].get("passed", False))
    gate_failed_topic = sum(1 for r in results if r["v2_gates"].get("failed_at") == "topic")
    gate_failed_completed = sum(1 for r in results if r["v2_gates"].get("failed_at") == "task_completed")
    
    report += f"""| Gate Result | Count |
|-------------|-------|
| Passed both gates | {gate_passed} |
| Failed at topic | {gate_failed_topic} |
| Failed at task_completed | {gate_failed_completed} |

---

## Verdict

"""
    
    if v2_rate >= 0.70:
        report += "✅ **PASS** - Agreement rate >= 70%"
    elif v2_rate >= 0.50:
        report += "⚠️ **PARTIAL** - Agreement rate improved but not yet >= 70%"
    else:
        report += "❌ **FAIL** - Agreement rate still below target"
    
    report += f"\n\nTarget: >= 70%\n"
    
    with open(OUTPUT_DIR / "REVALIDATION_SUMMARY.md", "w") as f:
        f.write(report)
    
    print(f"\n✅ Results saved to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
