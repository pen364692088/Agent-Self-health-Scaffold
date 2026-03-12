
# OpenClaw 项目任务书

## 项目名称

**Agent-Self-health-Scaffold v2：受约束的自愈执行内核**

## 一、项目背景

近期 OpenClaw 暴露出的问题表面上分散，实质上高度同源：

* gateway / agent 重启后，任务不会自动续跑，仍需用户说“继续”
* 在 agent 的 exec 内执行 restart，会导致正在执行的 gateway/exec 链路被 SIGTERM 中断
* session restore / compaction / ordering conflict 出问题时，会直接影响任务推进
* manager → coder → audit 虽能协作，但缺少稳定的持久化、恢复、重试、幂等机制
* 当前系统已有较多 guardrail / shadow / watcher / report / checklist，但主执行链仍脆弱

结论：
**当前系统的问题核心不是“看不见故障”，而是“故障后不能自动恢复并继续完成任务”。**

---

## 二、用户真实抱怨

请始终围绕以下真实问题设计，不要跑偏到“更多审计报表”：

1. 系统坏了以后，不能自己接着做
2. 重启后，任务不会自动恢复
3. 长任务执行过程中，当前会话或进程一出问题就断链
4. 多 agent 协作不够可靠，子任务可能丢失、重复、卡住
5. 用户不希望靠人工补一句“继续”来触发恢复
6. 用户真正要的是“任务完成”，不是“会话看起来连续”

---

## 三、系统当前行为

当前系统已经具备的东西，大多属于**观察层 / 保护层**：

* Gate A / Gate B / Gate C
* shadow / watcher / daily checklist / probe / incident capture
* session continuity / compaction safeguard / ordering fix
* write-guard / heartbeat / cleanup
* shared memory / sync-shared-memory
* manager / coder / audit 的基础协作链

但当前系统仍存在以下关键缺口：

* 任务状态真相层不独立
* 任务恢复依赖会话恢复，而非任务恢复
* restart 仍可能在当前执行链内发生
* 子任务无统一 durable orchestration
* transcript 与 task truth 混在一起
* 自修复能力缺乏约束边界、缺乏统一修复动作库

---

## 四、最小决策点

本项目的最小关键决策点只有一个：

> **任务状态是否独立于聊天消息和当前进程而存在。**

如果答案是否定的，那么系统再多 watcher、guardrail、shadow，也仍然会不断重复以下问题：

* 重启后不能续跑
* 会话坏了任务也坏
* compaction/ordering 问题影响真实执行
* 子任务状态不清
* 需要人工唤醒恢复

---

## 五、项目核心目标

将 Agent-Self-health-Scaffold 从“健康检查脚手架”升级为：

> **一个让 OpenClaw 在异常、重启、上下文漂移、工具失败后，仍能自动检测偏差、执行受约束修复、验证结果、恢复任务推进的自愈执行内核。**

核心目标拆分为四句话：

1. **任务是真相，会话只是展示**
2. **重启后恢复任务，而不是恢复聊天**
3. **修复动作必须受约束、可验证、可回滚**
4. **系统必须能在无人补一句“继续”的情况下自动续跑**

---

## 六、主解决链

这是主链，不要被保险链喧宾夺主。

### 主解决链必须打通的四个核心部件

1. **Task Ledger**

   * 持久记录 task/run/step/retry/repair/gate/completion 事件
   * 成为唯一真相层

2. **Resume Engine / Recovery Orchestrator**

   * 系统启动后自动扫描未完成 run
   * 判断是否 resume / retry / failover / abandon
   * 自动推进，不等待用户说“继续”

3. **Out-of-band Restart Executor**

   * 禁止 agent 在当前 exec 链内直接 restart 自己
   * restart 改为带外执行
   * restart 后自动触发 recovery scan

4. **Event-to-Transcript Rebuilder**

   * transcript 从 ledger 重建
   * session / compaction / ordering 出问题时，不再污染任务真相

---

## 七、保险链

以下内容保留，但全部降级为辅助层，不得代替主解决链：

* shadow metrics
* watcher / probe
* checklist
* incident capture / diff
* audit report
* health dashboard
* guardrail rules
* cleanup / heartbeat

原则：

> **保险链的职责是发现和解释问题，不是替代 durable execution。**

---

## 八、如果一周后问题还会反复出现，说明哪里没打中

若本项目完成后，一周内仍反复出现以下现象：

* 重启后仍要人工说“继续”
* session 出问题后任务仍中断
* 子任务丢失或重复执行
* message ordering / compaction 仍影响真实任务推进
* 依然只能靠守卫和人工补救收口

