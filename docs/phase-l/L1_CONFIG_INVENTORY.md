# Phase L-1: 配置补全盘点

**日期**: 2026-03-17

---

## 配置检查

### OpenClaw 配置

```json
{}
```

### Agent 目录配置检查

#### default
| 检查项 | 状态 |
|--------|------|
| agent/config.json | ❌ 不存在 |
| auth-profiles.json | ✅ 存在 |
| sessions 目录 | ✅ (0 会话) |

#### healthcheck
| 检查项 | 状态 |
|--------|------|
| agent/config.json | ❌ 不存在 |
| auth-profiles.json | ✅ 存在 |
| sessions 目录 | ✅ (0 会话) |

#### acp-codex
| 检查项 | 状态 |
|--------|------|
| agent/config.json | ❌ 不存在 |
| auth-profiles.json | ✅ 存在 |
| sessions 目录 | ✅ (0 会话) |

#### codex
| 检查项 | 状态 |
|--------|------|
| agent/config.json | ❌ 不存在 |
| auth-profiles.json | ✅ 存在 |
| sessions 目录 | ✅ (0 会话) |

#### mvp7-coder
| 检查项 | 状态 |
|--------|------|
| agent/config.json | ❌ 不存在 |
| auth-profiles.json | ✅ 存在 |
| sessions 目录 | ✅ (0 会话) |

#### cc-godmode
| 检查项 | 状态 |
|--------|------|
| agent/config.json | ❌ 不存在 |
| auth-profiles.json | ✅ 存在 |
| sessions 目录 | ✅ (0 会话) |

### 配置缺口汇总

| Agent | 缺口 | 需补全 |
|-------|------|--------|
| default | 未在系统配置注册 | 添加到 agents_list |
| healthcheck | 未在系统配置注册 | 添加到 agents_list |
| acp-codex | 未在系统配置注册 | 添加到 acp.allowedAgents |
| codex | 未在系统配置注册 | 添加到 agents_list |
| mvp7-coder | 未在系统配置注册 | 添加到 agents_list |
| cc-godmode | 未在系统配置注册 + 高权限 | 添加到 agents_list + 治理边界 |

---
**L1 状态**: ✅ 配置盘点完成
