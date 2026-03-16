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

### Daily Check

```bash
# Run daily observation check
python scripts/bridge_g35_daily_check.py --date YYYY-MM-DD
```

### Weekly Trend

```bash
# Run weekly trend analysis
python scripts/bridge_g35_weekly_trend.py --week YYYY-WW
```

### Observation Log

All observations logged to:
- `artifacts/memory/bridge_g35_observations/YYYY-MM-DD.json`

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

Each observation records:
```json
{
  "date": "2026-03-16",
  "session_id": "session_xxx",
  "request_count": 5,
  "allowed_count": 5,
  "denied_count": 0,
  "suggestion_count": 12,
  "adoption_count": 8,
  "helpful_count": 7,
  "noise_count": 1,
  "error_count": 0,
  "fail_open_count": 0
}
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
**Last Updated**: 2026-03-16T01:55:00Z
**Status**: 🔒 FROZEN (Observation Mode)

---

## ⚠️ FREEZE NOTICE

**观察期已冻结，至 2026-03-30 结束。**

在此期间：
- ❌ 禁止新增功能
- ❌ 禁止扩大范围
- ❌ 禁止调整边界
- ✅ 仅允许修复阻塞 bug

---

## Freeze Rules

1. **禁止新增功能**
2. **禁止扩大到多入口/多 agent**
3. **禁止调整 candidate / approved 边界**
4. **禁止放宽 recall 任务类型**
5. **禁止 full-on**
6. **仅允许修复阻塞主链或破坏观测有效性的 bug**

---

## Alert Thresholds

| Metric | Threshold | Severity |
|--------|-----------|----------|
| adoption_rate | < 40% | ⚠️ Warning |
| quality_improvement_rate | < 10% | ⚠️ Warning |
| noise_rate | > 15% | ⚠️ Warning |
| prompt_bloat_rate | > 25% | ⚠️ Warning |
| rollback_after_recall | > 5% | 🔴 Critical |
| demote_after_recall | > 10% | 🔴 Critical |
| main_chain_success_rate | Decrease | 🔴 Critical |
| fail_open_stability | < 100% | 🔴 Critical |

### Alert Response Protocol

When alert triggered:
1. **Do NOT expand scope**
2. **Record anomaly** in trends document
3. **Fix boundary/quality issues only**
4. **Do NOT add new features**

---

## Observation Execution

### Schedule

- **Frequency**: Every 1-2 days
- **Method**: Cron task → Send report to user
- **Location**: Telegram (user: 8420019401)

### Data Recording

Each observation record MUST include:
1. `adoption_rate`
2. `quality_improvement_rate`
3. `noise_rate`
4. `prompt_bloat_rate`
5. `rollback_after_recall`
6. `demote_after_recall`
7. `main_chain_success_rate`
8. `fail_open_stability`

### Required Attachments

Each record MUST include:
1. **Sample Size**: Number of requests/sessions
2. **Time Window**: Date range
3. **Task Type Distribution**: coding/decision/question counts
4. **Anomaly Notes**: Any anomalies observed

---

## Final Deliverable

**Due**: 2026-03-30
**Location**: `artifacts/memory/OPENCLAW_BRIDGE_G3_5_FINAL_REVIEW.md`

### Required Content

1. **Sample Size**: Total observations collected
2. **Metrics Status**: Each metric vs target
3. **Primary Benefits**: What worked well
4. **Primary Risks**: What didn't work
5. **Expansion Recommendation**: Yes/No
6. **Expansion Scope**: If yes, to what
7. **Blocking Issues**: If no, what blocks expansion

---

## Cron Task Configuration

```bash
# Schedule: Every 2 days at 09:00 CDT
0 9 */2 * * /home/moonlight/.openclaw/workspace/scripts/bridge_g35_report.sh
```

### Report Script

```bash
#!/bin/bash
# scripts/bridge_g35_report.sh
# Sends G3.5 observation report to user

cd /home/moonlight/Project/Github/MyProject/Agent-Self-health-Scaffold
python scripts/bridge_g35_daily_check.py --date $(date +%Y-%m-%d) --send-report
```

---

**Observation End**: 2026-03-30T23:59:59Z
