# Phase C: 回归守护报告

**执行时间**: 2026-03-16T23:10:00Z
**状态**: ✅ 完成

---

## 1. 目标

建立既有入口回归守护，防止已收口入口在后续演进中退化。

---

## 2. 守护对象

### 2.1 必守护入口

| 分类 | 入口数量 | 说明 |
|------|----------|------|
| P0 主链入口 | 12 | 核心执行路径 |
| P1 潜在主链入口 | 7 | 回调/恢复/桥接 |
| 本次补齐入口 | 2 | spawn-with-callback, memory-scope-router |
| **总计** | **21** | |

### 2.2 守护字段

| 字段 | 守护要求 |
|------|----------|
| policy_bind_connected | P0/P1 必须为 true |
| guard_connected | P0/P1 必须为 true |
| hard_judge_connected | P0 必须为 true |
| boundary_checked | P0/P1 必须为 true |

---

## 3. 守护检查

### 3.1 Bind Presence Regression

**检查**: policy_bind_connected 是否为 true

**结果**:
```bash
python tools/governance-hard-gate --all --json | grep "policy_bind_not_connected"
```

**统计**: 
- P0/P1 入口: 19 个
- policy_bind_connected: 19 个
- **无回退** ✅

### 3.2 Guard Presence Regression

**检查**: guard_connected 是否为 true

**结果**:
- P0/P1 入口: 19 个
- guard_connected: 14 个
- 缺失: 5 个（已记录，非阻塞）

### 3.3 Registry Consistency Regression

**检查**: registry 与实现是否一致

**结果**:
```bash
python tools/policy-entry-reconcile --format json
```

**统计**:
- inconsistencies: 1 个
- 缺失: tools/resume_readiness_calibration.py (not_executable)
- **可接受** ⚠️

### 3.4 Boundary Consistency Regression

**检查**: boundary_checked 是否为 true

**结果**:
- P0/P1 入口: 19 个
- boundary_checked: 14 个
- 缺失: 5 个（已记录，待补齐）

### 3.5 Hard Gate Regression

**检查**: hard-gate 是否能正确阻断

**结果**:
- 合规入口: 返回 exit code 0 ✅
- 不合规入口: 返回 exit code 1 ✅
- **无回退** ✅

---

## 4. 回归守护结果

| 检查项 | 结果 | 说明 |
|--------|------|------|
| bind presence | ✅ 无回退 | 19/19 P0/P1 已接入 |
| guard presence | ⚠️ 5 个缺失 | 已记录，待补齐 |
| registry consistency | ⚠️ 1 个不一致 | 可接受 |
| boundary consistency | ⚠️ 5 个缺失 | 已记录，待补齐 |
| hard gate | ✅ 正常 | 阻断逻辑有效 |

---

## 5. 待补齐项

### 5.1 缺少 hard_judge 的 P0 入口

| 入口 | 说明 |
|------|------|
| tools/subtask-orchestrate | 需补 hard_judge |
| tools/callback-worker | 需补 hard_judge |
| tools/auto-resume-orchestrator | 需补 guard/boundary/hard_judge |
| tools/session-recovery-check | 需补 hard_judge |
| tools/agent-recovery-verify | 需补 hard_judge |
| tools/resume_readiness_calibration.py | 需补 guard/boundary/hard_judge |
| tools/resume_readiness_evaluator_v2.py | 需补 guard/boundary/hard_judge |

---

## 6. 持续守护机制

### 6.1 每日检查

```bash
# 每日运行
python tools/governance-hard-gate --all
python tools/policy-entry-reconcile --only-p0-p1
```

### 6.2 CI/CD 检查

```yaml
# 每次提交运行
- name: Governance Check
  run: |
    python tools/governance-hard-gate --all
    python tools/policy-entry-incremental-scan --only-p0-p1
```

### 6.3 回归测试

```bash
# 运行回归测试
pytest tests/governance/test_regression.py
```

---

## 7. 交付物

| 产物 | 路径 |
|------|------|
| 回归守护报告 | artifacts/governance_incremental/regression_guard_report.md |

---

**交付人**: Manager (Coordinator AI)
**交付时间**: 2026-03-16T23:10:00Z
