# Phase L-5: 最终分流决策

**日期**: 2026-03-17

---

## 最终状态词典

**不新增状态词典**。使用现有：

| 状态 | 定义 |
|------|------|
| continue_default_enabled | 已配置、已验证、可用 |
| manual_enable_only | 有目录但未配置、需手动注册 |

---

## Agent 最终分类

### continue_default_enabled (3) - 不修改

| Agent | 状态 | 调用路径 | 验证 |
|-------|------|----------|------|
| main | continue_default_enabled | sessions_spawn | ✅ |
| audit | continue_default_enabled | sessions_spawn | ✅ |
| coder | continue_default_enabled | sessions_spawn | ✅ |

---

### manual_enable_only (5) - 批量处理

| Agent | 状态 | 缺口 | 最小接入条件 |
|-------|------|------|--------------|
| default | manual_enable_only | 未配置 | 添加到 acp.allowedAgents |
| healthcheck | manual_enable_only | 未配置 | 添加到 acp.allowedAgents |
| acp-codex | manual_enable_only | 未配置 | 添加到 acp.allowedAgents |
| codex | manual_enable_only | 未配置 | 添加到 acp.allowedAgents |
| mvp7-coder | manual_enable_only | 未配置 | 添加到 acp.allowedAgents |

#### 调用方式 (配置后)
```bash
sessions_spawn runtime="acp" agentId="<agent>" thread=true
```

#### 调用方式 (当前)
```bash
# 通过 main agent 间接调用
sessions_spawn runtime="subagent" agentId="main" task="使用 <agent> 执行 ..."
```

---

### manual_enable_only (1) - 单独处理

| Agent | 状态 | 缺口 | 治理要求 |
|-------|------|------|----------|
| cc-godmode | manual_enable_only | 未配置 + 高权限 | 强化审计 |

#### 最小接入条件
1. 添加到 acp.allowedAgents
2. 配置专属治理规则
3. 定义使用边界
4. 设置审计触发器

#### 调用方式 (配置后)
```bash
# 必须通过 main agent 发起
sessions_spawn runtime="acp" agentId="cc-godmode" thread=true
```

#### 调用限制
- 必须有明确审计目的
- 结果必须人工确认
- 全量日志记录

---

## 最终结论

### 状态不变
- 不新增状态词典
- 不修改 continue_default_enabled 的 3 个 agent
- 不要求 Telegram token

### 接入路径明确
- 已配置: sessions_spawn (subagent)
- 未配置: sessions_spawn (acp) 或通过 main 间接调用

### 治理边界清晰
- 低风险: 默认治理
- 中风险: 代码审计
- 高风险: 强化审计

### 每个 agent 有明确结论

| Agent | 最终状态 | 接入结论 |
|-------|----------|----------|
| main | continue_default_enabled | ✅ 已可用 |
| audit | continue_default_enabled | ✅ 已可用 |
| coder | continue_default_enabled | ✅ 已可用 |
| default | manual_enable_only | 需添加到 acp.allowedAgents |
| healthcheck | manual_enable_only | 需添加到 acp.allowedAgents |
| acp-codex | manual_enable_only | 需添加到 acp.allowedAgents |
| codex | manual_enable_only | 需添加到 acp.allowedAgents |
| mvp7-coder | manual_enable_only | 需添加到 acp.allowedAgents |
| cc-godmode | manual_enable_only | 需添加到 acp.allowedAgents + 治理配置 |

---
**L5 状态**: ✅ 最终分流决策完成
