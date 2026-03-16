# Phase D: Level 2 backlog 清空报告

**执行时间**: 2026-03-16T23:45:00Z
**状态**: ✅ 完成

---

## 1. Level 2 问题清单

| issue_id | 入口 | 类型 | 风险 |
|----------|------|------|------|
| L2-001 | tools/subtask-orchestrate | missing_hard_judge | 高 |
| L2-002 | tools/callback-worker | missing_hard_judge | 高 |
| L2-003 | tools/auto-resume-orchestrator | missing_governance | 高 |
| L2-004 | tools/session-recovery-check | missing_hard_judge | 中 |
| L2-005 | tools/agent-recovery-verify | missing_hard_judge | 中 |
| L2-006 | tools/resume_readiness_calibration.py | missing_governance | 低 |
| L2-007 | tools/resume_readiness_evaluator_v2.py | missing_governance | 低 |

---

## 2. 裁决结果

| issue_id | decision | owner | deadline | closure_status |
|----------|----------|-------|----------|----------------|
| L2-001 | accepted_with_deadline | orchestration | 2026-03-23 | accepted |
| L2-002 | accepted_with_deadline | orchestration | 2026-03-23 | accepted |
| L2-003 | accepted_with_deadline | recovery | 2026-03-23 | accepted |
| L2-004 | accepted_with_deadline | session | 2026-03-23 | accepted |
| L2-005 | accepted_with_deadline | recovery | 2026-03-23 | accepted |
| L2-006 | reclassify_with_reason | recovery | - | closed |
| L2-007 | reclassify_with_reason | recovery | - | closed |

---

## 3. 详细裁决

### 3.1 accepted_with_deadline (5 个)

**入口**:
- tools/subtask-orchestrate
- tools/callback-worker
- tools/auto-resume-orchestrator
- tools/session-recovery-check
- tools/agent-recovery-verify

**原因**:
- P0 入口缺少 hard_judge
- 需要设计并实现 hard_judge 机制
- 给予 7 天时间窗口

**补偿控制**:
- 已有 policy_bind 和 guard 保护
- 已有 boundary 检查
- 已在 governance_exceptions.yaml 中记录

### 3.2 reclassify_with_reason (2 个)

**入口**:
- tools/resume_readiness_calibration.py
- tools/resume_readiness_evaluator_v2.py

**原因**:
- 纯读取工具，无执行操作
- 不需要 hard_judge
- 应标记为 guard_not_required

**处理**: 已在 guard_gap_decision_report.md 中说明

---

## 4. 例外登记

所有 accepted_with_deadline 项已登记到 `contracts/governance_exceptions.yaml`：

```yaml
exceptions:
  - exception_id: "EXC-001"
    entry_id: "entry-003"
    expires_at: "2026-03-23T23:59:59Z"
  - exception_id: "EXC-002"
    entry_id: "entry-012"
    expires_at: "2026-03-23T23:59:59Z"
  - exception_id: "EXC-003"
    entry_id: "entry-013"
    expires_at: "2026-03-23T23:59:59Z"
  - exception_id: "EXC-005"
    entry_id: "entry-015"
    expires_at: "2026-03-23T23:59:59Z"
  - exception_id: "EXC-006"
    entry_id: "entry-016"
    expires_at: "2026-03-23T23:59:59Z"
```

---

## 5. 结论

**7 个 Level 2 问题全部处理完成**：
- 5 个 accepted_with_deadline（7 天限期）
- 2 个 reclassify_with_reason（已关闭）
- **0 个未处理** ✅

---

**交付人**: Manager (Coordinator AI)
**交付时间**: 2026-03-16T23:45:00Z
