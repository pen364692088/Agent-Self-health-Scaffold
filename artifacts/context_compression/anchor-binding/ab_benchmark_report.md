# A/B Benchmark Report: Anchor-Aware Ranking

**Benchmark**: old-topic-micro-benchmark-12
**Run At**: 2026-03-07T02:57:03.168699

## Summary

| Metric | Baseline (A) | Anchor-Aware (B) | Delta |
|--------|-------------|------------------|-------|
| Avg Coverage | 0.083 | 0.583 | +0.500 |
| Top-1 Anchor Hit Rate | 8.3% | 50.0% | +41.7% |
| Samples >= 0.75 | 1 | 7 | +6 |
| Correct Topic, Wrong Anchor | 0 | 0 | +0 |

## Key Findings

- **Total Samples**: 12
- **Improved**: 6 samples
- **Degraded**: 0 samples

## Per-Sample Results

| Sample ID | Source | Baseline Coverage | Anchor Coverage | Delta | Top1 Hit (B) |
|-----------|--------|------------------|-----------------|-------|--------------|
| sample_historical_old_topic_focus_4b1c43 | historical_repl | 1.000 | 1.000 | +0.000 | ✓ |
| sample_historical_old_topic_focus_d1f1ef | historical_repl | 0.000 | 1.000 | +1.000 | ✓ |
| sample_historical_old_topic_focus_c5ec44 | historical_repl | 0.000 | 1.000 | +1.000 | ✓ |
| sample_historical_old_topic_focus_455a80 | historical_repl | 0.000 | 1.000 | +1.000 | ✓ |
| sample_historical_old_topic_focus_4f39b5 | historical_repl | 0.000 | 1.000 | +1.000 |  |
| sample_historical_old_topic_focus_556067 | historical_repl | 0.000 | 1.000 | +1.000 | ✓ |
| sample_historical_old_topic_recall_a28c9 | historical_repl | 0.000 | 1.000 | +1.000 | ✓ |
| sample_real_main_agent_old_topic_recall_ |  | 0.000 | 0.000 | +0.000 |  |
| sample_real_main_agent_old_topic_recall_ |  | 0.000 | 0.000 | +0.000 |  |
| sample_real_main_agent_old_topic_recall_ |  | 0.000 | 0.000 | +0.000 |  |
| sample_real_main_agent_old_topic_recall_ |  | 0.000 | 0.000 | +0.000 |  |
| sample_real_main_agent_old_topic_recall_ |  | 0.000 | 0.000 | +0.000 |  |

## Recommendation

**✅ RECOMMEND**: Anchor-aware ranking shows significant improvement and is worth pursuing.

Next steps:
1. Integrate anchor extraction into capsule builder
2. Add anchor scoring to retrieve pipeline
3. Run full S1 validation with new ranking
