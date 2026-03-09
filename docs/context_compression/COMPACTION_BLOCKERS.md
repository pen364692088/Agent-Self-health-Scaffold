# Compaction Blockers v1.0

## Overview

This document defines conditions that prevent automatic compaction from occurring. Each blocker has a detection method, severity level, and bypass conditions.

---

## Blocker Categories

| Category | ID Prefix | Description |
|----------|-----------|-------------|
| State | BLK-STATE | Incomplete state persistence |
| Git | BLK-GIT | Uncommitted or immature changes |
| Workflow | BLK-WFLOW | Active workflow in progress |
| Timing | BLK-TIME | Cooldown or timing constraints |
| Critical | BLK-CRIT | Critical operations in progress |

---

## Blocker Definitions

### BLK-STATE-001: Unpersisted Working Buffer

**Description**: Working buffer has unsaved changes.

**Detection Method**:
```bash
# Check if working-buffer.md exists and has recent modifications
test -f working-buffer.md && \
  test $(stat -c %Y working-buffer.md) -gt $(($(date +%s) - 300))
```

**Severity**: Medium

**Bypass Conditions**:
- Emergency compression (auto-flush before compress)
- User explicitly approved bypass

**Resolution**:
```bash
# Flush working buffer to handoff
state-journal-append --action flush_working_buffer
```

---

### BLK-STATE-002: Open Loops Not Persisted

**Description**: Open loops or pending tasks not written to SESSION-STATE.md.

**Detection Method**:
```bash
# Check for "open_loop" entries not in persisted state
grep -q "open_loop" working-buffer.md && \
  ! grep -q "open_loop" SESSION-STATE.md
```

**Severity**: Medium

**Bypass Conditions**:
- Emergency compression with force flag
- All loops are informational only

**Resolution**:
```bash
# Persist open loops
state-write-atomic SESSION-STATE.md "$(cat SESSION-STATE.md)
# + append open loops section"
```

---

### BLK-STATE-003: Tool State Not Flushed

**Description**: Active tool state not persisted (e.g., running background processes).

**Detection Method**:
```bash
# Check for active exec sessions
process --action list | jq 'length > 0'

# Check for background jobs file
test -f artifacts/background_jobs.json && \
  jq 'length > 0' artifacts/background_jobs.json
```

**Severity**: High

**Bypass Conditions**:
- Jobs are in completed state
- Emergency compression with explicit job log

**Resolution**:
```bash
# Wait for jobs to complete or log state
process --action list --json > artifacts/background_jobs_snapshot.json
```

---

### BLK-GIT-001: Uncommitted WIP Changes

**Description**: Working directory has uncommitted changes that would be lost.

**Detection Method**:
```bash
# Check git status
git status --porcelain | grep -q .
```

**Severity**: High

**Bypass Conditions**:
- Emergency compression with stash
- Changes are auto-generated / temporary
- User explicitly approved bypass

**Resolution**:
```bash
# Auto-commit or stash
git add -A && git commit -m "auto: pre-compaction snapshot"
# OR
git stash push -m "pre-compaction stash"
```

---

### BLK-GIT-002: Branch Not Mature

**Description**: Branch created recently with insufficient testing.

**Detection Method**:
```bash
# Check branch age
branch_age=$(git log -1 --format=%ct HEAD)
current_time=$(date +%s)
age_hours=$(( (current_time - branch_age) / 3600 ))
test $age_hours -lt 1  # Less than 1 hour old
```

**Severity**: Low

**Bypass Conditions**:
- Emergency compression
- Branch is main/master
- User explicitly approved

**Resolution**:
- Wait for branch to mature
- Or proceed with explicit approval

---

### BLK-WFLOW-001: Critical Gate In Progress

**Description**: A critical Gate (A/B/C) validation is in progress.

**Detection Method**:
```bash
# Check for Gate in progress markers
test -f artifacts/gates/.gate_in_progress

# Or check SESSION-STATE.md
grep -q "Gate.*in_progress" SESSION-STATE.md
```

