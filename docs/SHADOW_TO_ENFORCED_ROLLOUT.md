# Shadow-to-Enforced Rollout Plan v1.0

**Purpose**: Define phased rollout from Shadow Mode to Full Enforcement.
**Effective Date**: 2026-03-06
**Owner**: SRAP Team

---

## Overview

Rollout from Shadow Mode to Enforced Mode follows a staged approach:

```
Shadow → C0 → C1 → C2 → C3 → Full Enforced
```

Each stage has clear entry/exit criteria, rollback rules, and owner actions.

---

## Stage Definitions

### Stage 0: Shadow Mode (Current)
**Status**: ✅ ACTIVE

| Aspect | Definition |
|--------|------------|
| Mode | Shadow only - log, never block |
| Data collection | 3-7 days minimum |
| Violation handling | Log to shadow_log.jsonl |
| User impact | None |

**Entry Criteria**:
- [x] Shadow Mode enabled in emotiond-enforcer
- [x] shadow_log.jsonl path configured
- [x] Daily reporting tool ready

**Exit Criteria**:
- [ ] Sample count ≥ 200
- [ ] numeric_leak_rate = 0 for 3+ days
- [ ] Violation distribution stable
- [ ] FP/FN validated by human review

**Rollback**: N/A (shadow mode is safe)

**Owner Action**: Monitor daily reports, check for anomalies

---

### Stage C0: Audit Mode
**Status**: ⏳ PENDING

| Aspect | Definition |
|--------|------------|
| Mode | Shadow + Audit alerts |
| Violation handling | Log + alert on P0 violations |
| User impact | None (alerts only) |

**Entry Criteria**:
- [ ] All Shadow exit criteria met
- [ ] Enforcement Matrix approved
- [ ] Alert channel configured

**Exit Criteria**:
- [ ] P0 violation rate < 1%
- [ ] No false positive alerts for 7 days
- [ ] Human review completed for 20+ samples

**Rollback Rule**: If FP alerts > 3/day for 3 days → return to Shadow

**Owner Action**: 
- Review daily alerts
- Validate P0 detections
- Investigate false positives

---

### Stage C1: Soft Block Mode
**Status**: ⏳ PENDING

| Aspect | Definition |
|--------|------------|
| Mode | Shadow + Block candidates for P0 |
| Violation handling | Log + block P0 violations |
| User impact | Blocked responses get fallback message |

**Entry Criteria**:
- [ ] All C0 exit criteria met
- [ ] Block fallback mechanism tested
- [ ] Rollback procedure documented

**Exit Criteria**:
- [ ] P0 block rate stable
- [ ] FP rate < 2%
- [ ] User complaints < 1/week
- [ ] 50+ blocks with validated outcomes

**Rollback Rule**: 
- If FP > 5% for 3 days → return to C0
- If user complaints > 3/week → return to C0

**Owner Action**:
- Monitor blocked responses
- Validate blocks weekly
- Review user complaints

---

### Stage C2: Extended Block Mode
**Status**: ⏳ PENDING

| Aspect | Definition |
|--------|------------|
| Mode | Shadow + Block P0 + Block candidate P1 |
| Violation handling | Log + block P0 and P1 violations |
| User impact | Blocked responses get context-aware fallback |

**Entry Criteria**:
- [ ] All C1 exit criteria met
- [ ] P1 violations analyzed (100+ samples)
- [ ] Context-aware fallback tested

**Exit Criteria**:
- [ ] P1 block rate stable
- [ ] FP rate for P1 < 5%
- [ ] No regression in P0 metrics
- [ ] 100+ P1 blocks with validated outcomes

**Rollback Rule**:
- If P1 FP > 10% → return to C1
- If P0 regression detected → return to C0

**Owner Action**:
- Weekly review of P1 blocks
- Monthly analysis of violation trends
- Quarterly policy review

---

### Stage C3: Full Enforced Mode
**Status**: ⏳ PENDING

| Aspect | Definition |
|--------|------------|
| Mode | Full enforcement with all P0/P1/P2 rules |
| Violation handling | Block P0/P1, log P2 |
| User impact | Consistent enforcement across all paths |

**Entry Criteria**:
- [ ] All C2 exit criteria met
- [ ] P2 violations analyzed (200+ samples)
- [ ] Coverage gate enforced on all paths
- [ ] Response path inventory complete

**Exit Criteria**:
- [ ] Stable enforcement for 30 days
- [ ] FP rate < 2% overall
- [ ] User satisfaction maintained
- [ ] No new violation types discovered

**Rollback Rule**:
- Critical incident → immediate rollback to C2
- FP spike → emergency review

**Owner Action**:
- Continuous monitoring
- Monthly enforcement report
- Quarterly policy review

---

## Rollout Timeline

| Stage | Duration | Start | End |
|-------|----------|-------|-----|
| Shadow | 3-7 days | 2026-03-06 | TBD |
| C0 | 7-14 days | TBD | TBD |
| C1 | 14-30 days | TBD | TBD |
| C2 | 30-60 days | TBD | TBD |
| C3 | Ongoing | TBD | - |

**Total Estimated Duration**: 60-120 days from Shadow start

---

## Rollback Procedures

### Immediate Rollback
```bash
# Emergency rollback to Shadow
echo '{"SRAP_MODE": "shadow"}' > ~/.openclaw/workspace/memory/sweeper_config.json
systemctl --user restart openclaw-gateway
```

### Staged Rollback
1. Review metrics for stage causing issues
2. Document rollback reason in `artifacts/self_report/rollback_log.jsonl`
3. Execute rollback command
4. Verify metrics stabilize
5. Update WORKFLOW_STATE.json

---

## Monitoring Requirements

### Per-Stage Metrics
| Metric | Shadow | C0 | C1 | C2 | C3 |
|--------|--------|----|----|----|----|
| Sample count | Daily | Daily | Daily | Daily | Daily |
| violation_rate | ✓ | ✓ | ✓ | ✓ | ✓ |
| numeric_leak_rate | ✓ | ✓ | ✓ | ✓ | ✓ |
| FP rate | - | ✓ | ✓ | ✓ | ✓ |
| Block count | - | - | ✓ | ✓ | ✓ |
| User complaints | - | - | ✓ | ✓ | ✓ |

### Alert Thresholds
| Alert | Threshold | Action |
|-------|-----------|--------|
| numeric_leak_detected | > 0 | Immediate investigation |
| FP_spike | > 5% in 1 day | Review within 24h |
| violation_rate_spike | > 20% increase | Review within 48h |
| user_complaints | > 3/week | Rollback consideration |

---

## Success Criteria

**Stage Completion**:
- All exit criteria met
- No critical issues for 7 days
- Owner sign-off

**Full Rollout Success**:
- Stable enforcement for 90 days
- FP rate < 2%
- User satisfaction maintained
- No new violation types

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| v1.0 | 2026-03-06 | Initial plan from MVP11.6 Task 7 |

