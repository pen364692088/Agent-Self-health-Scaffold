# Natural Traffic Validation Definition of Done

**Version**: 1.0
**Created**: 2026-03-07T23:38:00-06:00

---

## Purpose

验证默认 `max_tokens=100k` 配置下，Light Enforced 在自然低风险流量中也能以合理时机触发，而不是只在受控验证中成功。

---

## Pass Conditions

### Hard Requirements

| # | Condition | Description |
|---|-----------|-------------|
| 1 | `enforced_trigger_count >= 1` (natural) | 默认 100k 配置下自然触发 |
| 2 | `sessions_over_threshold` 可解释增长 | 不是异常尖刺 |
| 3 | `real_reply_corruption_count = 0` | 无回复污染 |
| 4 | `active_session_pollution_count = 0` | 无会话污染 |

### Evidence Requirements

必须保留：

1. Counter snapshot
2. Guardrail event log
3. Trigger report
4. Capsule file
5. Report path

### Must Answer

| Question | Required Answer |
|----------|-----------------|
| 触发时的 budget_ratio | 记录具体值 |
| 是否符合 "assemble 前压缩" | Yes |
| 压缩后是否回落安全区 | Yes |

---

## Forbidden Actions During Observation

- ❌ Change threshold
- ❌ Change scoring / metrics / schema
- ❌ Mix in OpenViking/L2 fixes
- ❌ Expand to high-risk scope

---

## Milestone Distinction

| Milestone | What It Proves | Status |
|-----------|----------------|--------|
| A: Controlled Validation | Mechanism correct | ✅ DONE |
| B: Natural Traffic Validation | Production timing reasonable | ⏳ IN PROGRESS |

---

## Exit Declaration

When all conditions met:

```markdown
## Natural Traffic Validation: PASSED

**Date**: [timestamp]
**Natural Triggers**: [count]
**First Natural Trigger Ratio**: [value]
**Compression Result**: [before] → [after]
**Safety**: All zeros
**Evidence**: [links]
```

---

*DoD defined: 2026-03-07T23:38:00-06:00*
