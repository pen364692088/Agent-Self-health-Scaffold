# Phase M-2: pilot 启用与接入锁定

**日期**: 2026-03-17
**状态**: ❌ BLOCKED

---

## 配置变更执行

### 变更证据
| 步骤 | 状态 | 详情 |
|------|------|------|
| 备份 | ✅ | `~/.openclaw/config.json.bak.20260317142900` |
| 读取当前 | ✅ | `acp.allowedAgents: []` |
| 增量合并 | ✅ | 添加 `default`, `healthcheck` |
| 保存 | ✅ | 配置文件已更新 |

### Diff
```diff
- 变更前: acp.allowedAgents: []
+ 变更后: acp.allowedAgents: ["default", "healthcheck"]
```

---

## 验证调用结果

### 尝试 1: sessions_spawn runtime="acp"

```json
{
  "status": "error",
  "error": "ACP runtime backend is not configured. Install and enable the acpx runtime plugin."
}
```

**结论**: ❌ ACP runtime backend 未安装/启用

### 尝试 2: sessions_spawn runtime="subagent"

```json
{
  "status": "forbidden",
  "error": "agentId is not allowed for sessions_spawn (allowed: coder, audit)"
}
```

**结论**: ❌ default 不在 sessions_spawn allowed 列表

---

## 真实调用证据

| Agent | runtime="acp" | runtime="subagent" | 调用结果 |
|-------|---------------|--------------------| ---------|
| default | ❌ ACP 未配置 | ❌ forbidden | **失败** |
| healthcheck | 未尝试 | 未尝试 | **失败** (同样原因) |

---

## 阻塞分析

### 问题 1: ACP Runtime 未配置
- **配置项**: `acp.allowedAgents` 已添加
- **依赖**: 需要 `acpx` runtime plugin
- **状态**: 未安装/未启用
- **影响**: runtime="acp" 调用失败

### 问题 2: sessions_spawn allowed 列表限制
- **当前 allowed**: `coder`, `audit` (来自 agents_list)
- **需求**: 添加 `default`, `healthcheck`
- **配置位置**: OpenClaw 内部管理，非简单配置文件
- **状态**: 无法直接修改
- **影响**: runtime="subagent" 调用失败

### 问题 3: agents_list 配置来源不明
- **main, audit, coder** 在 agents_list 中显示为 configured
- **但无 agent/config.json 文件**
- **配置来源**: OpenClaw 内部机制

---

## 判定

根据任务要求：
> 未拿到真实调用证据，不得宣称 Phase M 有效推进

**当前状态**:
- 配置变更: ✅ 已执行
- 调用验证: ❌ 全部失败
- **Phase M 未有效推进**

---

## 下一步选项

### 选项 A: 配置 ACP Runtime (推荐)
1. 安装 `acpx` runtime plugin
2. 启用 ACP runtime backend
3. 重新验证 `sessions_spawn runtime="acp"`
4. **优点**: 使用已配置的 acp.allowedAgents

### 选项 B: 研究 sessions_spawn allowed 配置
1. 研究 OpenClaw agents 配置机制
2. 找到添加 agent 到 allowed 列表的方法
3. **风险**: 可能需要修改 OpenClaw 核心配置

### 选项 C: 保持 manual_enable_only
1. 不强制启用
2. 文档记录当前阻塞状态
3. 等待后续能力建设
4. **优点**: 安全，无风险

---

## 建议

**建议选择选项 C**，理由：
1. ACP runtime 配置需要额外安装和配置
2. sessions_spawn allowed 列表修改需要深入了解 OpenClaw 内部机制
3. 当前 3 个 continue_default_enabled agents 已足够日常使用
4. manual_enable_only 状态已明确记录接入方式

---
**M2 状态**: ❌ BLOCKED - 需要 ACP Runtime 或 sessions_spawn allowed 配置
