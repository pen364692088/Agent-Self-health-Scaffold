# Execution Constraints

**Generated**: 2026-03-10 06:40 CST
**Status**: Active during consolidation period

---

## Constraint Overview

These constraints MUST be respected during post-freeze execution.

```
╔═══════════════════════════════════════════════════════════════╗
║                    EXECUTION CONSTRAINTS                        ║
╠═══════════════════════════════════════════════════════════════╣
║                                                                 ║
║  C1: Observation window must complete (minimum 3 days)          ║
║  C2: All exit criteria must be green                            ║
║  C3: Test suite must pass before each phase                     ║
║  C4: One patch per day maximum                                   ║
║  C5: Rollback tag required before each patch                    ║
║  C6: Monitoring required after each patch                       ║
║  C7: No patch on weekends (unless emergency)                    ║
║                                                                 ║
╚═══════════════════════════════════════════════════════════════╝
```

---

## Constraint C1: Observation Window

**Requirement**: Observation window must complete before execution.

### Minimum Duration
- **Minimum**: 3 days
- **Target**: 5-7 days
- **Maximum**: 7 days (extend if issues)

### Exit Criteria

| Criteria | Target | Current |
|----------|--------|---------|
| False captures | 0 | 0 ✅ |
| Duplicate captures | 0 | 0 ✅ |
| Embedding errors | 0 | 0 ✅ |
| Observation days | ≥ 3 | 1 ⏳ |

### Blocking Condition
- Observation window incomplete → NO EXECUTION

### Verification
```bash
# Check observation status
cat ~/.openclaw/workspace/artifacts/memory_freeze/OBSERVATION_METRICS.md

# Verify all exit criteria
~/.openclaw/workspace/tools/memory-daily-obs --json
```

---

## Constraint C2: Exit Criteria

**Requirement**: All exit criteria must be green.

### Criteria Checklist

| Criteria | Must Be | Check Command |
|----------|---------|---------------|
| False captures | 0 | `memory-daily-obs --json` |
| Duplicate captures | 0 | `memory-daily-obs --json` |
| Embedding errors | 0 | `memory-daily-obs --json` |
| Policy health | Healthy | `policy-doctor --json` |
| Heartbeat | HEARTBEAT_OK | Check logs |
| Test failures | 0 | `pytest tests/` |

### Blocking Condition
- Any criteria red → NO EXECUTION

### Verification
```bash
# Run all checks
~/.openclaw/workspace/tools/memory-daily-obs --json
~/.openclaw/workspace/tools/policy-doctor --json
python -m pytest tests/ -v
```

---

## Constraint C3: Test Suite

**Requirement**: All tests must pass before each phase.

### Pre-Phase Testing

```bash
# Before Phase 1
python -m pytest tests/ -v

# Before Phase 2 (each patch)
python -m pytest tests/ -v
python -m pytest tests/test_<patch>.py -v

# Before Phase 3 (each patch)
python -m pytest tests/ -v
python -m pytest tests/test_<patch>.py -v
```

### Blocking Condition
- Any test failure → NO EXECUTION until fixed

### Test Requirements Per Patch

| Patch | New Tests Required |
|-------|-------------------|
| P0-2 | 3 tests |
| P0-3 | 2 tests |
| P0-1 | 3 tests |
| P1-5 | 4 tests |
| P1-4 | 6 tests |

---

## Constraint C4: One Patch Per Day

**Requirement**: Maximum one patch per day.

### Rationale
- Allow time for monitoring
- Detect issues before next patch
- Reduce risk of cascading failures

### Schedule

| Day | Patch | Notes |
|-----|-------|-------|
| Day 3 | P0-2 | Receipt check |
| Day 4 | P0-3 | --force audit |
| Day 5 | P0-1 | Message block |
| Day 6 | P1-5 | State writing |
| Day 7 | P1-4 | Memory retrieval |

### Blocking Condition
- Multiple patches in one day → NOT ALLOWED

---

## Constraint C5: Rollback Tags

**Requirement**: Rollback tag required before each patch.

