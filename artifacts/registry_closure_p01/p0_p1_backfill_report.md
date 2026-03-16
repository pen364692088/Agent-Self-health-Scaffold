# Phase D: 应纳管入口补录与治理接入校正报告

**执行时间**: 2026-03-16T21:50:00Z
**状态**: ✅ 完成

---

## 1. Phase D 目标

将 13 个应纳管入口补录到 registry，并标记治理接入状态。

---

## 2. 补录入口清单

### 2.1 P0 入口（8 个新增）

| entry_id | 入口路径 | 治理状态 |
|----------|----------|----------|
| entry-009 | tools/session-start-recovery | ✅ 完整治理 |
| entry-010 | tools/agent-self-health-scheduler | ✅ 完整治理 |
| entry-011 | tools/callback-worker-doctor | ✅ 完整治理 |
| entry-012 | tools/session-recovery-check | ⚠️ 缺 hard_judge |
| entry-013 | tools/agent-recovery-verify | ⚠️ 缺 hard_judge |
| entry-014 | tools/gate-self-health-check | ✅ 完整治理 |
| entry-015 | tools/resume_readiness_calibration.py | ⚠️ 缺 guard/boundary/hard_judge |
| entry-016 | tools/resume_readiness_evaluator_v2.py | ⚠️ 缺 guard/boundary/hard_judge |

### 2.2 P1 入口（5 个新增）

| entry_id | 入口路径 | 治理状态 |
|----------|----------|----------|
| entry-017 | tools/subagent-completion-handler | ⚠️ 缺 hard_judge |
| entry-018 | tools/subagent-callback-hook | ⚠️ 缺 hard_judge |
| entry-019 | tools/callback-handler-auto-advance | ⚠️ 缺 guard/boundary/hard_judge |
| entry-020 | tools/spawn-with-callback | ❌ 待修复 (pending_fix) |
| entry-021 | tools/memory-scope-router | ❌ 待修复 (pending_fix) |

---

## 3. Registry 更新结果

### 3.1 版本

- registry_version: 1.0.0 → **1.1.0**
- total_entries: 8 → **21**

### 3.2 分类统计

| Class | 之前 | 之后 | 新增 |
|-------|------|------|------|
| P0 | 4 | 12 | +8 |
| P1 | 2 | 7 | +5 |
| P2 | 2 | 2 | 0 |
| P3 | 0 | 0 | 0 |
| **总计** | **8** | **21** | **+13** |

### 3.3 治理覆盖

| 指标 | 之前 | 之后 |
|------|------|------|
| policy_bind_connected | 6 | **17** |
| guard_connected | 4 | **13** |
| hard_judge_connected | 1 | **7** |
| boundary_checked | 4 | **13** |
| preflight_covered | 4 | **12** |
| ci_covered | 0 | 0 |

---

## 4. 治理缺口识别

### 4.1 缺少 hard_judge 的 P0 入口

| 入口 | 说明 |
|------|------|
| tools/subtask-orchestrate (原有) | 需补 hard_judge |
| tools/callback-worker (原有) | 需补 hard_judge |
| tools/auto-resume-orchestrator (原有) | 需补 guard/boundary/hard_judge |
| tools/session-recovery-check (新增) | 需补 hard_judge |
| tools/agent-recovery-verify (新增) | 需补 hard_judge |
| tools/resume_readiness_calibration.py (新增) | 需补 guard/boundary/hard_judge |
| tools/resume_readiness_evaluator_v2.py (新增) | 需补 guard/boundary/hard_judge |

### 4.2 待修复入口（status=pending_fix）

| 入口 | 说明 |
|------|------|
| tools/spawn-with-callback | 需补全套治理接入 |
| tools/memory-scope-router | 需补全套治理接入 |

---

## 5. 下一步

**进入 Phase E**: 非主链/排除项结构化留痕

目标：
- 为排除入口建立排除清单
- 记录排除理由

---

**交付人**: Manager (Coordinator AI)
**交付时间**: 2026-03-16T21:50:00Z
