# Replay Guardrail Report - Mainline Shadow

**Report Date**: 2026-03-07
**Integration Mode**: Shadow
**Status**: Active (Observing)

---

## Guardrail Status

**Current Status**: ✅ ACTIVE (baseline from validation)

Based on new baseline full validation:
- Replay improved by +0.289
- Zero regression
- Guardrail requirements met

---

## Baseline Metrics (From Validation)

| Metric | Value |
|--------|-------|
| Historical Replay Samples | 18 |
| Avg Baseline Score | 0.207 |
| Avg Patch Score | 0.496 |
| Delta | +0.289 |
| Improved | 18/18 |
| Regressed | 0/18 |

---

## Replay Failure Taxonomy (From Validation)

### Samples Not Reaching >=0.75

**All 18 samples** did not reach >=0.75.

**Root Causes**:

| Category | Count | Description |
|----------|-------|-------------|
| Limited decision anchors | 12 | Only 0-6 anchors |
| Limited entity anchors | 9 | Max 1 per sample |
| Limited open_loop anchors | 2 | Very few mentions |
| Limited constraint anchors | 4 | Rare extraction |

**Analysis**: Data format limitation, not patch failure.

---

## Mainline Shadow Observations

| Metric | Current | Target |
|--------|---------|--------|
| Sessions observed | 0 | - |
| Replay avg delta | N/A | >= 0 |
| Regressed samples | N/A | 0 |

*Will populate as mainline sessions are observed*

---

## Guardrail Requirements

| Requirement | Threshold | Baseline | Current |
|-------------|-----------|----------|---------|
| No regression | 0 regressed | 0 | N/A |
| Better than old baseline | Any improvement | +0.289 | N/A |
| Separate reporting | Required | ✅ | ✅ |

---

## Weak Spots (From Validation)

| Anchor Type | Replay Avg | Real Avg | Gap |
|-------------|------------|----------|-----|
| decision | 0.9 | 10.0 | -9.1 |
| entity | 0.5 | 7.1 | -6.6 |
| open_loop | 0.1 | 6.9 | -6.8 |
| constraint | 0.2 | 9.6 | -9.4 |

**Analysis**: Historical data format lacks rich anchor content.

---

## Guardrail Assessment

**Is Replay a Blocker?**: ❌ No

**Reasoning**:
1. Baseline validation shows improvement (+0.289)
2. Zero regression
3. Gap from >=0.75 is data format issue
4. Real samples (actual use case) perform well

**Guardrail Verdict**: ✅ PASS - Continue observation

---

## Ongoing Monitoring

### Daily Checks

- [ ] Replay avg score
- [ ] Regression count
- [ ] Anchor coverage distribution
- [ ] Failure taxonomy updates

### Alert Conditions

| Condition | Action |
|-----------|--------|
| Replay delta < 0 | Alert + investigate |
| Regressed samples > 0 | Alert + investigate |
| Anchor coverage drops | Log for analysis |

---

**Keywords**: `replay-guardrail` `mainline-shadow` `observation-mode`
