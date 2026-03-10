#!/usr/bin/env python3
"""
capsule-builder-v2.py - Enhanced Capsule Builder with V2 Readiness Evaluator

Features:
1. Multi-type anchor extraction (decision, file_path, tool_state, constraint, open_loop)
2. Anchor scoring based on position and relevance
3. V2 Resume-readiness evaluation (Gate-based scoring)
4. Version logging for production monitoring

Usage:
  capsule-builder-v2.py --input <history.jsonl> --session-id <id> --start <n> --end <n>
  capsule-builder-v2.py --health
  capsule-builder-v2.py --test
"""

import argparse
import json
import re
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

WORKSPACE = Path("/home/moonlight/.openclaw/workspace")
OUTPUT_DIR = WORKSPACE / "artifacts" / "capsules"

# Version tracking for production monitoring
EVALUATOR_VERSION = "2.0-gate-based"
CAPSULE_VERSION = "2.0"


class Anchor:
    """Represents an anchor point in the conversation."""
    
    def __init__(self, content: str, anchor_type: str, position: int, total: int):
        self.content = content
        self.anchor_type = anchor_type
        self.position = position
        self.total = total
        # Score based on position (later = higher relevance)
        self.score = 0.5 + 0.5 * (position / total) if total > 0 else 0.5
    
    def to_dict(self) -> Dict:
        return {
            "content": self.content,
            "type": self.anchor_type,
            "position": self.position,
            "score": round(self.score, 2)
        }


