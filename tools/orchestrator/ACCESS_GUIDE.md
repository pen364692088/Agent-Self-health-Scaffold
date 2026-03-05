# Subagent Callback Reliability System - Access Guide

## Why This Exists

**Problem**: Main agents spawn subagents and wait for callbacks. But callbacks can be lost/delayed, causing main tasks to stall until user sends another message.

**Solution**: Upgrade to **Join/Poll-driven + optional receipts + fallback mailbox** architecture.

## Architecture Overview

```
SPAWN → PENDING → JOIN(POLL) → COLLECT → CONTINUE
           │          │           │
           │          ├─ Check session history
           │          ├─ Check mailbox files
           │          └─ Handle timeout/retry
           │
           └─ Persist for recovery
```

## Quick Start

### For Main Agents

```python
from orchestrator import Orchestrator

# Initialize
orch = Orchestrator()

# Spawn subtask
task_id = orch.spawn_subtask(
    run_id="run_123",
    child_session_key="session_xyz",
    description="Process data"
)

# Join and wait (with timeout)
success = orch.join_all(timeout=300)  # 5 min

# Check results
if success:
    for task in orch.completed_subtasks.values():
        print(f"Completed: {task.summary}")

# Generate audit report
report = orch.generate_run_report()
```

### For Subagents

```python
from subagent_receipt import subtask_done, subtask_fail

# On completion
subtask_done(
    task_id="task_abc123",
    run_id="run_xyz",
    summary="Completed analysis",
    output_paths=["/path/to/output.json"]
)

# On failure
subtask_fail(
    task_id="task_abc123",
    run_id="run_xyz",
    error="Processing failed: timeout"
)
```

### CLI Usage

```bash
# Check status
./orchestrator-cli status -v

# Join pending tasks
./orchestrator-cli join -t 300 -r report.json

# Generate report
./orchestrator-cli report -o run_report.json

# Send receipt (subagent)
./orchestrator-cli receipt task_abc run_123 -s "Done" -o output.json

# Cleanup old tasks
./orchestrator-cli cleanup -d 7
```

## Key Features

### 1. Join/Poll Mechanism (Primary)

Main agent actively polls for completion instead of passively waiting:
- **Exponential backoff**: 1s → 2s → 4s → ... → 20s max
- **Multiple sources**: Session history, mailbox files
- **No external dependencies**: Works even if messaging channel fails

### 2. Explicit Receipts (Acceleration)

Subagents can send structured receipts:
```json
{
  "task_id": "task_abc123",
  "run_id": "run_xyz",
  "status": "ok",
  "output_paths": ["/path/to/output"],
  "summary": "Task completed",
  "timestamp": "2026-03-03T00:00:00"
}
```

### 3. Mailbox Fallback (Reliability)

Files written to `reports/subtasks/<task_id>.done.json`:
- Persists across restarts
- Works without messaging capabilities
- Audit trail

### 4. Recovery

Main agent restart → Load from `pending_subtasks.json`:
- Pending tasks restored
- Can continue from where it left off

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `max_poll_interval` | 20s | Max wait between polls |
| `initial_poll_interval` | 1s | Initial poll interval |
| `default_deadline` | 1 hour | Task deadline |
| `max_retries` | 3 | Retry attempts before fail |

## Testing

Run integration tests:
```bash
python3 test_orchestrator.py
```

Tests cover:
1. ✅ Normal receipt flow
2. ✅ Announce lost → mailbox recovery
3. ✅ Timeout and retry
4. ✅ Restart recovery
5. ✅ Parallel subtasks
6. ✅ Run report generation

## File Structure

```
~/.openclaw/workspace/
├── tools/orchestrator/
│   ├── orchestrator.py         # Core orchestrator
│   ├── subagent_receipt.py     # Receipt handler
│   ├── orchestrator-cli        # CLI tool
│   ├── test_orchestrator.py    # Tests
│   ├── pending_subtasks.json   # Persistent state
│   └── run_report_*.json       # Audit reports
└── reports/subtasks/
    └── *.done.json             # Mailbox files
```

## Integration with OpenClaw

### In AGENTS.md

```markdown
## Subagent Orchestration

Use the orchestrator system for reliable subagent coordination:

from orchestrator import Orchestrator

orch = Orchestrator()
task_id = orch.spawn_subtask(run_id, child_session_key, description)
orch.join_all(timeout=300)
```

### In Subagent Tasks

Always end with receipt:
```python
from subagent_receipt import subtask_done

# ... do work ...

subtask_done(task_id, run_id, summary="Completed", output_paths=[...])
```

## Troubleshooting

### Task stuck in pending

1. Check mailbox: `ls reports/subtasks/`
2. Check persistent state: `cat tools/orchestrator/pending_subtasks.json`
3. Force poll: `./orchestrator-cli join -t 30`

### Recovery not working

1. Verify `pending_subtasks.json` exists
2. Check file permissions
3. Run `./orchestrator-cli status -v`

### Receipt not detected

1. Verify task_id and run_id match
2. Check mailbox file format
3. Ensure file is valid JSON

## Best Practices

1. **Always use join_all()**: Don't assume callbacks will arrive
2. **Set reasonable deadlines**: Match expected task duration
3. **Send receipts**: Both explicit and mailbox for redundancy
4. **Generate reports**: For audit trail
5. **Cleanup periodically**: `./orchestrator-cli cleanup -d 7`

## Comparison

| Approach | Reliability | Recovery | Audit |
|----------|-------------|----------|-------|
| Wait for announce | ❌ Low | ❌ No | ❌ No |
| Join/Poll only | ✅ Medium | ✅ Yes | ✅ Yes |
| Join/Poll + Receipt | ✅ High | ✅ Yes | ✅ Yes |
| + Mailbox fallback | ✅ Highest | ✅ Yes | ✅ Yes |

---

**Version**: 1.0.0
**Author**: CC-Godmode Orchestrator
**License**: MIT