则说明：

> **本项目仍然停留在 observability / guardrail 层，没有真正打中 task durability / auto recovery 主链。**

---

# 九、架构目标

## 目标架构：六层自愈执行内核

### 1. Task Control Plane

定义期望状态（desired state）

职责：

* TaskSpec
* Run policy
* Gate policy
* Allowed repair set
* Success criteria
* Timeout / retry policy

作用：

* 明确“这个任务最终要达成什么”
* 重启后系统按目标状态继续，而不是按上下文猜测

---

### 2. Run Ledger

唯一真相层（append-only）

记录事件：

* task_created
* run_started
* step_started
* step_heartbeat
* step_succeeded
* step_failed
* retry_scheduled
* repair_proposed
* repair_applied
* gate_passed
* gate_failed
* transcript_rebuilt
* run_completed
* run_abandoned

原则：

* append-only
* 可恢复
* 可审计
* transcript 由此派生，不反向作为真相

---

### 3. Reconciler

持续比较 desired state 与 actual state

职责：

* 读取 TaskSpec
* 读取 RunLedger 当前状态
* 识别 drift
* 计算最小动作
* 执行动作后重新观察

目标：

* 借鉴 controller/reconcile 模式
* 让恢复行为变成系统循环，而不是偶发脚本

---

### 4. Supervisor Tree

故障分层治理

建议分层：

* **L0 进程层**：gateway / worker / watcher / queue consumer
* **L1 任务层**：manager run / coder run / audit run
* **L2 步骤层**：某次 patch、测试、sync、compaction、handoff

每层策略不同：

* step 失败：retry / fallback
* run 失败：resume from last-good-step
* process 失败：external restart + recovery scan
* repeated failure：escalate / safe-stop

---

### 5. Repair Library

受约束修复动作库

只允许执行白名单修复动作，不允许“自由发挥式自修复”。

首批修复动作建议：

* resume-from-last-good-step
* rebuild-transcript-from-ledger
* requeue-missing-child
* out-of-band-restart-gateway
* repair-message-order
* recover-stalled-run
* restore-step-pointer
* patch-from-template-and-test
* promote-shadow-rule-to-enforced
* rollback-bad-repair

要求：

* 每个 repair action 必须定义

  * 适用条件
  * 风险等级
  * 前置检查
  * 执行器
  * 验证器
  * 回滚器

---

### 6. Verification & Rollback Layer

所有修复动作都必须验证，不通过必须回滚或降级

验证层至少包括：

* contract validity
* syntax/config validity
* e2e continuation
* no duplicate execution
* health check
* gate result
* rollback if worse

---

# 十、明确非目标

以下方向本阶段不要继续膨胀：

1. 不以“更多 dashboard / report”为主要产出
2. 不以“更多 shadow 统计”为主要成果
3. 不以“更复杂的 prompt 纪律”替代持久执行
4. 不把“会话连续性”误当成“任务连续性”
5. 不允许 agent 无边界自动修改核心代码并直接提交
6. 不允许把 restart 继续放在当前 exec 调用链内处理

---

# 十一、P0 / P1 / P2 里程碑

## P0：打通主链，做到真正自动续跑

这是最高优先级，必须先完成。

### P0.1 Task Ledger

交付物：

* `core/task-ledger/`
* ledger schema
* append-only event writer
* event reader / query API
* run state materializer

要求：

* 能从 ledger 推导 run 当前状态
* 能恢复 step pointer / retry pointer / last-good-step
* 不依赖 transcript 判断任务进度

### P0.2 Recovery Orchestrator

交付物：

* `core/recovery-orchestrator/`
* boot scan
* stalled run detector
* resume policy engine
* retry/backoff policy

要求：

* gateway / worker 重启后自动扫描未完成 run
* 自动恢复 eligible run
* 不要求用户补“继续”

### P0.3 Out-of-band Restart Executor

交付物：

* `runtime/restart-executor/`
* restart intent model
* external restart runner
* restart completion hook

要求：

* agent 内禁止直接 restart 当前 gateway 进程
* restart 改由带外执行
* restart 完成后自动触发 recovery scan

### P0.4 Event-to-Transcript Rebuilder

交付物：

* `runtime/transcript-rebuilder/`
* transcript materializer
* message order normalizer
* rebuild tests

要求：

* transcript 从 ledger 重建
* session/compaction/order 错误不再影响任务真相
* 修复后对话层仍可阅读、可追踪

### P0.5 Durable Subtask Orchestration

交付物：

