# Freeze-End Execution Order

**Generated**: 2026-03-10 07:00 CST
**Version**: 1.0
**Observation Window End**: ~2026-03-13 to 2026-03-17

---

## Execution Timeline Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    POST-FREEZE EXECUTION                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Day 0   │ Observation window ends, freeze lifted              │
│  Day 1-2 │ Phase 1: Safe Deletes (no behavior change)          │
│  Day 3-4 │ Phase 2: P1 Patches (consolidation)                 │
│  Day 5-7 │ Phase 3: P0 Patches (security)                      │
│  Day 8+  │ Phase 4: Monitoring & cleanup                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 0: Pre-Execution Checklist

**Execute immediately when observation window ends.**

### Step 0.1: Verify Observation Metrics

```bash
# Check all exit criteria met
~/.openclaw/workspace/tools/memory-daily-obs --json

# Verify:
# - false_captures = 0
# - duplicate_captures = 0
# - embedding_errors = 0
```

### Step 0.2: Create Git Tags

```bash
git tag pre-consolidation-$(date +%Y%m%d)
git add -A
git commit -m "Pre-consolidation baseline: observation window complete"
git tag post-observation-$(date +%Y%m%d)
```

### Step 0.3: Backup Critical Files

```bash
# Backup current state
tar -czf ~/.openclaw/backups/pre-consolidation-$(date +%Y%m%d).tar.gz \
    ~/.openclaw/workspace/tools/ \
    ~/.openclaw/workspace/POLICIES/ \
    ~/.openclaw/workspace/SOUL.md \
    ~/.openclaw/workspace/TOOLS.md
```

### Step 0.4: Verify Tests Pass

```bash
# Run full test suite
cd ~/.openclaw/workspace
python -m pytest tests/ -v

# All tests must pass before proceeding
```

---

## Phase 1: Safe Deletes (Day 1-2)

**Risk Level: MINIMAL - Removing unused code**

### Step 1.1: Delete Deprecated Tools

```bash
# Create tag before deletion
git tag pre-delete-$(date +%Y%m%d)

# Delete deprecated tools
rm -v ~/.openclaw/workspace/tools/verify-and-close-v2
rm -v ~/.openclaw/workspace/tools/legacy/check-subagent-mailbox
rm -v ~/.openclaw/workspace/tools/callback-handler
rm -v ~/.openclaw/workspace/tools/session-archive.original
rm -v ~/.openclaw/workspace/tools/session-start-recovery.bak

# Verify no references
grep -r "verify-and-close-v2" ~/.openclaw/workspace/ 2>/dev/null || echo "No references"
grep -r "check-subagent-mailbox" ~/.openclaw/workspace/ --exclude-dir=legacy 2>/dev/null || echo "No references"
grep -r "callback-handler[^-]" ~/.openclaw/workspace/ 2>/dev/null || echo "No references"

# Commit
git add -A
git commit -m "Phase 1: Delete deprecated tools"
git tag post-delete-$(date +%Y%m%d)
```

### Step 1.2: Update Documentation

```bash
# Update TOOL_LAYER_MAP.md to remove deleted entries
# Update SOUL.md to remove references

git add -A
git commit -m "Phase 1: Update documentation after deletions"
```

### Step 1.3: Verify

```bash
# Run tests again
python -m pytest tests/ -v

# If any test fails, rollback
# git checkout post-observation-$(date +%Y%m%d)
```

---

## Phase 2: P1 Patches (Day 3-4)

**Risk Level: LOW - Consolidation, not security**

### Step 2.1: Integrate State Writing (P1-5)

```bash
# Create tag
git tag pre-p1-5-$(date +%Y%m%d)

# Update safe-write with --atomic option
# (Edit tools/safe-write)

# Update state-write-atomic
# (Edit tools/state-write-atomic)

# Run tests
python -m pytest tests/test_state_write_integration.py -v

# Commit
git add -A
git commit -m "Phase 2.1: P1-5 - Integrate state writing through safe-write"
git tag post-p1-5-$(date +%Y%m%d)
```

### Step 2.2: Merge Memory Retrieval (P1-4)

```bash
# Create tag
git tag pre-p1-4-$(date +%Y%m%d)

# Update session-query with --mode
# (Edit tools/session-query)

# Create deprecation wrappers
# (Edit tools/memory-retrieve)
# (Edit tools/memory-search)

# Run tests
python -m pytest tests/test_session_query_modes.py -v

# Commit
git add -A
git commit -m "Phase 2.2: P1-4 - Merge memory retrieval to session-query --mode"
git tag post-p1-4-$(date +%Y%m%d)
```

### Step 2.3: Update Documentation

```bash
# Update TOOLS.md
# Update memory.md
# Update TOOL_LAYER_MAP.md

git add -A
git commit -m "Phase 2.3: Update documentation for P1 patches"
```

### Step 2.4: Full Test Suite

```bash
# Run all tests
python -m pytest tests/ -v

# If failures, investigate and fix or rollback
```

---

## Phase 3: P0 Patches (Day 5-7)

**Risk Level: MEDIUM - Security changes, behavior modification**

### Step 3.1: Add Receipt Check (P0-2)

```bash
# Create tag
git tag pre-p0-2-$(date +%Y%m%d)

# Update finalize-response
# (Edit tools/finalize-response)

# Run tests
python -m pytest tests/test_finalize_response_receipt.py -v

# Commit
git add -A
git commit -m "Phase 3.1: P0-2 - Add receipt check to finalize-response"
git tag post-p0-2-$(date +%Y%m%d)
```

