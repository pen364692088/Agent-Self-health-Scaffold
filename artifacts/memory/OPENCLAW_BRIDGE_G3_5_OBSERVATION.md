# OpenClaw Bridge G3.5: Mainline Limited Observation Window

**Version**: 1.0.0
**Date**: 2026-03-16
**Status**: Active
**Duration**: 14 days (2026-03-16 ~ 2026-03-30)

---

## Objective

不新增功能，不扩大范围，只观察 G3 limited mainline assist 在真实主链中的稳定性、帮助率与噪音率。

---

## Observation Scope

### Current State (G3)

| Aspect | Value |
|--------|-------|
| Mode | Limited Mainline Assist |
| Allowed Task Types | coding, decision, question |
| Entry Point | Single (main chain query) |
| Rate Limit | 10 requests / 5000 tokens per session |
| Suggestion Format | Block (not auto-inject) |
| Candidate Access | No |
| Fail-Open | Yes |

### What We Observe

1. **Stability**: Does the system run without errors?
2. **Helpfulness**: Do suggestions improve outcomes?
3. **Noise**: Are suggestions relevant and useful?
4. **Safety**: Are all constraints maintained?

---

## Metrics to Track

### Primary Metrics

| Metric | Description | Target | Collection |
|--------|-------------|--------|------------|
| adoption_rate | 采纳率 | ≥40% | Per session |
| quality_improvement_rate | 质量提升率 | ≥10% | Per adoption |
| noise_rate | 噪音率 | ≤15% | Per adoption |
| prompt_bloat_rate | prompt 膨胀率 | ≤25% | Per request |

### Secondary Metrics

| Metric | Description | Target | Collection |
|--------|-------------|--------|------------|
| rollback_after_recall | 召回后回滚比例 | ≤5% | Weekly |
| demote_after_recall | 召回后降级比例 | ≤10% | Weekly |
| main_chain_success_rate | 主链成功率变化 | No decrease | Daily |
| fail_open_stability | fail-open 稳定性 | 100% | Daily |

### Observation Metrics

| Metric | Description | Collection |
|--------|-------------|------------|
| request_count | 请求总数 | Daily |
| allowed_count | 允许的请求数 | Daily |
| denied_task_type | 任务类型拒绝数 | Daily |
| denied_rate_limit | 限流拒绝数 | Daily |
| suggestion_count | 建议总数 | Daily |
| error_count | 错误数 | Daily |
| timeout_count | 超时数 | Daily |

---

## Observation Method

### Frequency

- **Default**: 1 window per day
- **Minimum**: 1 window per 2 days (if sample too small)
- **Requirement**: Complete observation window, not fragmented reports

### Daily Check

```bash
# Run daily observation check
python scripts/bridge_g35_daily_check.py --date YYYY-MM-DD
```

### Observation Log

All observations logged to:
- `artifacts/memory/bridge_g35_observations/YYYY-MM-DD.json`

### Report Requirements

Each observation report MUST include:
1. **window_start / window_end**: Complete observation window
2. **sample_count**: Total requests/sessions
3. **task_type_distribution**: Breakdown by task type
4. **All metrics with value + numerator + denominator**: e.g., `42% (8/19)`
5. **warning_triggered / critical_triggered**: Threshold violations
6. **anomalies**: Any anomalies observed
7. **status**: healthy | warning | critical-review-required
8. **summary**: Human-readable conclusion

---

## Data Collection

### Source Data

| Source | Description |
|--------|-------------|
| Bridge Statistics | `BridgeMainlineLimited.get_statistics()` |
| Adoption Reports | `BridgeMainlineLimited.report_adoption()` |
| Session Logs | Session-level request tracking |
| Error Logs | Exception and timeout tracking |

### Data Points

Each observation record MUST use this standardized format:

```json
{
  "window_start": "2026-03-16T00:00:00-05:00",
  "window_end": "2026-03-16T23:59:59-05:00",
  "sample_count": 0,
  "task_type_distribution": {
    "coding": 0,
    "decision": 0,
    "question": 0
  },
  "metrics": {
    "adoption_rate": {"value": null, "num": 0, "den": 0},
    "quality_improvement_rate": {"value": null, "num": 0, "den": 0},
    "noise_rate": {"value": null, "num": 0, "den": 0},
    "prompt_bloat_rate": {"value": null, "num": 0, "den": 0},
    "rollback_after_recall": {"value": null, "num": 0, "den": 0},
    "demote_after_recall": {"value": null, "num": 0, "den": 0},
    "main_chain_success_rate": {"value": null, "baseline_delta": null},
    "fail_open_stability": {"value": null, "num": 0, "den": 0}
  },
  "threshold_result": {
    "warning_triggered": [],
    "critical_triggered": [],
    "not_evaluable": [
      "adoption_rate",
      "quality_improvement_rate",
      "noise_rate",
      "prompt_bloat_rate",
      "rollback_after_recall",
      "demote_after_recall",
      "main_chain_success_rate",
      "fail_open_stability"
    ]
  },
  "anomalies": [],
  "status": "insufficient_evidence",
  "summary": "Observation period started. No eligible samples collected in this window yet."
}
```

### Required Fields

Every observation record MUST include:

