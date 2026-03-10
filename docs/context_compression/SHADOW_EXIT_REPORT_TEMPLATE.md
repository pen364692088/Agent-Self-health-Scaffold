# Shadow Exit Report Template

**Generated**: YYYY-MM-DD
**Shadow Period**: YYYY-MM-DD to YYYY-MM-DD
**Decision**: PENDING / ENABLE / EXTEND / DISABLE

---

## 1. Sample Window

| Metric | Value |
|--------|-------|
| Shadow Duration | X days |
| Total Observed Windows | N |
| Eligible Trigger Windows | N |
| Blocked Trigger Windows | N |
| Emergency Candidates | N |
| Near-Threshold Windows | N |
| Ratio Unavailable Count | N |

---

## 2. Exit Criteria Status

| # | Criterion | Threshold | Observed | Pass |
|---|-----------|-----------|----------|------|
| 1 | 触发频率合理 | 1-5/hour (non-emergency) | N | ✅/❌ |
| 2 | 无连续异常触发 | 0 consecutive errors | N | ✅/❌ |
| 3 | 无抖动/重复压缩 | No oscillation within 30min | N | ✅/❌ |
| 4 | 压后回落达标 | ratio <= 0.65 post-compact | N | ✅/❌ |
| 5 | Recovery Quality 正常 | session_state intact | N | ✅/❌ |
| 6 | Emergency 正常 | 0 unexpected emergencies | N | ✅/❌ |
| 7 | Blockers 可解释 | All blockers documented | N | ✅/❌ |

**Overall**: X/7 criteria passed

---

## 3. Trigger Statistics

### 3.1 Action Distribution

| Action | Count | % |
|--------|-------|---|
| none (below threshold) | N | X% |
| none (blocked) | N | X% |
| none (cooldown) | N | X% |
| compact_normal | N | X% |
| compact_emergency | N | X% |
| **Total** | N | 100% |

### 3.2 Blocker Hit Distribution

| Blocker ID | Description | Hits | % |
|------------|-------------|------|---|
| BLK-GIT-001 | Uncommitted WIP | N | X% |
| BLK-LOOP-001 | Open loops unpersisted | N | X% |
| BLK-GATE-001 | Critical gate in progress | N | X% |
| **Total** | | N | 100% |

### 3.3 Skip Reasons

| Reason | Count | % |
|--------|-------|---|
| below_threshold | N | X% |
| ratio_unavailable | N | X% |
| cooldown_active | N | X% |
| blocker_hit | N | X% |
| **Total** | N | 100% |

---

## 4. Ratio Distribution

### 4.1 Pre-Trigger Ratios

| Range | Count | % |
|-------|-------|---|
| 0.00 - 0.50 | N | X% |
| 0.50 - 0.65 | N | X% |
| 0.65 - 0.80 | N | X% |
| 0.80 - 0.90 | N | X% |
| 0.90 - 1.00 | N | X% |

### 4.2 Post-Compaction Ratios (if any)

| Range | Count | % |
|-------|-------|---|
| 0.00 - 0.45 | N | X% |
| 0.45 - 0.55 | N | X% |
| 0.55 - 0.65 | N | X% |
| 0.65 - 0.80 | N | X% |
| 0.80+ | N | X% |

---

## 5. Anomaly Log

| Timestamp | Type | Details | Resolution |
|-----------|------|---------|------------|
| ... | ... | ... | ... |

### Anomaly Categories

- **ratio_unavailable**: Budget watcher couldn't determine ratio
- **should_trigger_skip**: Met threshold but skipped unexpectedly
- **oscillation**: Repeated near-threshold triggers within short window
- **blocker_overfire**: Blocker hit too frequently
- **insufficient_drop**: Post-compact ratio didn't drop enough
- **emergency_anomaly**: Emergency trigger when not expected

---

## 6. Emergency Events

| Timestamp | Trigger Ratio | Expected | Actual | Notes |
|-----------|---------------|----------|--------|-------|
| ... | ... | ... | ... | ... |

**Total Emergencies**: N
**Expected Emergencies** (ratio >= 0.90): N
**Unexpected Emergencies**: N

---

## 7. Cooldown Effectiveness

| Metric | Value |
|--------|-------|
| Normal Cooldown Hits | N |
| Emergency Cooldown Hits | N |
| Cooldown Bypass (emergency) | N |
| Avg Time Between Compressions | X min |

---

## 8. Recommendation

### Decision Matrix

| Scenario | Action |
|----------|--------|
| 7/7 criteria pass | ENABLE default |
| 5-6 criteria pass | EXTEND shadow |
| < 5 criteria pass | INVESTIGATE |

### Recommendation

- [ ] **ENABLE**: Ready for default enablement
- [ ] **EXTEND**: Extend shadow period by X days
- [ ] **INVESTIGATE**: Anomalies need investigation
- [ ] **DISABLE**: Systemic issues found

### Rationale

[Explain reasoning for recommendation]

### Conditions for Enablement (if EXTEND)

1. [Condition 1]
2. [Condition 2]

---

## 9. Sign-off

| Role | Name | Date |
|------|------|------|
| Reviewer | | |
| Approver | | |

---

## Appendix

### A. Full SHADOW_TRACE.jsonl

[Link or summary]

### B. Configuration Snapshot

```json
{
  "trigger_ratio_normal": 0.80,
  "trigger_ratio_emergency": 0.90,
  "target_ratio_normal": "0.55-0.65",
  "target_ratio_emergency": "0.45-0.55",
  "cooldown_normal_min": 30,
  "cooldown_emergency_min": 15
}
```

### C. Exit Criteria Definitions

See: `docs/context_compression/SHADOW_EXIT_CRITERIA.md`
