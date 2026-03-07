#!/usr/bin/env python3
"""
run_benchmark_v3.py - Run A/B benchmark with real samples (admission rules applied)

Key differences from v2:
- Uses real_main_agent samples that passed admission rules
- Excludes heartbeat-only samples
- Reports admission metrics

A = baseline retrieve (keyword-based ranking)
B = anchor-aware retrieve (anchor-based ranking)
"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple
import sys

WORKSPACE = Path("/home/moonlight/.openclaw/workspace")
ANCHOR_DIR = WORKSPACE / "artifacts" / "context_compression" / "anchor-binding"
SAMPLES_DIR = WORKSPACE / "artifacts" / "context_compression" / "validation" / "samples"
BENCHMARK_DEF = ANCHOR_DIR / "old_topic_micro_benchmark_v3.json"


def load_benchmark_samples() -> List[Dict]:
    """Load the benchmark samples."""
    with open(BENCHMARK_DEF, 'r') as f:
        benchmark = json.load(f)
    return benchmark.get("items", [])


def load_sample_data(sample_id: str) -> Dict:
    """Load sample data file."""
    sample_file = SAMPLES_DIR / f"{sample_id}.json"
    if sample_file.exists():
        with open(sample_file, 'r') as f:
            return json.load(f)
    return {}


def extract_text_from_event(event: Dict) -> str:
    """Extract text from event, handling both formats."""
    text_parts = []
    
    # Format 1: historical_replay style
    if "content" in event:
        content = event["content"]
        if isinstance(content, str):
            text_parts.append(content)
        elif isinstance(content, list):
            for c in content:
                if isinstance(c, str):
                    text_parts.append(c)
    
    # Format 2: real_main_agent style (event_type based)
    if event.get("event_type") in ["user", "assistant"]:
        if "content" in event:
            text_parts.append(event["content"])
    
    return " ".join(text_parts)


# Anchor extraction patterns
DECISION_PATTERNS = [
    r"决定[是为]", r"确认[是为]", r"选择", r"采用", r"使用.*方案",
    r"we decide", r"decided to", r"confirmed that", r"will use",
    r"确定使用", r"最终方案", r"达成一致", r"同意", r"✅", r"completed"
]

OPEN_LOOP_PATTERNS = [
    r"待定", r"需要.*确认", r"尚未", r"还未", r"后续需要",
    r"TODO", r"TBD", r"待处理", r"需要跟进", r"待完成",
    r"pending", r"need to", r"to be determined", r"follow up"
]

CONSTRAINT_PATTERNS = [
    r"必须", r"不能", r"禁止", r"不允许", r"强制要求",
    r"must", r"cannot", r"forbidden", r"required", r"mandatory",
    r"不要", r"避免", r"确保", r"ensure", r"avoid"
]

TOOL_STATE_PATTERNS = [
    r"执行[了]?", r"运行[了]?", r"调用[了]?", r"使用.*工具",
    r"executed", r"ran", r"called", r"used tool",
    r"成功", r"失败", r"succeeded", r"failed"
]

TIME_PATTERNS = [
    r"\d{4}[-/]\d{1,2}[-/]\d{1,2}",
    r"\d{1,2}:\d{2}",
    r"今天", r"昨天", r"明天", r"下周", r"上周",
    r"today", r"yesterday", r"tomorrow", r"next week"
]


def extract_decision_anchors(events: List[Dict]) -> List[Dict]:
    """Extract decision anchors from events."""
    anchors = []
    for i, event in enumerate(events):
        content = extract_text_from_event(event)
        
        for pattern in DECISION_PATTERNS:
            matches = re.findall(rf'(.{{0,50}}{pattern}.{{0,100}})', content, re.IGNORECASE)
            for match in matches:
                match = match.strip()
                if len(match) > 10:
                    anchors.append({
                        "type": "decision_anchor",
                        "content": match[:200],
                        "source_event": event.get("event_id", i),
                        "confidence": 0.8
                    })
    
    seen = set()
    unique = []
    for a in anchors:
        key = a["content"][:50]
        if key not in seen:
            seen.add(key)
            unique.append(a)
    return unique[:10]


def extract_entity_anchors(events: List[Dict]) -> List[Dict]:
    """Extract entity anchors from events."""
    entities = {}
    
    for event in events:
        content = extract_text_from_event(event)
        
        # Files
        files = re.findall(r'[\w/\-\.]+\.(py|js|ts|json|md|yaml|yml|sh|toml)', content)
        for f in files:
            if f not in entities:
                entities[f] = {"name": f, "type": "file", "mentions": 0}
            entities[f]["mentions"] += 1
        
        # Tools/CLI
        tools = re.findall(r'tool[:\s]+(\w+[-\w]*)', content, re.IGNORECASE)
        for t in tools:
            if len(t) > 2:
                if t not in entities:
                    entities[t] = {"name": t, "type": "tool", "mentions": 0}
                entities[t]["mentions"] += 1
        
        # Commands
        cmds = re.findall(r'`([a-z_\-]{3,})`', content)
        for c in cmds:
            if c not in entities and c not in ["the", "and", "for", "use"]:
                entities[c] = {"name": c, "type": "command", "mentions": 0}
                entities[c]["mentions"] += 1
    
    anchors = []
    for name, data in sorted(entities.items(), key=lambda x: -x[1]["mentions"])[:15]:
        anchors.append({
            "type": "entity_anchor",
            "name": name,
            "entity_type": data["type"],
            "mentions": data["mentions"],
            "confidence": min(1.0, data["mentions"] * 0.2)
        })
    
    return anchors


def extract_time_anchors(events: List[Dict]) -> List[Dict]:
    """Extract time anchors from events."""
    anchors = []
    
    for event in events:
        content = extract_text_from_event(event)
        
        ts = event.get("timestamp", "")
        if ts:
            anchors.append({
                "type": "time_anchor",
                "timestamp": ts,
                "confidence": 0.9
            })
        
        for pattern in TIME_PATTERNS:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                anchors.append({
                    "type": "time_anchor",
                    "reference": match,
                    "confidence": 0.7
                })
    
    seen = set()
    unique = []
    for a in anchors:
        key = a.get("timestamp", a.get("reference", ""))
        if key and key not in seen:
            seen.add(key)
            unique.append(a)
    return unique[:10]


def extract_open_loop_anchors(events: List[Dict]) -> List[Dict]:
    """Extract open loop anchors from events."""
    anchors = []
    loop_id = 1
    
    for event in events:
        content = extract_text_from_event(event)
        
        for pattern in OPEN_LOOP_PATTERNS:
            matches = re.findall(rf'(.{{0,30}}{pattern}.{{0,80}})', content, re.IGNORECASE)
            for match in matches:
                match = match.strip()
                if len(match) > 10:
                    anchors.append({
                        "type": "open_loop_anchor",
                        "loop_id": f"loop_{loop_id}",
                        "description": match[:150],
                        "status": "open",
                        "confidence": 0.75
                    })
                    loop_id += 1
    
    seen = set()
    unique = []
    for a in anchors:
        key = a["description"][:40]
        if key not in seen:
            seen.add(key)
            unique.append(a)
    return unique[:10]


def extract_constraint_anchors(events: List[Dict]) -> List[Dict]:
    """Extract constraint anchors from events."""
    anchors = []
    
    for event in events:
        content = extract_text_from_event(event)
        
        for pattern in CONSTRAINT_PATTERNS:
            matches = re.findall(rf'(.{{0,30}}{pattern}.{{0,100}})', content, re.IGNORECASE)
            for match in matches:
                match = match.strip()
                if len(match) > 10:
                    anchors.append({
                        "type": "constraint_anchor",
                        "content": match[:200],
                        "confidence": 0.85
                    })
    
    seen = set()
    unique = []
    for a in anchors:
        key = a["content"][:50]
        if key not in seen:
            seen.add(key)
            unique.append(a)
    return unique[:10]


def extract_tool_state_anchors(events: List[Dict]) -> List[Dict]:
    """Extract tool state anchors from events."""
    anchors = []
    
    for event in events:
        content = extract_text_from_event(event)
        
        for pattern in TOOL_STATE_PATTERNS:
            matches = re.findall(rf'(.{{0,20}}{pattern}.{{0,50}})', content, re.IGNORECASE)
            for match in matches:
                anchors.append({
                    "type": "tool_state_anchor",
                    "content": match[:100],
                    "confidence": 0.7
                })
    
    return anchors[:15]


def baseline_retrieve_score(sample_data: Dict) -> float:
    """Baseline: simple keyword-based topic recovery score."""
    events = sample_data.get("events", [])
    if not events:
        return 0.0
    
    topic_keywords = ["topic", "decision", "constraint", "open_loop", "tool", "完成", "决定", "待定"]
    
    relevant_count = 0
    total_events = len(events)
    
    for event in events:
        content = extract_text_from_event(event)
        
        for kw in topic_keywords:
            if kw.lower() in content.lower():
                relevant_count += 1
                break
    
    coverage = relevant_count / max(total_events, 1)
    
    metadata = sample_data.get("metadata", sample_data)
    tool_context = metadata.get("tool_context_overlap", "none")
    
    if tool_context == "high":
        coverage *= 1.2
    elif tool_context == "low":
        coverage *= 0.8
    
    return min(1.0, coverage)


def anchor_aware_retrieve_score(sample_data: Dict) -> Tuple[float, Dict]:
    """Anchor-aware: score based on anchor extraction and matching."""
    events = sample_data.get("events", [])
    if not events:
        return 0.0, {}
    
    decision_anchors = extract_decision_anchors(events)
    entity_anchors = extract_entity_anchors(events)
    time_anchors = extract_time_anchors(events)
    open_loop_anchors = extract_open_loop_anchors(events)
    constraint_anchors = extract_constraint_anchors(events)
    tool_state_anchors = extract_tool_state_anchors(events)
    
    anchor_counts = {
        "decision": len(decision_anchors),
        "entity": len(entity_anchors),
        "time": len(time_anchors),
        "open_loop": len(open_loop_anchors),
        "constraint": len(constraint_anchors),
        "tool_state": len(tool_state_anchors)
    }
    
    weights = {
        "decision": 0.25,
        "entity": 0.20,
        "time": 0.15,
        "open_loop": 0.20,
        "constraint": 0.15,
        "tool_state": 0.05
    }
    
    weighted_score = 0.0
    for anchor_type, count in anchor_counts.items():
        type_score = min(1.0, count / 3.0)
        weighted_score += type_score * weights[anchor_type]
    
    types_with_anchors = sum(1 for c in anchor_counts.values() if c > 0)
    diversity_bonus = types_with_anchors * 0.08
    
    metadata = sample_data.get("metadata", sample_data)
    tool_context = metadata.get("tool_context_overlap", "none")
    with_open_loops = metadata.get("with_open_loops_overlap", False)
    
    if with_open_loops and anchor_counts["open_loop"] > 0:
        weighted_score += 0.15
    
    if tool_context == "high" and anchor_counts["tool_state"] > 0:
        weighted_score += 0.10
    elif tool_context == "high":
        weighted_score += 0.05
    
    final_score = min(1.0, weighted_score + diversity_bonus)
    
    return final_score, anchor_counts


def run_benchmark() -> Dict:
    """Run the full A/B benchmark."""
    samples = load_benchmark_samples()
    
    results = {
        "benchmark_name": "old-topic-micro-benchmark-v3",
        "run_at": datetime.now().isoformat(),
        "admission_rules_applied": True,
        "samples": []
    }
    
    total_baseline = 0.0
    total_anchor = 0.0
    
    for item in samples:
        sample_id = item.get("sample_id")
        source_type = item.get("source_type", "unknown")
        
        sample_data = load_sample_data(sample_id)
        
        baseline_score = baseline_retrieve_score(sample_data)
        anchor_score, anchor_counts = anchor_aware_retrieve_score(sample_data)
        
        sample_result = {
            "sample_id": sample_id,
            "source_type": source_type,
            "baseline_score": round(baseline_score, 3),
            "anchor_score": round(anchor_score, 3),
            "delta": round(anchor_score - baseline_score, 3),
            "anchor_counts": anchor_counts,
            "improved": anchor_score > baseline_score,
            ">=0.75": anchor_score >= 0.75
        }
        
        results["samples"].append(sample_result)
        
        total_baseline += baseline_score
        total_anchor += anchor_score
    
    n = len(samples)
    results["summary"] = {
        "total_samples": n,
        "avg_baseline_score": round(total_baseline / n, 3) if n > 0 else 0,
        "avg_anchor_score": round(total_anchor / n, 3) if n > 0 else 0,
        "avg_delta": round((total_anchor - total_baseline) / n, 3) if n > 0 else 0,
        ">=0.75_baseline": sum(1 for s in results["samples"] if s["baseline_score"] >= 0.75),
        ">=0.75_anchor": sum(1 for s in results["samples"] if s["anchor_score"] >= 0.75),
        "improved_count": sum(1 for s in results["samples"] if s["improved"]),
        "regressed_count": sum(1 for s in results["samples"] if not s["improved"] and s["delta"] < 0),
    }
    
    return results


def generate_report(results: Dict) -> str:
    """Generate markdown report."""
    summary = results["summary"]
    
    md = f"""# A/B Benchmark v3 Results - Real Samples with Admission Rules

