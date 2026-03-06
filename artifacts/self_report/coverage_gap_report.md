# Coverage Gap Report

**Generated**: 2026-03-06T08:45:00CST
**Coverage Rate**: 25% (1/4 Category A)

---

## Summary

| Metric | Current | Target | Gap |
|--------|---------|--------|-----|
| Category A | 1 | 3 | 2 paths |
| Category B | 3 | 1 | - |
| Category C | 0 | 0 | ✅ |
| Coverage Rate | 25% | 75% | 50% |

---

## Path Analysis

### ✅ main_chat_response (Category A)
- Components: interpreter, contract, checker, shadow_log
- Status: Fully covered
- Action: None

### ⚠️ subagent_response (Category B → migrating)
- Components: checker, shadow_log (50%)
- Missing: interpreter, contract
- Action: Task 1.5A in progress
- Tool: `tools/subagent-srap-check`

### ⚠️ heartbeat_response (Category B)
- Components: None
- Justification: Fixed format, internal use
- Risk: Low
- Action: Consider adding shadow_log

### ⚠️ error_response (Category B)
- Components: None
- Justification: Should add shadow_log
- Risk: Medium
- Action: Planned

---

## Coverage Improvement Plan

### Phase 1: subagent_response Migration
- [x] Create subagent-srap-check tool
- [x] Add checker component
- [x] Add shadow_log component
- [ ] Add interpreter component
- [ ] Add contract component
- **Expected Coverage**: 75%

### Phase 2: error_response Migration
- [ ] Add shadow_log for error context
- [ ] Consider checker for sensitive errors
- **Expected Coverage**: 87.5%

---

## Phase C Readiness

| Requirement | Status |
|-------------|--------|
| Sample count ≥200 | ⏳ |
| Coverage rate ≥75% | ⏳ |
| Category C paths = 0 | ✅ |
| Numeric leak rate = 0% | ⏳ |

**Verdict**: NOT READY - awaiting samples and coverage completion

---

## Next Steps

1. Continue shadow data collection
2. Complete subagent_response migration
3. Re-run daily check
4. When coverage ≥75% and samples ≥200, proceed to Phase C