### Tag Convention

```bash
# Before patch
git tag pre-<patch>-$(date +%Y%m%d)

# After patch
git tag post-<patch>-$(date +%Y%m%d)
```

### Required Tags

| Point | Tag |
|-------|-----|
| Before all | pre-consolidation-* |
| After delete | post-delete-* |
| Before P0-2 | pre-p0-2-* |
| After P0-2 | post-p0-2-* |
| Before P0-3 | pre-p0-3-* |
| After P0-3 | post-p0-3-* |
| Before P0-1 | pre-p0-1-* |
| After P0-1 | post-p0-1-* |
| Before P1-5 | pre-p1-5-* |
| After P1-5 | post-p1-5-* |
| Before P1-4 | pre-p1-4-* |
| After P1-4 | post-p1-4-* |
| After all | post-consolidation-* |

### Blocking Condition
- Missing rollback tag → NO EXECUTION

---

## Constraint C6: Post-Patch Monitoring

**Requirement**: Monitor for issues after each patch.

### Monitoring Period
- **Minimum**: 2 hours
- **Recommended**: 24 hours
- **Critical patches**: 48 hours

### Monitoring Checklist

```bash
# After each patch, check:
1. Test suite passes
2. Heartbeat healthy
3. No error logs
4. Policy working
5. Memory stable
```

### Monitoring Commands

```bash
# Quick health check
~/.openclaw/workspace/tools/policy-doctor --json
~/.openclaw/workspace/tools/memory-daily-obs --json

# Check logs
grep -r "ERROR\|Exception" ~/.openclaw/workspace/logs/ --since="1 hour ago"

# Check heartbeat
journalctl --user -u openclaw-heartbeat --since "1 hour ago" | grep ALERT
```

### Blocking Condition
- Anomaly detected → ROLLBACK, investigate

---

## Constraint C7: No Weekend Patches

**Requirement**: No patches on weekends unless emergency.

### Weekend Definition
- Saturday, Sunday

### Emergency Exception
- Critical security issue
- Must be documented
- Requires rollback tag before and after

### Blocking Condition
- Weekend + non-emergency → NO EXECUTION

---

## Constraint Enforcement Matrix

| Constraint | When | Enforcement |
|------------|------|-------------|
| C1: Observation | Pre-execution | Block if incomplete |
| C2: Exit criteria | Pre-execution | Block if red |
| C3: Test suite | Pre-patch | Block if fail |
| C4: One patch/day | Daily | Block if exceeded |
| C5: Rollback tags | Pre-patch | Block if missing |
| C6: Monitoring | Post-patch | Block if anomaly |
| C7: Weekend | Daily | Block if weekend |

---

## Constraint Violation Response

| Violation | Response |
|-----------|----------|
| C1, C2 | Block execution, wait until met |
| C3 | Fix tests or rollback |
| C4 | Defer to next day |
| C5 | Create tag, then proceed |
| C6 | Rollback, investigate |
| C7 | Wait for weekday |

---

## Pre-Execution Checklist

**Run before starting consolidation:**

```bash
# C1: Observation complete?
cat artifacts/memory_freeze/OBSERVATION_METRICS.md
# Check for 3+ days

# C2: Exit criteria green?
~/.openclaw/workspace/tools/memory-daily-obs --json
~/.openclaw/workspace/tools/policy-doctor --json
# All should be PASS

# C3: Tests pass?
python -m pytest tests/ -v
# All should PASS

# C5: Tags ready?
git tag pre-consolidation-$(date +%Y%m%d)

# C7: Not weekend?
date +%A
# Should be Mon-Fri
```

---

## Emergency Override

In case of critical need to bypass constraints:

### Override Procedure

1. Document reason
2. Get approval (if applicable)
3. Create override tag
4. Proceed with caution
5. Extra monitoring required

### Override Log

```json
{
  "timestamp": "ISO8601",
  "constraint": "C7",
  "reason": "Critical security fix",
  "approved_by": "...",
  "override_tag": "override-C7-YYYYMMDD"
}
```
