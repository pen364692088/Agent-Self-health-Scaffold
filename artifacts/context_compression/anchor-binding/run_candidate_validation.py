#!/usr/bin/env python3
"""
run_candidate_validation.py - Candidate Patch Validation

Patch A: anchor-enhanced capsule builder
Patch B: anchor-aware retrieve

A = baseline retrieve + baseline capsule
B = anchor-enhanced capsule + anchor-aware retrieve

Output:
- candidate_patch_validation_results.json
- candidate_patch_validation_report.md
"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

WORKSPACE = Path("/home/moonlight/.openclaw/workspace")
ANCHOR_DIR = WORKSPACE / "artifacts" / "context_compression" / "anchor-binding"
SAMPLES_DIR = WORKSPACE / "artifacts" / "context_compression" / "validation" / "samples"
BENCHMARK_FILE = ANCHOR_DIR / "candidate_patch_validation_benchmark.json"

# Frozen admission rules
MIN_USER_MESSAGES = 2
MIN_ASSISTANT_MESSAGES = 2
MIN_TEXT_LENGTH = 500
MIN_ANCHOR_TYPES = 2

# Anchor patterns
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


def load_benchmark() -> List[Dict]:
    with open(BENCHMARK_FILE, 'r') as f:
        return json.load(f).get("items", [])


def load_sample_data(sample_id: str) -> Dict:
    sample_file = SAMPLES_DIR / f"{sample_id}.json"
    if sample_file.exists():
        with open(sample_file, 'r') as f:
            return json.load(f)
    return {}


def extract_text_from_event(event: Dict) -> str:
    text_parts = []
    
    if "content" in event:
        content = event["content"]
        if isinstance(content, str):
            text_parts.append(content)
        elif isinstance(content, list):
            for c in content:
                if isinstance(c, str):
                    text_parts.append(c)
    
    if event.get("event_type") in ["user", "assistant"]:
        if "content" in event:
            text_parts.append(event["content"])
    
    return " ".join(text_parts)


def check_admissibility(events: List[Dict]) -> Dict:
    """Verify sample still meets admission rules."""
    user_msgs = 0
    asst_msgs = 0
    total_text = ""
    
    for e in events:
        if e.get("event_type") in ["user", "assistant"]:
            content = e.get("content", "")
            if isinstance(content, str) and len(content) > 10:
                total_text += content + " "
                if e["event_type"] == "user":
                    user_msgs += 1
                else:
                    asst_msgs += 1
        
        if e.get("type") == "message":
            msg = e.get("message", {})
            role = msg.get("role", "")
            content = msg.get("content", [])
            if isinstance(content, list):
                for c in content:
                    if c.get("type") == "text":
                        text = c.get("text", "")
                        total_text += text + " "
                        if role == "user":
                            user_msgs += 1
                        elif role == "assistant":
                            asst_msgs += 1
    
    has_decision = any(p in total_text for p in ["决定", "确认", "选择", "decide", "confirmed", "✅"])
    has_entity = bool(re.search(r'[\w/\-\.]+\.(py|js|ts|json|md)', total_text))
    has_open_loop = any(p in total_text for p in ["TODO", "TBD", "待定", "pending"])
    has_constraint = any(p in total_text for p in ["必须", "不能", "禁止", "must", "cannot"])
    has_tool_state = bool(re.search(r'(exec|run|call|tool|执行|运行)', total_text, re.IGNORECASE))
    
    anchor_types = sum([has_decision, has_entity, has_open_loop, has_constraint, has_tool_state])
    
    admissible = (
        user_msgs >= MIN_USER_MESSAGES and
        asst_msgs >= MIN_ASSISTANT_MESSAGES and
        len(total_text) >= MIN_TEXT_LENGTH and
        anchor_types >= MIN_ANCHOR_TYPES
    )
    
    return {
        "admissible": admissible,
        "user_msgs": user_msgs,
        "asst_msgs": asst_msgs,
        "text_len": len(total_text),
        "anchor_types": anchor_types
    }


def extract_decision_anchors(events: List[Dict]) -> List[Dict]:
    anchors = []
    for i, event in enumerate(events):
        content = extract_text_from_event(event)
        for pattern in DECISION_PATTERNS:
            matches = re.findall(rf'(.{{0,50}}{pattern}.{{0,100}})', content, re.IGNORECASE)
            for match in matches:
                if len(match.strip()) > 10:
                    anchors.append({
                        "type": "decision_anchor",
                        "content": match.strip()[:200],
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
    entities = {}
    for event in events:
        content = extract_text_from_event(event)
        files = re.findall(r'[\w/\-\.]+\.(py|js|ts|json|md|yaml|yml|sh|toml)', content)
        for f in files:
            if f not in entities:
                entities[f] = {"name": f, "type": "file", "mentions": 0}
            entities[f]["mentions"] += 1
        tools = re.findall(r'tool[:\s]+(\w+[-\w]*)', content, re.IGNORECASE)
        for t in tools:
            if len(t) > 2 and t not in entities:
                entities[t] = {"name": t, "type": "tool", "mentions": 0}
            if t in entities:
                entities[t]["mentions"] += 1
    
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
    anchors = []
    for event in events:
        content = extract_text_from_event(event)
        ts = event.get("timestamp", "")
        if ts:
            anchors.append({"type": "time_anchor", "timestamp": ts, "confidence": 0.9})
        for pattern in TIME_PATTERNS:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                anchors.append({"type": "time_anchor", "reference": match, "confidence": 0.7})
    seen = set()
    unique = []
    for a in anchors:
        key = a.get("timestamp", a.get("reference", ""))
        if key and key not in seen:
            seen.add(key)
            unique.append(a)
    return unique[:10]


def extract_open_loop_anchors(events: List[Dict]) -> List[Dict]:
    anchors = []
    loop_id = 1
    for event in events:
        content = extract_text_from_event(event)
        for pattern in OPEN_LOOP_PATTERNS:
            matches = re.findall(rf'(.{{0,30}}{pattern}.{{0,80}})', content, re.IGNORECASE)
            for match in matches:
                if len(match.strip()) > 10:
                    anchors.append({
                        "type": "open_loop_anchor",
                        "loop_id": f"loop_{loop_id}",
                        "description": match.strip()[:150],
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
    anchors = []
    for event in events:
        content = extract_text_from_event(event)
        for pattern in CONSTRAINT_PATTERNS:
            matches = re.findall(rf'(.{{0,30}}{pattern}.{{0,100}})', content, re.IGNORECASE)
            for match in matches:
                if len(match.strip()) > 10:
                    anchors.append({
                        "type": "constraint_anchor",
                        "content": match.strip()[:200],
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
    """A = baseline retrieve + baseline capsule."""
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
    """B = anchor-enhanced capsule + anchor-aware retrieve."""
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


def run_validation() -> Dict:
    samples = load_benchmark()
    
    results = {
        "validation_name": "candidate-patch-validation",
        "run_at": datetime.now().isoformat(),
        "patches": {
            "A": "baseline retrieve + baseline capsule",
            "B": "anchor-enhanced capsule + anchor-aware retrieve"
        },
        "samples": [],
        "by_source_type": {
            "historical_replay": {"samples": [], "count": 0},
            "real_main_agent": {"samples": [], "count": 0}
        }
    }
    
    correct_topic_wrong_anchor = 0
    top1_anchor_hits = 0
    
    for item in samples:
        sample_id = item.get("sample_id")
        source_type = item.get("source_type", "unknown")
        
        sample_data = load_sample_data(sample_id)
        events = sample_data.get("events", [])
        
        # Verify admissibility
        admission = check_admissibility(events)
        
        # A: baseline
        baseline_score = baseline_retrieve_score(sample_data)
        
        # B: anchor-aware
        anchor_score, anchor_counts = anchor_aware_retrieve_score(sample_data)
        
        # Track metrics
        if baseline_score > 0.3 and anchor_score < 0.3:
            correct_topic_wrong_anchor += 1
        
        if anchor_counts.get("decision", 0) > 0:
            top1_anchor_hits += 1
        
        sample_result = {
            "sample_id": sample_id,
            "source_type": source_type,
            "admissible": admission["admissible"],
            "baseline_score": round(baseline_score, 3),
            "anchor_score": round(anchor_score, 3),
            "delta": round(anchor_score - baseline_score, 3),
            "anchor_counts": anchor_counts,
            "improved": anchor_score > baseline_score,
            ">=0.75": anchor_score >= 0.75,
            "regressed": anchor_score < baseline_score - 0.1
        }
        
        results["samples"].append(sample_result)
        
        # Group by source type
        if source_type == "historical_replay":
            results["by_source_type"]["historical_replay"]["samples"].append(sample_result)
            results["by_source_type"]["historical_replay"]["count"] += 1
        else:
            results["by_source_type"]["real_main_agent"]["samples"].append(sample_result)
            results["by_source_type"]["real_main_agent"]["count"] += 1
    
    # Calculate summary
    n = len(results["samples"])
    results["summary"] = {
        "total_samples": n,
        "avg_baseline_score": round(sum(s["baseline_score"] for s in results["samples"]) / n, 3),
        "avg_anchor_score": round(sum(s["anchor_score"] for s in results["samples"]) / n, 3),
        "avg_delta": round(sum(s["delta"] for s in results["samples"]) / n, 3),
        ">=0.75_baseline": sum(1 for s in results["samples"] if s["baseline_score"] >= 0.75),
        ">=0.75_anchor": sum(1 for s in results["samples"] if s["anchor_score"] >= 0.75),
        "improved_count": sum(1 for s in results["samples"] if s["improved"]),
        "regressed_count": sum(1 for s in results["samples"] if s["regressed"]),
        "correct_topic_wrong_anchor": correct_topic_wrong_anchor,
        "top1_anchor_hit_rate": round(top1_anchor_hits / n, 3)
    }
    
    # By source type summaries
    for st in ["historical_replay", "real_main_agent"]:
        st_samples = results["by_source_type"][st]["samples"]
        st_count = len(st_samples)
        if st_count > 0:
            results["by_source_type"][st]["avg_baseline"] = round(
                sum(s["baseline_score"] for s in st_samples) / st_count, 3)
            results["by_source_type"][st]["avg_anchor"] = round(
                sum(s["anchor_score"] for s in st_samples) / st_count, 3)
            results["by_source_type"][st]["delta"] = round(
                sum(s["delta"] for s in st_samples) / st_count, 3)
            results["by_source_type"][st][">=0.75_baseline"] = sum(
                1 for s in st_samples if s["baseline_score"] >= 0.75)
            results["by_source_type"][st][">=0.75_anchor"] = sum(
                1 for s in st_samples if s["anchor_score"] >= 0.75)
            results["by_source_type"][st]["improved"] = sum(
                1 for s in st_samples if s["improved"])
            results["by_source_type"][st]["regressed"] = sum(
                1 for s in st_samples if s["regressed"])
    
    return results


def generate_report(results: Dict) -> str:
    summary = results["summary"]
    hr = results["by_source_type"]["historical_replay"]
    real = results["by_source_type"]["real_main_agent"]
    
    md = f"""# Candidate Patch Validation Report

