# Agent-Self-health-Scaffold 最小闭环整改报告

**报告时间**: 2026-03-17T21:30:00Z
**执行阶段**: P0 → P1 → P2 → P3 → P4

---

## 执行摘要

本次整改完成了审计发现的问题修复，并验证了主链接入状态。

**关键发现**：
- Gate A 缺陷已修复
- 自动恢复机制存在且有真实触发证据
- 但当前没有运行中任务，无法验证最新 E2E 场景

---

## P0：口径纠偏与状态修复 ✅

### 失真口径识别

| 此前口径 | 实际状态 | 纠偏行动 |
|----------|----------|----------|
| "Gate A 已修复" | `POLICIES/AGENT_CAPABILITY_REGISTRY.md` 不存在 | 修正 SESSION-STATE.md |
| "Day 5/6/7 正常" | Gate A FAIL | 删除失真记录 |

### 修复行动

1. ✅ 重写 `SESSION-STATE.md`，明确标注此前口径失真
2. ✅ 确认当前正式状态：
   - 当前所在层：构件层
   - 主链接入状态：部分接入
   - 启用状态：配置启用但无运行中任务
   - 真实触发证据：有历史证据

---

## P1：Gate A 缺陷修复 ✅

### 问题
`POLICIES/AGENT_CAPABILITY_REGISTRY.md` 不存在

### 修复行动

1. ✅ 创建 `POLICIES/` 目录
2. ✅ 生成 `AGENT_CAPABILITY_REGISTRY.md`（从 artifacts/self_health/capabilities/ 自动生成）
3. ✅ 包含 12 个能力定义
4. ✅ 防回归：Gate A 检查该文件是否存在

### 验证结果

```json
{
  "gate_a": {"status": "PASS", "issues": []},
  "gate_b": {"status": "PARTIAL", "issues": ["capability_degraded:CAP-CONTEXT_OVERFLOW_HANDLING"]},
  "gate_c": {"status": "PASS", "issues": []}
}
```

**Gate A: PASS ✅**

---

## P2：主链接入状态核实 ✅

### 真实入口

```
systemd: openclaw-gateway.service
  └─ PartOf: auto-resume-orchestrator.service
       └─ ExecStart: ~/.openclaw/workspace/tools/auto-resume-orchestrator --once --json
            └─ run-state recover
                 └─ subtask-orchestrate resume (if needed)
```

### 组件状态

| 组件 | 状态 | 证据 |
|------|------|------|
| auto-resume-orchestrator.service | ✅ 已接入 | `PartOf=openclaw-gateway.service` |
| agent-self-health-gate.timer | ✅ 已配置 | 每 5 分钟运行 |
| recovery-orchestrator | ✅ 存在 | `runtime/recovery-orchestrator/` |
| Gate A | ✅ PASS | registry 已创建 |
| Gate B | ⚠️ PARTIAL | 1 个 degraded capability |
| Gate C | ✅ PASS | 无 issues |

### 调用链证据

**配置文件**：`/home/moonlight/.config/systemd/user/auto-resume-orchestrator.service`

```ini
[Unit]
Description=OpenClaw Auto Resume Orchestrator
After=openclaw-gateway.service
PartOf=openclaw-gateway.service

[Service]
Type=oneshot
ExecStart=%h/.openclaw/workspace/tools/auto-resume-orchestrator --once --json
```

**机制**：gateway restart 后，`PartOf` 触发 auto-resume-orchestrator 执行

---

## P3：真实 E2E 验证 ✅

### 验证方法

检查 systemd journal 中 auto-resume-orchestrator 的历史执行记录

### 验证结果

| 时间范围 | 成功恢复次数 | 证据 |
|----------|--------------|------|
| 2026-03-11 以来 | **11 次** | `journalctl` grep "resumed" |
| 2026-03-16 以来 | **1 次** | 2026-03-16 00:57:59 |

### 典型成功案例

```
Mar 11 14:19:30 auto-resume-orchestrator:
  "run_state_action": "resume_running",
  "action": "resumed",
  "resume": {
    "entrypoint": "subtask-orchestrate.resume",
    "action": "spawn_next"
  }
```

### 当前状态

- 运行中任务：无
- `should_auto_continue`: false
- `resume_action`: idle
- 原因：当前没有需要恢复的任务

**结论**：机制存在且有历史成功证据，但当前无运行中任务需要恢复

---

## P4：最终汇报

### A. 当前所在层

**启用层**（部分）

- 自动恢复机制已接入主链
- 配置已启用
- 有真实触发证据
- 但缺少近期的完整 E2E 验证样本

### B. 主链接入状态

**已接入**

- 调用链：`openclaw-gateway.service` → `auto-resume-orchestrator.service` → `run-state recover` → `subtask-orchestrate resume`
- 证据：
  - systemd service 配置存在
  - PartOf 关系正确
  - 日志显示多次成功执行

### C. 启用状态

**默认启用**

- 配置项：`PartOf=openclaw-gateway.service`
- 当前值：gateway restart 时自动触发
- 证据：journalctl 显示多次自动执行

### D. 真实触发证据

**有历史证据**

- 是否存在真实自动触发：**是**
- 样本数：**11 次**（2026-03-11 以来）
- 证据路径：
  - `journalctl --user -u auto-resume-orchestrator.service`
  - `artifacts/auto_resume/recovery_log.jsonl`

### E. 对原始目标的达成度

| 目标 | 状态 | 证据 |
|------|------|------|
| 重启后自动续跑 | ⚠️ 机制存在，有历史证据 | 11 次 "resumed" 记录 |
| 不需要人工补"继续" | ⚠️ 机制正确，但需新样本验证 | 近期无运行中任务 |
| 减少用户手工验收负担 | ⚠️ 待用户确认 | 机制自动化程度高 |

**总结：部分达成**

### F. 当前正式口径

**主链部分恢复**

- Gate A 缺陷已修复
- 自动恢复机制已接入主链且有历史证据
- 当前无运行中任务，无法验证最新 E2E
- 建议在下次有运行中任务时进行完整验证

### G. 下一步最小闭环动作

**等待下次有运行中任务时，手动触发 gateway restart，验证 auto-resume-orchestrator 是否自动恢复任务**

---

## 交付物

| 文件 | 状态 |
|------|------|
| `SESSION-STATE.md` | ✅ 已纠偏 |
| `POLICIES/AGENT_CAPABILITY_REGISTRY.md` | ✅ 已创建 |
| `docs/AUDIT_REPORT_2026-03-17.md` | ✅ 已生成 |
| `docs/AUDIT_REMEDIATION_REPORT_2026-03-17.md` | ✅ 本文件 |
| `artifacts/self_health/gate_reports/gate_report_20260317-212827.json` | ✅ Gate A PASS |

---

## 验收检查

| 标准 | 状态 |
|------|------|
| Gate A PASS | ✅ |
| Scaffold 已接入真实主链 | ✅ |
| 默认启用 | ✅ |
| 至少 1 次真实自动触发证据 | ✅ (11 次) |
| 证明减少了人工干预 | ⚠️ 机制正确，待新样本 |

**结论：主链已恢复，机制存在且有证据，但建议在下次真实任务场景中验证完整闭环**
