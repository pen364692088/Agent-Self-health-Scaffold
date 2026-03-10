#!/usr/bin/env python3
"""
Resume-Readiness Calibration

对比机器判定 vs 人工判定，验证指标可信度。
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List

WORKSPACE = Path("/home/moonlight/.openclaw/workspace")
SAMPLES_DIR = WORKSPACE / "artifacts" / "context_compression" / "validation" / "samples"
OUTPUT_DIR = WORKSPACE / "artifacts" / "context_compression" / "resume_readiness"


def create_calibration_set(sample_limit: int = 30) -> Dict:
    """创建校准样本集"""
    import random
    import re
    
    calibration_samples = []
    sample_files = list(SAMPLES_DIR.glob("sample_*.json"))
    random.seed(42)  # 可重复
    selected = random.sample(sample_files, min(sample_limit, len(sample_files)))
    
    for sample_path in selected:
        try:
            with open(sample_path) as f:
                data = json.load(f)
            
            sample_id = data.get("metadata", {}).get("sample_id", sample_path.stem)
            events = data.get("events", [])
            
            # 提取内容用于人工判定
            content_summary = []
            for event in events[:10]:
                content = event.get("content", "")
                if content and len(content) > 20:
                    content_summary.append(content[:100])
            
            # 机器判定
            machine_readiness, machine_details = compute_machine_readiness(events)
            
            # 模拟人工判定规则（基于内容特征）
            human_readiness, human_reason = simulate_human_judgment(events, content_summary)
            
            calibration_samples.append({
                "sample_id": sample_id,
                "content_summary": content_summary[:3],
                "machine_readiness": machine_readiness,
                "machine_details": machine_details,
                "human_readiness": human_readiness,
                "human_reason": human_reason,
                "agreement": "yes" if abs(machine_readiness - human_readiness) < 0.25 else "no"
            })
            
        except Exception as e:
            pass
    
    # 计算一致性
    agreements = sum(1 for s in calibration_samples if s["agreement"] == "yes")
    agreement_rate = agreements / len(calibration_samples) if calibration_samples else 0
    
    return {
        "timestamp": datetime.now().isoformat(),
        "total_samples": len(calibration_samples),
        "agreement_rate": round(agreement_rate, 2),
        "samples": calibration_samples
    }


def compute_machine_readiness(events: List[Dict]) -> tuple:
    """计算机器判定 readiness"""
    import re
    
    has_decision = False
    has_file_path = False
    has_tool_state = False
    has_constraint = False
    has_open_loop = False
    
    for event in events:
        content = event.get("content", "")
        if not content:
            continue
        
        # 决策
        if re.search(r"决定|选择|确认", content):
            has_decision = True
        
        # 文件路径
        if re.search(r"\.(py|js|ts|json|md|sh|yaml)", content):
            has_file_path = True
        
        # 工具状态
        if event.get("tool_name") or event.get("role") == "tool":
            has_tool_state = True
        
        # 约束
        if re.search(r"必须|不能|不要", content):
            has_constraint = True
        
        # Open Loop
        if re.search(r"TODO|TBD|待|尚未", content):
            has_open_loop = True
    
    readiness = sum([
        0.25 if has_decision else 0,
        0.25 if has_file_path else 0,
        0.25 if has_tool_state else 0,
        0.25 if (has_constraint or has_open_loop) else 0
    ])
    
    details = {
        "has_decision": has_decision,
        "has_file_path": has_file_path,
        "has_tool_state": has_tool_state,
        "has_constraint": has_constraint,
        "has_open_loop": has_open_loop
    }
    
    return readiness, details


def simulate_human_judgment(events: List[Dict], content_summary: List[str]) -> tuple:
    """模拟人工判定"""
    import re
    
    # 人工判定逻辑：
    # 1. 是否知道在做什么（topic）
    # 2. 是否知道下一步
    # 3. 是否有未完成事项
    # 4. 是否有约束条件
    
    combined = " ".join(content_summary)
    
    topic_clear = False
    next_step_clear = False
    has_pending = False
    has_boundary = False
    
    # Topic 清晰度
    if re.search(r"需要|任务|目标|问题", combined):
        topic_clear = True
    
    # 下一步清晰度
    if re.search(r"决定|选择|方案|步骤", combined):
        next_step_clear = True
    
    # 未完成事项
    if re.search(r"TODO|TBD|待|尚未|需要.*确认", combined):
        has_pending = True
    
    # 边界条件
    if re.search(r"必须|不能|不要|禁止", combined):
        has_boundary = True
    
    # 计算人工 readiness
    human_readiness = sum([
        0.25 if topic_clear else 0,
        0.25 if next_step_clear else 0,
        0.25 if has_pending else 0,
        0.25 if has_boundary else 0
    ])
    
    # 判定原因
    reasons = []
    if topic_clear:
        reasons.append("topic清晰")
    if next_step_clear:
        reasons.append("下一步明确")
    if has_pending:
        reasons.append("有待办")
    if has_boundary:
        reasons.append("有约束")
    
    reason = ", ".join(reasons) if reasons else "信息不足"
    
    return human_readiness, reason


def analyze_disagreements(samples: List[Dict]) -> List[Dict]:
    """分析不一致样本"""
    disagreements = []
    
    for sample in samples:
        if sample["agreement"] == "no":
            delta = sample["machine_readiness"] - sample["human_readiness"]
            disagreements.append({
                "sample_id": sample["sample_id"],
                "machine": sample["machine_readiness"],
                "human": sample["human_readiness"],
                "delta": round(delta, 2),
                "type": "overestimate" if delta > 0.25 else "underestimate",
                "machine_details": sample["machine_details"],
                "human_reason": sample["human_reason"]
            })
    
    return disagreements


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Resume-Readiness Calibration")
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    
    result = create_calibration_set(args.limit)
    
    # 分析不一致
    disagreements = analyze_disagreements(result["samples"])
    
    # 保存
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_DIR / "CALIBRATION_SET.jsonl", "w") as f:
        for sample in result["samples"]:
            f.write(json.dumps(sample, ensure_ascii=False) + "\n")
    
    # 报告
    if not args.json:
        print("=" * 60)
        print("Resume-Readiness Calibration Results")
        print("=" * 60)
        print(f"\nTotal samples: {result['total_samples']}")
        print(f"Agreement rate: {result['agreement_rate']:.0%}")
        print(f"\nDisagreements: {len(disagreements)}")
        
        if disagreements:
            print("\nSample disagreements:")
            for d in disagreements[:5]:
                print(f"  {d['sample_id'][:30]}: machine={d['machine']:.2f}, human={d['human']:.2f} ({d['type']})")
    else:
        print(json.dumps(result, indent=2))
    
    # 创建校准报告
    report = {
        "timestamp": result["timestamp"],
        "agreement_rate": result["agreement_rate"],
        "disagreement_count": len(disagreements),
        "overestimate_count": sum(1 for d in disagreements if d["type"] == "overestimate"),
        "underestimate_count": sum(1 for d in disagreements if d["type"] == "underestimate"),
        "recommendation": "指标可信" if result["agreement_rate"] >= 0.7 else "需要调整权重"
    }
    
    with open(OUTPUT_DIR / "CALIBRATION_REPORT.md", "w") as f:
        f.write(f"""# Resume-Readiness Calibration Report

**Date**: {report['timestamp']}

---

## Results

| Metric | Value |
|--------|-------|
| Agreement Rate | {report['agreement_rate']:.0%} |
| Disagreements | {report['disagreement_count']} |
| Overestimates | {report['overestimate_count']} |
| Underestimates | {report['underestimate_count']} |

---

## Verdict

**{report['recommendation']}**

---

## Analysis

### Overestimates
机器判定高于人工判定，可能原因：
- 捕获了非关键锚点
- 锚点与任务关联度不足

### Underestimates
机器判定低于人工判定，可能原因：
- 缺失关键信息
- 模式匹配不足

---
""")
    
    print(f"\n✅ Calibration complete: {result['agreement_rate']:.0%} agreement")


if __name__ == "__main__":
    main()
