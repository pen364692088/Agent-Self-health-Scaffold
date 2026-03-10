# Day 1-4 Runbook

**Generated**: 2026-03-10 06:42 CST
**Version**: 1.0
**Purpose**: Step-by-step execution guide for first 4 days post-observation

---

## Pre-Runbook Checklist

**Execute this before starting Day 1:**

```bash
#!/bin/bash
echo "=== PRE-RUNBOOK CHECKLIST ==="

# 1. Observation window complete?
echo "1. Observation status:"
cat ~/.openclaw/workspace/artifacts/memory_freeze/OBSERVATION_METRICS.md | grep -A5 "Day"

# 2. Exit criteria green?
echo "2. Exit criteria:"
~/.openclaw/workspace/tools/memory-daily-obs --json | grep -E "false_captures|duplicate|embedding_errors"

# 3. Policy healthy?
echo "3. Policy health:"
~/.openclaw/workspace/tools/policy-doctor --json | grep "healthy"

# 4. Tests pass?
echo "4. Running tests..."
python -m pytest tests/ -v --tb=short 2>&1 | tail -10

# 5. Create baseline tag
echo "5. Creating baseline tag..."
git tag pre-consolidation-$(date +%Y%m%d)
git add -A
git commit -m "Pre-consolidation baseline" 2>/dev/null || echo "No changes to commit"

echo "=== CHECKLIST COMPLETE ==="
```

---

## Day 1: Delete Deprecated Tools

**Objective**: Remove 5 deprecated/backup files.

**Risk Level**: MINIMAL

**Duration**: 30 minutes

### Step 1.1: Pre-Delete Verification

```bash
#!/bin/bash
echo "=== STEP 1.1: PRE-DELETE VERIFICATION ==="

# Verify all candidates have 0 usage
candidates=(
    "verify-and-close-v2"
    "check-subagent-mailbox"
    "callback-handler"
    "session-archive.original"
    "session-start-recovery.bak"
)

for c in "${candidates[@]}"; do
    count=$(grep -r "$c" ~/.openclaw/workspace/tools/ 2>/dev/null | grep -v "^Binary" | wc -l)
    echo "$c: $count references"
done

# All should be 0
echo "If any > 0, DO NOT DELETE. Investigate first."
```

### Step 1.2: Create Rollback Tag

```bash
#!/bin/bash
echo "=== STEP 1.2: CREATE ROLLBACK TAG ==="

git tag pre-delete-$(date +%Y%m%d-%H%M)
echo "Tag created: pre-delete-$(date +%Y%m%d-%H%M)"
```

### Step 1.3: Delete Files

```bash
#!/bin/bash
echo "=== STEP 1.3: DELETE FILES ==="

# Delete deprecated tools
rm -v ~/.openclaw/workspace/tools/verify-and-close-v2
rm -v ~/.openclaw/workspace/tools/legacy/check-subagent-mailbox
rm -v ~/.openclaw/workspace/tools/callback-handler
rm -v ~/.openclaw/workspace/tools/session-archive.original
rm -v ~/.openclaw/workspace/tools/session-start-recovery.bak

echo "Files deleted successfully"
```

### Step 1.4: Verify Deletion

```bash
#!/bin/bash
echo "=== STEP 1.4: VERIFY DELETION ==="

# Check files are gone
for f in \
    ~/.openclaw/workspace/tools/verify-and-close-v2 \
    ~/.openclaw/workspace/tools/legacy/check-subagent-mailbox \
    ~/.openclaw/workspace/tools/callback-handler \
    ~/.openclaw/workspace/tools/session-archive.original \
    ~/.openclaw/workspace/tools/session-start-recovery.bak
do
    if [ -f "$f" ]; then
        echo "FAIL: $f still exists"
    else
        echo "PASS: $f deleted"
    fi
done
```

### Step 1.5: Run Tests

```bash
#!/bin/bash
echo "=== STEP 1.5: RUN TESTS ==="

python -m pytest tests/ -v --tb=short 2>&1 | tail -20
```

### Step 1.6: Commit and Tag

```bash
#!/bin/bash
echo "=== STEP 1.6: COMMIT AND TAG ==="

git add -A
git commit -m "Day 1: Delete deprecated tools

Deleted:
- verify-and-close-v2 (superseded)
- check-subagent-mailbox (deprecated)
- callback-handler (deprecated)
- session-archive.original (backup)
- session-start-recovery.bak (backup)"

git tag post-delete-$(date +%Y%m%d-%H%M)
echo "Tag created: post-delete-$(date +%Y%m%d-%H%M)"
```

### Step 1.7: Post-Delete Monitoring

```bash
#!/bin/bash
echo "=== STEP 1.7: POST-DELETE MONITORING ==="

# Wait 5 minutes, then check
sleep 300

# Check heartbeat
echo "Heartbeat check:"
journalctl --user -u openclaw-heartbeat --since "5 minutes ago" | grep -E "HEARTBEAT|ALERT" | tail -5

# Check for errors
echo "Error check:"
grep -r "ERROR\|Exception" ~/.openclaw/workspace/logs/ --since="5 minutes ago" | head -5 || echo "No errors"

echo "Day 1 complete. Proceed to Day 2 after 24 hours."
```

