# Configuration Plan

**Version**: 1.0.0  
**Created**: 2026-03-09

---

## 1. Configuration Overview

本文档定义 CEO 和 main agent 的共享知识库配置方案。

### 1.1 Configuration File

**Primary**: `~/.openclaw/openclaw.json`

### 1.2 Configuration Scope

| Agent | Config Section | Shared Paths |
|-------|---------------|--------------|
| CEO | `agents.ceo` | `shared/` |
| main | `agents.main` | `shared/` |

---

## 2. memorySearch Configuration

### 2.1 Purpose

让 agent 在检索记忆时能访问共享知识库。

### 2.2 Configuration

```json
{
  "agents": {
    "ceo": {
      "memorySearch": {
        "extraPaths": [
          "~/.openclaw/shared/docs",
          "~/.openclaw/shared/facts"
        ]
      }
    },
    "main": {
      "memorySearch": {
        "extraPaths": [
          "~/.openclaw/shared/docs",
          "~/.openclaw/shared/facts"
        ]
      }
    }
  }
}
```

### 2.3 Search Priority

1. Agent's private workspace
2. Agent's agentDir
3. Shared docs/
4. Shared facts/

### 2.4 Isolation Guarantee

- CEO 的 `workspace-ceo/memory.md` 不在 main 的搜索路径
- main 的 `workspace/memory.md` 不在 CEO 的搜索路径

---

## 3. Skills Configuration

### 3.1 Purpose

让 agent 能加载共享技能。

### 3.2 Configuration

```json
{
  "agents": {
    "ceo": {
      "skills": {
        "load": {
          "extraDirs": [
            "~/.openclaw/shared/skills"
          ]
        }
      }
    },
    "main": {
      "skills": {
        "load": {
          "extraDirs": [
            "~/.openclaw/shared/skills"
          ]
        }
      }
    }
  }
}
```

### 3.3 Skills Priority

1. Agent's private skills
2. Shared skills

---

## 4. Full Configuration Example

### 4.1 Minimal Config

```json
{
  "agents": {
    "ceo": {
      "memorySearch": {
        "extraPaths": [
          "~/.openclaw/shared/docs",
          "~/.openclaw/shared/facts"
        ]
      },
      "skills": {
        "load": {
          "extraDirs": [
            "~/.openclaw/shared/skills"
          ]
        }
      }
    },
    "main": {
      "memorySearch": {
        "extraPaths": [
          "~/.openclaw/shared/docs",
          "~/.openclaw/shared/facts"
        ]
      },
      "skills": {
        "load": {
          "extraDirs": [
            "~/.openclaw/shared/skills"
          ]
        }
      }
    }
  }
}
```

### 4.2 Merge Strategy

OpenClaw 使用 `merge` 模式：

- 不替换原有配置
- 追加到现有配置
- 保留 agent 独立性

---

## 5. Configuration Validation

### 5.1 Validation Checklist

- [ ] `~/.openclaw/shared/` 目录存在
- [ ] `extraPaths` 指向有效路径
- [ ] `extraDirs` 指向有效目录
- [ ] 配置语法正确

### 5.2 Validation Commands

```bash
# Check shared directory
ls -la ~/.openclaw/shared/

# Validate JSON syntax
cat ~/.openclaw/openclaw.json | jq .agents

# Test path resolution
ls ~/.openclaw/shared/docs/
ls ~/.openclaw/shared/facts/
```

---

## 6. Rollback Procedure

### 6.1 Remove Shared Config

```json
{
  "agents": {
    "ceo": {
      "memorySearch": {
        "extraPaths": []
      },
      "skills": {
        "load": {
          "extraDirs": []
        }
      }
    },
    "main": {
      "memorySearch": {
        "extraPaths": []
      },
      "skills": {
        "load": {
          "extraDirs": []
        }
      }
    }
  }
}
```

### 6.2 Verify Rollback

```bash
# Restart OpenClaw
openclaw gateway restart

# Verify no shared access
cat ~/.openclaw/openclaw.json | jq .agents.ceo.memorySearch.extraPaths
# Should be empty []
```

---

## 7. Configuration Change Log

| Date | Version | Change | Author |
|------|---------|--------|--------|
| 2026-03-09 | 1.0.0 | Initial config plan | main |
