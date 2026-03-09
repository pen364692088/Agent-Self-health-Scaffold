# Phase 4: Threshold Replay Results

**Generated**: 2026-03-09T19:40:34.783953+00:00
**Duration**: 269ms

## Summary

| Metric | Value |
|--------|-------|
| Total Scenarios | 10 |
| Passed | 10 |
| Failed | 0 |
| Pass Rate | 100.0% |
| Critical Passed | 6/6 |
| Status | ✅ PASS |

## Test Results

| # | Scenario | Input | Expected | Actual | Result |
|---|----------|-------|----------|--------|--------|
| 1 | Below threshold | r=0.79 | none | none | ✅ |
| 2 | Normal trigger | r=0.8 | normal | normal | ✅ |
| 3 | Normal mid-range | r=0.85 | normal | normal | ✅ |
| 4 | Near emergency with blocker | r=0.88 +1bl | blocked | blocked | ✅ |
| 5 | Emergency trigger | r=0.9 | emergency | emergency | ✅ |
| 6 | Emergency high | r=0.95 | emergency | emergency | ✅ |
| 7 | Cooldown active | r=0.82 +cooldown | none | none | ✅ |
| 8 | Post-compaction safe | r=0.62 | none | none | ✅ |
| 9 | Post-compaction marginal | r=0.72 | none | none | ✅ |
| 10 | Critical blocker | r=0.85 +1bl | blocked | blocked | ✅ |

## Acceptance Criteria

| Criteria | Status |
|----------|--------|
| All 10 scenarios tested | ✅ |
| Pass rate >= 90% | ✅ (100.0%) |
| No critical failures | ✅ (0 failed) |
| Results documented | ✅ |

## Thresholds Verified

- **Normal Trigger**: 0.80
- **Emergency Trigger**: 0.90
- **Hysteresis Exit Warning**: 0.75
- **Hysteresis Exit Emergency**: 0.85
