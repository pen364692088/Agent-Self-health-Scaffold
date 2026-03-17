# Phase K: Batch 1 Plan

**版本**: 1.0
**日期**: 2026-03-17
**状态**: 规划中

---

## 1. Batch 概述

| 项目 | 值 |
|------|-----|
| Batch 编号 | Batch 1 |
| 风险等级 | 低 |
| 候选 Agent | default, healthcheck |
| 目标状态 | pilot_enabled |
| 预计周期 | 3-5 天 |

---

## 2. 候选 Agent 详情

### 2.1 default

| 属性 | 值 |
|------|-----|
| Agent ID | default |
| 风险等级 | 低 |
| 当前状态 | disabled (Telegram account disabled) |
| 启用目标 | pilot_enabled |
| 目录 | ~/.openclaw/agents/default/ |
| Workspace | 不存在 (需创建) |

**启用要求**:
- [ ] 创建 Telegram bot (需 BotFather)
- [ ] 配置 bot token 到 openclaw.json
- [ ] 创建 workspace-default/ 目录
- [ ] 设置 pilot_enabled = True

### 2.2 healthcheck

| 属性 | 值 |
|------|-----|
| Agent ID | healthcheck |
| 风险等级 | 低 |
| 当前状态 | 无 Telegram 绑定 |
| 启用目标 | pilot_enabled |
| 目录 | ~/.openclaw/agents/healthcheck/ |
| Workspace | 不存在 (需创建) |

**启用要求**:
- [ ] 创建 Telegram bot (需 BotFather)
- [ ] 配置 bot token 到 openclaw.json
- [ ] 创建 workspace-healthcheck/ 目录
- [ ] 设置 enabled = True

---

## 3. 启用步骤

### Step 1: 创建 Telegram Bots

需要用户操作：
1. 打开 Telegram，搜索 @BotFather
2. 发送 `/newbot`
3. 按提示命名 (例如: `OpenClaw Default`, `OpenClaw Healthcheck`)
4. 获取 bot token

### Step 2: 更新 openclaw.json

在 `channels.telegram.accounts` 中添加：

```json
{
  "default": {
    "enabled": true,
    "dmPolicy": "pairing",
    "botToken": "<BOT_TOKEN>",
    "groupPolicy": "open",
    "streaming": "partial"
  },
  "healthcheck": {
    "enabled": true,
    "dmPolicy": "pairing",
    "botToken": "<BOT_TOKEN>",
    "groupPolicy": "open",
    "streaming": "partial"
  }
}
```

### Step 3: 创建 Workspace

```bash
mkdir -p ~/.openclaw/workspace-default
mkdir -p ~/.openclaw/workspace-healthcheck
```

### Step 4: 初始化 Workspace 文件

每个 workspace 需要基础文件：
- SOUL.md
- USER.md
- AGENTS.md (可选)
- SESSION-STATE.md

### Step 5: 重启 OpenClaw

```bash
openclaw gateway restart
```

---

## 4. 观察指标 (K3)

启用后需收集以下指标：

| 指标 | 目标值 | 收集方式 |
|------|--------|----------|
| cold_start 成功率 | > 95% | 日志分析 |
| 消息响应成功率 | > 98% | 日志分析 |
| 错误率 | < 2% | 日志分析 |
| 会话连续性 | 正常 | 用户反馈 |

---

## 5. 治理验证 (K4)

低风险 Agent 最低验证：

### 5.1 warning_repeated
- 触发条件：连续 warning
- 预期：降级到 disabled
- 验证方法：模拟 warning 场景

### 5.2 recover
- 触发条件：从 disabled 恢复
- 预期：正常启动，无残留状态
- 验证方法：手动恢复后检查

---

## 6. 回退方案

如出现问题：
1. 设置 `enabled: false`
2. 重启 OpenClaw
3. 记录问题详情

---

## 7. Blockers

**当前 Blocker**:
- [ ] 缺少 default 的 Telegram bot token
- [ ] 缺少 healthcheck 的 Telegram bot token

**解决方案**:
- 用户通过 BotFather 创建 bot 并提供 token

---

## 8. 下一步

1. 用户创建 Telegram bots
2. 用户提供 bot tokens
3. 执行 Step 2-5
4. 进入 K3 观察期
