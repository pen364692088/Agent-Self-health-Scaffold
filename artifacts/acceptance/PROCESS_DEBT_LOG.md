# Process Debt Log

Track process deviations that don't block acceptance but should be avoided in future work.

---

## PD-2026-03-15-001: Mixed Commit (M0-M2 + v3-D/E)

### Date
2026-03-15

### Commit
e48fdf9b4b75101cc463f287575b67ec3fd6f2aa

### Description
Single commit combined two independent feature sets:
- Memory Kernel M0-M2 (8 files)
- v3-D/E Autonomous Runner (9 files)

### Impact
- **Low**: No functional impact
- **Audit**: Harder to isolate changes for review
- **Rollback**: Cannot rollback M0-M2 without losing v3-D/E

### Root Cause
Rapid iteration during development; commit discipline not enforced.

### Mitigation
- Both feature sets verified independently
- Separate test suites (19 tests for M0-M2, 74 tests for v3-D/E)
- Acceptance documented separately

### Resolution
- **Immediate**: Document as process debt, accept current state
- **Future**: Enforce independent commits from M3 onward

### Enforcement Rules (from M3)
1. **Independent branch**: Each feature on its own branch
2. **Independent commit**: One feature = one commit series
3. **Independent test**: Feature must have its own test file
4. **Independent acceptance**: Separate acceptance document

---

## Process Debt Metrics

| Metric | Value |
|--------|-------|
| Total Debts | 1 |
| Open | 1 |
| Resolved | 0 |
| Severity | Low |

---

## Review Schedule
- Weekly review during observation window
- Close debt when resolution verified