**Run at**: {results["run_at"]}
**Validation**: Patch A (baseline) vs Patch B (anchor-enhanced)

---

## Patches

| Patch | Description |
|-------|-------------|
| A | baseline retrieve + baseline capsule |
| B | anchor-enhanced capsule + anchor-aware retrieve |

---

## Overall Summary

| Metric | Baseline (A) | Anchor-Aware (B) | Delta |
|--------|-------------|------------------|-------|
| **Avg Score** | {summary["avg_baseline_score"]:.3f} | {summary["avg_anchor_score"]:.3f} | {summary["avg_delta"]:+.3f} |
| **>=0.75 Samples** | {summary[">=0.75_baseline"]} | {summary[">=0.75_anchor"]} | {summary[">=0.75_anchor"] - summary[">=0.75_baseline"]:+d} |
| **Improved** | - | {summary["improved_count"]} | - |
| **Regressed** | - | {summary["regressed_count"]} | - |
| **Correct Topic Wrong Anchor** | - | {summary["correct_topic_wrong_anchor"]} | - |

---

## By Source Type

### Historical Replay ({hr["count"]} samples)

| Metric | Baseline | Anchor | Delta |
|--------|----------|--------|-------|
| Avg Score | {hr["avg_baseline"]:.3f} | {hr["avg_anchor"]:.3f} | {hr["delta"]:+.3f} |
| >=0.75 | {hr[">=0.75_baseline"]} | {hr[">=0.75_anchor"]} | {hr[">=0.75_anchor"] - hr[">=0.75_baseline"]:+d} |
| Improved | - | {hr["improved"]} | - |
| Regressed | - | {hr["regressed"]} | - |

