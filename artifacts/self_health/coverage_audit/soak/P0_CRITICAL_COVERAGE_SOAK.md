# P0 Critical Coverage Soak

**Started**: 2026-03-09
**Status**: IN PROGRESS
**Objective**: 验证 9 个 P0 critical probes 在 always-on 下稳定、无噪音、语义一致

---

## Soak Goals

### 1. Stability
- 9 个 critical probes 在 always-on 下稳定运行
- 无崩溃、超时、资源泄漏

### 2. Noise Assessment
- 无 probe 风暴
- 无重复 incident/proposal 噪音
- Cooldown 和 dedup 机制有效

### 3. Accuracy
- 无假阳性（probe fail 但系统实际健康）
- 无假阴性（probe pass 但系统实际有问题）
- 与 capability / gate / truth semantics 一致

### 4. Overhead
- Scheduler 运行 probes 后无额外负担
- 执行时间在 budget 内
- 资源消耗可接受

### 5. Closure Criteria
- P0 critical coverage 可以标记为 CLOSED

---

## P0 Probes (9)

| # | Probe | Verification Mode |
|---|-------|-------------------|
| 1 | probe-native-compaction | probe_check |
| 2 | probe-context-overflow | synthetic_input_check |
| 3 | probe-callback-delivery | chain_integrity_check |
| 4 | probe-mailbox-integrity | artifact_output_check |
| 5 | probe-gate-consistency | chain_integrity_check |
| 6 | probe-session-persistence | probe_check |
| 7 | probe-proposal-boundary | synthetic_input_check |
| 8 | probe-truth-alignment | chain_integrity_check |
| 9 | probe-handoff-integrity | artifact_output_check |

---

## Soak Metrics to Collect

### Per-Probe Metrics
- `run_count` - 运行次数
- `pass_count` - 通过次数
- `fail_count` - 失败次数
- `warn_count` - 警告次数
- `avg_duration_ms` - 平均执行时间
- `max_duration_ms` - 最大执行时间
- `last_status` - 最后状态
- `last_run_at` - 最后运行时间

### Aggregate Metrics
- `total_probe_runs` - 总 probe 运行次数
- `pass_rate` - 通过率
- `false_positive_count` - 假阳性次数
- `false_negative_count` - 假阴性次数
- `noise_events` - 噪音事件数
- `scheduler_budget_hits` - 预算超限次数

### Noise Indicators
- 重复 incident（相同 fingerprint）
- 重复 proposal（相同 action）
- probe 结果频繁 flip-flop
- scheduler lock contention

---

## Soak Timeline

| Phase | Duration | Activities |
|-------|----------|------------|
| Phase 1 | 1 hour | Initial stability check |
| Phase 2 | 6 hours | Extended observation |
| Phase 3 | 24 hours | Full soak cycle |

---

## Questions to Answer

### Q1: Stability
- [ ] All 9 probes run without errors
- [ ] No crashes or timeouts
- [ ] Execution time within budget

### Q2: Noise
- [ ] No probe storms
- [ ] Dedup working correctly
- [ ] Cooldown respected

### Q3: Accuracy
- [ ] No false positives detected
- [ ] No false negatives detected
- [ ] Results consistent with system state

### Q4: Consistency
- [ ] Probe results align with capability semantics
- [ ] Probe results align with gate semantics
- [ ] Probe results align with truth semantics

### Q5: Closure
- [ ] P0 critical coverage can be marked CLOSED

---

## Deliverables

1. `P0_CRITICAL_COVERAGE_SOAK_REPORT.md` - Soak 结果报告
2. `P0_FALSE_POSITIVE_FALSE_NEGATIVE_REVIEW.md` - 误报/漏报分析
3. `P0_PROBE_NOISE_ASSESSMENT.md` - 噪音评估
4. `P0_CLOSURE_VERDICT.md` - 收口判定

---

## Current Status

```
Started: 2026-03-09 01:55 CST
Phase: 1 (Initial Stability Check)
Next Check: 2026-03-09 02:55 CST
```
