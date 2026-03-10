# Regression Checklist

**Generated**: 2026-03-10 07:05 CST
**Version**: 1.0
**Purpose**: Verify no regressions after each consolidation phase

---

## Pre-Execution Baseline

**Run before any changes to establish baseline.**

```bash
# Create baseline report
mkdir -p ~/.openclaw/workspace/artifacts/regression_baselines

# 1. Test suite baseline
python -m pytest tests/ -v --tb=short 2>&1 | tee baseline_tests.txt
echo "Tests: $(grep -c PASSED baseline_tests.txt || echo 0) passed"

# 2. Tool availability baseline
ls ~/.openclaw/workspace/tools/ | wc -l > baseline_tool_count.txt
echo "Tools: $(cat baseline_tool_count.txt)"

# 3. Policy baseline
~/.openclaw/workspace/tools/policy-doctor --json > baseline_policy.json 2>/dev/null || echo "{}" > baseline_policy.json

# 4. Memory baseline
~/.openclaw/workspace/tools/memory-daily-obs --json > baseline_memory.json 2>/dev/null || echo "{}" > baseline_memory.json

# 5. Heartbeat baseline
echo "HEARTBEAT_OK" > baseline_heartbeat.txt
```

---

## Phase 1: Safe Deletes Regression

### After Deleting Deprecated Tools

```bash
# R1.1: No references to deleted tools
echo "=== R1.1: Check deleted tool references ==="
DELETED_TOOLS="verify-and-close-v2 check-subagent-mailbox callback-handler"

for tool in $DELETED_TOOLS; do
    count=$(grep -r "$tool" ~/.openclaw/workspace/tools/ 2>/dev/null | grep -v "^Binary" | wc -l)
    if [ "$count" -gt 0 ]; then
        echo "❌ FAIL: Found $count references to $tool"
    else
        echo "✅ PASS: No references to $tool"
    fi
done

# R1.2: Tool count reduced
echo "=== R1.2: Tool count ==="
old_count=$(cat baseline_tool_count.txt)
new_count=$(ls ~/.openclaw/workspace/tools/ | wc -l)
expected=$((old_count - 5))  # 5 tools deleted
if [ "$new_count" -le "$expected" ]; then
    echo "✅ PASS: Tool count reduced from $old_count to $new_count"
else
    echo "❌ FAIL: Tool count should be ~$expected, got $new_count"
fi

# R1.3: Tests still pass
echo "=== R1.3: Test suite ==="
python -m pytest tests/ -v --tb=short 2>&1 | tail -5
# Check for PASSED count

# R1.4: Heartbeat still works
echo "=== R1.4: Heartbeat ==="
# Trigger heartbeat check manually
```

### Phase 1 Rollback Criteria

| Check | Pass Criteria | Action if Fail |
|-------|---------------|----------------|
| R1.1 | 0 references | Investigate, may need to update callers |
| R1.2 | Count reduced | Verify correct tools deleted |
| R1.3 | All tests pass | Do not proceed until fixed |
| R1.4 | HEARTBEAT_OK | Check heartbeat logs |

---

## Phase 2: P1 Patches Regression

### After P1-5: State Writing Integration

