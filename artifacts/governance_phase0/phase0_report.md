# Phase 0: 最小治理基础设施搭建报告

**执行时间**: 2026-03-16T21:30:00Z
**状态**: ✅ 完成

---

## 1. 任务目标

从零落地真实可验证的治理基础设施最小集，替代此前"口头完成"状态。

---

## 2. 交付产物

### 2.1 核心产物

| 产物 | 路径 | 状态 |
|------|------|------|
| 入口注册表 | contracts/policy_entry_registry.yaml | ✅ 已创建 |
| 硬门禁检查工具 | tools/governance-hard-gate | ✅ 已创建 |
| 入口对账工具 | tools/policy-entry-reconcile | ✅ 已创建 |

### 2.2 辅助产物

| 产物 | 路径 | 状态 |
|------|------|------|
| 首次扫描结果 | artifacts/governance_phase0/initial_reconcile_results.json | ✅ 已生成 |
| Registry 基线 | artifacts/governance_phase0/initial_registry_baseline.yaml | ✅ 已备份 |
| Phase 0 报告 | artifacts/governance_phase0/phase0_report.md | ✅ 本文档 |

---

## 3. 首次扫描结果（真实数据）

### 3.1 总体统计

| 指标 | 值 |
|------|-----|
| 总候选入口 | 234 |
| 已注册入口 | 8 |
| 未注册入口 | 226 |
| 不一致项 | 0 |
| P0/P1 未注册入口 | 23 |

### 3.2 已注册入口分布

| Class | 数量 | 说明 |
|-------|------|------|
| P0 | 4 | 主链强相关入口 |
| P1 | 2 | 潜在主链旁路入口 |
| P2 | 2 | 辅助治理入口 |
| P3 | 0 | 测试/示例/废弃入口 |
| **总计** | **8** | |

### 3.3 未注册 P0/P1 入口（需优先处理）

**P0 类（11 个）**:
- tools/session-start-recovery
- tools/resume_readiness_calibration.py
- tools/agent-recovery-summary
- tools/probe-callback-worker-doctor
- tools/demo-auto-resume-restart-test
- tools/session-start-recovery.bak
- tools/gate-self-health-check
- tools/agent-self-health-scheduler
- tools/callback-worker-doctor
- tools/session-recovery-check
- tools/resume_readiness_evaluator_v2.py
- tools/agent-recovery-verify

**P1 类（12 个）**:
- tools/test-callback-acceptance
- tools/probe-callback-delivery
- tools/subagent-callback-hook
- tools/verify-callback-guards
- tools/subagent-completion-handler
- tools/test-callback-auto
- tools/test-callback-regression
- tools/memory-scope-router
- tools/spawn-with-callback
- tools/callback-handler-auto-advance
- tools/callback-daily-summary

---

## 4. 硬门禁验证

### 4.1 合规入口测试（应返回 exit code 0）

| 入口 | Class | Exit Code | 结果 |
|------|-------|-----------|------|
| tools/policy-daily-check | P2 | 0 | ✅ PASS |
| tools/callback-handler | P1 | 0 | ✅ PASS |
| tools/agent-self-heal | P0 | 0 | ✅ PASS |

### 4.2 不合规入口测试（应返回 exit code 1）

| 入口 | Class | Exit Code | 原因 |
|------|-------|-----------|------|
| tools/subtask-orchestrate | P0 | 1 | hard_judge_not_connected |
| tools/callback-worker | P0 | 1 | hard_judge_not_connected |
| tools/auto-resume-orchestrator | P0 | 1 | guard/boundary/hard_judge 缺失 |
| tools/callback-handler-auto | P1 | 1 | guard_not_connected, boundary_not_checked |
| tools/session-start-recovery | - | 1 | not_registered |

### 4.3 验证结论

✅ hard-gate 能对不合规入口返回非零退出码

---

## 5. Registry 基线内容

### 5.1 Schema 定义

- `schema_version`: 1.0
- `entry_classes`: P0/P1/P2/P3 四级分类
- 每个入口包含 13 个字段：entry_id, entry_path, entry_type, class, owner, description, policy_bind_connected, guard_connected, hard_judge_connected, boundary_checked, preflight_covered, ci_covered, status

### 5.2 初始样本入口

- entry-001 ~ entry-008 共 8 个真实入口
- 覆盖编排、回调、恢复、治理等关键路径

---

## 6. 与虚构数据的对比

### 6.1 之前声称的数据（不存在）

| 指标 | 声称值 | 真实性 |
|------|--------|--------|
| 发现入口 | 244 | ❌ 不存在 |
| 已注册入口 | 14 | ❌ 不存在 |
| 未注册入口 | 232 | ❌ 不存在 |
| 不一致项 | 7 | ❌ 不存在 |

### 6.2 当前真实数据

| 指标 | 真实值 | 来源 |
|------|--------|------|
| 发现入口 | 234 | policy-entry-reconcile 扫描 |
| 已注册入口 | 8 | policy_entry_registry.yaml |
| 未注册入口 | 226 | reconcile 对账 |
| 不一致项 | 0 | reconcile 检查 |

---

## 7. 工具使用方法

### 7.1 入口扫描

```bash
# 全量扫描
python tools/policy-entry-reconcile --format json

# 仅 P0/P1
python tools/policy-entry-reconcile --only-p0-p1 --format json

# 文本格式
python tools/policy-entry-reconcile --format text
```

### 7.2 硬门禁检查

```bash
# 检查单个入口
python tools/governance-hard-gate tools/subtask-orchestrate

# 检查所有注册入口
python tools/governance-hard-gate --all

# JSON 输出
python tools/governance-hard-gate tools/subtask-orchestrate --json
```

---

## 8. 下一步建议

### 8.1 立即可执行

原任务单《历史入口库存治理与 Registry 收口》可以启动，Phase A-F 流程已具备基础设施。

### 8.2 Phase A 目标

修复 registry 中 P0 入口的治理缺陷：
- tools/subtask-orchestrate - 需补 hard_judge
- tools/callback-worker - 需补 hard_judge
- tools/auto-resume-orchestrator - 需补 guard/boundary/hard_judge

### 8.3 Phase B 目标

处理 23 个未注册 P0/P1 入口：
- 人工审查分类
- 决定纳管或排除
- 补录 registry

---

## 9. 验收标准

| 标准 | 状态 |
|------|------|
| 三个核心产物已落地 | ✅ 通过 |
| 不沿用 244/14/7 虚构数据 | ✅ 通过 |
| reconcile 能扫描真实数据 | ✅ 通过 |
| hard-gate 能返回非零退出码 | ✅ 通过 |
| registry 包含 schema 和样本入口 | ✅ 通过 |

---

**交付人**: Manager (Coordinator AI)
**交付时间**: 2026-03-16T21:30:00Z
**验收状态**: ✅ 完成
