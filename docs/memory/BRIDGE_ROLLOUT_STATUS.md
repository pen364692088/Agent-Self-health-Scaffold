# Bridge Rollout Status

**Version**: 1.0.0
**Date**: 2026-03-16
**Status**: G3.5 Observation

---

## Overview

OpenClaw Bridge 是 Memory Kernel 与 OpenClaw 主链的集成层，采用分阶段灰度推进策略。

---

## Rollout Phases

### G1: Shadow ✅ COMPLETE

| Aspect | Value |
|--------|-------|
| Date | 2026-03-16 |
| Mode | Shadow (read-only) |
| Visibility | Log only |
| Influence | None |
| Tests | 17 passed |
| Status | ✅ Passed |

**Key Results**:
- Fail-open 100% 成功
- Candidate 不泄露
- 主状态不被污染
- 可进入 G2

**Documentation**:
- `docs/memory/OPENCLAW_BRIDGE_SHADOW_PLAN.md`
- `artifacts/memory/OPENCLAW_BRIDGE_SHADOW_REPORT.md`

---

### G2: Canary Assist ✅ COMPLETE

| Aspect | Value |
|--------|-------|
| Date | 2026-03-16 |
| Mode | Canary Assist (suggestion) |
| Visibility | Available to chain |
| Influence | Suggestion only |
| Adoption Tracking | Yes |
| Tests | 24 passed |
| Status | ✅ Passed |

**Key Results**:
- 采纳追踪工作正常
- 质量指标可测量
- Fail-open 100% 成功
- 可进入 G3

**Documentation**:
- `docs/memory/OPENCLAW_BRIDGE_CANARY_PLAN.md`
- `artifacts/memory/OPENCLAW_BRIDGE_CANARY_REPORT.md`

---

### G3: Limited Mainline ✅ COMPLETE

| Aspect | Value |
|--------|-------|
| Date | 2026-03-16 |
| Mode | Limited Mainline Assist |
| Task Types | coding, decision, question |
| Entry Points | Single (main chain) |
| Rate Limiting | Yes (session-based) |
| Tests | 23 passed |
| Status | ✅ Passed |

**Key Results**:
- 任务类型限制生效
- 限流机制正常
- Fail-open 100% 成功
- 可进入 G3.5

**Documentation**:
- `docs/memory/OPENCLAW_BRIDGE_G3_PLAN.md`
- `artifacts/memory/OPENCLAW_BRIDGE_G3_REPORT.md`

---

### G3.5: Observation Window 🔄 IN PROGRESS

| Aspect | Value |
|--------|-------|
| Start Date | 2026-03-16 |
| Duration | 14 days |
| Mode | Observation only |
| New Features | None |
| Status | 🔄 Active |

**Objectives**:
- 观察稳定性
- 追踪帮助率
- 追踪噪音率
- 验证安全性

**Documentation**:
- `artifacts/memory/OPENCLAW_BRIDGE_G3_5_OBSERVATION.md`
- `artifacts/memory/OPENCLAW_BRIDGE_G3_5_TRENDS.md`

---

### Future Phases (Planned)

#### G4: Expanded Mainline Assist

| Aspect | Planned |
|--------|---------|
| Task Types | Expand to analysis, creative |
| Entry Points | Multiple |
| Auto-Inject | No |
| Timeline | After G3.5 success |

#### G5: Full Mainline Assist

| Aspect | Planned |
|--------|---------|
| Task Types | All |
| Entry Points | Multiple |
| Auto-Inject | Optional |
| Timeline | After G4 success |

---

## Current Configuration

### G3 Limited Mainline Settings

```yaml
allowed_task_types:
  - coding
  - decision
  - question

denied_task_types:
  - analysis
  - creative

rate_limits:
  max_requests_per_session: 10
  max_tokens_per_session: 5000

budget:
  coding: 800 tokens
  decision: 600 tokens
  question: 400 tokens

safety:
  fail_open: true
  candidate_access: false
  auto_inject: false
```

---

## Rollout Metrics

### Cumulative Tests

| Phase | Tests | Cumulative |
|-------|-------|------------|
| G1 | 17 | 17 |
| G2 | 24 | 41 |
| G3 | 23 | 64 |
| G3.5 | 0 | 64 |

### Cumulative Files

| Phase | Files | Lines |
|-------|-------|-------|
| G1 | 4 | ~1,200 |
| G2 | 4 | ~1,400 |
| G3 | 5 | ~1,600 |

---

## Safety Guarantees

| Guarantee | Status | Verification |
|-----------|--------|--------------|
| Fail-open always works | ✅ | Tests |
| Candidate never leaked | ✅ | Tests |
| No state writeback | ✅ | Tests |
| No auto-inject | ✅ | Tests |
| Rate limiting works | ✅ | Tests |
| Task type restriction | ✅ | Tests |

---

## Decision Tree

```
G3.5 Observation Complete
         │
         ├─► All metrics met ──────────► G4: Expand
         │
         ├─► Some metrics off ─────────► Maintain & Observe
         │
         └─► Critical issues ──────────► Rollback & Fix
```

---

## Rollback Plan

### Triggers

- Main chain success rate decrease > 5%
- Fail-open stability < 100%
- Noise rate > 30%
- Critical safety violation

### Procedure

1. Disable bridge integration
2. Analyze failure root cause
3. Fix issues in isolation
4. Re-run tests
5. Restart from G2

---

## Key Contacts

| Role | Responsibility |
|------|----------------|
| Manager | Rollout decisions |
| Tests | Verification |
| Documentation | Evidence |

---

## References

- Memory Kernel Index: `docs/memory/MEMORY_KERNEL_INDEX.md`
- Process Debt Log: `artifacts/acceptance/PROCESS_DEBT_LOG.md`

---

**Last Updated**: 2026-03-16T01:50:00Z
**Next Milestone**: G3.5 Observation Complete (2026-03-30)
