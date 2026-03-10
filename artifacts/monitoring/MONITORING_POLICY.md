# Context Compression Pipeline · Monitoring Policy

**Version**: V3 (2.1-decision-context-enhanced)
**Established**: 2026-03-09
**Baseline File**: `baselines/V3_BASELINE_20260309.json`

---

## V3 Baseline Metrics

| Metric | Value | Alert Threshold |
|--------|-------|-----------------|
| Agreement Rate | 92% | < 80% |
| FP Rate | 0% | > 20% |
| FN Rate | 2% | > 15% |
| DC Coverage | 66.7% | < 50% |
| create_action_ambiguity | 8% | > 15% |

---

## Tail-Risk Escalation Rules

### create_action_ambiguity → 升级为修复专项

满足以下**任一**条件即升级：

1. 连续 2 个 window 上升
2. 与 recovery failure/partial 明显相关
3. 某 bucket 内占比持续偏高
4. 触发新 FP/disagreement 聚集

### long_technical_variants → 升级条件

1. 真实样本中出现同类模式
2. FP 数量 > 0
3. 影响 recovery outcome

---

## Drift Detection

### Alert Thresholds

| Metric | V3 Baseline | Alert |
|--------|-------------|-------|
| Agreement | 92% | Δ < -12% |
| DC Coverage | 66.7% | Δ < -16.7% |
| FP Rate | 0% | Δ > +20% |

### Check Frequency

- **Drift Check**: 每次用户请求时执行
- **Tail-Risk Scan**: 每周或用户请求时
- **Outcome Consistency**: 新样本积累后

---

## Monitoring Tasks

| Task | Status | Schedule |
|------|--------|----------|
| Drift Watch | ✅ Active | On-demand |
| Tail-Risk Scan | ✅ Active | Weekly / On-demand |
| Outcome Consistency | ⏳ Pending | Next window |

---

## Version History

| Version | Date | Notes |
|---------|------|-------|
| V2 Baseline | Pre-2026-03-09 | Archived, DC Coverage = 0% |
| V3 Baseline | 2026-03-09 | DC Coverage = 66.7%, FP = 0% |

---

*Last Updated: 2026-03-09T12:42 CST*

---

## Monitoring Enhancements (2026-03-09 13:05)

### 1. 样本量下限检测

每次 drift check 必须报告：

| 指标 | 最小阈值 | 说明 |
|------|----------|------|
| 总样本数 | ≥ 20 | 低于此值不判定趋势 |
| 单 bucket 样本数 | ≥ 3 | 低于此值标记 `insufficient_data` |

**Sample-insufficient handling**:
- 不基于样本不足的 bucket 做漂移判定
- 标记 `samples: insufficient` 而非 `status: warning`

### 2. create_action_ambiguity 影响度追踪

不只是计数，还需追踪：

| Impact Type | Description | Weight |
|-------------|-------------|--------|
| recovery_failure | 导致恢复失败 | High |
| recovery_partial | 导致恢复部分失败 | Medium |
| disagreement | 判定不一致 | Low |
| FP | 导致误报 | Medium |

**区分**:
- **高频低影响**: 标签噪声，观察即可
- **低频高影响**: 业务风险，优先处理

---

*Enhanced: 2026-03-09T13:05 CST*
