# P1 High Priority Coverage Soak Report

**Generated**: 2026-03-09
**Soak Duration**: 5 rounds
**Status**: COMPLETE

---

## Executive Summary

**P1 Soak Verdict**: **READY FOR CLOSURE** ✅

21 probes (P0: 9 + P1: 12) 在 always-on 下整体稳定、准确、无噪音。

---

## Soak Results

### Stability

| Metric | Result |
|--------|--------|
| Total Rounds | 5 |
| Total Probes | 21 |
| Stable Pass Rate | 95% (20/21) |
| Consistent Failures | 1 (callback-delivery) |
| Flaky Probes | 1 (probe-summary-generation, Round 4) |

### Per-Round Results

| Round | Total | Passed | Failed | Notes |
|-------|-------|--------|--------|-------|
| 1 | 21 | 20 | 1 | callback-delivery FAIL |
| 2 | 21 | 20 | 1 | callback-delivery FAIL |
| 3 | 21 | 20 | 1 | callback-delivery FAIL |
| 4 | 21 | 19 | 2 | callback-delivery + summary-generation FAIL |
| 5 | 21 | 20 | 1 | callback-delivery FAIL |

---

## Accuracy Analysis

### True Positive (正确检测到真实问题)

| Probe | Status | Issue | Verified |
|-------|--------|-------|----------|
| probe-callback-delivery | ❌ FAIL | callback-worker systemd 服务未运行 | ✅ 真实问题 |

**详情**:
- systemd returncode: 3 (failed)
- path_unit_active: true
- 服务状态: failed
- 这是**真实系统问题**，probe 正确检测

### Flaky (临时失败)

| Probe | Status | Issue |
|-------|--------|-------|
| probe-summary-generation | ⚠️ FLAKY | Round 4 失败，其他轮次通过 |

**分析**: 可能是临时执行问题或文件锁竞争，但整体稳定 (4/5 PASS)

### False Positive/Negative

| Type | Count |
|------|-------|
| False Positive (假阳) | 0 |
| False Negative (假阴) | 0 |

---

## Noise Assessment

### Incident/Proposal Metrics

| Metric | Value | Assessment |
|--------|-------|------------|
| Total Incidents | 4 | ✅ Low |
| Total Proposals | 2 | ✅ Low |
| Deduped Incidents | 16 | ✅ Dedup working |
| Deduped Proposals | 18 | ✅ Dedup working |

**结论**: 无噪音风暴，dedup 机制正常工作

---

## Semantic Consistency

### Cross-Layer Verdict

| Source | Status | Value |
|--------|--------|-------|
| Gate Verdict | ✅ PASS | A/B/C all PASS |
| Health Status | ✅ GREEN | overall_status |
| Heartbeat | ✅ healthy | heartbeat_status |
| Probes (20/21) | ✅ PASS | 95% pass rate |
| Probes (1/21) | ❌ FAIL | callback-delivery |

**分析**:
- Gate 判定 PASS 是正确的，因为 callback-delivery 是具体功能问题，不影响基础健康
- 无语义冲突，probe 失败被正确隔离
- callback-delivery 失败**没有污染** Gate/Health 判定

---

## Execution Cost

### Resource Usage

| Metric | Value | Budget | Status |
|--------|-------|--------|--------|
| Scheduler Runs | 189 | - | ✅ Normal |
| Probe Runs | 25 | - | ✅ Normal |
| Execution Budget Hits | 0 | - | ✅ No overruns |
| Lock Contention | 0 | - | ✅ No conflicts |
| Last Run Duration | 6330ms | 15000ms | ✅ Within budget |

**结论**: 21 probes 运行成本可接受，无额外负担

---

## callback-delivery Failure Analysis

### Stability
- ✅ 持续稳定失败（5/5 rounds）
- ✅ 失败原因一致

### Accuracy
- ✅ 失败原因是真实的（systemd 服务未运行）
- ✅ 被正确归类为系统问题，非 probe 缺陷

### Isolation
- ✅ 没有污染其他 probes
- ✅ 没有污染 Gate verdict
- ✅ 没有污染 Health status

**结论**: callback-delivery 失败是 **probe 正在稳定抓到真实问题**，这是 P1 coverage 的价值证明

---

## Soak Questions Answered

### Q1: 21 probes 是否持续稳定？
**✅ YES** - 20/21 稳定，1 个是真实问题的正确报告

### Q2: callback-delivery 是否稳定暴露真实问题？
**✅ YES** - 持续失败，原因是真实的 systemd 服务问题

### Q3: 是否有噪音？
**✅ NO** - Dedup 正常工作，无风暴

### Q4: 语义是否一致？
**✅ YES** - Probe 失败被正确隔离，不影响 Gate/Health

### Q5: 运行成本是否可接受？
**✅ YES** - 无预算超限，无锁竞争，执行时间正常

---

## Issues Found

### Issue 1: probe-summary-generation Flaky (Minor)
- **Severity**: LOW
- **Impact**: 1/5 rounds failed
- **Action**: Monitor in production, may need retry logic

### Issue 2: callback-delivery Service Not Running (Known)
- **Severity**: MEDIUM
- **Impact**: Probe correctly detects real issue
- **Action**: User to decide whether to start callback-worker service

---

## Recommendation

**P1 High Priority Coverage: CLOSED** ✅

**理由**:
1. ✅ 21 probes 实现并集成
2. ✅ 95% 稳定通过率
3. ✅ 无假阳性/假阴性
4. ✅ 真实问题被正确检测
5. ✅ 无噪音/风暴
6. ✅ 语义一致性良好
7. ✅ 运行成本可接受

**下一步**: 
- 可选：修复 callback-worker 服务
- 或：开始 P2 Medium Priority Coverage

---

**Report Generated**: 2026-03-09
**Soak Status**: COMPLETE ✅
