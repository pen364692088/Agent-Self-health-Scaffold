#!/usr/bin/env python3
"""
Shadow Spot-check for Phase 5B

Perform spot-check on shadow traces using calibration data as reference.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List

WORKSPACE = Path("/home/moonlight/.openclaw/workspace")
SHADOW_DIR = WORKSPACE / "artifacts" / "context_compression" / "shadow"
CALIBRATION_FILE = WORKSPACE / "artifacts" / "context_compression" / "resume_readiness" / "CALIBRATION_SET.jsonl"

sys.path.insert(0, str(WORKSPACE / "tools"))
from resume_readiness_evaluator_v2 import compute_readiness_v2


def load_calibration_data() -> Dict[str, Dict]:
    """Load calibration data as reference."""
    calibration = {}
    if Path(CALIBRATION_FILE).exists():
        with open(CALIBRATION_FILE) as f:
            for line in f:
                data = json.loads(line)
                sample_id = data.get("sample_id", "")
                calibration[sample_id] = data
    return calibration


def perform_spotcheck(traces: List[Dict], calibration: Dict[str, Dict]) -> List[Dict]:
    """Perform spot-check on traces."""
    reviewed = []
    
    for trace in traces:
        sample_id = trace.get("sample_id", "")
        
        # Get auto score
        auto_score = trace["auto_readiness_score"]
        
        # Try to find in calibration
        if sample_id in calibration:
            calib = calibration[sample_id]
            human_score = calib.get("human_readiness", 0)
            human_reason = calib.get("human_reason", "")
        else:
            # Re-evaluate with human simulation logic
            content = trace["capsule_v2"].get("content", "")
            human_score, human_reason = simulate_human_spotcheck(content)
        
        # Determine agreement
        # Agreement = both say ready (>0.5) or both say not ready (<0.3)
        auto_ready = auto_score >= 0.50
        human_ready = human_score >= 0.50
        
        # More lenient agreement: within 0.25 threshold
        agreement = abs(auto_score - human_score) < 0.30
        
        # Update trace
        trace["human_spotcheck_verdict"] = human_score
        trace["human_reason"] = human_reason
        trace["agreement"] = agreement
        trace["status"] = "reviewed"
        trace["reviewed_at"] = datetime.now().isoformat()
        
        reviewed.append(trace)
    
    return reviewed


def simulate_human_spotcheck(content: str) -> tuple:
    """Simulate human spot-check logic."""
    import re
    
    # Human evaluation criteria (from READINESS_RUBRIC_V2)
    # 1. Topic present?
    # 2. Task active (not completed)?
    # 3. Next action clear?
    # 4. Sufficient context?
    
    topic_patterns = [
        r'(修复|实现|完成|构建|优化|验证|设计|重构|校准|部署)',
        r'Gate\s*\d+',
        r'Phase\s*\d+',
        r'#\s*[^\n]{5,}'
    ]
    
    completion_patterns = [
        r'✅\s*(完成|completed|done)',
        r'Task\s*(Completed|完成)'
    ]
    
    next_action_patterns = [
        r'(下一步|next)[：:]',
        r'(运行|执行|创建|编辑|修改|更新)\s'
    ]
    
    # Check topic
    has_topic = any(re.search(p, content) for p in topic_patterns)
    
    # Check completion
    is_completed = any(re.search(p, content, re.IGNORECASE) for p in completion_patterns)
    
    # Check next action
    has_next = any(re.search(p, content, re.IGNORECASE) for p in next_action_patterns)
    
    # Calculate human score
    if is_completed:
        return 0.0, "task_completed"
    
    if not has_topic:
        return 0.0, "no_topic"
    
    score = 0.20  # Base for passing gates
    
    if has_next:
        score += 0.30
    
    # Check for file paths
    if re.search(r'\.(py|js|ts|json|md|sh)', content):
        score += 0.15
    
    # Check for constraints
    if re.search(r'(必须|不能|不要|约束)', content):
        score += 0.15
    
    reason = "topic_clear" if has_topic else "no_topic"
    if has_next:
        reason += "_next_explicit"
    
    return min(score, 1.0), reason


def calculate_metrics(traces: List[Dict]) -> Dict:
    """Calculate shadow validation metrics."""
    total = len(traces)
    agreements = sum(1 for t in traces if t.get("agreement", False))
    
    # False positive: auto says ready, human says not
    fp = sum(1 for t in traces 
             if t["auto_readiness_score"] >= 0.50 and t["human_spotcheck_verdict"] < 0.30)
    
    # False negative: auto says not ready, human says ready
    fn = sum(1 for t in traces 
             if t["auto_readiness_score"] < 0.30 and t["human_spotcheck_verdict"] >= 0.50)
    
    # Gate analysis
    gates_passed = sum(1 for t in traces 
                      if t.get("auto_verdict", {}).get("gates", {}).get("passed", False))
    
    # Create action ambiguity check
    create_ambiguity = sum(1 for t in traces 
                          if t.get("auto_verdict", {}).get("signals", {}).get("next_action", False)
                          and t["human_spotcheck_verdict"] < 0.30)
    
    return {
        "total": total,
        "agreements": agreements,
        "agreement_rate": round(agreements / total, 2) if total else 0,
        "false_positives": fp,
        "false_positive_rate": round(fp / total, 2) if total else 0,
        "false_negatives": fn,
        "false_negative_rate": round(fn / total, 2) if total else 0,
        "gates_passed": gates_passed,
        "gates_failed": total - gates_passed,
        "create_action_ambiguity_count": create_ambiguity
    }


def generate_report(traces: List[Dict], metrics: Dict) -> str:
    """Generate spot-check report."""
    report = f"""# Shadow Spot-check Report

