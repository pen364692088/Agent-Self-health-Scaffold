# Agent-Self-health-Scaffold 最小闭环审计报告

**审计时间**: 2026-03-17T21:22:00Z
**审计结论**: 未达成最小闭环

---

## 1) 它当初要解决的真实问题是什么？

**不是**"单元测试过了，仍需用户自己反复手测、找 bug、补需求，交付前没有自验收闭环"。

**真正问题是**（依据 docs/OpenClaw项目任务书Agent-Self-health-Scaffold受约束的自愈执行内核.md）：

1. 系统坏了以后，不能自己接着做任务
2. 重启后，任务不会自动恢复
3. 长任务执行过程中，当前会话或进程一出问题就断链
4. 多 agent 协作不够可靠，子任务可能丢失、重复、卡住
5. 用户不希望靠人工补一句"继续"来触发恢复
6. 用户真正要的是"任务完成"，不是"会话看起来连续"

**核心目标**：让 OpenClaw 在异常、重启、上下文漂移、工具失败后，仍能自动检测偏差、执行受约束修复、验证结果、恢复任务推进。

---

## 2) 当前它在主流程里的最小决策点在哪里？

**已配置但未生效**：

- **入口**: `systemd user timer` → `agent-self-health-gate.timer`
- **服务**: `agent-self-health-gate.service`
- **调用链**: 
  ```
  systemd timer (每 5 分钟)
  → agent-self-health-scheduler --mode gate
  → gate-self-health-check --write --json
  → 检查 Gate A/B/C
  ```
- **配置文件**: `/home/moonlight/.config/systemd/user/agent-self-health-gate.service`

**问题**：调度器在运行，但日志显示 `"tasks": {}`，最近 2 天无实质性任务执行记录。

---

## 3) 是否已接入主链？

**状态**: 部分接入

| 项目 | 状态 | 证据 |
|------|------|------|
| systemd timer 配置 | ✅ 已配置 | `systemctl --user list-timers` 显示 timer 存在且运行中 |
| 调度器入口 | ✅ 存在 | `tools/agent-self-health-scheduler` 文件存在 |
| gate-self-health-check | ✅ 存在 | `tools/gate-self-health-check` 文件存在 |
| 实际任务执行 | ❌ 未生效 | 日志显示 `"tasks": {}`，最近 2 天无任务执行记录 |
| Gate 检查结果持久化 | ❌ 缺失 | `artifacts/self_health/gate_reports/` 目录刚创建，仅 1 个手动运行生成的报告 |

**调用链证据**:
```bash
$ systemctl --user list-timers
Tue 2026-03-17 16:26:29 CDT  agent-self-health-gate.timer  agent-self-health-gate.service

$ journalctl --user -u agent-self-health-gate.service --since "1 hour ago"
# 输出显示调度器在运行，但 tasks 字段为空
{
  "mode": "gate",
  "tasks": {},  # ← 空
  "started_at": "2026-03-17T21:21:29.203583+00:00",
  "completed_at": "2026-03-17T21:21:29.204212+00:00"
}
```

**卡点**: 调度器被调用但不执行实际任务（可能是冷却期逻辑导致跳过）。

---

## 4) 是否已启用？

**状态**: 配置已启用，但功能未生效

| 配置项 | 当前值 | 证据 |
|--------|--------|------|
| systemd timer | 启用 | `systemctl --user list-timers` 显示 active |
| timer 间隔 | 5 分钟 | timer 配置 |
| 调度器 mode | gate | service 配置 `--mode gate` |
| Gate A 状态 | **FAIL** | `capability_registry_missing` |
| Gate B 状态 | PARTIAL | `capability_degraded:CAP-CONTEXT_OVERFLOW_HANDLING` |
| Gate C 状态 | PASS | 无 issues |

**问题**: 虽然定时器在跑，但:
1. Gate A 检查失败（缺少 `POLICIES/AGENT_CAPABILITY_REGISTRY.md`）
2. 调度器日志显示无实际任务执行
3. 没有自动修复/恢复行为

---

## 5) 是否已有真实触发证据？

**状态**: **无真实触发证据**

### 检查项

| 检查项 | 结果 | 证据 |
|--------|------|------|
| 定时器运行 | ✅ | systemd timer active |
| 调度器被调用 | ✅ | journalctl 日志有记录 |
| 实际任务执行 | ❌ | `tasks: {}` 空 |
| Gate 检查通过 | ❌ | Gate A FAIL |
| 自动恢复行为 | ❌ | 无 recovery_apply 记录 |
| 任务续跑证据 | ❌ | 无真实任务自动续跑案例 |

