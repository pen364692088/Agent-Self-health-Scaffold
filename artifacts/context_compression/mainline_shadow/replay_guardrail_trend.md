# Replay Guardrail Trend Report

**Period**: 2026-03-07 (Initial)
**Status**: Baseline Only (No New Data)

---

## Baseline Metrics (From Validation)

| Metric | Value |
|--------|-------|
| Samples | 18 |
| Avg Baseline | 0.207 |
| Avg Patch | 0.496 |
| Delta | +0.289 |
| Regressed | 0 |

---

## Trend Data

| Date | Sessions | Avg Score | Delta | Regressed |
|------|----------|-----------|-------|-----------|
| 2026-03-07 (baseline) | 18 | 0.496 | +0.289 | 0 |
| 2026-03-07 (shadow) | 0 | N/A | N/A | N/A |

**Note**: No mainline shadow sessions observed yet.

---

## Guardrail Status

| Requirement | Threshold | Status |
|-------------|-----------|--------|
| No regression | 0 regressed | ✅ PASS |
| Improvement maintained | delta >= 0 | ✅ PASS |
| Separate reporting | required | ✅ Active |

---

## Anchor Coverage Trend

| Type | Baseline Avg | Current | Trend |
|------|--------------|---------|-------|
| decision | 0.9 | N/A | - |
| entity | 0.5 | N/A | - |
| time | 5.4 | N/A | - |
| open_loop | 0.1 | N/A | - |
| constraint | 0.2 | N/A | - |
| tool_state | 7.8 | N/A | - |

---

## Failure Taxonomy

From baseline validation:

| Category | Count | Description |
|----------|-------|-------------|
| Low anchor diversity | 12/18 | decision, entity limited |
| Time-only | 4/18 | Only time anchors |
| Tool-state dominant | 6/18 | High tool_state, low others |

**Root Cause**: Historical data format limitations

---

## Watch Points

| Point | Priority | Action |
|-------|----------|--------|
| Replay avg score | High | Monitor for < 0.4 |
| Regression count | High | Alert if > 0 |
| Anchor coverage | Medium | Track for drops |

---

## Next Update

After collecting mainline shadow replay sessions.

---

**Keywords**: `replay-guardrail` `trend` `baseline`