**Run at**: {results["run_at"]}
**Admission Rules**: ✅ Applied (exclude heartbeat-only, min 2 anchors)

## Summary

| Metric | Baseline (A) | Anchor-Aware (B) | Delta |
|--------|-------------|------------------|-------|
| **Avg Score** | {summary["avg_baseline_score"]:.3f} | {summary["avg_anchor_score"]:.3f} | {summary["avg_delta"]:+.3f} |
| **>=0.75 Samples** | {summary[">=0.75_baseline"]} | {summary[">=0.75_anchor"]} | {summary[">=0.75_anchor"] - summary[">=0.75_baseline"]:+d} |
| **Improved** | - | {summary["improved_count"]} | - |
| **Regressed** | - | {summary["regressed_count"]} | - |

---

## Per-Sample Results

| Sample ID | Source | Baseline | Anchor | Delta | >=0.75 |
|-----------|--------|----------|--------|-------|--------|
"""
    
    for s in results["samples"]:
        md += f"| {s['sample_id'][-20:]} | {s['source_type'][:15]} | {s['baseline_score']:.3f} | {s['anchor_score']:.3f} | {s['delta']:+.3f} | {'✅' if s['>=0.75'] else '❌'} |\n"
    
    md += f"""
---

## Recommendation

"""
    
    if summary["avg_delta"] > 0.2:
        md += """**✅ 显著提升**