---

## Day 2: Monitoring Day

**Objective**: Monitor for any issues from Day 1 deletion.

**Risk Level**: NONE

**Duration**: 15 minutes (check-in)

### Step 2.1: Morning Check

```bash
#!/bin/bash
echo "=== DAY 2: MORNING CHECK ==="

# Check heartbeat
echo "1. Heartbeat status:"
journalctl --user -u openclaw-heartbeat --since "24 hours ago" | grep ALERT | wc -l
echo "ALERT count (should be 0)"

# Check memory
echo "2. Memory status:"
~/.openclaw/workspace/tools/memory-daily-obs --json | head -20

# Check policy
echo "3. Policy status:"
~/.openclaw/workspace/tools/policy-doctor --json | grep -A2 "summary"

# Check for errors
echo "4. Error count:"
grep -r "ERROR" ~/.openclaw/workspace/logs/ --since="24 hours ago" | wc -l
echo "(Should be low)"

echo "Day 2 monitoring complete. If all green, proceed to Day 3."
```

### Step 2.2: Decision Point

```
IF issues detected:
    → Investigate
    → May need to rollback: git checkout pre-delete-*

IF all green:
    → Proceed to Day 3 (P0-2: Receipt check)
```

---

## Day 3: P0-2 Receipt Check

**Objective**: Enforce receipt requirement in finalize-response.

**Risk Level**: MEDIUM

**Duration**: 1-2 hours

### Step 3.1: Pre-Patch Verification

```bash
#!/bin/bash
echo "=== STEP 3.1: PRE-PATCH VERIFICATION ==="

# Verify tests pass
python -m pytest tests/ -v --tb=short 2>&1 | tail -10

# Verify Day 1 deletion stable
ls ~/.openclaw/workspace/tools/verify-and-close-v2 2>/dev/null && echo "FAIL: v2 still exists" || echo "PASS: v2 deleted"
```

### Step 3.2: Create Rollback Tag

```bash
#!/bin/bash
echo "=== STEP 3.2: CREATE ROLLBACK TAG ==="

git tag pre-p0-2-$(date +%Y%m%d-%H%M)
echo "Tag created: pre-p0-2-$(date +%Y%m%d-%H%M)"
```

### Step 3.3: Apply Patch

**Edit file**: `tools/finalize-response`

**Changes**:

1. **Require final receipt** (change from check to enforce):

```python
# Find the check_receipts_exist function
# Modify to enforce at least final receipt

def check_receipts_exist(task_id):
    required = ["final"]  # At minimum, final receipt
    missing = []
    
    for rtype in required:
        path = ARTIFACTS_DIR / f"{task_id}_{rtype}_receipt.json"
        if not path.exists():
            missing.append(rtype)
    
    return len(missing) == 0, missing
```

2. **Update main function** to block if missing:

```python
# In main(), after receipt check:

if not receipts_ok:
    result["action"] = "BLOCK"
    result["reason"] = "missing_receipts"
    result["missing"] = missing
    result["hint"] = f"Run verify-and-close --task-id {args.task_id} first"
    
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"❌ BLOCK: Missing receipts: {missing}")
        print(f"   Run: verify-and-close --task-id {args.task_id}")
    
    return 1  # Exit with error
```

### Step 3.4: Run Tests

```bash
#!/bin/bash
echo "=== STEP 3.4: RUN TESTS ==="

# Create test file if not exists
cat > ~/.openclaw/workspace/tests/test_finalize_response_receipt.py << 'TESTEOF'
import subprocess
import json
from pathlib import Path

def test_block_without_receipt():
    """Verify finalize-response blocks without receipt."""
    result = subprocess.run(
        ["python3", str(Path.home() / ".openclaw/workspace/tools/finalize-response"),
         "--task-id", "no_receipt_test", "--summary", "Done", "--json"],
        capture_output=True, text=True
    )
    try:
        data = json.loads(result.stdout)
        assert data.get("action") == "BLOCK"
        assert "missing_receipts" in data.get("reason", "")
        print("PASS: Blocks without receipt")
    except Exception as e:
        print(f"FAIL: {e}")
        assert False

if __name__ == "__main__":
    test_block_without_receipt()
TESTEOF

python -m pytest tests/test_finalize_response_receipt.py -v
```

### Step 3.5: Commit and Tag

```bash
#!/bin/bash
echo "=== STEP 3.5: COMMIT AND TAG ==="

git add -A
git commit -m "Day 3: P0-2 - Enforce receipt requirement in finalize-response

Changes:
- Require final receipt before allowing completion
- Block with clear error message if missing
- Provides hint to run verify-and-close"

git tag post-p0-2-$(date +%Y%m%d-%H%M)
echo "Tag created: post-p0-2-$(date +%Y%m%d-%H%M)"
```

### Step 3.6: Post-Patch Monitoring

