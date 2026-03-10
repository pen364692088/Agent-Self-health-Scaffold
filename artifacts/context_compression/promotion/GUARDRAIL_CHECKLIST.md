# Production Guardrail Checklist

**Date**: 2026-03-09T11:38:00-06:00
**Phase**: Post-Gate 1 · Production Guardrails

---

## Guardrail Implementation Status

### 1. Evaluator Version Logging ✅

- [x] `evaluator_version` field added to capsule output
- [x] Version string: "2.0-gate-based"
- [x] Included in `resume_readiness.version` field
- [x] Test verified version appears in output

**Evidence**: `capsule-builder-v2.py` line 20, lines 265-270

---

### 2. Readiness Score Distribution Logging ⏳

- [x] Scores logged in each capsule
- [ ] Distribution aggregation script (P2)
- [ ] Alert on distribution shift (P2)

**Current**: Scores captured, aggregation TBD

---

### 3. False Positive Spike Alert ⏳

- [x] Baseline established (7%)
- [ ] Automated alert (P2)
- [ ] Threshold configuration (P2)

**Current**: Manual monitoring via spot-check

---

### 4. Agreement Drift Watch ⏳

- [x] Baseline established (92%)
- [x] Shadow trace collection tool ready
- [ ] Automated drift detection (P2)

**Current**: Manual spot-check weekly

---

### 5. Shadow Trace Sampling ✅

- [x] `shadow_trace_collector.py` implemented
- [x] `shadow_spotcheck.py` implemented
- [x] SHADOW_TRACE.jsonl format defined
- [ ] Production automation (P2)

---

### 6. Rollback Switch ✅

- [x] Version tracking in place
- [x] V1 fallback path defined (not implemented)
- [ ] One-command rollback (P2)

**Current**: Can revert via code deployment

---

## Guardrails Summary

| Guardrail | Status | Automation |
|-----------|--------|------------|
| Version Logging | ✅ Complete | Automatic |
| Score Distribution | ⏳ Partial | Manual |
| FP Spike Alert | ⏳ Partial | Manual |
| Agreement Drift | ⏳ Partial | Manual |
| Shadow Sampling | ✅ Complete | Semi-automatic |
| Rollback Switch | ✅ Defined | Manual |

---

## Minimal Viable Guardrails (Current)

✅ **Implemented**:
1. evaluator_version logging
2. Gate results in capsule output
3. Shadow trace collection tools
4. Version tracking for rollback

⏳ **P2 Future**:
1. Automated distribution monitoring
2. Alert integration
3. One-command rollback

---

## Acceptance Criteria

For Post-Gate 1 promotion:

- [x] evaluator_version appears in all capsules
- [x] Version is "2.0-gate-based"
- [x] Gate results are logged
- [x] Shadow tools available
- [x] Rollback path defined

**Verdict**: ✅ Minimal guardrails in place

---

Created: 2026-03-09 11:38 CST