def load_jsonl(path: Path) -> List[Dict]:
    """Load JSONL file."""
    records = []
    with open(path, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return records


def extract_messages(records: List[Dict], start: int, end: int) -> List[Dict]:
    """Extract messages from records within turn range."""
    messages = []
    turn_count = 0
    
    for record in records:
        if record.get("type") != "message":
            continue
        
        msg = record.get("message", record)
        role = msg.get("role", "")
        
        if role in ("user", "assistant"):
            turn_count += 1
            if start <= turn_count <= end:
                messages.append({
                    "role": role,
                    "content": msg.get("content", ""),
                    "turn": turn_count
                })
    
    return messages


def extract_decision_anchors(messages: List[Dict], total: int) -> List[Anchor]:
    """Extract decision anchors."""
    anchors = []
    patterns = [
        r'(决定|选择|确认|采用|方案)[^\n]{5,50}',
        r'(因为|由于)[^\n]{5,}(选择|决定)',
    ]
    
    for msg in messages:
        content = msg.get("content", "")
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                text = match if isinstance(match, str) else match[0]
                if len(text) > 5:
                    anchors.append(Anchor(text, "decision", msg.get("turn", 1), total))
    
    return anchors


def extract_file_path_anchors(messages: List[Dict], total: int) -> List[Anchor]:
    """Extract file path anchors."""
    anchors = []
    pattern = r'[a-zA-Z0-9_\-/]+\.(py|js|ts|json|md|sh|yaml|yml)'
    
    for msg in messages:
        content = msg.get("content", "")
        matches = re.findall(pattern, content)
        for match in matches:
            anchors.append(Anchor(match, "file_path", msg.get("turn", 1), total))
    
    return anchors


def extract_tool_state_anchors(messages: List[Dict], total: int) -> List[Anchor]:
    """Extract tool state anchors."""
    anchors = []
    
    for msg in messages:
        content = msg.get("content", "")
        role = msg.get("role", "")
        
        # Check for tool-related content
        if role == "tool" or "tool" in content.lower():
            # Extract tool name
            tool_match = re.search(r'(tools?|scripts?)/([a-zA-Z0-9_\-]+)', content)
            if tool_match:
                anchors.append(Anchor(f"tool:{tool_match.group(2)}", "tool_state", msg.get("turn", 1), total))
            elif "运行" in content or "执行" in content:
                anchors.append(Anchor(content[:50], "tool_state", msg.get("turn", 1), total))
    
    return anchors


def extract_constraint_anchors(messages: List[Dict], total: int) -> List[Anchor]:
    """Extract constraint anchors."""
    anchors = []
    patterns = [
        r'(必须|不能|不要|禁止)[^\n]{5,50}',
        r'(约束|限制|条件)[：:][^\n]{5,}',
    ]
    
    for msg in messages:
        content = msg.get("content", "")
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                text = match if isinstance(match, str) else match[0]
                if len(text) > 5:
                    anchors.append(Anchor(text, "constraint", msg.get("turn", 1), total))
    
    return anchors


def extract_open_loop_anchors(messages: List[Dict], total: int) -> List[Anchor]:
    """Extract open loop anchors."""
    anchors = []
    patterns = [
        r'(TODO|TBD|FIXME|XXX)[：:]?\s*([^\n]{5,})',
        r'(待[办做写确认]|尚未|还需要)[^\n]{5,}',
    ]
    
    for msg in messages:
        content = msg.get("content", "")
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                text = match[-1] if isinstance(match, tuple) else match
                if len(text) > 5:
                    anchors.append(Anchor(text, "open_loop", msg.get("turn", 1), total))
    
    return anchors


def compute_readiness_v2_gates(content: str) -> Dict:
    """
    V2 Readiness Evaluator with Gate-based scoring.
    
    This is the new evaluator that achieved 92% agreement in calibration.
    """
    # === Gate 1: Topic Detection ===
    topic_patterns = [
        r'[A-Z][a-zA-Z\s]+\s*(V\d+|v\d+)',  # Project names
        r'Gate\s*\d+\.?\d*',
        r'Phase\s*\d+',
        r'#\s*[^\n]{5,50}',
        r'(修复|实现|完成|构建|优化|验证|设计|重构|校准|部署)[^\n]{5,50}',
    ]
    
    topic_present = any(re.search(p, content) for p in topic_patterns)
    topic_text = ""
    for p in topic_patterns:
        match = re.search(p, content)
        if match:
            topic_text = match.group(0)[:50]
            break
    
    # === Gate 2: Task Active Check ===
    completion_patterns = [
        r'✅\s*(完成|completed|done)',
        r'Task\s*(Completed|完成)',
        r'##\s*完成',
        r'已[经]?完成',
    ]
    
    task_completed = any(re.search(p, content, re.IGNORECASE) for p in completion_patterns)
    task_active = not task_completed
    
    # === Gate Results ===
    gates = {
        "topic_present": topic_present,
        "task_active": task_active,
        "passed": topic_present and task_active
    }
    
    if not topic_present:
        gates["failed_at"] = "topic"
        return {"readiness": 0.0, "gates": gates, "signals": {}, "details": {"topic": topic_text}}
    
    if task_completed:
        gates["failed_at"] = "task_completed"
        return {"readiness": 0.0, "gates": gates, "signals": {}, "details": {"topic": topic_text}}
    
    # === Enhancement Signals ===
    score = 0.20  # Base for passing gates
    signals = {}
    
    # Next Action
    next_patterns = [
        r'(下一步|next)[：:]',
        r'(运行|执行|创建|编辑|修改|更新)\s',
    ]
    has_next = any(re.search(p, content, re.IGNORECASE) for p in next_patterns)
    signals["next_action"] = has_next
    if has_next:
        score += 0.30
    
    # Decision Context
    decision_patterns = [
        r'(选择|决定|确认|采用|使用)[^\n]{5,}因为',
        r'(因为|由于)[^\n]{5,}(选择|决定|确认)',
        r'(必须|不能|不要|禁止)',
        r'(优先|重要|关键)',
    ]
    has_decision = sum(1 for p in decision_patterns if re.search(p, content)) >= 2
    signals["decision_context"] = has_decision
    if has_decision:
        score += 0.20
    
    # Tool State
    has_tool = bool(re.search(r'\.(py|js|ts|json|md|sh)', content))
    signals["tool_state"] = has_tool
    if has_tool:
        score += 0.15
    
    # Open Loops
    has_loops = bool(re.search(r'(TODO|TBD|待|尚未)', content))
    signals["open_loops"] = has_loops
    if has_loops:
        score += 0.15
    
    return {
        "readiness": min(score, 1.0),
        "gates": gates,
        "signals": signals,
        "details": {"topic": topic_text}
    }


def build_capsule(session_id: str, start: int, end: int, messages: List[Dict]) -> Dict:
    """Build capsule V2 with V2 Readiness Evaluator."""
    total = len(messages)
    
    # Extract all anchor types
    decision_anchors = extract_decision_anchors(messages, total)
    file_path_anchors = extract_file_path_anchors(messages, total)
    tool_state_anchors = extract_tool_state_anchors(messages, total)
    constraint_anchors = extract_constraint_anchors(messages, total)
    open_loop_anchors = extract_open_loop_anchors(messages, total)
    
    # Combine and sort
    all_anchors = decision_anchors + file_path_anchors + tool_state_anchors + constraint_anchors + open_loop_anchors
    all_anchors.sort(key=lambda x: -x.score)
    
    # Build topic
    topic = "对话片段"
    if decision_anchors:
        topic = decision_anchors[0].content[:50]
    
    # Build summary
    summary = f"Turn {start}-{end}, {total} messages"
    if tool_state_anchors:
        tools = [a.content.split(":")[0] for a in tool_state_anchors[:3]]
        summary += f", tools: {', '.join(tools)}"
    
    # Capsule ID
    timestamp = datetime.now().strftime("%Y%m%d")
    capsule_id = f"cap_v2_{timestamp}_{session_id[:8]}_{start}_{end}"
    
    # === V2 Readiness Evaluation ===
    # Build content for evaluation
    content_parts = [msg.get("content", "") for msg in messages if msg.get("content")]
    content = "\n".join(content_parts)
    
    # Call V2 evaluator
    v2_result = compute_readiness_v2_gates(content)
    readiness = v2_result["readiness"]
    
    capsule = {
        "capsule_id": capsule_id,
        "session_id": session_id,
        "source_turn_range": {"start": start, "end": end},
        "created_at": datetime.now().isoformat(),
        "version": CAPSULE_VERSION,
        
        # === Evaluator Version (for production monitoring) ===
        "evaluator_version": EVALUATOR_VERSION,
        
        "topic": topic,
        "summary": summary,
        
        # Anchors
        "anchors": [a.to_dict() for a in all_anchors[:15]],
        "anchors_by_type": {
            "decision": [a.to_dict() for a in decision_anchors],
            "file_path": [a.to_dict() for a in file_path_anchors],
            "tool_state": [a.to_dict() for a in tool_state_anchors],
            "constraint": [a.to_dict() for a in constraint_anchors],
            "open_loop": [a.to_dict() for a in open_loop_anchors]
        },
        
        # Compatibility fields
        "decisions": [{"decision": a.content, "rationale": ""} for a in decision_anchors],
        "open_loops": [{"loop_id": f"loop_{i+1}", "description": a.content, "status": "open"} for i, a in enumerate(open_loop_anchors)],
        "hard_constraints": [a.content for a in constraint_anchors],
        "entities": [{"name": a.content, "type": "file"} for a in file_path_anchors],
        "retrieval_keys": [a.content[:30] for a in all_anchors[:10]],
        
        # Metrics
        "anchor_counts": {
            "decision": len(decision_anchors),
            "file_path": len(file_path_anchors),
            "tool_state": len(tool_state_anchors),
            "constraint": len(constraint_anchors),
            "open_loop": len(open_loop_anchors)
        },
        
        # === V2 Resume Readiness ===
        "resume_readiness": {
            "score": readiness,
            "version": EVALUATOR_VERSION,
            "gates": v2_result["gates"],
            "signals": v2_result["signals"]
        },
        
        "reconstructable": True
    }
    
    return capsule


def run_health_check() -> Dict:
    return {
        "status": "healthy",
        "version": CAPSULE_VERSION,
        "evaluator_version": EVALUATOR_VERSION,
        "features": ["anchor_scoring", "tool_state_extraction", "resume_readiness_v2"]
    }


def run_self_test() -> Dict:
    """Run self-test with V2 evaluator."""
    tests = []
    
    # Test 1: Topic detection
    content1 = "# Gate 1.5 · Readiness Evaluator 校准"
    result1 = compute_readiness_v2_gates(content1)
    tests.append({
        "name": "topic_detection",
        "status": "pass" if result1["gates"]["topic_present"] else "fail"
    })
    
    # Test 2: Task completed detection
    content2 = "✅ Task Completed: Monitoring Setup"
    result2 = compute_readiness_v2_gates(content2)
    tests.append({
        "name": "task_completed_detection",
        "status": "pass" if result2["readiness"] == 0 else "fail"
    })
    
    # Test 3: Gate-based scoring
    content3 = """
    # Gate 1.5 · Readiness Evaluator 校准
    ## Phase 1 进行中
    下一步：标注 calibration error set
    文件：tools/resume_readiness_calibration.py
    """
    result3 = compute_readiness_v2_gates(content3)
    tests.append({
        "name": "gate_based_scoring",
        "status": "pass" if result3["readiness"] >= 0.50 else "fail",
        "details": f"score={result3['readiness']}"
    })
    
    # Test 4: No topic = zero
    content4 = "这是一些普通对话，没有明确主题"
    result4 = compute_readiness_v2_gates(content4)
    tests.append({
        "name": "no_topic_zero",
        "status": "pass" if result4["readiness"] == 0 else "fail",
        "details": f"score={result4['readiness']}"
    })
    
    passed = sum(1 for t in tests if t["status"] == "pass")
    
    return {
        "status": "pass" if passed == len(tests) else "fail",
        "total": len(tests),
        "passed": passed,
        "failed": len(tests) - passed,
        "tests": tests,
        "evaluator_version": EVALUATOR_VERSION
    }


def main():
    parser = argparse.ArgumentParser(description="Capsule Builder V2 with V2 Readiness Evaluator")
    
    parser.add_argument("--input", type=Path, help="Input history file (JSONL)")
    parser.add_argument("--session-id", help="Session ID")
    parser.add_argument("--start", type=int, default=1, help="Start turn")
    parser.add_argument("--end", type=int, default=10, help="End turn")
    parser.add_argument("--output", type=Path, help="Output directory")
    parser.add_argument("--health", action="store_true", help="Run health check")
    parser.add_argument("--test", action="store_true", help="Run self-test")
    parser.add_argument("--json", action="store_true", help="JSON output")
    
    args = parser.parse_args()
    
    if args.health:
        result = run_health_check()
        print(json.dumps(result, indent=2))
        return 0
    
    if args.test:
        result = run_self_test()
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"Self-test: {result['passed']}/{result['total']} passed")
            print(f"Evaluator version: {EVALUATOR_VERSION}")
        return 0 if result["status"] == "pass" else 1
    
    # Validate required args
    if not args.input:
        print("Error: --input is required", file=sys.stderr)
        return 1
    
    if not args.session_id:
        print("Error: --session-id is required", file=sys.stderr)
        return 1
    
    # Load records
    records = load_jsonl(args.input)
    
    # Extract messages
    messages = extract_messages(records, args.start, args.end)
    
    if not messages:
        print(json.dumps({
            "error": "No messages found in range",
            "start": args.start,
            "end": args.end
        }, indent=2))
        return 1
    
    # Build capsule
    capsule = build_capsule(args.session_id, args.start, args.end, messages)
    
    # Save
    output_dir = args.output or OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / f"{capsule['capsule_id']}.json"
    with open(output_path, 'w') as f:
        json.dump(capsule, f, indent=2, ensure_ascii=False)
    
    result = {
        "status": "success",
        "capsule_id": capsule["capsule_id"],
        "path": str(output_path),
        "readiness": capsule["resume_readiness"]["score"],
        "evaluator_version": EVALUATOR_VERSION,
        "gates": capsule["resume_readiness"]["gates"]
    }
    
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