```bash
#!/bin/bash
echo "=== STEP 3.6: POST-PATCH MONITORING ==="

# Test the new behavior
echo "Testing finalize-response:"
python3 ~/.openclaw/workspace/tools/finalize-response --task-id test_no_receipt --summary "Test" --json

# Should show BLOCK
echo ""
echo "Monitoring for 30 minutes..."
sleep 1800

# Check logs
echo "Finalize log entries:"
tail -5 ~/.openclaw/workspace/reports/finalize_log.jsonl 2>/dev/null || echo "No log"

echo "Day 3 complete. Proceed to Day 4 after 24 hours."
```

---

## Day 4: P0-3 --force Audit

**Objective**: Add audit trail for safe-message --force.

**Risk Level**: LOW

**Duration**: 1 hour

### Step 4.1: Pre-Patch Verification

```bash
#!/bin/bash
echo "=== STEP 4.1: PRE-PATCH VERIFICATION ==="

# Verify Day 3 stable
python -m pytest tests/test_finalize_response_receipt.py -v

# Verify tests pass
python -m pytest tests/ -v --tb=short 2>&1 | tail -10
```

### Step 4.2: Create Rollback Tag

```bash
#!/bin/bash
echo "=== STEP 4.2: CREATE ROLLBACK TAG ==="

git tag pre-p0-3-$(date +%Y%m%d-%H%M)
echo "Tag created: pre-p0-3-$(date +%Y%m%d-%H%M)"
```

### Step 4.3: Apply Patch

**Edit file**: `tools/safe-message`

**Changes**:

1. **Add audit function**:

```python
def audit_force_send(task_id, channel, message):
    """Log force send to audit trail."""
    import os
    from datetime import datetime
    
    audit_dir = WORKSPACE / "artifacts" / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    
    entry = {
        "timestamp": datetime.now().isoformat(),
        "action": "FORCE_SEND",
        "task_id": task_id,
        "channel": channel,
        "message_length": len(message),
        "message_preview": message[:100],
        "session_key": os.environ.get("OPENCLAW_SESSION_KEY", "unknown")
    }
    
    audit_file = audit_dir / "force_send_audit.jsonl"
    with open(audit_file, "a") as f:
        f.write(json.dumps(entry) + "\n")
    
    return entry
```

2. **Modify force handling**:

```python
if args.force:
    # Audit the force send
    audit_entry = audit_force_send(task_id, channel, message)
    
    # Warn user
    if not args.json:
        print(f"⚠️  FORCE SEND AUDITED")
        print(f"   Audit ID: {audit_entry['timestamp']}")
        print(f"   Channel: {channel}")
    
    # Proceed with send...
```

### Step 4.4: Create Audit Directory

```bash
#!/bin/bash
echo "=== STEP 4.4: CREATE AUDIT DIRECTORY ==="

mkdir -p ~/.openclaw/workspace/artifacts/audit
echo "Audit directory created"
```

### Step 4.5: Run Tests

```bash
#!/bin/bash
echo "=== STEP 4.5: RUN TESTS ==="

# Test --force creates audit
python3 ~/.openclaw/workspace/tools/safe-message --task-id test_force --channel telegram --message "test" --force --json

# Check audit log
cat ~/.openclaw/workspace/artifacts/audit/force_send_audit.jsonl | tail -1
```

### Step 4.6: Commit and Tag

```bash
#!/bin/bash
echo "=== STEP 4.6: COMMIT AND TAG ==="

git add -A
git commit -m "Day 4: P0-3 - Add audit trail for safe-message --force

Changes:
- Force sends are now logged to audit/force_send_audit.jsonl
- User sees warning when using --force
- Audit includes timestamp, task_id, channel, session"

git tag post-p0-3-$(date +%Y%m%d-%H%M)
echo "Tag created: post-p0-3-$(date +%Y%m%d-%H%M)"
```

### Step 4.7: Post-Patch Monitoring

```bash
#!/bin/bash
echo "=== STEP 4.7: POST-PATCH MONITORING ==="

echo "Checking audit log:"
cat ~/.openclaw/workspace/artifacts/audit/force_send_audit.jsonl 2>/dev/null || echo "No entries yet (expected)"

echo ""
echo "Day 4 complete. Proceed to Day 5 (P0-1) after 24 hours."
```

---

## Day 5-7: Continue with P0-1, P1-5, P1-4

**Follow similar pattern for remaining patches.**

Reference: `PATCH_QUEUE_P0.md` and `PATCH_QUEUE_P1.md`

---

## Rollback Quick Reference

```bash
# Rollback Day 1 (deletions)
git checkout pre-delete-* -- tools/

# Rollback Day 3 (P0-2)
git checkout pre-p0-2-* -- tools/finalize-response

# Rollback Day 4 (P0-3)
git checkout pre-p0-3-* -- tools/safe-message

# Full rollback
git checkout pre-consolidation-*
```

---

## Success Criteria

| Day | Success Criteria |
|-----|------------------|
| 1 | All 5 files deleted, tests pass |
| 2 | No issues detected |
| 3 | Receipt check enforced, tests pass |
| 4 | Audit working, tests pass |
| 5-7 | All patches applied, tests pass |

---

## Emergency Contacts

If critical issue detected:

1. Stop immediately
2. Rollback to previous tag
3. Document issue
4. Investigate before proceeding