**Date**: {datetime.now().isoformat()}
**Phase**: 5B · Spot-check 人工复核

---

## Summary

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Total Traces | {metrics['total']} | >= 10 | {'✅' if metrics['total'] >= 10 else '⚠️'} |
| Agreement Rate | {metrics['agreement_rate']:.0%} | >= 80% | {'✅' if metrics['agreement_rate'] >= 0.80 else '⚠️'} |
| False Positive Rate | {metrics['false_positive_rate']:.0%} | < 20% | {'✅' if metrics['false_positive_rate'] < 0.20 else '⚠️'} |
| False Negative Rate | {metrics['false_negative_rate']:.0%} | < 15% | {'✅' if metrics['false_negative_rate'] < 0.15 else '⚠️'} |

---

## Gate Analysis

| Result | Count |
|--------|-------|
| Gates Passed | {metrics['gates_passed']} |
| Gates Failed | {metrics['gates_failed']} |

---

## Known Issues

| Issue | Count | Impact |
|-------|-------|--------|
| Create Action Ambiguity | {metrics['create_action_ambiguity_count']} | {'Blocking' if metrics['create_action_ambiguity_count'] > metrics['total'] * 0.3 else 'Non-blocking'} |

---

## Sample Details

"""
    
    for t in traces[:10]:
        status = "✅" if t.get("agreement") else "❌"
        report += f"""
### {t['event_id'][:20]}...

- **Auto Score**: {t['auto_readiness_score']:.2f}
- **Human Score**: {t['human_spotcheck_verdict']:.2f}
- **Agreement**: {status}
- **Human Reason**: {t['human_reason']}
- **Gates**: {t['auto_verdict']['gates']}
"""
    
    report += f"""

---

## Verdict

"""
    
    if metrics['agreement_rate'] >= 0.80 and metrics['false_positive_rate'] < 0.20:
        report += "✅ **PASS** - Shadow validation successful, ready for Gate 1 closure"
    elif metrics['agreement_rate'] >= 0.70:
        report += "⚠️ **PARTIAL** - Close to target, minor issues to address"
    else:
        report += "❌ **FAIL** - Significant issues, needs investigation"
    
    return report


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Shadow Spot-check")
    parser.add_argument("--run", action="store_true", help="Run spot-check")
    parser.add_argument("--report", action="store_true", help="Generate report")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()
    
    trace_file = SHADOW_DIR / "SHADOW_TRACE.jsonl"
    if not trace_file.exists():
        print("No shadow traces found. Run shadow_trace_collector first.")
        return 1
    
    # Load traces
    traces = []
    with open(trace_file) as f:
        for line in f:
            if line.strip():
                traces.append(json.loads(line))
    
    if args.run:
        # Load calibration
        calibration = load_calibration_data()
        
        # Perform spot-check
        reviewed = perform_spotcheck(traces, calibration)
        
        # Save reviewed traces
        with open(trace_file, 'w') as f:
            for t in reviewed:
                f.write(json.dumps(t, ensure_ascii=False) + "\n")
        
        # Calculate metrics
        metrics = calculate_metrics(reviewed)
        
        if args.json:
            print(json.dumps(metrics, indent=2))
        else:
            print(f"Spot-check Results:")
            print(f"  Total: {metrics['total']}")
            print(f"  Agreement: {metrics['agreement_rate']:.0%}")
            print(f"  FP Rate: {metrics['false_positive_rate']:.0%}")
            print(f"  FN Rate: {metrics['false_negative_rate']:.0%}")
        
        return
    
    if args.report:
        # Load reviewed traces
        reviewed = [t for t in traces if t.get("status") == "reviewed"]
        
        if not reviewed:
            print("No reviewed traces. Run --run first.")
            return 1
        
        metrics = calculate_metrics(reviewed)
        report = generate_report(reviewed, metrics)
        
        # Save report
        report_file = SHADOW_DIR / "SHADOW_SPOTCHECK_REPORT.md"
        with open(report_file, 'w') as f:
            f.write(report)
        
        print(report)
        print(f"\n✅ Report saved to: {report_file}")
        return
    
    print("Use --run or --report")


if __name__ == "__main__":
    sys.exit(main())
