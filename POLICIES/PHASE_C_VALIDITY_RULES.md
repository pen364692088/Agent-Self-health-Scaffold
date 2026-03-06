# Phase C Data Validity Rules v1.0

**Purpose**: Define minimum requirements for Phase C decision data.
**Effective Date**: 2026-03-06
**Priority**: CRITICAL - Must be enforced before any Phase C decision.

---

## Core Rule

> **Coverage 未达到阈值时，样本数即使 ≥200，也不能作为 READY_FOR_PHASE_C 的依据。**

---

## Phase C Validity Gates

| Gate | Requirement | Current | Status |
|------|-------------|---------|--------|
| Sample Count | ≥200 | 0 | ⏳ |
| Coverage Rate | ≥75% | 25% | ⏳ |
| Numeric Leak Rate | 0% | N/A | ⏳ |
| Category C Paths | 0 | 0 | ✅ |

**All gates must pass for Phase C data to be valid.**

---

## Data Validity Decision Matrix

| Sample Count | Coverage Rate | Validity | Action |
|--------------|---------------|----------|--------|
| <200 | <75% | INVALID | Continue collection |
| <200 | ≥75% | INVALID | Need more samples |
| ≥200 | <75% | **INVALID** | Fix coverage first |
| ≥200 | ≥75% | **VALID** | Proceed to Phase C analysis |

---

## Why Coverage Matters

### Problem: Local Correctness Illusion

If coverage is low:
- You see covered paths are clean
- Uncovered paths are not in statistics
- You conclude "system is stable" incorrectly

### Example

| Path | Coverage | Samples | Violations |
|------|----------|---------|------------|
| main_chat_response | 100% | 150 | 0 |
| subagent_response | 0% | 0 | ??? |
| error_response | 0% | 0 | ??? |

Total samples: 150/200 (almost ready)
Reality: Only 1/4 paths covered → data NOT representative

---

## Coverage Requirements

### Minimum Coverage: 75%

- At least 75% of paths must be Category A or B
- All Category C paths must be migrated or documented
- Each covered path must have interpreter/contract/checker/shadow_log

### Path Categories

| Category | Definition | Phase C Eligible |
|----------|------------|------------------|
| A | Full coverage (all 4 components) | ✅ Yes |
| B | Partial coverage (1-3 components) | ✅ Yes |
| C | No coverage | ❌ No - must migrate |

---

## Enforcement

### Daily Check Integration

```bash
~/.openclaw/workspace/tools/mvp11-6-daily-check
```

Output includes:
- Sample count vs target
- Coverage rate vs threshold
- Phase C validity: VALID/INVALID
- Blocking issues

### Gate File

`artifacts/self_report/phase_c_gate.json`:
```json
{
  "valid": false,
  "issues": ["Sample count 0 < 200", "Coverage rate 25.0% < 75%"]
}
```

### Decision Time

Before making Phase C decision:
1. Check `phase_c_gate.json`
2. If `valid: false` → DO NOT proceed
3. Fix issues, wait for more data
4. Re-check

---

## Exceptions

### GATES_DISABLE

Only allowed with explicit justification:
- Emergency hotfix
- Critical security issue
- Documented reason in `GATES_DISABLE_REASON`

### Override

Only operator can override with manual review:
1. Document why coverage is insufficient but data is still valid
2. Risk assessment for uncovered paths
3. Sign-off required

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| v1.0 | 2026-03-06 | Created from MVP11.6 Task 1.5C |

