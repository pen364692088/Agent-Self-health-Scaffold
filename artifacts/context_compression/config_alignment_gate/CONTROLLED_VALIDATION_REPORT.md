# Controlled Validation Report

**Phase**: C
**Status**: ⏳ READY TO EXECUTE
**Created**: 2026-03-08T00:50:00-06:00

---

## Purpose

验证配置对齐后的压缩行为符合预期。

---

## Validation Scenarios

### Scenario 1: Threshold Enforcement

**Setup**:
- Create test session with context ratio ~0.85
- Verify compression triggers at 0.85, not 0.92

**Expected**:
```
ratio = 0.85 → pressure_level = standard → should_compress = true
```

**Result**: ⏳ PENDING

---

### Scenario 2: Pre-Assemble Execution

**Setup**:
- Trigger compression at ratio >= 0.85
- Verify prompt-assemble is called before LLM request

**Expected**:
- Compression happens BEFORE prompt is sent to LLM
- Context is reduced, not just observed

**Result**: ⏳ PENDING

---

### Scenario 3: Safety Counters

**Setup**:
- Run multiple compression cycles
- Verify all safety counters remain zero

**Expected**:
```
real_reply_corruption_count = 0
active_session_pollution_count = 0
rollback_event_count = 0
```

**Result**: ⏳ PENDING

---

### Scenario 4: Kill Switch

**Setup**:
- Set KILL_SWITCH_TRIGGERED: true
- Verify hook exits without processing

**Expected**:
- Hook detects kill switch
- No compression attempted
- Counters unchanged

**Result**: ⏳ PENDING

---

## Metrics to Collect

| Metric | Before | After | Target |
|--------|--------|-------|--------|
| enforced_trigger_count | 0 | ? | >= 1 |
| threshold_85_triggers | 0 | ? | >= 1 |
| threshold_92_triggers | 1 | ? | 0 (should not trigger first) |
| safety_counters | 0 | ? | 0 |

---

## Execution Commands

```bash
# Check current counters
cat ~/.openclaw/workspace/artifacts/context_compression/light_enforced/light_enforced_counters.json

# Run budget check manually
~/.openclaw/workspace/tools/context-budget-check --history <session_file> --max-tokens 200000

# Test prompt-assemble
~/.openclaw/workspace/tools/prompt-assemble --session-id test --state <state_file> --history <history_file> --dry-run
```

---

## Pass Conditions

- [ ] Compression triggers at 0.85, not only at 0.92
- [ ] prompt-assemble is called before LLM request
- [ ] All safety counters remain zero
- [ ] Kill switch works
- [ ] Rollback capability verified

---

## Validation Timeline

**Estimated Duration**: 2-4 hours of natural traffic

**Success Criteria**:
1. At least 1 natural trigger at 0.85
2. No safety violations
3. Evidence preserved

---

*Report created: 2026-03-08T00:50:00-06:00*
