# Phase K - Agent 卡片

## Tier 1: continue_default_enabled (3)

### main
- **状态**: continue_default_enabled
- **Telegram**: ✅ 已绑定
- **会话路径**: `~/.openclaw/agents/main/sessions/`
- **Governance**: ✅ 已验证
- **启用方式**: 已启用，无需操作

### audit
- **状态**: continue_default_enabled
- **Telegram**: ❌ 未绑定
- **会话路径**: `~/.openclaw/agents/audit/sessions/`
- **Governance**: ✅ 权限 600
- **启用方式**: ACP harness / sessions_spawn

### coder
- **状态**: continue_default_enabled
- **Telegram**: ❌ 未绑定
- **会话路径**: `~/.openclaw/agents/coder/sessions/`
- **Governance**: ✅ 权限 600
- **启用方式**: ACP harness / sessions_spawn

---

## Tier 2: manual_enable_only (6)

### default
- **状态**: manual_enable_only
- **卡点**: 未在 OpenClaw config 中注册
- **目录结构**: ✅ 完整
- **Sessions 目录**: ✅ 存在
- **再评估条件**: 
  1. 在 `~/.openclaw/config.json` 中添加 agent 配置
  2. 重启 gateway 或刷新配置
- **启用后进入**: observation 阶段

### healthcheck
- **状态**: manual_enable_only
- **卡点**: 未在 OpenClaw config 中注册
- **目录结构**: ✅ 完整
- **Sessions 目录**: ✅ 存在
- **再评估条件**: 
  1. 在 `~/.openclaw/config.json` 中添加 agent 配置
  2. 重启 gateway 或刷新配置
- **启用后进入**: observation 阶段

### acp-codex
- **状态**: manual_enable_only
- **卡点**: 未在 OpenClaw config 中注册
- **目录结构**: ✅ 完整
- **Sessions 目录**: ✅ 存在
- **再评估条件**: 
  1. 在 `~/.openclaw/config.json` 中添加 agent 配置
  2. 重启 gateway 或刷新配置
- **启用后进入**: observation 阶段

### codex
- **状态**: manual_enable_only
- **卡点**: 未在 OpenClaw config 中注册
- **目录结构**: ✅ 完整
- **Sessions 目录**: ✅ 存在
- **再评估条件**: 
  1. 在 `~/.openclaw/config.json` 中添加 agent 配置
  2. 重启 gateway 或刷新配置
- **启用后进入**: observation 阶段

### mvp7-coder
- **状态**: manual_enable_only
- **卡点**: 未在 OpenClaw config 中注册
- **目录结构**: ✅ 完整
- **Sessions 目录**: ✅ 存在
- **再评估条件**: 
  1. 在 `~/.openclaw/config.json` 中添加 agent 配置
  2. 重启 gateway 或刷新配置
- **启用后进入**: observation 阶段

### cc-godmode
- **状态**: manual_enable_only
- **卡点**: 未在 OpenClaw config 中注册 + 高权限风险
- **目录结构**: ✅ 完整
- **Sessions 目录**: ✅ 存在
- **风险等级**: 高
- **再评估条件**: 
  1. 在 `~/.openclaw/config.json` 中添加 agent 配置
  2. 进行额外权限审查
  3. 定义使用边界和审计要求
  4. 重启 gateway 或刷新配置
- **启用后进入**: observation 阶段 + 强化审计

---

## Tier 3: manual_enable_only + prerequisite (4)

### implementer
- **状态**: manual_enable_only
- **卡点**: 缺少 sessions 目录
- **目录结构**: ❌ 不完整
- **Sessions 目录**: ❌ 缺失
- **再评估条件**: 
  1. 创建 sessions 目录: `mkdir -p ~/.openclaw/agents/implementer/sessions`
  2. 在 `~/.openclaw/config.json` 中添加 agent 配置
  3. 重启 gateway 或刷新配置
- **启用后进入**: observation 阶段

### planner
- **状态**: manual_enable_only
- **卡点**: 缺少 sessions 目录
- **目录结构**: ❌ 不完整
- **Sessions 目录**: ❌ 缺失
- **再评估条件**: 
  1. 创建 sessions 目录: `mkdir -p ~/.openclaw/agents/planner/sessions`
  2. 在 `~/.openclaw/config.json` 中添加 agent 配置
  3. 重启 gateway 或刷新配置
- **启用后进入**: observation 阶段

### verifier
- **状态**: manual_enable_only
- **卡点**: 缺少 sessions 目录
- **目录结构**: ❌ 不完整
- **Sessions 目录**: ❌ 缺失
- **再评估条件**: 
  1. 创建 sessions 目录: `mkdir -p ~/.openclaw/agents/verifier/sessions`
  2. 在 `~/.openclaw/config.json` 中添加 agent 配置
  3. 重启 gateway 或刷新配置
- **启用后进入**: observation 阶段

### test
- **状态**: manual_enable_only
- **卡点**: 缺少 sessions 目录
- **目录结构**: ❌ 不完整
- **Sessions 目录**: ❌ 缺失
- **再评估条件**: 
  1. 创建 sessions 目录: `mkdir -p ~/.openclaw/agents/test/sessions`
  2. 在 `~/.openclaw/config.json` 中添加 agent 配置
  3. 重启 gateway 或刷新配置
- **启用后进入**: observation 阶段