* `runtime/job-orchestrator/`
* parent/child job model
* retry/backoff
* dependency DAG
* idempotency key support

要求：

* manager / coder / audit 全部变成正式 run/job
* 父任务等待子任务完成
* 已完成子任务不会因重启重复跑

---

## P1：做受约束自修复闭环

### P1.1 Repair Library

交付物：

* `core/repair-library/`
* repair action registry
* action validator
* action rollback hooks

### P1.2 Drift Classification

交付物：

* `core/drift-detector/`
* fault code taxonomy
* diagnosis routing

建议故障码首版：

* TASK_STALLED
* PROCESS_RESTARTED
* STEP_POINTER_LOST
* TRANSCRIPT_CORRUPTED
* CHILD_JOB_MISSING
* DUPLICATE_EXECUTION_RISK
* REPAIR_FAILED
* ORDER_CONFLICT_DETECTED

### P1.3 Gate-verified Repair Pipeline

交付物：

* `pipelines/repair-runner/`
* repair proposal → execution → verification → commit/rollback

要求：

* 高风险修复不能直接生效
* 先跑 Gate A/B/C
* 不通过则回滚或降级

---

## P2：进阶自治与学习

### P2.1 Repeated Failure Memory

对高频失败模式形成可复用修复策略

### P2.2 Adaptive Repair Policy

根据历史成功率调整 repair priority / fallback order

### P2.3 Long-horizon Self-healing Analytics

衡量系统是否真正减少人工恢复

---

# 十二、建议目录结构

```text
Agent-Self-health-Scaffold/
├─ core/
│  ├─ task-ledger/
│  ├─ task-spec/
│  ├─ reconciler/
│  ├─ supervisor-tree/
│  ├─ repair-library/
│  ├─ drift-detector/
│  └─ state-materializer/
├─ runtime/
│  ├─ recovery-orchestrator/
│  ├─ restart-executor/
│  ├─ transcript-rebuilder/
│  ├─ job-orchestrator/
│  └─ heartbeat/
├─ pipelines/
│  ├─ repair-runner/
│  ├─ gate-runner/
│  └─ rollback-runner/
├─ schemas/
│  ├─ task-spec.schema.json
│  ├─ ledger-event.schema.json
│  ├─ repair-action.schema.json
│  └─ run-state.schema.json
├─ tests/
│  ├─ ledger/
│  ├─ recovery/
│  ├─ restart/
│  ├─ transcript/
│  ├─ repair/
│  ├─ orchestration/
│  └─ e2e/
├─ docs/
│  ├─ ARCHITECTURE.md
│  ├─ REPAIR_ACTIONS.md
│  ├─ FAILURE_TAXONOMY.md
│  ├─ RECOVERY_POLICY.md
│  └─ OPERATION_RUNBOOK.md
└─ artifacts/
   ├─ recovery_evidence/
   ├─ repair_trials/
   ├─ gate_reports/
   └─ e2e_runs/
```

---

# 十三、关键数据结构建议

## 1. TaskSpec

```json
{
  "task_id": "string",
  "goal": "string",
  "desired_state": "string",
  "success_criteria": ["string"],
  "gates_required": ["A", "B", "C"],
  "allowed_repairs": ["resume-from-last-good-step", "rebuild-transcript-from-ledger"],
  "retry_policy": {
    "max_attempts": 3,
    "backoff": "exponential"
  },
  "timeout_policy": {
    "soft_timeout_sec": 1800,
    "hard_timeout_sec": 7200
  }
}
```

## 2. LedgerEvent

```json
{
  "event_id": "uuid",
  "task_id": "string",
  "run_id": "string",
  "parent_run_id": "string|null",
  "step_id": "string|null",
  "type": "step_started",
  "ts": "iso8601",
  "payload": {},
  "idempotency_key": "string"
}
```

## 3. RunState

```json
{
  "task_id": "string",
  "run_id": "string",
  "status": "running",
  "current_step": "repair-runner",
  "last_good_step": "coder-tests-passed",
  "pending_children": ["audit-run-001"],
  "retry_count": 1,
  "last_heartbeat": "iso8601",
  "recovery_status": "eligible"
}
```

## 4. RepairAction

```json
{
  "action_id": "resume-from-last-good-step",
  "risk_level": "low",
  "preconditions": ["run_is_stalled", "last_good_step_exists"],
  "executor": "resume_executor",
  "validator": "continuation_validator",
  "rollback": "rollback_to_last_good_checkpoint"
}
```

---

# 十四、首批 E2E 场景

必须优先覆盖真实痛点，不要先写漂亮但无关的测试。