1. **window_start / window_end**: Observation window timestamps
2. **sample_count**: Total number of requests/sessions
3. **task_type_distribution**: Breakdown by coding/decision/question
4. **All metrics with value + numerator + denominator**: Not just percentages
5. **warning_triggered / critical_triggered / not_evaluable**: Threshold analysis
6. **anomalies**: Any anomalies observed
7. **status**: insufficient_evidence | healthy | warning | critical-review-required
8. **summary**: Human-readable conclusion

### Status Values

| Status | Meaning |
|--------|---------|
| insufficient_evidence | sample_count = 0 or all metrics not_evaluable |
| healthy | No thresholds triggered (with valid samples) |
| warning | Warning threshold(s) triggered |
| critical-review-required | Critical threshold(s) triggered |

### Critical Rule: Not Evaluable Metrics

```text
当 sample_count = 0 或某指标 den = 0 时，该指标状态为 not_evaluable，
不得计入 healthy / warning / critical 判定。

这样不会因为空窗口把趋势判断搞偏，也不会把"无数据"误记成"好数据"。
```

---

## Observation Windows

| Window | Dates | Focus |
|--------|-------|-------|
| W1 | 2026-03-16 ~ 2026-03-22 | Baseline establishment |
| W2 | 2026-03-23 ~ 2026-03-30 | Trend validation |

---

## Decision Criteria

### Continue Expansion

All conditions met:
- adoption_rate ≥ 40%
- quality_improvement_rate ≥ 10%
- noise_rate ≤ 15%
- main_chain_success_rate: no decrease
- fail_open_stability = 100%
- No safety violations

### Maintain & Continue Observing

Some conditions not met:
- One or two metrics slightly off target
- No critical issues
- Potential for improvement with tuning

### Rollback & Fix

Critical issues:
- Multiple metrics significantly off target
- Main chain success rate decreased
- Fail-open stability compromised
- Safety violations

---

## Hard Constraints (Non-Negotiable)

1. **No New Features**: This is observation only
2. **No Scope Expansion**: Stay within G3 limits
3. **No Full-On**: Limited mode only
4. **No Candidate in Recall**: Only approved records
5. **No Process Debt**: Clean observation data

---

## Freeze Rules

| Rule | Status |
|------|--------|
| 禁止新增功能 | 🔒 Forbidden |
| 禁止扩大到多入口/多 agent | 🔒 Forbidden |
| 禁止调整 candidate / approved 边界 | 🔒 Forbidden |
| 禁止放宽 recall 任务类型 | 🔒 Forbidden |
| 禁止 full-on | 🔒 Forbidden |
| 仅允许修复阻塞 bug | ✅ Allowed |

---

## Critical Alert Rules

### Auto-Freeze Rule (Critical)

```text
若任一 Critical 指标连续 2 个观测窗口触发，则自动冻结扩大计划，转入异常复盘；不得借机新增功能。
```

**Critical Metrics**:
- rollback_after_recall > 5%
- demote_after_recall > 10%
- main_chain_success_rate decrease
- fail_open_stability < 100%

### Immediate Review Rules

```text
若 main_chain_success_rate 任一窗口出现下降，则立即人工复核。

若 fail_open_stability < 100%，立即视为阻塞项，暂停扩大计划。
```

---

## Escalation Protocol

### Warning Threshold Triggered

| Step | Action |
|------|--------|
| 1 | Continue observation, do NOT expand scope |
| 2 | Record anomaly in trends document |
| 3 | Confirm recovery in next window |

### Critical Threshold Triggered (Single Window)

| Step | Action |
|------|--------|
| 1 | Immediately halt expansion plan |
| 2 | Manual review required |
| 3 | Do NOT expand scope |
| 4 | Record root cause |
| 5 | Fix boundary/quality issues only |
| 6 | Do NOT add new features |

### Critical Threshold Triggered (Consecutive Windows)

```text
若任一 Critical 指标连续 2 个观测窗口触发：
1. 自动冻结扩大计划
2. 转入异常复盘
3. 只允许修边界/质量问题
4. 不允许借机加功能
```

### fail_open_stability < 100%

| Step | Action |
|------|--------|
| 1 | Immediately treat as blocking issue |
| 2 | Do NOT wait for second window |
| 3 | Halt expansion plan |
| 4 | Manual review required |

---

## Reporting

### Daily Report

- Generated: Daily at end of day
- Location: `artifacts/memory/bridge_g35_daily/YYYY-MM-DD.md`
- Content: Basic metrics snapshot

### Weekly Report

- Generated: Weekly (Sunday)
- Location: `artifacts/memory/bridge_g35_weekly/YYYY-WW.md`
- Content: Trend analysis and recommendations

### Final Report

- Generated: End of observation window
- Location: `artifacts/memory/OPENCLAW_BRIDGE_G3_5_FINAL.md`
- Content: Complete analysis and decision

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Data collection failure | Manual fallback, log parsing |
| Metric calculation error | Validation scripts, cross-check |
| Observation bias | Multiple data sources, blind analysis |
| False positives | Threshold tuning, manual review |

---

## Timeline

| Day | Activity |
|-----|----------|
| D1-D7 | Establish baseline, collect initial data |
| D8-D14 | Validate trends, prepare final report |
| D15 | Generate final report and decision |

---

**Created**: 2026-03-16T01:45:00Z
**Last Updated**: 2026-03-16T02:05:00Z
**Status**: 🔒 FROZEN (Observation Mode)
**Observation End**: 2026-03-30 23:59:59 America/Winnipeg (2026-03-31T04:59:59Z)