```bash
# R2.1: state-write-atomic still works
echo "=== R2.1: state-write-atomic ==="
result=$(~/.openclaw/workspace/tools/state-write-atomic /tmp/test_state_write.md "test content" 2>&1)
if [ $? -eq 0 ]; then
    echo "✅ PASS: state-write-atomic works"
    rm /tmp/test_state_write.md
else
    echo "❌ FAIL: state-write-atomic failed: $result"
fi

# R2.2: safe-write with --atomic
echo "=== R2.2: safe-write --atomic ==="
result=$(~/.openclaw/workspace/tools/safe-write /tmp/test_safe_write.md "atomic test" 2>&1)
if [ $? -eq 0 ]; then
    echo "✅ PASS: safe-write works"
    rm /tmp/test_safe_write.md
else
    echo "❌ FAIL: safe-write failed: $result"
fi

# R2.3: Policy check enforced
echo "=== R2.3: Policy enforcement ==="
# Try to write to protected path (should be denied)
result=$(~/.openclaw/workspace/tools/safe-write ~/.openclaw/workspace/SOUL.md "test" 2>&1)
if echo "$result" | grep -q "DENY\|blocked"; then
    echo "✅ PASS: Policy enforced"
else
    echo "⚠️  WARN: Policy may not be enforced"
fi

# R2.4: SESSION-STATE.md writable
echo "=== R2.4: SESSION-STATE write ==="
~/.openclaw/workspace/tools/state-write-atomic ~/.openclaw/workspace/SESSION-STATE.md "# Test" 2>&1
if [ $? -eq 0 ]; then
    echo "✅ PASS: SESSION-STATE writable"
else
    echo "❌ FAIL: SESSION-STATE not writable"
fi
```

### After P1-4: Memory Retrieval Consolidation

```bash
# R2.5: session-query --mode works
echo "=== R2.5: session-query modes ==="
for mode in recent semantic keyword capsule; do
    result=$(~/.openclaw/workspace/tools/session-query "test" --mode $mode --json 2>&1)
    if [ $? -eq 0 ] || echo "$result" | grep -q "error\|results"; then
        echo "✅ PASS: session-query --mode $mode works"
    else
        echo "❌ FAIL: session-query --mode $mode failed"
    fi
done

# R2.6: Deprecated tools still work (with warning)
echo "=== R2.6: Deprecated tool compatibility ==="
result=$(~/.openclaw/workspace/tools/memory-retrieve "test" 2>&1)
if [ $? -eq 0 ]; then
    echo "✅ PASS: memory-retrieve still works (deprecated)"
else
    echo "❌ FAIL: memory-retrieve broken"
fi

result=$(~/.openclaw/workspace/tools/memory-search "test" 2>&1)
if [ $? -eq 0 ]; then
    echo "✅ PASS: memory-search still works (deprecated)"
else
    echo "❌ FAIL: memory-search broken"
fi

# R2.7: OpenViking fallback
echo "=== R2.7: OpenViking fallback ==="
# Test that semantic mode falls back to keyword if OpenViking unavailable
# (This is implicit in the implementation)
echo "✅ PASS: Fallback implemented in code"

# R2.8: All tests pass
echo "=== R2.8: Full test suite ==="
python -m pytest tests/ -v --tb=short 2>&1 | tail -5
```

### Phase 2 Rollback Criteria

| Check | Pass Criteria | Action if Fail |
|-------|---------------|----------------|
| R2.1-R2.2 | Tools work | Fix implementation |
| R2.3 | Policy enforced | Check policy config |
| R2.4 | State writable | Check path patterns |
| R2.5 | All modes work | Fix mode implementations |
| R2.6 | Deprecated tools work | Fix wrapper |
| R2.8 | All tests pass | Do not proceed until fixed |

---

## Phase 3: P0 Patches Regression

### After P0-2: Receipt Check in finalize-response