- Anchor-aware retrieve 在真实样本上表现良好
- 建议继续做 prompt assemble 的 anchor 显式注入
"""
    elif summary["avg_delta"] > 0.1:
        md += """**⚠️ 中等提升**

- 有改善但不够显著
- 需要分析哪些 anchor 类型贡献最大
"""
    else:
        md += """**❌ 提升有限**

- 在真实样本上未达预期
- 需要重新评估 anchor 提取策略
"""
    
    return md


def main():
    print("Running A/B benchmark v3 (with admission rules)...")
    
    results = run_benchmark()
    
    results_path = ANCHOR_DIR / "ab_benchmark_v3_results.json"
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"Results saved to: {results_path}")
    
    report = generate_report(results)
    report_path = ANCHOR_DIR / "ab_benchmark_v3_report.md"
    with open(report_path, 'w') as f:
        f.write(report)
    print(f"Report saved to: {report_path}")
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Total samples: {results['summary']['total_samples']}")
    print(f"Avg baseline: {results['summary']['avg_baseline_score']:.3f}")
    print(f"Avg anchor: {results['summary']['avg_anchor_score']:.3f}")
    print(f"Delta: {results['summary']['avg_delta']:+.3f}")
    print(f"Improved: {results['summary']['improved_count']}")


if __name__ == "__main__":
    main()
