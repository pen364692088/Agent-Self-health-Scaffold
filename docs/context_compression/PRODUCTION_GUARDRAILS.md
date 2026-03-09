# Production Guardrails for Context Compression

**Version**: 1.0
**Date**: 2026-03-09
**Evaluator Version**: 2.0-gate-based

---

## Monitoring Strategy

### 1. Evaluator Version Logging

Every capsule includes `evaluator_version` field:
```json
{
  "evaluator_version": "2.0-gate-based",
  "resume_readiness": {
    "score": 0.65,
    "gates": {...},
    "signals": {...}
  }
}
```

**Check**: All production capsules should have `evaluator_version: "2.0-gate-based"`

---

### 2. Readiness Score Distribution

Monitor the distribution of readiness scores:

| Bucket | Expected Range | Alert if |
|--------|----------------|----------|
| Zero (0.0) | 40-60% of samples | < 30% or > 70% |
| Low (0.01-0.49) | 10-20% | > 30% |
| Medium (0.50-0.69) | 15-25% | > 35% |
| High (0.70-1.0) | 10-20% | > 30% |

**Alert Condition**: Distribution shifts significantly from baseline

---

### 3. Agreement Rate Monitoring

Periodic spot-check against human evaluation:

| Metric | Baseline | Alert Threshold |
|--------|----------|-----------------|
| Agreement Rate | 92% | < 80% |
| False Positive Rate | 7% | > 20% |
| False Negative Rate | 0% | > 15% |

**Sampling**: 5-10 capsules per week

---

### 4. Gate Hit Rates

Monitor gate passage rates:

| Gate | Expected | Alert if |
|------|----------|----------|
| topic_present | 30-50% pass | < 20% or > 60% |
| task_active | 90-95% pass | < 85% |

**Alert Condition**: Gate rates shift significantly

---

### 5. Create Action Ambiguity

Known P2 issue - monitor for growth:

| Metric | Baseline | Alert Threshold |
|--------|----------|-----------------|
| Create Action Ambiguity Rate | 6.7% (1/15) | > 15% |

**Action**: If exceeds threshold, prioritize P2 fix

---

## Alert Thresholds Summary

| Alert | Threshold | Action |
|-------|-----------|--------|
| Agreement Drop | < 80% | Investigate immediately |
| FP Spike | > 20% | Check for evaluator drift |
| FN Spike | > 15% | Check for evaluator drift |
| Create Ambiguity | > 15% | Prioritize P2 fix |
| Version Mismatch | Any V1 capsule | Investigate call path |

---

## Rollback Procedure

### If V2 evaluator shows issues:

1. **Immediate**: Add `--version v1` support to capsule-builder
2. **Revert**: Deploy previous version of capsule-builder-v2.py
3. **Verify**: Check `evaluator_version` in new capsules

### Rollback Trigger Conditions:
- Agreement rate drops below 70%
- False positive rate exceeds 30%
- Production incident caused by evaluator

---

## Monitoring Checklist

### Daily
- [ ] Check readiness score distribution
- [ ] Verify evaluator_version in recent capsules

### Weekly
- [ ] Spot-check 5-10 capsules for agreement
- [ ] Review gate hit rates
- [ ] Check create action ambiguity rate

### Monthly
- [ ] Full calibration run
- [ ] Compare against baseline
- [ ] Update thresholds if needed

---

## Metrics Collection

### Log Files
```
artifacts/capsules/*.json          # Individual capsules
artifacts/compression_events/*.json # Compression events
artifacts/context_compression/shadow/SHADOW_TRACE.jsonl # Shadow traces
```

### Key Queries
```bash
# Check evaluator version distribution
jq '.evaluator_version' artifacts/capsules/*.json | sort | uniq -c

# Readiness score distribution
jq '.resume_readiness.score' artifacts/capsules/*.json | sort -n | uniq -c

# Gate passage rate
jq '.resume_readiness.gates.passed' artifacts/capsules/*.json | sort | uniq -c
```

---

## Baseline (Post-Promotion)

| Metric | Value | Date |
|--------|-------|------|
| Evaluator Version | 2.0-gate-based | 2026-03-09 |
| Agreement Rate | 92% | Calibration |
| Shadow Agreement | 93% | Shadow |
| False Positive | 7% | Calibration |
| False Negative | 0% | Calibration |

---

Created: 2026-03-09 11:37 CST
