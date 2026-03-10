#!/usr/bin/env python3
"""
Shadow Trace Collector for Phase 5

Collects shadow traces from:
1. Live compression events (preferred)
2. Historical session replay (fallback for initial validation)

Usage:
  shadow_trace_collector --session-id <id> --history <file>
  shadow_trace_collector --replay-samples --limit 10
  shadow_trace_collector --status
"""

import json
import sys
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

WORKSPACE = Path("/home/moonlight/.openclaw/workspace")
SHADOW_DIR = WORKSPACE / "artifacts" / "context_compression" / "shadow"
VALIDATION_DIR = WORKSPACE / "artifacts" / "context_compression" / "validation"

sys.path.insert(0, str(WORKSPACE / "tools"))
from resume_readiness_evaluator_v2 import compute_readiness_v2


def generate_event_id() -> str:
    """Generate unique event ID."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    import random
    return f"shadow_{ts}_{random.randint(1000, 9999)}"


def collect_from_replay(limit: int = 10) -> List[Dict]:
    """Collect shadow traces from historical validation samples."""
    traces = []
    
    samples_dir = VALIDATION_DIR / "samples"
    if not samples_dir.exists():
        print(f"No samples directory: {samples_dir}", file=sys.stderr)
        return traces
    
    import random
    sample_files = list(samples_dir.glob("sample_*.json"))
    random.seed(42)
    selected = random.sample(sample_files, min(limit, len(sample_files)))
    
    for sample_path in selected:
        try:
            with open(sample_path) as f:
                data = json.load(f)
            
            sample_id = data.get("metadata", {}).get("sample_id", sample_path.stem)
            events = data.get("events", [])
            
            # Extract content for evaluation
            content_parts = []
            for event in events[:20]:
                content = event.get("content", "")
                if content and len(content) > 10:
                    content_parts.append(content)
            
            content = "\n".join(content_parts)
            
            # Evaluate with V2
            v2_result = compute_readiness_v2(content)
            
            # Create shadow trace entry
            trace = {
                "event_id": generate_event_id(),
                "source": "replay_sample",
                "sample_id": sample_id,
                "trigger_time": datetime.now().isoformat(),
                
                # Context before (simulated)
                "context_before_compress": {
                    "turn_count": len(events),
                    "content_preview": content_parts[:3]
                },
                
                # Capsule (simulated from extracted content)
                "capsule_v2": {
                    "topic": v2_result.get("details", {}).get("topic", ""),
                    "signals": v2_result.get("signals", {}),
                    "content": content
                },
                
                # V2 evaluation
                "auto_readiness_score": v2_result["readiness"],
                "auto_verdict": {
                    "gates": v2_result["gates"],
                    "signals": v2_result["signals"],
                    "penalties": v2_result.get("penalties", {})
                },
                
                # Human spot-check (placeholder - needs actual review)
                "human_spotcheck_verdict": None,
                "human_reason": None,
                "agreement": None,
                
                # Status
                "status": "pending_review"
            }
            
            traces.append(trace)
            
        except Exception as e:
            print(f"Error processing {sample_path}: {e}", file=sys.stderr)
            continue
    
    return traces


def collect_from_live_event(
    session_id: str,
    history_path: Path,
    state_path: Optional[Path] = None
) -> Dict:
    """Collect shadow trace from live compression event."""
    # Load history
    if not history_path.exists():
        return {"error": f"History file not found: {history_path}"}
    
    events = []
    with open(history_path) as f:
        for line in f:
            if line.strip():
                try:
                    events.append(json.loads(line))
                except:
                    continue
    
    # Extract content
    content_parts = []
    for event in events[-30:]:  # Last 30 events
        content = event.get("content", "")
        if content and len(content) > 10:
            content_parts.append(content)
    
    content = "\n".join(content_parts)
    
    # Evaluate with V2
    v2_result = compute_readiness_v2(content)
    
    # Create shadow trace
    trace = {
        "event_id": generate_event_id(),
        "source": "live_compression",
        "session_id": session_id,
        "trigger_time": datetime.now().isoformat(),
        
        "context_before_compress": {
            "turn_count": len(events),
            "content_preview": content_parts[:3]
        },
        
        "capsule_v2": {
            "topic": v2_result.get("details", {}).get("topic", ""),
            "signals": v2_result["signals"],
            "content": content
        },
        
        "auto_readiness_score": v2_result["readiness"],
        "auto_verdict": {
            "gates": v2_result["gates"],
            "signals": v2_result["signals"],
            "penalties": v2_result.get("penalties", {})
        },
        
        "human_spotcheck_verdict": None,
        "human_reason": None,
        "agreement": None,
        
        "status": "pending_review"
    }
    
    return trace


def save_traces(traces: List[Dict], append: bool = True):
    """Save traces to SHADOW_TRACE.jsonl."""
    SHADOW_DIR.mkdir(parents=True, exist_ok=True)
    trace_file = SHADOW_DIR / "SHADOW_TRACE.jsonl"
    
    mode = "a" if append else "w"
    with open(trace_file, mode) as f:
        for trace in traces:
            f.write(json.dumps(trace, ensure_ascii=False) + "\n")
    
    return trace_file


def get_status() -> Dict:
    """Get shadow trace collection status."""
    trace_file = SHADOW_DIR / "SHADOW_TRACE.jsonl"
    
    traces = []
    if trace_file.exists():
        with open(trace_file) as f:
            for line in f:
                if line.strip():
                    traces.append(json.loads(line))
    
    pending = [t for t in traces if t.get("status") == "pending_review"]
    reviewed = [t for t in traces if t.get("status") == "reviewed"]
    
    return {
        "total_traces": len(traces),
        "pending_review": len(pending),
        "reviewed": len(reviewed),
        "target": 10,
        "progress": f"{len(traces)}/10"
    }


def generate_summary() -> Dict:
    """Generate shadow trace summary."""
    trace_file = SHADOW_DIR / "SHADOW_TRACE.jsonl"
    
    traces = []
    if trace_file.exists():
        with open(trace_file) as f:
            for line in f:
                if line.strip():
                    traces.append(json.loads(line))
    
    if not traces:
        return {"error": "No traces collected"}
    
    # Calculate metrics
    reviewed = [t for t in traces if t.get("agreement") is not None]
    
    if reviewed:
        agreements = sum(1 for t in reviewed if t["agreement"])
        agreement_rate = agreements / len(reviewed)
        
        false_positives = sum(1 for t in reviewed 
                            if t["auto_readiness_score"] > 0.5 and t["human_spotcheck_verdict"] == 0)
        false_negatives = sum(1 for t in reviewed 
                            if t["auto_readiness_score"] < 0.3 and t["human_spotcheck_verdict"] > 0.5)
        
        fp_rate = false_positives / len(reviewed) if reviewed else 0
        fn_rate = false_negatives / len(reviewed) if reviewed else 0
    else:
        agreement_rate = 0
        fp_rate = 0
        fn_rate = 0
    
    # Gate analysis
    gates_passed = sum(1 for t in traces 
                      if t.get("auto_verdict", {}).get("gates", {}).get("passed", False))
    
    summary = {
        "timestamp": datetime.now().isoformat(),
        "total_traces": len(traces),
        "reviewed_traces": len(reviewed),
        "pending_review": len(traces) - len(reviewed),
        
        "metrics": {
            "agreement_rate": round(agreement_rate, 2),
            "false_positive_rate": round(fp_rate, 2),
            "false_negative_rate": round(fn_rate, 2)
        },
        
        "gate_analysis": {
            "gates_passed": gates_passed,
            "gates_failed": len(traces) - gates_passed
        },
        
        "target_status": {
            "samples_target": 10,
            "samples_collected": len(traces),
            "samples_reviewed": len(reviewed),
            "ready_for_closure": len(reviewed) >= 10 and agreement_rate >= 0.80
        }
    }
    
    return summary


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Shadow Trace Collector")
    parser.add_argument("--session-id", help="Session ID for live collection")
    parser.add_argument("--history", type=Path, help="History file path")
    parser.add_argument("--state", type=Path, help="State file path")
    parser.add_argument("--replay-samples", action="store_true", help="Collect from replay samples")
    parser.add_argument("--limit", type=int, default=10, help="Number of samples")
    parser.add_argument("--status", action="store_true", help="Show collection status")
    parser.add_argument("--summary", action="store_true", help="Generate summary")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()
    
    if args.status:
        status = get_status()
        if args.json:
            print(json.dumps(status, indent=2))
        else:
            print(f"Shadow Trace Collection Status")
            print(f"  Total: {status['total_traces']}")
            print(f"  Pending Review: {status['pending_review']}")
            print(f"  Reviewed: {status['reviewed']}")
            print(f"  Progress: {status['progress']}")
        return
    
    if args.summary:
        summary = generate_summary()
        if args.json:
            print(json.dumps(summary, indent=2))
        else:
            print(f"Shadow Trace Summary")
            print(f"  Collected: {summary['total_traces']}")
            print(f"  Reviewed: {summary['reviewed_traces']}")
            print(f"  Agreement Rate: {summary['metrics']['agreement_rate']:.0%}")
            print(f"  FP Rate: {summary['metrics']['false_positive_rate']:.0%}")
        return
    
    if args.replay_samples:
        print(f"Collecting {args.limit} shadow traces from replay samples...")
        traces = collect_from_replay(args.limit)
        
        if traces:
            trace_file = save_traces(traces)
            print(f"✅ Collected {len(traces)} traces")
            print(f"   Saved to: {trace_file}")
            print(f"   Next: Run spot-check review")
        else:
            print("❌ No traces collected")
        return
    
    if args.session_id and args.history:
        trace = collect_from_live_event(args.session_id, args.history, args.state)
        
        if "error" in trace:
            print(json.dumps(trace, indent=2))
            return 1
        
        save_traces([trace])
        print(f"✅ Collected shadow trace: {trace['event_id']}")
        print(f"   Auto Score: {trace['auto_readiness_score']:.2f}")
        print(f"   Gates: {trace['auto_verdict']['gates']}")
        return 0
    
    print("Use --replay-samples, --status, or --summary")
    return 1


if __name__ == "__main__":
    sys.exit(main())