**Severity**: Critical

**Bypass Conditions**:
- None (must wait for Gate completion)

**Resolution**:
- Wait for Gate to complete
- Check Gate status with verify-and-close

---

### BLK-WFLOW-002: Subagent Task In Progress

**Description**: Active subagent task that may report back.

**Detection Method**:
```bash
# Check for active subagent sessions
subtask-orchestrate status --json | jq '.active_count > 0'

# Check inbox for pending receipts
test -f reports/subtasks/.active_task
```

**Severity**: High

**Bypass Conditions**:
- Emergency compression with task log
- Subagent has completed (check inbox)

**Resolution**:
```bash
# Wait for subagent completion or log state
subtask-orchestrate status > artifacts/subagent_snapshot.json
```

---

### BLK-WFLOW-003: User Interaction Pending

**Description**: Waiting for user response to a question or confirmation.

**Detection Method**:
```bash
# Check for pending user input marker
test -f artifacts/.awaiting_user_input

# Or check last message in conversation
# (requires conversation history access)
```

**Severity**: Medium

**Bypass Conditions**:
- Emergency compression
- Timeout exceeded (> 10 minutes)

**Resolution**:
- Wait for user response
- Or proceed after timeout with note

---

### BLK-TIME-001: Recent Compaction (Cooldown)

**Description**: Last compaction was too recent.

**Detection Method**:
```bash
# Check cooldown state
if [ -f artifacts/context_compression/cooldown_state.json ]; then
  last_time=$(jq -r '.last_compaction_time' artifacts/context_compression/cooldown_state.json)
  last_epoch=$(date -d "$last_time" +%s 2>/dev/null || echo 0)
  current_epoch=$(date +%s)
  elapsed=$((current_epoch - last_epoch))
  min_interval=1800  # 30 minutes
  test $elapsed -lt $min_interval
fi
```

**Severity**: Medium

**Bypass Conditions**:
- Emergency compression
- Force flag set

**Resolution**:
- Wait for cooldown to expire
- Or use force flag with justification

---

### BLK-CRIT-001: Critical Operation In Progress

**Description**: A critical operation that cannot be interrupted.

**Detection Method**:
```bash
# Check for critical operation marker
test -f artifacts/.critical_operation_in_progress

# Check specific critical states
# (deployment, payment, etc.)
```

**Severity**: Critical

**Bypass Conditions**:
- None

**Resolution**:
- Wait for operation to complete
- Must not interrupt

---

## Blocker Summary Table

| ID | Name | Severity | Emergency Bypass | Detection |
|----|------|----------|------------------|-----------|
| BLK-STATE-001 | Unpersisted Working Buffer | Medium | Yes | file mtime |
| BLK-STATE-002 | Open Loops Not Persisted | Medium | Yes | grep pattern |
| BLK-STATE-003 | Tool State Not Flushed | High | Yes | process list |
| BLK-GIT-001 | Uncommitted WIP | High | Yes | git status |
| BLK-GIT-002 | Branch Not Mature | Low | Yes | branch age |
| BLK-WFLOW-001 | Critical Gate In Progress | Critical | No | marker file |
| BLK-WFLOW-002 | Subagent Task In Progress | High | Yes | orchestration status |
| BLK-WFLOW-003 | User Interaction Pending | Medium | Yes | marker file |
| BLK-TIME-001 | Recent Compaction (Cooldown) | Medium | Yes | cooldown state |
| BLK-CRIT-001 | Critical Operation In Progress | Critical | No | marker file |

---

## Detection Implementation

### All Blockers Check

