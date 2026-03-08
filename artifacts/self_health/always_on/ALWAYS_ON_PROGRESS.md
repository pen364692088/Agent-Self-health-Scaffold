# ALWAYS_ON_PROGRESS

**Status**: SOAK_IN_PROGRESS (intermediate evidence collected)
**Updated**: 2026-03-08T16:33:00-05:00

---

## Completed in current round
- OAI-5 baseline safety controls are now observable in scheduler runtime:
  - single-run lock
  - cooldown block accounting
  - execution budget accounting
  - dedup ledger for incidents/proposals
- OAI-3 baseline automatic flow is now connected:
  - quick/full runs can auto-generate health summary
  - degraded states can auto-generate incidents
  - ORANGE/RED states can auto-generate proposal-only outputs
- OAI-4 baseline gate residency is now connected:
  - gate runs write history
  - gate inconsistency can increment always-on metrics

---

## Soak Evidence (2h 21m)

**Time Range**: 2026-03-08 19:11 → 21:32 CDT
**Total Runs**: 41
  - Gate: 31 (every 5 min)
  - Full: 6 (hourly)
  - Quick: 4

**Health Indicators**:
| Metric | Value |
|--------|-------|
| Gate PASS rate | 100% (41/41) |
| Lock contention | 0 |
| Execution budget hit | 0 |
| Cooldown blocks | 2 (expected) |

**Runtime Telemetry Freshness**:
- heartbeat_status: healthy (lag: 0s)
- callback_worker_status: degraded (inactive - expected for event-driven service)
- mailbox_worker_status: healthy
- summary_status: healthy

**Gate Report (latest)**:
- Gate A: PASS (registry/policy/tool presence)
- Gate B: PASS (runtime telemetry present and fresh)
- Gate C: PASS (preflight/doctor/execution-guard baseline checks)

---

## Known Limitations
1. callback-worker telemetry shows "degraded" when inactive (semantic mismatch for event-driven services)
2. mailbox-worker telemetry is file/flow heuristic, not process-backed
3. proposal auto-flow not yet exercised in real degraded scenario
4. soak duration < 24h (need longer observation)

---

## Next Milestone
- Target: 24h soak with continuous Gate PASS
- Blocker: None (system stable)
- ETA: 2026-03-09 14:00 CDT

---

## Verdict (intermediate)
**PASS with caveats**. Baseline wiring is functional. Need 24h evidence before declaring WIRING_ACTIVE.

---

## Telemetry Semantic Fix (2026-03-08 16:42 CDT)

### 问题
callback-worker 是事件驱动服务（path-activated），但 telemetry 把 inactive 误报为 "degraded"。

### 修改
1. **tools/callback-worker-doctor**:
   - 新增 `check_service_expected_state()` 区分三种状态：
     - `active`: 服务运行中
     - `idle_expected`: inactive + 无 pending work (OK)
     - `degraded`: inactive + 有 pending work (问题)

2. **tools/agent-self-health-scheduler**:
   - 解析 doctor 输出的 service_state
   - 映射 worker_status: `idle_expected` → `healthy`
   - 新增 `service_state` 字段

### 影响范围
- ✅ 只修改 telemetry 语义映射
- ✅ 不改变 scheduler/Gate/proposal 逻辑
- ✅ 不破坏 soak 连续性
- ✅ run_history 持续写入

### 验证
- Gate A/B/C: PASS
- callback_worker_status.worker_status: healthy
- callback_worker_status.service_state: idle_expected
- Telemetry age: < 15s

### 原则
**只做低风险语义修正，不动主链路。**
