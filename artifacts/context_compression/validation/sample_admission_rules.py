#!/usr/bin/env python3
"""
sample_admission_rules.py - Sample admission rules for benchmark

Filters out heartbeat-only samples and selects real conversations with
extractable anchors.
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class SampleAdmissionResult:
    """Result of sample admission check."""
    sample_id: str
    admitted: bool
    reason: str
    metrics: Dict
    
    # Anchor potential
    has_decision_anchor: bool = False
    has_entity_anchor: bool = False
    has_open_loop_anchor: bool = False
    has_constraint_anchor: bool = False
    has_tool_state_anchor: bool = False
    
    # Content metrics
    user_message_count: int = 0
    assistant_message_count: int = 0
    tool_call_count: int = 0
    total_text_length: int = 0


# Admission thresholds
MIN_USER_MESSAGES = 1
MIN_ASSISTANT_MESSAGES = 1
MIN_TOTAL_TEXT_LENGTH = 200
MIN_ANCHOR_TYPES = 2  # At least 2 anchor types with potential


def check_sample_admission(events: List[Dict]) -> SampleAdmissionResult:
    """
    Check if a sample meets admission criteria.
    
    Returns SampleAdmissionResult with detailed metrics.
    """
    result = SampleAdmissionResult(
        sample_id="",
        admitted=False,
        reason="",
        metrics={}
    )
    
    # Count message types
    user_texts = []
    assistant_texts = []
    tool_names = set()
    
    for event in events:
        # Check inbound (user message)
        inbound = event.get("inbound", {})
        if inbound.get("text"):
            user_texts.append(inbound["text"])
        if inbound.get("body"):
            user_texts.append(inbound["body"])
        
        # Check sent_events
        for se in event.get("sent_events", []):
            se_type = se.get("type", "")
            
            if se_type == "message":
                if se.get("text"):
                    assistant_texts.append(se["text"])
            elif se_type == "tool_call":
                tool_names.add(se.get("name", "unknown"))
                result.tool_call_count += 1
        
        # Also check historical format
        content = event.get("content", "")
        if isinstance(content, str) and len(content) > 10:
            if event.get("event_type") == "user":
                user_texts.append(content)
            elif event.get("event_type") == "assistant":
                assistant_texts.append(content)
    
    result.user_message_count = len(user_texts)
    result.assistant_message_count = len(assistant_texts)
    result.total_text_length = sum(len(t) for t in user_texts + assistant_texts)
    
    # Check for anchor potential
    all_text = " ".join(user_texts + assistant_texts)
    
    # Decision anchors
    decision_patterns = ["决定", "确认", "选择", "采用", "we decide", "decided", "✅", "completed", "完成"]
    result.has_decision_anchor = any(p in all_text.lower() for p in decision_patterns)
    
    # Entity anchors (files, tools, concepts)
    import re
    files = re.findall(r'[\w/\-\.]+\.(py|js|ts|json|md|yaml|yml|sh|toml)', all_text)
    tools_mentioned = re.findall(r'tool[:\s]+(\w+)', all_text, re.IGNORECASE)
    result.has_entity_anchor = len(files) > 0 or len(tools_mentioned) > 0 or len(tool_names) > 0
    
    # Open loop anchors
    open_loop_patterns = ["TODO", "TBD", "待定", "待处理", "pending", "need to", "后续"]
    result.has_open_loop_anchor = any(p in all_text for p in open_loop_patterns)
    
    # Constraint anchors
    constraint_patterns = ["必须", "不能", "禁止", "must", "cannot", "forbidden", "确保"]
    result.has_constraint_anchor = any(p in all_text for p in constraint_patterns)
    
    # Tool state anchors
    result.has_tool_state_anchor = result.tool_call_count > 0
    
    # Count anchor types
    anchor_types = sum([
        result.has_decision_anchor,
        result.has_entity_anchor,
        result.has_open_loop_anchor,
        result.has_constraint_anchor,
        result.has_tool_state_anchor
    ])
    
    # Determine admission
    reasons = []
    
    if result.user_message_count < MIN_USER_MESSAGES:
        reasons.append(f"user_messages={result.user_message_count}<{MIN_USER_MESSAGES}")
    
    if result.assistant_message_count < MIN_ASSISTANT_MESSAGES:
        reasons.append(f"assistant_messages={result.assistant_message_count}<{MIN_ASSISTANT_MESSAGES}")
    
    if result.total_text_length < MIN_TOTAL_TEXT_LENGTH:
        reasons.append(f"text_length={result.total_text_length}<{MIN_TOTAL_TEXT_LENGTH}")
    
    if anchor_types < MIN_ANCHOR_TYPES:
        reasons.append(f"anchor_types={anchor_types}<{MIN_ANCHOR_TYPES}")
    
    if reasons:
        result.admitted = False
        result.reason = "; ".join(reasons)
    else:
        result.admitted = True
        result.reason = "passed all checks"
    
    result.metrics = {
        "user_message_count": result.user_message_count,
        "assistant_message_count": result.assistant_message_count,
        "tool_call_count": result.tool_call_count,
        "total_text_length": result.total_text_length,
        "anchor_types": anchor_types,
        "anchor_breakdown": {
            "decision": result.has_decision_anchor,
            "entity": result.has_entity_anchor,
            "open_loop": result.has_open_loop_anchor,
            "constraint": result.has_constraint_anchor,
            "tool_state": result.has_tool_state_anchor
        }
    }
    
    return result


def scan_session_for_old_topic(session_file: Path) -> Optional[Dict]:
    """
    Scan a session file for old topic recall potential.
    
    Returns sample dict if suitable, None otherwise.
    """
    events = []
    
    with open(session_file) as f:
        for line in f:
            try:
                d = json.loads(line)
                if d.get("type") in ["message", "tool_call", "toolResult", "custom"]:
                    events.append(d)
            except:
                pass
    
    if len(events) < 5:  # Need enough events
        return None
    
    # Check admission
    result = check_sample_admission(events)
    
    if not result.admitted:
        return None
    
    # Check for old topic indicators
    all_text = ""
    for e in events:
        msg = e.get("message", {})
        content = msg.get("content", [])
        if isinstance(content, list):
            for c in content:
                if c.get("type") == "text":
                    all_text += c.get("text", "") + " "
        elif isinstance(content, str):
            all_text += content + " "
    
    # Old topic patterns
    old_topic_patterns = [
        "之前", "上次", "之前提到", "继续", "回到", "刚才说",
        "earlier", "last time", "mentioned before", "continue",
        "let's get back", "回到", "继续做", "继续完成"
    ]
    
    has_old_topic = any(p in all_text for p in old_topic_patterns)
    
    if not has_old_topic:
        return None
    
    return {
        "session_file": str(session_file),
        "sample_id": f"real_main_{session_file.stem[:8]}",
        "admission": result.metrics,
        "has_old_topic_indicator": True
    }


def main():
    """Scan main agent sessions for admissible samples."""
    main_sessions = Path("~/.openclaw/agents/main/sessions").expanduser()
    jsonl_files = sorted(main_sessions.glob("*.jsonl"), key=lambda x: x.stat().st_mtime, reverse=True)
    
    print(f"Scanning {len(jsonl_files)} main agent sessions...\n")
    
    admitted = []
    rejected_counts = {
        "no_old_topic": 0,
        "heartbeat_only": 0,
        "insufficient_content": 0
    }
    
    for jf in jsonl_files[:500]:  # Scan recent 500
        result = scan_session_for_old_topic(jf)
        
        if result:
            admitted.append(result)
        else:
            # Quick check why rejected
            with open(jf) as f:
                events = [json.loads(l) for l in f if l.strip()]
            
            check = check_sample_admission(events)
            
            if check.user_message_count == 0:
                rejected_counts["heartbeat_only"] += 1
            elif check.total_text_length < 200:
                rejected_counts["insufficient_content"] += 1
            else:
                rejected_counts["no_old_topic"] += 1
    
    print(f"Results:\n")
    print(f"  Admitted: {len(admitted)}")
    print(f"  Rejected (heartbeat_only): {rejected_counts['heartbeat_only']}")
    print(f"  Rejected (insufficient_content): {rejected_counts['insufficient_content']}")
    print(f"  Rejected (no_old_topic): {rejected_counts['no_old_topic']}")
    
    print(f"\nAdmitted samples:")
    for s in admitted[:10]:
        print(f"  {s['sample_id']}: anchors={s['admission']['anchor_types']}, text_len={s['admission']['total_text_length']}")
    
    # Save admitted samples
    if admitted:
        output = Path("~/.openclaw/workspace/artifacts/context_compression/validation/admissible_real_samples.json").expanduser()
        with open(output, "w") as f:
            json.dump({
                "generated_at": datetime.now().isoformat(),
                "total_scanned": min(500, len(jsonl_files)),
                "admitted_count": len(admitted),
                "samples": admitted
            }, f, indent=2)
        print(f"\nSaved to: {output}")
    
    return admitted


if __name__ == "__main__":
    main()