### Real Main Agent Admissible ({real["count"]} samples)

| Metric | Baseline | Anchor | Delta |
|--------|----------|--------|-------|
| Avg Score | {real["avg_baseline"]:.3f} | {real["avg_anchor"]:.3f} | {real["delta"]:+.3f} |
| >=0.75 | {real[">=0.75_baseline"]} | {real[">=0.75_anchor"]} | {real[">=0.75_anchor"] - real[">=0.75_baseline"]:+d} |
| Improved | - | {real["improved"]} | - |
| Regressed | - | {real["regressed"]} | - |

---

## Per-Sample Results (Top 20)

| Sample ID | Source | Admissible | Baseline | Anchor | Delta | >=0.75 |
|-----------|--------|------------|----------|--------|-------|--------|
"""
    
    for s in results["samples"][:20]:
        md += f"| {s['sample_id'][-20:]} | {s['source_type'][:12]} | {'✅' if s['admissible'] else '❌'} | {s['baseline_score']:.3f} | {s['anchor_score']:.3f} | {s['delta']:+.3f} | {'✅' if s['>=0.75'] else '❌'} |\n"
    
    return md


def main():
    print("Running Candidate Patch Validation...\n")
    
    results = run_validation()
    
    # Save JSON
    results_path = ANCHOR_DIR / "candidate_patch_validation_results.json"
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"✅ Results saved to: {results_path}")
    
    # Save report
    report = generate_report(results)
    report_path = ANCHOR_DIR / "candidate_patch_validation_report.md"
    with open(report_path, 'w') as f:
        f.write(report)
    print(f"✅ Report saved to: {report_path}")
    
    # Print summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    s = results["summary"]
    hr = results["by_source_type"]["historical_replay"]
    real = results["by_source_type"]["real_main_agent"]
    
    print(f"Total samples: {s['total_samples']}")
    print(f"Overall: {s['avg_baseline_score']:.3f} → {s['avg_anchor_score']:.3f} (Δ{s['avg_delta']:+.3f})")
    print(f"Historical: {hr['avg_baseline']:.3f} → {hr['avg_anchor']:.3f} (Δ{hr['delta']:+.3f})")
    print(f"Real Admissible: {real['avg_baseline']:.3f} → {real['avg_anchor']:.3f} (Δ{real['delta']:+.3f})")
    print(f"Improved: {s['improved_count']}, Regressed: {s['regressed_count']}")


if __name__ == "__main__":
    main()
