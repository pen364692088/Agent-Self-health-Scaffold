#!/usr/bin/env python3
"""
anchor_enhanced_capsule_builder.py - Capsule builder with anchor extraction

Enhanced version for parallel hardening branch.
Extracts 6 anchor types from conversation events:
- decision_anchor
- entity_anchor
- time_anchor
- open_loop_anchor
- constraint_anchor
- tool_state_anchor
"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

WORKSPACE = Path("/home/moonlight/.openclaw/workspace")

# Anchor extraction patterns
DECISION_PATTERNS = [
    r"决定[是为]", r"确认[是为]", r"选择", r"采用", r"使用.*方案",
    r"we decide", r"decided to", r"confirmed that", r"will use",
    r"确定使用", r"最终方案", r"达成一致", r"同意"
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
    for event in events:
        content = event.get("content", "") or event.get("text", "")
        if isinstance(content, list):
            content = " ".join(str(c) for c in content)
        
        for pattern in DECISION_PATTERNS:
            matches = re.findall(rf'(.{{0,50}}{pattern}.{{0,100}})', content, re.IGNORECASE)
            for match in matches:
                match = match.strip()
                if len(match) > 15:
                    anchors.append({
                        "type": "decision_anchor",
                        "content": match[:200],
                        "source_event": event.get("event_id", event.get("timestamp", "")),
                        "confidence": 0.8
                    })
    
    # Deduplicate
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
        content = event.get("content", "") or event.get("text", "")
        if isinstance(content, list):
            content = " ".join(str(c) for c in content)
        
        # Files
        files = re.findall(r'[\w/\-\.]+\.(py|js|ts|json|md|yaml|yml|sh|toml)', content)
        for f in files:
            if f not in entities:
                entities[f] = {"name": f, "type": "file", "mentions": 0}
            entities[f]["mentions"] += 1
        
        # Tools/CLI commands
        tools = re.findall(r'\b(\w+-\w+|\w+_\w+)\b', content)
        for t in tools:
            if len(t) > 3 and t not in ["tool_name", "event_type"]:
                if t not in entities:
                    entities[t] = {"name": t, "type": "tool", "mentions": 0}
                entities[t]["mentions"] += 1
        
        # Projects/Concepts
        concepts = re.findall(r'\b([A-Z][a-zA-Z]{2,})\b', content)
        for c in concepts:
            if c not in ["The", "This", "That", "OpenClaw", "JSON", "TODO", "TBD"]:
                if c not in entities:
                    entities[c] = {"name": c, "type": "concept", "mentions": 0}
                entities[c]["mentions"] += 1
    
    # Convert to anchor format
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
        content = event.get("content", "") or event.get("text", "")
        if isinstance(content, list):
            content = " ".join(str(c) for c in content)
        
        # Event timestamp
        ts = event.get("timestamp", event.get("ts", ""))
        if ts:
            anchors.append({
                "type": "time_anchor",
                "timestamp": ts,
                "confidence": 0.9
            })
        
        # Time references in content
        for pattern in TIME_PATTERNS:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                anchors.append({
                    "type": "time_anchor",
                    "reference": match,
                    "confidence": 0.7
                })
    
    # Deduplicate timestamps
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
        content = event.get("content", "") or event.get("text", "")
        if isinstance(content, list):
            content = " ".join(str(c) for c in content)
        
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
    
    # Deduplicate
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
        content = event.get("content", "") or event.get("text", "")
        if isinstance(content, list):
            content = " ".join(str(c) for c in content)
        
        for pattern in CONSTRAINT_PATTERNS:
            matches = re.findall(rf'(.{{0,30}}{pattern}.{{0,100}})', content, re.IGNORECASE)
            for match in matches:
                match = match.strip()
                if len(match) > 15:
                    anchors.append({
                        "type": "constraint_anchor",
                        "content": match[:200],
                        "confidence": 0.85
                    })
    
    # Deduplicate
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
        tool_name = event.get("tool_name", "")
        event_type = event.get("event_type", "")
        content = event.get("content", "") or event.get("text", "")
        
        if isinstance(content, list):
            content = " ".join(str(c) for c in content)
        
        if tool_name:
            # Determine state
            state = "called"
            if re.search(r"成功|succeed|complete|done", content, re.IGNORECASE):
                state = "success"
            elif re.search(r"失败|fail|error", content, re.IGNORECASE):
                state = "failed"
            
            anchors.append({
                "type": "tool_state_anchor",
                "tool_name": tool_name,
                "state": state,
                "event_type": event_type,
                "confidence": 0.9
            })
        
        # Also check for tool mentions in content
        for pattern in TOOL_STATE_PATTERNS:
            matches = re.findall(rf'(.{{0,20}}{pattern}.{{0,50}})', content, re.IGNORECASE)
            for match in matches:
                anchors.append({
                    "type": "tool_state_anchor",
                    "content": match[:100],
                    "confidence": 0.7
                })
    
    return anchors[:10]


def build_capsule_with_anchors(sample_data: Dict) -> Dict:
    """Build capsule with anchor extraction from sample data."""
    sample_id = sample_data.get("sample_id", "unknown")
    session_id = sample_data.get("session_id", sample_id)
    events = sample_data.get("events", [])
    
    # Extract all anchor types
    decision_anchors = extract_decision_anchors(events)
    entity_anchors = extract_entity_anchors(events)
    time_anchors = extract_time_anchors(events)
    open_loop_anchors = extract_open_loop_anchors(events)
    constraint_anchors = extract_constraint_anchors(events)
    tool_state_anchors = extract_tool_state_anchors(events)
    
    # Build topic from sample metadata
    topic = "old_topic_recall"  # Default
    if "old_topic_focus" in sample_id:
        topic = "old_topic_focus"
    
    # Build capsule
    capsule = {
        "capsule_id": f"cap_{sample_id}",
        "session_id": session_id,
        "sample_id": sample_id,
        "source_type": sample_data.get("source_type", "unknown"),
        "topic": topic,
        "summary": f"Session with {len(events)} events",
        "created_at": datetime.now().isoformat(),
        
        # Anchor fields (the key enhancement)
        "anchors": {
            "decision_anchor": decision_anchors,
            "entity_anchor": entity_anchors,
            "time_anchor": time_anchors,
            "open_loop_anchor": open_loop_anchors,
            "constraint_anchor": constraint_anchors,
            "tool_state_anchor": tool_state_anchors
        },
        
        # Summary counts
        "anchor_counts": {
            "decision": len(decision_anchors),
            "entity": len(entity_anchors),
            "time": len(time_anchors),
            "open_loop": len(open_loop_anchors),
            "constraint": len(constraint_anchors),
            "tool_state": len(tool_state_anchors)
        },
        
        # Legacy fields for compatibility
        "decisions": [{"decision": a["content"], "rationale": ""} for a in decision_anchors],
        "open_loops": open_loop_anchors,
        "hard_constraints": [a["content"] for a in constraint_anchors],
        "entities": entity_anchors,
        "retrieval_keys": [e["name"] for e in entity_anchors[:10]]
    }
    
    return capsule


def main():
    import sys
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: anchor_enhanced_capsule_builder.py <sample.json>"}))
        sys.exit(1)
    
    sample_path = Path(sys.argv[1])
    if not sample_path.exists():
        print(json.dumps({"error": f"File not found: {sample_path}"}))
        sys.exit(1)
    
    with open(sample_path, 'r') as f:
        sample_data = json.load(f)
    
    capsule = build_capsule_with_anchors(sample_data)
    print(json.dumps(capsule, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