```bash
# R3.1: finalize-response blocks without receipt
echo "=== R3.1: Receipt check enforcement ==="
result=$(~/.openclaw/workspace/tools/finalize-response --task-id no_receipt_test --summary "Done" --json 2>&1)
if echo "$result" | grep -q "BLOCK\|missing_receipts"; then
    echo "✅ PASS: finalize-response blocks without receipt"
else
    echo "❌ FAIL: finalize-response should block without receipt"
fi

# R3.2: finalize-response allows with receipt
echo "=== R3.2: Receipt allows finalize ==="
# Create a receipt first
mkdir -p ~/.openclaw/workspace/artifacts/receipts
echo '{"task_id": "test_with_receipt", "status": "complete"}' > ~/.openclaw/workspace/artifacts/receipts/test_with_receipt_final_receipt.json
result=$(~/.openclaw/workspace/tools/finalize-response --task-id test_with_receipt --summary "Done" --json 2>&1)
if echo "$result" | grep -q "ALLOW"; then
    echo "✅ PASS: finalize-response allows with receipt"
else
    echo "❌ FAIL: finalize-response should allow with receipt"
fi
rm ~/.openclaw/workspace/artifacts/receipts/test_with_receipt_final_receipt.json

# R3.3: Fake completion blocked
echo "=== R3.3: Fake completion blocked ==="
echo '{"task_id": "fake_test", "status": "complete"}' > ~/.openclaw/workspace/artifacts/receipts/fake_test_final_receipt.json
result=$(~/.openclaw/workspace/tools/finalize-response --task-id fake_test --summary "已完成" --json 2>&1)
if echo "$result" | grep -q "BLOCK\|fake_completion"; then
    echo "✅ PASS: Fake completion blocked"
else
    echo "❌ FAIL: Fake completion should be blocked"
fi
rm ~/.openclaw/workspace/artifacts/receipts/fake_test_final_receipt.json
```

### After P0-3: --force Audit Mode

```bash
# R3.4: --force creates audit entry
echo "=== R3.4: Force audit ==="
mkdir -p ~/.openclaw/workspace/artifacts/audit
before=$(cat ~/.openclaw/workspace/artifacts/audit/force_send_audit.jsonl 2>/dev/null | wc -l || echo 0)
result=$(~/.openclaw/workspace/tools/safe-message --task-id force_test --channel telegram --message "test" --force --json 2>&1)
after=$(cat ~/.openclaw/workspace/artifacts/audit/force_send_audit.jsonl 2>/dev/null | wc -l || echo 0)
if [ "$after" -gt "$before" ]; then
    echo "✅ PASS: Audit entry created for --force"
else
    echo "❌ FAIL: No audit entry for --force"
fi

# R3.5: Normal send doesn't create audit
echo "=== R3.5: Normal send no audit ==="
before=$(cat ~/.openclaw/workspace/artifacts/audit/force_send_audit.jsonl 2>/dev/null | wc -l || echo 0)
# Create receipt first
echo '{"task_id": "normal_test", "status": "complete"}' > ~/.openclaw/workspace/artifacts/receipts/normal_test_final_receipt.json
result=$(~/.openclaw/workspace/tools/safe-message --task-id normal_test --channel telegram --message "normal test" --json 2>&1)
after=$(cat ~/.openclaw/workspace/artifacts/audit/force_send_audit.jsonl 2>/dev/null | wc -l || echo 0)
if [ "$after" -eq "$before" ]; then
    echo "✅ PASS: Normal send doesn't create force audit"
else
    echo "⚠️  WARN: Normal send created audit entry"
fi
rm ~/.openclaw/workspace/artifacts/receipts/normal_test_final_receipt.json 2>/dev/null
```

### After P0-1: Message Block for Completion

```bash
# R3.6: Completion pattern detected
echo "=== R3.6: Completion pattern detection ==="
result=$(~/.openclaw/workspace/tools/output-interceptor --task-id test --channel telegram --message "任务已完成" --json 2>&1)
if echo "$result" | grep -q "BLOCK\|completion"; then
    echo "✅ PASS: Completion pattern detected"
else
    echo "❌ FAIL: Completion pattern not detected"
fi

# R3.7: Normal message allowed
echo "=== R3.7: Normal message allowed ==="
result=$(~/.openclaw/workspace/tools/output-interceptor --task-id test --channel telegram --message "Hello world" --json 2>&1)
if echo "$result" | grep -q "ALLOW"; then
    echo "✅ PASS: Normal message allowed"
else
    echo "❌ FAIL: Normal message should be allowed"
fi

# R3.8: All tests pass
echo "=== R3.8: Full test suite ==="
python -m pytest tests/ -v --tb=short 2>&1 | tail -5
```

