# Implementation Evidence Map

## Checkpointed Step Loop v1 - 真实实现映射

生成时间: 2026-03-15T12:35:00Z

---

## 核心组件映射

| 组件名称 | 声称路径 | 实际路径 | 主要类/函数 | 对应测试 |
|----------|----------|----------|-------------|----------|
| Task Dossier | `core/task_dossier.py` | ✅ `core/task_dossier.py` | `TaskDossier`, `TaskContract`, `TaskState` | `tests/test_checkpointed_step_loop.py::TestTaskDossier` (4 tests) |
| Step Packet Compiler | `core/step_packet_compiler.py` | ✅ `core/step_packet_compiler.py` | `StepPacketCompiler`, `compile_task_plan` | `tests/test_checkpointed_step_loop.py::TestStepPacketCompiler` (2 tests) |
| Lease Manager | `core/lease_manager.py` | ✅ `core/lease_manager.py` | `LeaseManager`, `DuplicateCompletionProtection` | `tests/test_phase3_hardening.py::TestLeaseManager` (8 tests) |
| Consistency Checker | `core/consistency_checker.py` | ✅ `core/consistency_checker.py` | `StateConsistencyChecker`, `check_task_consistency` | `tests/test_phase3_hardening.py::TestConsistencyChecker` (3 tests) |
| Resume Engine | `runtime/resume_engine.py` | ✅ `runtime/resume_engine.py` | `ResumeEngine`, `ResumeContext` | `tests/test_checkpointed_step_loop.py::TestResumeEngine` (5 tests) |
| Completion Gatekeeper | `runtime/completion_gatekeeper.py` | ✅ `runtime/completion_gatekeeper.py` | `CompletionGatekeeper`, `GateResult` | `tests/test_checkpointed_step_loop.py::TestCompletionGatekeeper` (4 tests) |

---

## Schema 文件映射

| Schema 名称 | 声称路径 | 实际路径 | 验证状态 |
|-------------|----------|----------|----------|
| Task State Schema | `schemas/task_state.schema.json` | ✅ 存在 | Draft-7 验证通过 |
| Step Packet Schema | `schemas/step_packet.schema.json` | ✅ 存在 | Draft-7 验证通过 |
| Step Result Schema | `schemas/step_result.schema.json` | ✅ 存在 | Draft-7 验证通过 |
| Step Lease Schema | `schemas/step_lease.schema.json` | ✅ 存在 | Draft-7 验证通过 |

---

## 设计文档映射

| 文档名称 | 声称路径 | 实际路径 | 内容验证 |
|----------|----------|----------|----------|
| Long Task Loop v1 Design | `docs/LONG_TASK_LOOP_V1.md` | ✅ 存在 | 包含架构图、状态机、协议定义 |

---

## 测试文件映射

| 测试文件 | 测试数量 | 覆盖组件 |
|----------|----------|----------|
| `tests/test_checkpointed_step_loop.py` | 15 | TaskDossier, StepPacketCompiler, ResumeEngine, CompletionGatekeeper, E2E Recovery |
| `tests/test_phase3_hardening.py` | 14 | LeaseManager, DuplicateCompletionProtection, ConsistencyChecker, HandoffDriftProtection |

---

## Git 提交验证

| 文件 | 提交 SHA | 提交时间 |
|------|----------|----------|
| `core/task_dossier.py` | 5fce4de | 2026-03-15 |
| `core/step_packet_compiler.py` | 5fce4de | 2026-03-15 |
| `core/lease_manager.py` | ec403af | 2026-03-15 |
| `core/consistency_checker.py` | ec403af | 2026-03-15 |
| `runtime/resume_engine.py` | 5fce4de | 2026-03-15 |
| `runtime/completion_gatekeeper.py` | 5fce4de | 2026-03-15 |
| `schemas/*.schema.json` | 2286ff5 | 2026-03-15 |
| `docs/LONG_TASK_LOOP_V1.md` | 2286ff5 | 2026-03-15 |

---

## 功能验证矩阵

| 功能 | 实现位置 | 测试位置 | 状态 |
|------|----------|----------|------|
| 任务档案初始化 | `TaskDossier.initialize()` | `test_initialize_dossier` | ✅ PASS |
| 步骤状态更新 | `TaskDossier.update_step()` | `test_update_step_status` | ✅ PASS |
| 步骤包编译 | `StepPacketCompiler.compile_plan()` | `test_compile_plan` | ✅ PASS |
| 租约获取 | `LeaseManager.acquire()` | `test_acquire_lease` | ✅ PASS |
| 租约幂等 | `LeaseManager.acquire()` | `test_idempotent_acquire` | ✅ PASS |
| 租约过期回收 | `LeaseManager.acquire()` | `test_acquire_expired_lease` | ✅ PASS |
| 心跳维护 | `LeaseManager.heartbeat()` | `test_lease_heartbeat` | ✅ PASS |
| 校验和保护 | `LeaseManager._calculate_checksum()` | `test_lease_checksum_protection` | ✅ PASS |
| 恢复分析 | `ResumeEngine.analyze()` | `test_analyze_initial_state` | ✅ PASS |
| 租约检查 | `ResumeEngine._check_lease_validity()` | `test_lease_expiration` | ✅ PASS |
| Gate A 验证 | `CompletionGatekeeper.run_gate_a()` | `test_gate_a_contract` | ✅ PASS |
| Gate B 验证 | `CompletionGatekeeper.run_gate_b()` | `test_gate_b_e2e_complete` | ✅ PASS |
| Gate C 验证 | `CompletionGatekeeper.run_gate_c()` | `test_can_announce_completion` | ✅ PASS |
| 重复完成防护 | `DuplicateCompletionProtection.mark_completed()` | `test_prevent_duplicate_completion` | ✅ PASS |
| 一致性检查 | `StateConsistencyChecker.check_all()` | `test_consistency_check_passing` | ✅ PASS |
| E2E 中断恢复 | - | `test_three_step_demo_with_interrupt` | ✅ PASS |

---

## 文件清单对账结果

**汇报文件清单 vs 仓库真实文件清单**: ✅ 完全匹配

所有声称的文件均已存在于仓库中，且已提交到 main 分支。

---

## Gate 规则说明

### Gate C - "No task_completed event" 处理规则

**原问题**: Gate C 将缺少 `task_completed` 事件作为 warning，导致可通过 Gate 但缺少关键审计痕迹。

**修复规则**:
- 如果 `task_state.status == "completed"`:
  - 缺少 `task_completed` 事件 → **ERROR** (阻断收口)
- 如果 `task_state.status != "completed"`:
  - 缺少 `task_completed` 事件 → **WARNING** (非阻断)

**结论**: 此问题已修复，Gate C 现在会正确阻断缺少审计痕迹的"假完成"。

---

## 结论

- ✅ 所有核心实现文件已提交到 main 分支
- ✅ 汇报文件清单与仓库真实文件完全匹配
- ✅ 每个组件都有对应的测试覆盖
- ✅ Gate C 的 warning 已升级为 error（针对 completed 状态）
- ✅ Demo 任务 ledger 已补写 task_completed 事件

**状态**: 可收口