### Step 3.2: Neutralize --force (P0-3)

```bash
# Create tag
git tag pre-p0-3-$(date +%Y%m%d)

# Update safe-message with audit mode
# (Edit tools/safe-message)

# Create audit directory
mkdir -p ~/.openclaw/workspace/artifacts/audit

# Run tests
python -m pytest tests/test_safe_message_force.py -v

# Commit
git add -A
git commit -m "Phase 3.2: P0-3 - Add audit mode to safe-message --force"
git tag post-p0-3-$(date +%Y%m%d)
```

### Step 3.3: Block Direct Message (P0-1)

```bash
# Create tag
git tag pre-p0-1-$(date +%Y%m%d)

# Update output-interceptor
# (Edit tools/output-interceptor)

# Add policy rule
# (Edit POLICIES/EXECUTION_POLICY_RULES.yaml)

# Run tests
python -m pytest tests/test_completion_message_block.py -v

# Commit
git add -A
git commit -m "Phase 3.3: P0-1 - Block direct message tool for completion"
git tag post-p0-1-$(date +%Y%m%d)
```

### Step 3.4: Update Documentation

```bash
# Update SOUL.md with new rules
# Update TOOLS.md

git add -A
git commit -m "Phase 3.4: Update documentation for P0 patches"
```

### Step 3.5: Full Test Suite

```bash
# Run all tests
python -m pytest tests/ -v

# Must pass before proceeding
```

---

## Phase 4: Monitoring & Cleanup (Day 8+)

### Step 4.1: Monitor Metrics

```bash
# Check for policy violations
~/.openclaw/workspace/tools/policy-violations-report --today --summary

# Check audit log for force sends
cat ~/.openclaw/workspace/artifacts/audit/force_send_audit.jsonl 2>/dev/null | tail -20

# Check finalize log
cat ~/.openclaw/workspace/reports/finalize_log.jsonl 2>/dev/null | tail -20
```

### Step 4.2: Monitor for Issues

```bash
# Check heartbeat alerts
journalctl --user -u openclaw-heartbeat --since "1 day ago" | grep ALERT

# Check for errors
grep -r "ERROR\|Exception" ~/.openclaw/workspace/logs/ 2>/dev/null | tail -20
```

### Step 4.3: Cleanup

```bash
# Remove backup files older than 7 days
find ~/.openclaw/backups/ -name "*.tar.gz" -mtime +7 -delete

# Rotate audit logs
# (Implement log rotation)
```

---

## Execution Summary Table

| Phase | Day | Actions | Risk | Rollback Tag |
|-------|-----|---------|------|--------------|
| 0 | 0 | Pre-flight checks | NONE | N/A |
| 1 | 1-2 | Delete deprecated | MINIMAL | post-observation-* |
| 2.1 | 3 | P1-5: State writing | LOW | pre-p1-5-* |
| 2.2 | 4 | P1-4: Memory retrieval | LOW | pre-p1-4-* |
| 3.1 | 5 | P0-2: Receipt check | MEDIUM | pre-p0-2-* |
| 3.2 | 6 | P0-3: --force audit | MEDIUM | pre-p0-3-* |
| 3.3 | 7 | P0-1: Message block | MEDIUM | pre-p0-1-* |
| 4 | 8+ | Monitoring | NONE | N/A |

---

## Rollback Decision Matrix

| Issue Type | Severity | Action |
|------------|----------|--------|
| Test failure | ANY | Stop, fix, or rollback to previous tag |
| Policy denial for valid op | HIGH | Rollback to pre-p0-* tag |
| User complaint | MEDIUM | Investigate, may rollback specific patch |
| Performance degradation | MEDIUM | Investigate, may rollback |
| Audit log errors | LOW | Fix in place, no rollback needed |

---

## Post-Execution Verification

### Final Checklist

```bash
# 1. All tests pass
python -m pytest tests/ -v

# 2. Deprecated tools removed
ls ~/.openclaw/workspace/tools/verify-and-close-v2 2>/dev/null && echo "FAIL" || echo "PASS"

# 3. P1 patches working
session-query "test" --mode semantic --json

# 4. P0 patches working
# (Verify completion messages blocked without receipt)

# 5. Documentation updated
grep -q "session-query --mode" ~/.openclaw/workspace/TOOLS.md && echo "PASS" || echo "FAIL"

# 6. No heartbeat alerts
journalctl --user -u openclaw-heartbeat --since "1 hour ago" | grep -c ALERT || echo "0 alerts"
```

---

## Contingency Plan

### If Phase 2 Issues

```bash
# Rollback to post-delete
git checkout post-delete-$(date +%Y%m%d)

# Skip P1, proceed to P0 after investigation
```

### If Phase 3 Issues

```bash
# Rollback specific patch
git checkout pre-p0-2-$(date +%Y%m%d) -- tools/finalize-response
# Or rollback entire phase
git checkout post-p1-4-$(date +%Y%m%d)
```

### If Major Issues

```bash
# Full rollback to pre-consolidation
git checkout pre-consolidation-$(date +%Y%m%d)

# Restore backup
tar -xzf ~/.openclaw/backups/pre-consolidation-*.tar.gz -C /
```
