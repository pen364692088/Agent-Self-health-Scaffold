# Natural Traffic Validation Bootstrap

**Created**: 2026-03-07T23:50:00-06:00
**Purpose**: 锁定运行配置，准备自然流量验证

---

## Runtime Configuration (LOCKED)

| Config | Value | Status |
|--------|-------|--------|
| Mode | Light Enforced | ✅ Active |
| Scope | low-risk only | ✅ Enforced |
| max_tokens | 100,000 | ✅ Default |
| Kill Switch | Available | ✅ Ready |
| Replay Guardrail | Active | ✅ On |
| L2 Branch | Isolated | ✅ Not Mixed |
| New Patch Set | None | ✅ Clean |

---

## Current Session State

```
Context: 162k/200k (81%)
Budget Ratio: 0.81
Phase: candidate (75-85%)
Distance to Threshold: 0.04 (need >= 0.85)
```

---

## What This Task Proves

**NOT**: 机制是否存在 (Milestone A 已证明)
**YES**: 默认 100k 配置下，自然流量触发时机是否合理

---

## Constraints

### Allowed
- ✅ Default 100k config
- ✅ Natural low-risk sessions
- ✅ Existing Light Enforced pipeline
- ✅ Existing counter/guardrail/capsule/report

### Forbidden
- ❌ Modify threshold
- ❌ Modify scoring/metrics/schema
- ❌ Mix OpenViking/L2 fixes
- ❌ Expand to high-risk scope
- ❌ New patch sets
- ❌ Artificially lower max_tokens

---

## Success Criteria

| # | Condition | Target |
|---|-----------|--------|
| 1 | Natural enforced_trigger | >= 1 |
| 2 | sessions_over_threshold | Explainable growth |
| 3 | real_reply_corruption_count | 0 |
| 4 | active_session_pollution_count | 0 |
| 5 | Evidence package | Complete |
| 6 | Timing questions | Answerable |

---

*Bootstrap locked: 2026-03-07T23:50:00-06:00*
