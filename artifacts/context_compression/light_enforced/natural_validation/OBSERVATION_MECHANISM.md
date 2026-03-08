# Natural Traffic Observation Mechanism

**Purpose**: 持续观测 budget 与状态，等待自然触发

---

## Observation Points

每次实质性交互时记录：

| Field | Description |
|-------|-------------|
| ts | 时间戳 |
| session_id | 会话 ID |
| turn_number | 轮次 |
| estimated_tokens | 估算 tokens |
| budget_ratio | 预算比率 |
| compression_state | 压缩状态 |
| recommended_action | 推荐动作 |

---

## Current Baseline (2026-03-07T23:52:00-06:00)

```
Session: 89cbc6ee-8dae-4a70-bb27-32fcf4fac44c
Budget Ratio: 0.81
Phase: candidate (75-85%)
Threshold: 0.85
Gap: 0.04
```

---

## Trigger Condition

**Hard Threshold Enforcement**: 当 budget_ratio >= 0.85 且进入下一轮 assemble

**Expected Flow**:
```
budget_check (assemble前) → ratio >= 0.85 → forced_standard_compression → capsule created
```

---

## What NOT To Do

- ❌ 不降低 max_tokens 来制造触发
- ❌ 不修改 threshold
- ❌ 不使用 controlled 60k 方式替代
- ❌ 不扩大到 high-risk

---

## Evidence to Capture

一旦触发，必须记录：

1. Counter before/after
2. Guardrail event
3. Trigger report
4. Budget before/after
5. Capsule metadata
6. Session note

---

*Observation mechanism defined: 2026-03-07T23:52:00-06:00*

---

## Evidence Hot Zone Rules

### Activation
When budget_ratio >= 0.84, enter **evidence hot zone**:
- Increase trace granularity
- Auto-capture before/after each assemble
- Ensure no evidence is lost

### Auto-Capture Checklist

Per-assemble when in hot zone:

**Before Assemble**:
- [ ] counter_snapshot_before.json
- [ ] budget_snapshot_before.json
- [ ] session_note.md

**After Assemble (if triggered)**:
- [ ] counter_snapshot_after.json
- [ ] budget_snapshot_after.json
- [ ] guardrail_event.json
- [ ] capsule_metadata.json
- [ ] trigger_report.json

### Critical Insight

**最容易丢失**: 阈值附近那一轮的 before/after
**解决方案**: 预埋捕获点，不等事后回捞

---

## Current Distance to Hot Zone

```
Current Ratio: ~0.825
Hot Zone: 0.84
Trigger: 0.85

Gap to Hot Zone: ~0.015
Gap to Trigger: ~0.025
```

---

*Hot zone rules added: 2026-03-07T23:58:00-06:00*