## E2E-01：gateway 重启后自动续跑

目标：

* 运行中的任务在 gateway 重启后自动恢复
* 不需要用户补“继续”

## E2E-02：step 中断后从 last-good-step 恢复

目标：

* 中间步骤失败后从最近稳定点恢复
* 不重复执行已经完成的 step

## E2E-03：session/order/transcript 损坏后任务不丢

目标：

* transcript 重建成功
* 任务仍按 ledger 正常推进

## E2E-04：子任务丢失后自动补投递

目标：

* parent/child DAG 可恢复
* 丢失子任务可重新入队
* 已完成子任务不重复跑

## E2E-05：高风险 repair 不通过 Gate 自动回滚

目标：

* repair proposal 失败后不污染主链
* run 回到安全状态

## E2E-06：无人值守长任务跨重启完成

目标：

* 跨重启、跨会话、跨 watcher 中断后仍可完成 end-to-end 任务

---

# 十五、Gate 验收标准

## Gate A：Contract / Schema / Safety

通过条件：

* TaskSpec / LedgerEvent / RepairAction schema 稳定
* repair action 全部有前置条件、验证器、回滚器
* restart 不再允许发生于当前 exec 自杀链内

## Gate B：E2E Continuity

通过条件：

* 至少通过 E2E-01 ~ E2E-06
* 自动续跑成功率达到可量化阈值
* 无重复执行污染
* 无人工“继续”依赖

## Gate C：Preflight / Operational Readiness

通过条件：

* recovery scan 可重复运行
* repeated restart 不造成 run 混乱
* transcript rebuild 对主链无副作用
* 关键故障码都能被正确分类并进入修复链

---

# 十六、成功指标

本项目成功不是看产出多少报告，而是看以下指标是否下降/提升：

## 核心指标

* 人工“继续”触发次数
* 重启后未自动恢复的 run 数
* 因 transcript/session/order 问题导致的任务中断数
* 子任务丢失/重复执行数
* 自修复成功率
* 修复后 Gate 通过率
* 从故障到恢复推进的平均时间

## 成功标准建议

* 重启后自动续跑覆盖率显著提高
* 用户手动补“继续”需求接近 0
* 会话/排序问题不再直接打断任务
* 多 agent 任务树在重启后仍可恢复
* repair pipeline 对高风险修复具备可验证可回滚能力

---

# 十七、执行约束

OpenClaw 执行本项目时，必须遵守以下约束：

1. 不要先做新的 dashboard、报表、观察窗美化
2. 不要先做更多 shadow 指标
3. 不要把会话恢复当作任务恢复
4. 不要用 prompt 规则代替 durable state
5. 不要允许 agent 无约束直接自改核心执行逻辑并生效
6. 任何 restart 相关方案，必须优先解决“exec 自杀链”问题
7. 所有新增能力必须优先围绕真实痛点验证
8. 本项目先实现最小闭环，再做泛化和美化

---

# 十八、推荐执行顺序

建议按以下顺序推进，不要乱序：

1. 产出 Architecture / TaskSpec / Ledger schema
2. 实现 Task Ledger + State Materializer
3. 实现 Recovery Orchestrator
4. 实现 Out-of-band Restart Executor
5. 实现 Transcript Rebuilder
6. 接入 Durable Subtask Orchestration
7. 实现 Repair Library
8. 接入 Gate-verified Repair Pipeline
9. 跑 E2E-01 ~ E2E-06
10. 输出 evidence pack 与 handoff

---

# 十九、最终交付要求

最终必须交付以下产物：

1. `ARCHITECTURE.md`
2. `TASK_SPEC.md`
3. `RUN_LEDGER_SCHEMA.json`
4. `RECOVERY_POLICY.md`
5. `REPAIR_ACTIONS.md`
6. `FAILURE_TAXONOMY.md`
7. `OUT_OF_BAND_RESTART_DESIGN.md`
8. `TRANSCRIPT_REBUILDER_DESIGN.md`
9. `E2E_TEST_MATRIX.md`
10. `FINAL_GATE_REPORT.md`
11. `HANDOFF_FOR_NEXT_SESSION.md`

---

# 二十、给 OpenClaw 的一句话指令

> 请将 Agent-Self-health-Scaffold v2 聚焦为“受约束的自愈执行内核”，优先解决任务真相独立、重启后自动续跑、带外重启、事件到 transcript 重建、子任务 durable orchestration 五条主链，不要把工作重心继续放在报表、shadow、watcher 美化上；所有设计与实现必须围绕“坏了能发现、能修复、还能继续把任务做完”这一真实目标展开。