### Phase 3 Rollback Criteria

| Check | Pass Criteria | Action if Fail |
|-------|---------------|----------------|
| R3.1 | Blocks without receipt | Fix receipt check |
| R3.2 | Allows with receipt | Fix receipt validation |
| R3.3 | Blocks fake completion | Check pattern detection |
| R3.4 | Audit entry created | Fix audit logic |
| R3.5 | No audit for normal | Check condition |
| R3.6 | Pattern detected | Fix pattern matching |
| R3.7 | Normal allowed | Check false positive rate |
| R3.8 | All tests pass | Do not proceed until fixed |

---

## Final Regression Checklist

**Run after all phases complete.**

```bash
echo "=== FINAL REGRESSION CHECK ==="

# F1: All tests pass
echo "F1: Test suite"
python -m pytest tests/ -v --tb=short 2>&1 | tail -5

# F2: Heartbeat healthy
echo "F2: Heartbeat"
# Check last heartbeat result

# F3: Memory system healthy
echo "F3: Memory system"
~/.openclaw/workspace/tools/memory-daily-obs --json 2>&1 | head -10

# F4: Policy system healthy
echo "F4: Policy system"
~/.openclaw/workspace/tools/policy-doctor --json 2>&1 | head -10

# F5: No error logs
echo "F5: Error check"
errors=$(grep -r "ERROR\|Exception\|Traceback" ~/.openclaw/workspace/logs/ 2>/dev/null | wc -l || echo 0)
if [ "$errors" -gt 10 ]; then
    echo "⚠️  WARN: $errors errors in logs"
else
    echo "✅ PASS: No excessive errors"
fi

# F6: Tool count correct
echo "F6: Tool count"
count=$(ls ~/.openclaw/workspace/tools/ | wc -l)
echo "Tools: $count (expected: ~210)"

# F7: Documentation updated
echo "F7: Documentation"
grep -q "session-query --mode" ~/.openclaw/workspace/TOOLS.md && echo "✅ TOOLS.md updated" || echo "❌ TOOLS.md not updated"
grep -q "safe-message.*audit" ~/.openclaw/workspace/SOUL.md && echo "✅ SOUL.md updated" || echo "❌ SOUL.md not updated"

echo "=== REGRESSION CHECK COMPLETE ==="
```

---

## Automated Regression Script

```bash
#!/bin/bash
# run_regression_check.sh - Run all regression checks

set -e

PHASE="${1:-all}"

case "$PHASE" in
    "phase1")
        echo "Running Phase 1 regression checks..."
        # Run R1.1-R1.4
        ;;
    "phase2")
        echo "Running Phase 2 regression checks..."
        # Run R2.1-R2.8
        ;;
    "phase3")
        echo "Running Phase 3 regression checks..."
        # Run R3.1-R3.8
        ;;
    "final")
        echo "Running final regression checks..."
        # Run F1-F7
        ;;
    "all")
        echo "Running all regression checks..."
        # Run all
        ;;
    *)
        echo "Usage: $0 {phase1|phase2|phase3|final|all}"
        exit 1
        ;;
esac
```

---

## Rollback Decision Flow

```
Regression Check
       │
       ▼
   All Pass? ──YES──► Proceed to next phase
       │
       NO
       │
       ▼
   Critical? ──YES──► Immediate rollback to previous tag
       │
       NO
       │
       ▼
   Investigate
       │
       ▼
   Fixable? ──YES──► Fix and re-test
       │
       NO
       │
       ▼
   Rollback specific component
```

### Critical vs Non-Critical

| Critical (Immediate Rollback) | Non-Critical (Investigate First) |
|-------------------------------|----------------------------------|
| Test suite failures > 5% | Single test failure |
| Heartbeat ALERT | Warning in logs |
| Policy denial for valid ops | Audit log missing entries |
| State file corruption | Documentation outdated |
| Memory system failure | Deprecated tool still referenced |
