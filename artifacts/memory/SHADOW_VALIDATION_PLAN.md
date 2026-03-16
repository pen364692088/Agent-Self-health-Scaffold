# Shadow Validation Plan

**Version**: 1.0.0
**Date**: 2026-03-15
**Branch**: validation/memory-kernel-shadow

---

## Objective

验证 M4a + M5a 在真实链路中的 capture / recall / fail-open 边界是否成立，在不影响主链输出的前提下，评估是否具备进入下一阶段的条件。

---

## Validation Scope

### M4a Capture Governance
- [ ] 捕获只写 candidate，不进入 authority knowledge
- [ ] 白名单机制生效
- [ ] 去重机制生效
- [ ] 噪音拦截生效
- [ ] candidate promotion 需要显式操作

### M5a Controlled Recall
- [ ] 默认只从 approved 召回
- [ ] candidate 仅 shadow/debug 可见
- [ ] top-k 限制生效
- [ ] trace 输出完整
- [ ] Truth 精确引用
- [ ] fail-open 生效

---

## Validation Method

### Shadow Mode

本次验证使用 shadow 模式：
- 不影响主回复/主决策
- 记录所有行为到日志
- 不改变任何状态

### Test Scenarios

| Scenario | Description |
|----------|-------------|
| capture_basic | 基本捕获流程 |
| capture_noise | 噪音拦截测试 |
| capture_dedup | 去重测试 |
| recall_approved | approved 召回测试 |
| recall_candidate | candidate 可见性测试 |
| recall_truth | Truth 精确引用测试 |
| fail_open | 失败处理测试 |

---

## Metrics to Collect

### Capture Metrics

| Metric | Description |
|--------|-------------|
| total_candidates | candidate 总数 |
| noise_filtered | 噪音拦截数 |
| noise_filter_rate | 噪音拦截率 |
| duplicates | 重复数 |
| dedup_rate | 去重率 |
| whitelist_rejected | 白名单拒绝数 |
| promotion_suggested | 建议提升数 |
| promotion_approved | 批准提升数 |
| promotion_rate | promotion 建议通过率 |

### Recall Metrics

| Metric | Description |
|--------|-------------|
| total_queries | 查询总数 |
| approved_hits | approved 命中数 |
| approved_hit_rate | recall 命中率 |
| candidate_visible | candidate 可见数 |
| candidate_leaked | candidate 泄露数（应为 0）|
| scope_filtered | scope 过滤命中数 |
| truth_quotes | Truth 引用数 |
| truth_correct | Truth 精确引用正确数 |
| truth_correct_rate | Truth 精确引用正确率 |
| fail_open_triggered | fail-open 触发次数 |

### Safety Metrics

| Metric | Description |
|--------|-------------|
| main_chain_affected | 主链是否受影响（应为 False）|
| authority_leaked | candidate 越权数（应为 0）|
| truth_summary_used | Truth 被摘要冒充数（应为 0）|

---

## Validation Steps

### Step 1: Capture Validation
1. 初始化 CaptureEngine 和 CandidateStore
2. 运行捕获测试场景
3. 记录所有捕获行为
4. 验证 candidate 不进入 authority knowledge

### Step 2: Recall Validation
1. 初始化 RecallEngine
2. 运行召回测试场景
3. 验证只从 approved 召回
4. 验证 candidate 不可见（production 模式）
5. 验证 candidate 可见（shadow 模式）

### Step 3: Truth Quote Validation
1. 提取 Truth 层记录
2. 验证精确引用
3. 验证无摘要冒充

### Step 4: Fail-Open Validation
1. 模拟错误场景
2. 验证 fail-open 行为
3. 验证主链不受影响

---

## Pass Criteria

| Criterion | Threshold |
|-----------|-----------|
| candidate 不越权 | 100% |
| Truth 精确引用 | 100% |
| fail-open 生效 | 100% |
| 主链不受影响 | 100% |
| 噪音拦截率 | ≥ 80% |
| 去重率 | ≥ 90% |
| recall 命中率 | ≥ 50% |

---

## Exit Criteria

最终输出只允许三种结论：

1. **可进入 M4b/M5b** - 所有 pass criteria 满足
2. **需先修边界** - 存在可修复的边界问题
3. **暂停推进并列出阻塞项** - 存在严重问题

---

## Deliverables

| File | Description |
|------|-------------|
| SHADOW_CAPTURE_REPORT.md | 捕获验证报告 |
| SHADOW_RECALL_REPORT.md | 召回验证报告 |
| SHADOW_FAIL_OPEN_REPORT.md | Fail-Open 验证报告 |
| SHADOW_DECISION.md | 最终决策 |

---

## Timeline

| Step | Duration |
|------|----------|
| Capture Validation | ~5 min |
| Recall Validation | ~5 min |
| Fail-Open Validation | ~5 min |
| Report Generation | ~5 min |
| **Total** | ~20 min |

---

**Created**: 2026-03-15T23:58:00Z