### 关键证据缺失

1. **`artifacts/self_health/state/gate_check.last_run` 不存在**
   ```bash
   $ cat artifacts/self_health/state/gate_check.last_run
   No such file or directory
   ```

2. **调度器运行记录最后时间是 2026-03-15（2 天前）**
   ```bash
   $ tail artifacts/self_health/pilot/scheduler_runs.jsonl
   {"task": "recovery_summary", "timestamp": "2026-03-15T04:02:39.314136+00:00", ...}
   ```

3. **Gate A 要求的 registry 文件不存在**
   ```bash
   $ ls POLICIES/AGENT_CAPABILITY_REGISTRY.md
   No such file or directory
   ```

4. **gate_reports 目录为空（刚手动运行生成 1 个报告）**
   ```bash
   $ ls artifacts/self_health/gate_reports/
   gate_report_20260317-212208.json  # 手动运行生成的
   ```

**结论**: 只有框架在跑，没有产生实质性的健康检查/修复效果。

---

## 6) 是否达到最初设计目的？

**状态**: 未达到

### 对比原始目标

| 原始目标 | 当前状态 | 达成度 |
|----------|----------|--------|
| 重启后自动续跑 | ❌ 无证据 | 未达成 |
| 不需要人工补"继续" | ❌ 无自动恢复机制 | 未达成 |
| 任务真相独立于会话 | ⚠️ 有 ledger 结构，但未接入主流程 | 部分 |
| 受约束修复动作库 | ❌ 未实现 | 未达成 |
| Gate 验证自动通过 | ❌ Gate A FAIL | 未达成 |

### 是否减少用户手工验收负担？

**否**。当前系统只做了定时检查框架，没有：
- 自动恢复能力
- 自动修复能力
- 实际任务续跑证据

### 是否避免了"局部完成但未生效"？

**否**。SESSION-STATE.md 记录失真：
- 声称 "Gate A capability_registry_missing: ✅ 已修复"
- 实际 `POLICIES/AGENT_CAPABILITY_REGISTRY.md` 不存在
- `docs/GATE_A_CAPABILITY_REGISTRY_FIX.md` 不存在

---

## 强制输出格式

### A. 当前所在层

**构件层**

有定时检查框架、调度器、gate 工具，但：
- 未接入真实任务完成链路
- 未产生实际修复效果
- Gate A 检查失败

---

### B. 主链接入状态

**部分接入**

- 调用链：`systemd timer` → `agent-self-health-scheduler` → `gate-self-health-check`
- 证据：timer 配置存在，但实际任务执行为空
- 卡点：调度器被调用但不执行（冷却期逻辑）

---

### C. 启用状态

**配置已启用，功能未生效**

- 开关：systemd timer active
- 当前值：每 5 分钟运行
- 证据：Gate A FAIL，无实际修复行为

---

### D. 真实触发证据

**无真实触发证据**

- 是否有真实任务自动触发：否
- 样本数：0
- 证据路径：无
- 说明：定时器在跑，但没有产生实质性检查/修复效果

---

### E. 对设计目标的达成度

| 指标 | 结果 |
|------|------|
| 是否真正减少用户手工验收负担 | 否 |
| 是否避免了"局部完成但未生效" | 否（SESSION-STATE.md 记录失真） |
| **总结** | **未达成** |

---

### F. 下一步最小闭环动作

**修复 Gate A 缺失的 capability_registry，让定时健康检查至少能产出 PASS 结果**

```bash
# 1. 创建 POLICIES 目录
mkdir -p POLICIES

# 2. 创建 AGENT_CAPABILITY_REGISTRY.md
# 3. 重新运行 gate-self-health-check 验证 Gate A PASS
# 4. 确认 systemd timer 下次运行时产出实质性检查报告
```

**预期效果**: 执行后，Gate A 从 FAIL 变为 PASS，定时健康检查产出有效的 gate_report.json

---

## 审计结论

| 层级 | 状态 |
|------|------|
| 想法层 | ✅ 问题定义清晰 |
| 构件层 | ⚠️ 框架存在但不完整 |
| 接入层 | ⚠️ 接入定时器但未生效 |
| 启用层 | ❌ Gate A FAIL |
| 生效层 | ❌ 无真实触发证据 |
| 观察层 | ❌ 不适用（尚未生效） |

**离最小闭环还差**: 
1. Gate A 修复（capability_registry_missing）
2. 调度器实际执行任务（非空 tasks）
3. 至少 1 次真实自动恢复案例
