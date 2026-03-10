# Shared Knowledge Architecture

**Version**: 1.0.0  
**Created**: 2026-03-09  
**Status**: IMPLEMENTED

---

## 1. Overview

### 1.1 Purpose

实现 CEO 和 main 双 agent 的共享知识库，同时保持私有记忆隔离。

### 1.2 Goals

- ✅ CEO 和 main 可检索同一批共享项目知识
- ✅ 私有记忆（MEMORY.md）不会自然泄露
- ✅ 配置最小改动、可回滚
- ✅ 不共享 agentDir、workspace、私有文件

### 1.3 Non-Goals

- ❌ 不共享 agentDir
- ❌ 不共享 workspace
- ❌ 不共享私有 MEMORY.md
- ❌ 不共享 session 状态

---

## 2. Architecture

### 2.1 Layer Model

```
┌─────────────────────────────────────────────────────────┐
│                    Shared Layer                          │
│              ~/.openclaw/shared/                         │
│  ┌─────────┬──────────┬───────────┬───────┬─────────┐   │
│  │  docs/  │ runbooks/│ interfaces│ facts │ systems │   │
│  └─────────┴──────────┴───────────┴───────┴─────────┘   │
│              ↓ read access ↓                             │
├─────────────────────┬───────────────────────────────────┤
│     CEO Agent       │          Main Agent               │
│  ~/.openclaw/       │       ~/.openclaw/                │
│  agents/ceo/        │       agents/main/                │
│  workspace-ceo/     │       workspace/                  │
│  ┌──────────────┐   │       ┌──────────────┐            │
│  │ MEMORY.md    │   │       │ memory.md    │            │
│  │ (private)    │   │       │ (private)    │            │
│  └──────────────┘   │       └──────────────┘            │
└─────────────────────┴───────────────────────────────────┘
```

### 2.2 Directory Structure

```
~/.openclaw/shared/
├── docs/                    # 项目文档
│   └── PROJECT_OVERVIEW.md
├── runbooks/                # 操作手册
│   └── GATE_FLOW.md
├── interfaces/              # 接口规范
│   └── API_CONTRACTS.md
├── facts/                   # 项目事实
│   └── PROJECT_FACTS.md
├── systems/                 # 系统架构
│   └── SYSTEM_MAP.md
└── skills/                  # 共享技能
    └── shared-workflow/
        └── SKILL.md
```

### 2.3 Access Pattern

| Agent | Shared Access | Private Access |
|-------|---------------|----------------|
| CEO | `~/.openclaw/shared/` (read) | `workspace-ceo/`, `agents/ceo/` |
| main | `~/.openclaw/shared/` (read) | `workspace/`, `agents/main/` |

---

## 3. Configuration

### 3.1 memorySearch.extraPaths

```json
{
  "agents": {
    "ceo": {
      "memorySearch": {
        "extraPaths": ["~/.openclaw/shared/docs", "~/.openclaw/shared/facts"]
      }
    },
    "main": {
      "memorySearch": {
        "extraPaths": ["~/.openclaw/shared/docs", "~/.openclaw/shared/facts"]
      }
    }
  }
}
```

### 3.2 skills.load.extraDirs

```json
{
  "agents": {
    "ceo": {
      "skills": {
        "load": {
          "extraDirs": ["~/.openclaw/shared/skills"]
        }
      }
    },
    "main": {
      "skills": {
        "load": {
          "extraDirs": ["~/.openclaw/shared/skills"]
        }
      }
    }
  }
}
```

---

## 4. Boundaries

### 4.1 What IS Shared

| Category | Path | Owner | Update Rule |
|----------|------|-------|-------------|
| 项目文档 | shared/docs/ | main | 评审后更新 |
| 操作手册 | shared/runbooks/ | main | 流程变更时更新 |
| 接口规范 | shared/interfaces/ | main | API 变更时更新 |
| 项目事实 | shared/facts/ | main | 事实变更时更新 |
| 系统架构 | shared/systems/ | main | 架构变更时更新 |
| 共享技能 | shared/skills/ | main | 技能变更时更新 |

### 4.2 What IS NOT Shared

| Category | Location | Owner | Reason |
|----------|----------|-------|--------|
| 私有记忆 | workspace*/MEMORY.md | 各 agent | 隔离 |
| 会话状态 | workspace*/SESSION-STATE.md | 各 agent | 隔离 |
| 工作缓冲 | workspace*/working-buffer.md | 各 agent | 隔离 |
| 交接摘要 | workspace*/handoff.md | 各 agent | 隔离 |
| 身份定义 | workspace*/IDENTITY.md | 各 agent | 隔离 |

---

## 5. Data Flow

### 5.1 Read Flow

```
Agent Query → memorySearch → 
  ├─ [1] Private workspace/ 
  ├─ [2] shared/docs/
  └─ [3] shared/facts/
```

### 5.2 Write Flow

```
Content Update → 
  ├─ If project knowledge → shared/
  └─ If private memory → workspace*/MEMORY.md
```

---

## 6. Rollback

### 6.1 Configuration Rollback

Remove `extraPaths` and `extraDirs` from config:

```json
{
  "agents": {
    "ceo": {
      "memorySearch": { "extraPaths": [] },
      "skills": { "load": { "extraDirs": [] } }
    },
    "main": {
      "memorySearch": { "extraPaths": [] },
      "skills": { "load": { "extraDirs": [] } }
    }
  }
}
```

### 6.2 Data Rollback

```bash
rm -rf ~/.openclaw/shared/
```

---

## 7. Monitoring

### 7.1 Health Check

```bash
# Verify shared directory exists
ls -la ~/.openclaw/shared/

# Verify agent can access
cat ~/.openclaw/shared/facts/PROJECT_FACTS.md
```

### 7.2 Metrics

| Metric | Target | Alert |
|--------|--------|-------|
| Shared docs count | ≥ 1 | < 1 |
| Shared skills count | ≥ 1 | < 1 |
| Config applied | true | false |

---

## 8. References

- [02_DIRECTORY_LAYOUT.md](./02_DIRECTORY_LAYOUT.md) - 目录布局详解
- [03_CONFIG_PLAN.md](./03_CONFIG_PLAN.md) - 配置方案
- [04_BOUNDARIES_AND_RULES.md](./04_BOUNDARIES_AND_RULES.md) - 边界规则
- [05_MIGRATION_RUNBOOK.md](./05_MIGRATION_RUNBOOK.md) - 迁移手册
- [06_VALIDATION_PLAN.md](./06_VALIDATION_PLAN.md) - 验证计划
