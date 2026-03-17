# Self-Health v2 观察期执行方案（规则锁定版）

**生效时间**: 2026-03-17T22:20:00Z
**基线 Tag**: `self-health-v2-obs-day0`
**观察周期**: 2026-03-17 ~ 2026-03-24（7 天）
**版本锁定**: 当前核心恢复链版本

---

## 一、观察期目标

验证"最小闭环达成"在真实生产环境中的稳定性，收集足够样本以判定：
- **Promote**: 正式毕业，进入稳定运维期
- **Extend**: 延长观察期，收集更多样本
- **Rollback**: 回滚修复，重新进入开发期

---

## 二、Baseline 与样本分离规则

### ⚠️ 强制规则：历史样本不计入本轮毕业统计

| 项目 | 说明 |
|------|------|
| 历史样本数 | 11 次 |
| 历史成功率 | 100% |
| 历史红线违规 | 0 |
| **用途** | **Baseline only，不计入本轮 Promote 样本统计** |

> **明确规则**：历史 11 次样本仅用于 baseline 展示，不计入 2026-03-17 ~ 2026-03-24 观察窗口内的 Promote 样本统计。
> Promote 要求的 `样本总数 ≥ 10`，仅统计观察窗口内新增有效样本。

---

## 三、恢复机会定义（收紧版）

### 什么是"恢复机会"

gateway restart 发生时，存在至少 1 个真实任务，且该任务满足以下全部条件：

| 条件 | 说明 |
|------|------|
| 状态合法 | `running` / `waiting` / `recoverable` |
| 未完成 | 任务未到达 completed 状态 |
| 未封账 | 未生成最终 receipt |
| 未 receipt | 未写入 final/receipt.json |
| 允许 resume | 当前步骤的 auto_resume ≠ false |

**只有满足以上全部条件时，才计入一次"恢复机会"分母。**

### 什么不计入分母

| 场景 | 原因 |
|------|------|
| 已完成但状态写回滞后 | 非真实恢复需求 |
| 已封账/已 receipt | 任务已闭环 |
| 不允许 resume 的步骤 | 明确标记不可恢复 |
| 表面 running、实际不可恢复 | 状态不一致 |
| 无任务时的 restart | 无恢复需求 |
| mock / 单测 / 空载 restart | 非真实场景 |

---

## 四、样本来源分层

### 自然样本

真实使用过程中自然发生的 gateway restart 恢复样本。

特征：
- 用户或系统自然触发的 restart
- 非人为演练

### 主动演练样本

在存在真实运行中任务时，按观察方案人为触发 gateway restart 的恢复样本。

特征：
- 有真实任务在运行
- 人为触发的 restart
- 目的是验证恢复能力

### 样本有效性条件（两类样本都必须满足）

| 条件 | 说明 |
|------|------|
| 真实任务 | 非 mock / 单测 |
| gateway restart | 有重启动作 |
| auto-resume 自动触发 | 无人工启动恢复 |
| 任务推进 | 恢复后状态正确推进 |
| 无人工补"继续" | 全程自动化 |
| 证据完整 | 有日志/状态文件 |

### 无效样本（一律不计入）

- mock / 单测 / 演示场景
- 空载 restart（无任务）
- 无任务 restart
- 人工启动恢复（非 auto-resume）

---

## 五、版本冻结规则

### 版本锁定

本观察期绑定当前核心恢复链版本。

### 核心路径

以下路径变更后，观察期必须重置或重新定义 baseline 与样本窗口：

| 路径 | 文件 |
|------|------|
| auto-resume-orchestrator | `~/.openclaw/workspace/tools/auto-resume-orchestrator` |
| run-state recover | `~/.openclaw/workspace/tools/run-state` |
| subtask-orchestrate resume | `~/.openclaw/workspace/tools/subtask-orchestrate` |
| recovery-orchestrator | `Agent-Self-health-Scaffold/runtime/recovery-orchestrator/` |

### 变更处理

| 变更类型 | 处理方式 |
|----------|----------|
| 核心路径代码变更 | 观察期重置，重新定义窗口 |
| 非核心路径变更 | 观察期继续，记录变更 |
| 配置变更 | 评估影响，决定是否重置 |

**禁止代码变了还沿用旧观察窗口直接毕业。**

---

## 六、核心指标与门槛

### 毕业门槛（Promote）

| 条件 | 门槛 |
|------|------|
| 观察天数 | ≥ 7 天 |
| **观察窗口新增有效样本** | **≥ 10** |
| 自动恢复成功率 | ≥ 95% |
| 人工补继续次数 | = 0 |
| 误恢复次数 | = 0 |
| 红线违规次数 | = 0 |

### 延长门槛（Extend）

| 条件 | 说明 |
|------|------|
| 样本不足 | 新增有效样本 < 10 次，但无红线违规 |
| 边缘案例 | 有 1-2 次失败需分析根因 |

### 回滚门槛（Rollback）

| 条件 | 触发值 |
|------|--------|
| 人工补继续次数 | ≥ 1 次 |
| 自动恢复成功率 | < 80% |
| 误恢复次数 | ≥ 1 次 |
| 红线违规次数 | ≥ 1 次 |

---

## 七、红线定义

| 红线 | 定义 | 触发条件 |
|------|------|----------|
| R1: 人工补继续 | 用户手动发送"继续"类命令 | ≥ 1 次 |
| R2: 重复执行 | 已完成步骤被重复执行 | ≥ 1 次 |
| R3: Ledger 分叉 | 任务状态出现不一致 | ≥ 1 次 |
| R4: 恢复后停滞 | 恢复后任务停滞超过 5 分钟 | ≥ 1 次 |

---

## 八、每日检查流程

### 自动检查（每 5 分钟）

```
systemd timer: agent-self-health-gate.timer
  → gate-self-health-check --write --json
```

### 每日汇总（每天 00:00）

1. 统计过去 24 小时的恢复事件
2. 检查四条红线
3. 区分自然样本 / 主动演练样本
4. 记录到 `observation_state.json`

---

## 九、状态文件字段

```json
{
  "observation_start": "2026-03-17T22:20:00Z",
  "observation_end": "2026-03-24T22:20:00Z",
  "version_lock": "self-health-v2-obs-day0",
  
  "baseline": {
    "sample_count": 11,
    "success_rate": 1.0,
    "redline_violations": 0,
    "note": "baseline only, not counted in graduation"
  },
  
  "window": {
    "sample_count": 0,
    "natural_sample_count": 0,
    "drill_sample_count": 0,
    "success_count": 0,
    "failure_count": 0,
    "manual_continue_count": 0,
    "false_resume_count": 0
  },
  
  "redline_violations": [],
  "graduation_status": "in_progress"
}
```

---

## 十、当前状态

| 项目 | 值 |
|------|-----|
| 观察期开始 | 2026-03-17T22:20:00Z |
| 预计结束 | 2026-03-24T22:20:00Z |
| 版本锁定 | self-health-v2-obs-day0 |
| Baseline 样本 | 11 次（不计入毕业） |
| **窗口新增样本** | **0 次** |
| 当前判定 | 进行中 |

---

## 十一、规则锁定确认

| 规则 | 状态 |
|------|------|
| 历史样本排除出本轮毕业统计 | ✅ 已锁定 |
| 恢复机会定义收紧 | ✅ 已锁定 |
| 自然/主动演练样本分层 | ✅ 已锁定 |
| 版本冻结写入 | ✅ 已锁定 |