```bash
#!/usr/bin/env python3
"""
Blocker detection for compaction.
Returns list of active blockers with severity levels.
"""

import subprocess
import json
import os
from datetime import datetime
from pathlib import Path

WORKSPACE = Path("/home/moonlight/.openclaw/workspace")

def check_unpersisted_working_buffer():
    """BLK-STATE-001"""
    wb = WORKSPACE / "working-buffer.md"
    if not wb.exists():
        return None
    
    # Check if modified in last 5 minutes
    mtime = wb.stat().st_mtime
    if datetime.now().timestamp() - mtime < 300:
        return {
            "id": "BLK-STATE-001",
            "name": "Unpersisted Working Buffer",
            "severity": "medium",
            "bypass": True
        }
    return None

def check_open_loops():
    """BLK-STATE-002"""
    wb = WORKSPACE / "working-buffer.md"
    ss = WORKSPACE / "SESSION-STATE.md"
    
    if not wb.exists():
        return None
    
    try:
        wb_content = wb.read_text()
        ss_content = ss.read_text() if ss.exists() else ""
        
        if "open_loop" in wb_content and "open_loop" not in ss_content:
            return {
                "id": "BLK-STATE-002",
                "name": "Open Loops Not Persisted",
                "severity": "medium",
                "bypass": True
            }
    except:
        pass
    return None

def check_tool_state():
    """BLK-STATE-003"""
    try:
        result = subprocess.run(
            ["process", "--action", "list"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            if data and len(data) > 0:
                return {
                    "id": "BLK-STATE-003",
                    "name": "Tool State Not Flushed",
                    "severity": "high",
                    "bypass": True
                }
    except:
        pass
    return None

def check_uncommitted_wip():
    """BLK-GIT-001"""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=WORKSPACE
        )
        if result.stdout.strip():
            return {
                "id": "BLK-GIT-001",
                "name": "Uncommitted WIP Changes",
                "severity": "high",
                "bypass": True
            }
    except:
        pass
    return None

def check_critical_gate():
    """BLK-WFLOW-001"""
    marker = WORKSPACE / "artifacts" / "gates" / ".gate_in_progress"
    if marker.exists():
        return {
            "id": "BLK-WFLOW-001",
            "name": "Critical Gate In Progress",
            "severity": "critical",
            "bypass": False
        }
    return None

def check_cooldown():
    """BLK-TIME-001"""
    cooldown_file = WORKSPACE / "artifacts" / "context_compression" / "cooldown_state.json"
    if not cooldown_file.exists():
        return None
    
    try:
        data = json.loads(cooldown_file.read_text())
        last_time = datetime.fromisoformat(data["last_compaction_time"].replace("Z", "+00:00"))
        elapsed = (datetime.now(last_time.tzinfo) - last_time).total_seconds()
        
        # 30 minute cooldown
        if elapsed < 1800:
            return {
                "id": "BLK-TIME-001",
                "name": "Recent Compaction (Cooldown)",
                "severity": "medium",
                "bypass": True,
                "remaining_seconds": int(1800 - elapsed)
            }
    except:
        pass
    return None

def detect_all_blockers():
    """Run all blocker checks."""
    blockers = []
    
    checks = [
        check_unpersisted_working_buffer,
        check_open_loops,
        check_tool_state,
        check_uncommitted_wip,
        check_critical_gate,
        check_cooldown,
    ]
    
    for check in checks:
        result = check()
        if result:
            blockers.append(result)
    
    return blockers

if __name__ == "__main__":
    blockers = detect_all_blockers()
    print(json.dumps(blockers, indent=2))
```

---

## Resolution Workflow

```
┌──────────────────────┐
│   Detect Blockers    │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Any Critical (No    │
│  Bypass)?            │
└──────────┬───────────┘
           │
     ┌─────┴─────┐
     │ Yes       │ No
     ▼           ▼
┌─────────┐  ┌──────────────────┐
│ BLOCKED │  │ Can Bypass?      │
│ Wait    │  │ (Emergency?)     │
└─────────┘  └────────┬─────────┘
                      │
                ┌─────┴─────┐
                │ Yes       │ No
                ▼           ▼
         ┌───────────┐  ┌────────────┐
         │ Apply     │  │ Resolve    │
         │ Bypass    │  │ Blockers   │
         │ Log Reason│  │ First      │
         └───────────┘  └────────────┘
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-03-09 | Initial blocker definitions |
