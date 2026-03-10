# Shadow Sample Summary

**Generated**: 2026-03-09 20:25 UTC
**Shadow Period**: 2026-03-09 20:03 - 2026-03-09 20:25 (0.35 hours)

---

## Overview

| Metric | Count |
|--------|-------|
| Total Observed Windows | 0 |
| Eligible Triggers | 0 |
| Blocked Triggers | 0 |
| Emergency Candidates | 0 |
| Near-Threshold Windows | 0 |
| Ratio Unavailable | 0 |

**Status**: 🟡 Data Collection Phase

Shadow mode just enabled. Need 3-7 days of data for meaningful analysis.

---

## Action Distribution

| Action | Count | % |
|--------|-------|---|
| none (below threshold) | 1 | 100% |
| none (blocked) | 0 | 0% |
| none (cooldown) | 0 | 0% |
| compact_normal | 0 | 0% |
| compact_emergency | 0 | 0% |

---

## Ratio Distribution (Pre-Trigger)

| Range | Count | % |
|-------|-------|---|
| 0.00 - 0.50 | 1 | 100% |
| 0.50 - 0.65 | 0 | 0% |
| 0.65 - 0.80 | 0 | 0% |
| 0.80 - 0.90 | 0 | 0% |
| 0.90 - 1.00 | 0 | 0% |

**Note**: First check showed ratio=0.0 (new session, expected)

---

## Exit Criteria Progress

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Trigger frequency reasonable | ⏳ Pending |
| 2 | No consecutive errors | ✅ Pass |
| 3 | No oscillation | ✅ Pass |
| 4 | Post-compact drop OK | ⏳ Pending |
| 5 | Recovery quality OK | ⏳ Pending |
| 6 | Emergency normal | ✅ Pass |
| 7 | Blockers explainable | ✅ Pass |

**Overall**: 4/7 criteria pass (3 pending data)

---

## Anomalies Detected

| Code | Count | Notes |
|------|-------|-------|
| A01 | 0 | No ratio_unavailable |
| A02 | 0 | No unexpected skips |
| A03 | 0 | No blocker overfire |
| A04 | 0 | No oscillation |
| A05 | 0 | No compression yet |
| A06 | 0 | No emergency anomaly |

---

## Next Steps

1. Continue shadow data collection
2. Review after 24 hours
3. Generate interim report at 72 hours
4. Full exit evaluation at 7 days

---

## Monitoring Commands

```bash
# Update this summary
~/.openclaw/workspace/tools/shadow_watcher --metrics

# View live trace
tail -f artifacts/context_compression/SHADOW_TRACE.jsonl | jq

# Check exit criteria
cat docs/context_compression/SHADOW_EXIT_CRITERIA.md
```

---

## Update Log

| Timestamp | Event |
|-----------|-------|
| 2026-03-09T20:03:21Z | Shadow mode enabled |
| 2026-03-09T20:03:21Z | First check: ratio=0.0 (normal) |
| 2026-03-09T20:25:00Z | Summary generated |
