# Repo Hygiene Report

**Generated**: 2026-03-14
**Purpose**: Summary of repository hygiene actions and current state

---

## Executive Summary

### Current State

| Aspect | Status |
|--------|--------|
| **Main Line** | Phase 2.9 Prompt Limited Pilot Ready |
| **Authority** | main_chain (all prompt/recovery decisions) |
| **Prompt** | DISABLED, ready for shadow mode with dual gate |
| **Recovery** | SHADOW ONLY (never live) |
| **Phase 3** | NOT STARTED |

### Key Finding

The repository had drifted from its "scaffold" narrative while the README remained outdated. Documentation was scattered across multiple phase files with no single source of truth.

---

## Actions Taken

### A. README Truth Sync ✅ COMPLETE

**Before**: "Scaffold / architecture phase"

**After**: Accurate reflection of Phase 2.9 with:
- Current status section
- Capability matrix
- Authority chain clarification
- Quick start commands
- Architecture diagram

### B. Single Source of Truth ✅ CREATED

**New File**: `CURRENT_STATUS.md`

Purpose: 1-minute readable current state with:
- Phase status
- Authority chain
- Prompt/recovery status
- Capability matrix
- Key file links
- Next decision point

### C. Document Drift Audit ✅ COMPLETE

**Audit Results**:
- 6 documents audited
- 1 critical fix applied (README)
- 1 minor update pending (RUNBOOK)
- 5 new documentation files created

### D. Config Truth Clarification ✅ COMPLETE

**Resolution**: 
- `metrics.effective_samples` is AUTHORITATIVE for gate decisions
- `effective_sample_count` (root) is DERIVED for display
- Comments added to config explaining relationships

### E. Directory Map ✅ CREATED

**New File**: `docs/TOP_LEVEL_DIRECTORY_MAP.md`

Classification:
- Main Kernel: 6 directories (15%)
- Documentation: 3 directories (7%)
- Runtime/Artifacts: 5 directories (12%)
- Experimental: 9 directories (22%)
- Supporting: 14 directories (34%)
- Infrastructure: 10 directories (24%)

---

## Files Modified

| File | Action | Reason |
|------|--------|--------|
| `README.md` | Updated | Sync with current state |
| `config/prompt_pilot.json` | Clarified | Fix field duplication |
| `CURRENT_STATUS.md` | Created | Single truth index |

## Files Created

| File | Purpose |
|------|---------|
| `CURRENT_STATUS.md` | Single source of truth |
| `docs/TOP_LEVEL_DIRECTORY_MAP.md` | Directory classification |
| `docs/PROMPT_PILOT_CONFIG_TRUTH.md` | Config relationships |
| `docs/DOC_SYNC_REPORT.md` | Document audit |
| `docs/REPO_HYGIENE_REPORT.md` | This report |

---

## Constraints Verified

| Constraint | Status |
|------------|--------|
| No new features added | ✅ |
| No recovery live enabled | ✅ |
| No Phase 3 started | ✅ |
| No main_chain changes | ✅ |
| No materialized_state authority | ✅ |
| No handoff/capsule input | ✅ |
| Only hygiene/docs changes | ✅ |

---

## Outstanding Items

### Priority 2 (Can do later)

1. Update `docs/PROMPT_PILOT_RUNBOOK.md` to emphasize dual gate
2. Consider creating `experiments/` directory for external projects
3. Add `.gitignore` entries for generated directories

### Not Recommended

1. ❌ Moving directories (requires import updates)
2. ❌ Deleting historical phase documents
3. ❌ Large-scale reorganization

---

## Final State

### Repository Truth Hierarchy

```
CURRENT_STATUS.md     ← Primary truth (1-min read)
├── README.md         ← Project overview
├── PHASE_2_9_DESIGN.md  ← Current phase design
├── config/prompt_pilot.json  ← Config (with truth comments)
└── docs/
    ├── PROMPT_PILOT_RUNBOOK.md  ← Operations
    ├── MATERIALIZED_STATE_V0_SCOPE.md  ← Frozen scope
    ├── TOP_LEVEL_DIRECTORY_MAP.md  ← Directory classification
    ├── PROMPT_PILOT_CONFIG_TRUTH.md  ← Config relationships
    ├── DOC_SYNC_REPORT.md  ← Document audit
    └── REPO_HYGIENE_REPORT.md  ← This report
```

### Verification Commands

```bash
# Check current status
cat CURRENT_STATUS.md

# Verify pilot config truth
jq '{effective_samples: .metrics.effective_samples, count: .effective_sample_count}' config/prompt_pilot.json

# Run validation tests
python3 tests/test_phase_2_9_validation.py
```

---

## Recommendations for Future

1. **Maintain CURRENT_STATUS.md** as primary truth index
2. **Update README.md** when phases complete
3. **Keep config comments** synchronized with behavior
4. **Create experiments/** for new external projects
5. **Run doc sync audit** monthly

---

## File: docs/REPO_HYGIENE_REPORT.md
