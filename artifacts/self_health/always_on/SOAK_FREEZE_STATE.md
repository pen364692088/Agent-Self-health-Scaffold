# SOAK_FREEZE_STATE

**Status**: FROZEN_OBSERVATION
**Effective**: 2026-03-08T16:44:00-05:00
**Target**: 24h verdict (2026-03-09T14:00:00-05:00)

---

## Frozen Scope

**禁止修改**:
- scheduler 主逻辑
- Gate 判定逻辑
- proposal 边界
- capability contract
- telemetry 文件结构

**允许修改** (仅限必要):
- bugfix (阻断性问题)
- telemetry 语义微调 (不改主链路)
- 报告/指标补充 (不改判定)

---

## 24h Verdict 条件 (固定)

满足以下全部条件 → `MAIN_SYSTEM_ALWAYS_ON_ACTIVE`:

| 条件 | 阈值 |
|------|------|
| Gate A/B/C 持续 PASS | 100% |
| runtime telemetry 持续写入 | 无中断 > 5min |
| incident 风暴 | 无连续 > 3 同类型 |
| proposal 风暴 | 无连续 > 3 同类型 |
| summary 风暴 | 无连续 > 3 同类型 |
| lock contention | 0 或 < 1/h |
| execution budget hit | 0 或 < 1/h |
| 主循环影响 | 无明显卡顿/超时 |
| capability/summary/gate 口径一致 | 无矛盾 |

**Fallback 分类**:

| 状态 | 条件 |
|------|------|
| WIRING_ACTIVE_BUT_SOAK_PENDING | 满足大部分条件，minor caveats |
| ACTIVE_WITH_CAVEATS | 满足核心条件，有已知限制 |
| WIRING_ISSUES_DETECTED | 有明显问题需修复 |
| INSUFFICIENT_EVIDENCE | 数据不足，需延长 soak |

---

## Known Caveats (本轮不修)

1. **mailbox-worker telemetry**: file heuristic, not process-backed
   - 影响: 中等
   - 处理: 24h 后评估
   - 不阻断本轮 verdict

---

## Semantic Fixes Applied (记录)

### 2026-03-08 16:42 CDT - callback-worker 语义修正

**修改内容**:
- `tools/callback-worker-doctor`: 区分 active/idle_expected/degraded
- `tools/agent-self-health-scheduler`: 映射 idle_expected → healthy

**影响范围**:
- ✅ 只修改 telemetry 语义映射
- ✅ 不改变 scheduler/Gate/proposal 主链路
- ✅ 不影响 soak 连续性

**验证**:
- Gate A/B/C: PASS
- callback_worker_status.worker_status: healthy
- service_state: idle_expected

**注释**: 这是 inactive 解释的修正，不是系统行为改变。之前 "degraded" 是误报，实际系统正常。

---

## Commitment

从现在到 24h verdict 前，严格遵守冻结规则。除非出现阻断性问题，否则不做任何结构性修改。

**最终 verdict 由数据驱动，不凭感觉。**
