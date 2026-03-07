# Candidate Patch Validation Report

**Run at**: 2026-03-07T03:58:44.728485
**Validation**: Patch A (baseline) vs Patch B (anchor-enhanced)

---

## Patches

| Patch | Description |
|-------|-------------|
| A | baseline retrieve + baseline capsule |
| B | anchor-enhanced capsule + anchor-aware retrieve |

---

## Overall Summary

| Metric | Baseline (A) | Anchor-Aware (B) | Delta |
|--------|-------------|------------------|-------|
| **Avg Score** | 0.284 | 0.733 | +0.449 |
| **>=0.75 Samples** | 0 | 16 | +16 |
| **Improved** | - | 34 | - |
| **Regressed** | - | 0 | - |
| **Correct Topic Wrong Anchor** | - | 0 | - |

---

## By Source Type

### Historical Replay (18 samples)

| Metric | Baseline | Anchor | Delta |
|--------|----------|--------|-------|
| Avg Score | 0.207 | 0.496 | +0.289 |
| >=0.75 | 0 | 0 | +0 |
| Improved | - | 18 | - |
| Regressed | - | 0 | - |

### Real Main Agent Admissible (16 samples)

| Metric | Baseline | Anchor | Delta |
|--------|----------|--------|-------|
| Avg Score | 0.371 | 1.000 | +0.629 |
| >=0.75 | 0 | 16 | +16 |
| Improved | - | 16 | - |
| Regressed | - | 0 | - |

---

## Per-Sample Results (Top 20)

| Sample ID | Source | Admissible | Baseline | Anchor | Delta | >=0.75 |
|-----------|--------|------------|----------|--------|-------|--------|
| pic_focus_1fb6b1ae75 | historical_r | ❌ | 0.167 | 0.377 | +0.210 | ❌ |
| pic_focus_2b382ada01 | historical_r | ❌ | 0.000 | 0.670 | +0.670 | ❌ |
| pic_focus_455a807d7d | historical_r | ❌ | 0.267 | 0.360 | +0.093 | ❌ |
| pic_focus_4b1c43c501 | historical_r | ❌ | 0.167 | 0.623 | +0.457 | ❌ |
| pic_focus_4f39b50590 | historical_r | ❌ | 0.000 | 0.230 | +0.230 | ❌ |
| pic_focus_556067aef0 | historical_r | ❌ | 0.233 | 0.360 | +0.127 | ❌ |
| pic_focus_c5ec44456c | historical_r | ❌ | 0.367 | 0.507 | +0.140 | ❌ |
| pic_focus_d1f1efede8 | historical_r | ❌ | 0.250 | 0.670 | +0.420 | ❌ |
| opic_recall_93b294b2 | historical_r | ❌ | 0.280 | 0.360 | +0.080 | ❌ |
| opic_recall_a28c92e6 | historical_r | ❌ | 0.220 | 0.690 | +0.470 | ❌ |
| opic_recall_bc615b44 | historical_r | ❌ | 0.200 | 0.623 | +0.423 | ❌ |
| opic_recall_eb5e5b1c | historical_r | ❌ | 0.300 | 0.670 | +0.370 | ❌ |
| _correction_1f077dbd | historical_r | ❌ | 0.320 | 0.343 | +0.023 | ❌ |
| _correction_8aef97e0 | historical_r | ❌ | 0.320 | 0.670 | +0.350 | ❌ |
| _correction_c424e487 | historical_r | ❌ | 0.440 | 0.507 | +0.067 | ❌ |
| _open_loops_023391b1 | historical_r | ❌ | 0.000 | 0.670 | +0.670 | ❌ |
| _open_loops_446b5328 | historical_r | ❌ | 0.000 | 0.230 | +0.230 | ❌ |
| _open_loops_58c4cfbc | historical_r | ❌ | 0.200 | 0.377 | +0.177 | ❌ |
| opic_recall_3cc19cbd | real_main_ag | ✅ | 0.294 | 1.000 | +0.706 | ✅ |
| opic_recall_5ea9eb36 | real_main_ag | ✅ | 0.283 | 1.000 | +0.717 | ✅ |
