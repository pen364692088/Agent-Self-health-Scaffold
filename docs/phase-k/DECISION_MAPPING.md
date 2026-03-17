# Phase K - 决策词典映射

## 正式状态词典

| 状态 | 定义 | 触发条件 |
|------|------|----------|
| continue_default_enabled | 继续默认启用 | 已配置、已验证、可用 |
| continue_pilot_enabled | 继续 pilot 启用 | 已在 pilot 中、表现正常 |
| manual_enable_only | 仅手动启用 | 有目录但未配置、需手动注册 |
| move_to_quarantine | 移入隔离 | 存在问题、不建议启用 |

## 映射结果

### PROMOTE → continue_default_enabled
- **main**: 已配置、已绑定 Telegram、已验证
- **audit**: 已配置、权限正确、有活动会话
- **coder**: 已配置、权限正确、有使用历史

### CONDITIONAL → manual_enable_only
| Agent | 卡点 | 再评估条件 |
|-------|------|------------|
| default | 未在系统配置中注册 | 注册后可启用 |
| healthcheck | 未在系统配置中注册 | 注册后可启用 |
| acp-codex | 未在系统配置中注册 | 注册后可启用 |
| codex | 未在系统配置中注册 | 注册后可启用 |
| mvp7-coder | 未在系统配置中注册 | 注册后可启用 |
| cc-godmode | 未在系统配置中注册 + 高权限 | 注册后需额外权限审查 |

### DEFER → manual_enable_only (with prerequisite)
| Agent | 卡点 | 再评估条件 |
|-------|------|------------|
| implementer | 缺少 sessions 目录 | 补全目录结构后可评估 |
| planner | 缺少 sessions 目录 | 补全目录结构后可评估 |
| verifier | 缺少 sessions 目录 | 补全目录结构后可评估 |
| test | 缺少 sessions 目录 | 补全目录结构后可评估 |

## 非启用状态说明

### manual_enable_only 的具体含义
- agent 有目录结构但不可自动启用
- 需要管理员手动：
  1. 在 OpenClaw config 中注册
  2. (如需要) 补全目录结构
  3. (如需要) 进行权限审查
- 启用后进入 observation 阶段

### 无需 quarantine
当前所有 agent 均未发现阻塞性问题，无需移入隔离。
