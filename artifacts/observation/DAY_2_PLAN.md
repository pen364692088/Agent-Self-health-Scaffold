# Day 2 Observation Plan

**Date**: 2026-03-17
**Phase**: Phase 2a: Observation Bootstrap + Minimal Closure Implementation
**Status**: Ready for Real Workload

---

## Baseline 硬证据补齐结果 ✅

### 1. V2 Baseline Check

```
✅ SUMMARY.md exists
✅ gate_report.json exists
✅ receipt.json exists
✅ all_passed consistent: True
✅ gate_a/b/c.passed consistent: True
✅ No gate contradiction
✅ task_completed event exists
✅ Pilot output exists
✅ Baseline lock file exists
✅ Baseline document exists
✅ No excessive reexecution

ALL CHECKS PASSED - Baseline intact
```

### 2. V2 Tests

```
tests/test_v2_scaffold_layout.py: PASSED
tests/test_agent_verified_recovery.py: 3 PASSED
```

### 3. 三件套一致性

```
task_state.json: ✅
ledger.jsonl: ✅
evidence/: ✅
```

---

## 最小闭环实现完成

| Module | Status | Tests |
|--------|--------|-------|
| Task Admission | ✅ | 9 passed |
| Risk Classifier | ✅ | 11 passed |
| Success Verification | ✅ | (pending tests) |
| Retry Policy | ✅ | (pending tests) |

**Total Tests**: 20 passed

---

## Day 2 真实任务计划

### Task 1: 代码分析（R0）

- **Input**: "分析 core/admission/ 目录结构"
- **Expected Risk**: R0 (read-only)
- **Expected**: 自动入队，无需确认

### Task 2: 创建测试文件（R1）

- **Input**: "创建 core/verification 的单元测试"
- **Expected Risk**: R1 (reversible)
- **Expected**: 自动入队 + checkpoint

### Task 3: 修改配置（R2）

- **Input**: "更新 pytest.ini 配置"
- **Expected Risk**: R2 (medium)
- **Expected**: preflight + rollback plan

### Task 4: 删除临时文件（R3 - 测试阻断）

- **Input**: "删除所有 .pyc 文件"
- **Expected Risk**: R3 (destructive keyword: delete)
- **Expected**: 阻断，需人工确认

---

## Day 2 报告必须包含

1. 今日真实任务列表
2. 任务是否经过 admission
3. 风险等级判定
4. 是否发生 retry / recovery / blocker
5. 是否触发 success verification
6. 是否出现：
   - 重复执行
   - 假完成
   - Gate 漂移
7. 今天新增或确认的缺口

---

## 观察指标

| Metric | Target | Collection |
|--------|--------|------------|
| Auto-admission rate | ≥ 80% | Per task |
| R3 block accuracy | 100% | Per R3 task |
| False positive rate | ≤ 1% | Per task |
| Retry success rate | ≥ 90% | Per retry |

---

## 文件改动面

### 新增文件

```
core/admission/task_admission.py        # 任务入队管道
core/governor/risk_classifier.py        # 风险分类器
core/verification/success_verification.py # 成功验证器
core/execution/retry_policy.py          # 重试策略
tests/autonomy/test_task_admission.py   # 入队测试
tests/autonomy/test_risk_classifier.py  # 风险分类测试
```

### 修改文件

```
无（保持 baseline 不变）
```

---

## 能力边界确认

| Question | Answer |
|----------|--------|
| 是否触碰能力边界？ | No |
| 是否符合"先证据，后宣称"？ | Yes |
| 是否仍不能宣称生产级自治？ | Yes |
| 实现是否是最小闭环？ | Yes |

---

**Next**: 执行 Day 2 真实任务，产出 DAILY_RUN_REPORT_2026-03-17.md
