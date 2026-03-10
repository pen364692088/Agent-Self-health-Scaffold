# Migration Runbook

**Version**: 1.0.0  
**Created**: 2026-03-09

---

## 1. Overview

本 runbook 描述如何从当前状态迁移到共享知识库架构。

### 1.1 Current State

- CEO 和 main 各自独立
- 无共享知识层
- 项目知识分散在 main workspace

### 1.2 Target State

- CEO 和 main 共享 `~/.openclaw/shared/`
- 私有记忆保持隔离
- 配置可回滚

---

## 2. Prerequisites

### 2.1 System Requirements

- OpenClaw 运行中
- CEO 和 main agent 已创建
- Git 已初始化

### 2.2 Backup

```bash
# Backup current config
cp ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.bak

# Backup workspaces
tar -czf /tmp/workspace-backup.tar.gz \
  ~/.openclaw/workspace \
  ~/.openclaw/workspace-ceo
```

---

## 3. Migration Steps

### Step 1: Create Shared Directory

```bash
mkdir -p ~/.openclaw/shared/{docs,runbooks,interfaces,facts,systems,skills/shared-workflow}
```

**Verify**:
```bash
ls -la ~/.openclaw/shared/
```

### Step 2: Create Shared Documents

```bash
# Create PROJECT_OVERVIEW.md
cat > ~/.openclaw/shared/docs/PROJECT_OVERVIEW.md << 'EOF'
# Project Overview

... content ...
EOF

# Create other shared documents...
```

**Verify**:
```bash
ls ~/.openclaw/shared/docs/
ls ~/.openclaw/shared/runbooks/
```

### Step 3: Update Configuration

编辑 `~/.openclaw/openclaw.json`:

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

**Verify**:
```bash
cat ~/.openclaw/openclaw.json | jq .agents.ceo
cat ~/.openclaw/openclaw.json | jq .agents.main
```

### Step 4: Restart OpenClaw

```bash
openclaw gateway restart
```

**Verify**:
```bash
openclaw gateway status
```

### Step 5: Verify Access

```bash
# CEO should be able to read shared facts
# (Run as CEO agent)
cat ~/.openclaw/shared/facts/PROJECT_FACTS.md

# main should be able to read shared facts
# (Run as main agent)
cat ~/.openclaw/shared/facts/PROJECT_FACTS.md
```

### Step 6: Commit Changes

```bash
cd ~/.openclaw
git add shared/
git add openclaw.json
git commit -m "Implement shared knowledge architecture"
git push
```

---

## 4. Rollback Procedure

### 4.1 Quick Rollback

```bash
# Restore config backup
cp ~/.openclaw/openclaw.json.bak ~/.openclaw/openclaw.json

# Restart OpenClaw
openclaw gateway restart
```

### 4.2 Full Rollback

```bash
# Remove shared directory
rm -rf ~/.openclaw/shared/

# Restore config
cp ~/.openclaw/openclaw.json.bak ~/.openclaw/openclaw.json

# Restart OpenClaw
openclaw gateway restart

# Restore workspaces if needed
tar -xzf /tmp/workspace-backup.tar.gz -C /
```

---

## 5. Post-Migration Tasks

### 5.1 Validation

- [ ] CEO can read shared docs
- [ ] main can read shared docs
- [ ] CEO private memory not visible to main
- [ ] main private memory not visible to CEO

### 5.2 Documentation

- [ ] Update ARCHITECTURE.md
- [ ] Update DIRECTORY_LAYOUT.md
- [ ] Update CONFIG_PLAN.md
- [ ] Create validation report

### 5.3 Monitoring

- [ ] Set up health checks
- [ ] Configure alerts
- [ ] Review access logs

---

## 6. Troubleshooting

### 6.1 Shared Content Not Found

**Symptom**: Agent cannot find shared content

**Check**:
```bash
# Verify path exists
ls ~/.openclaw/shared/docs/

# Verify config
cat ~/.openclaw/openclaw.json | jq .agents.ceo.memorySearch.extraPaths
```

**Fix**: Ensure paths are correctly configured and OpenClaw restarted

### 6.2 Private Memory Leaked

**Symptom**: CEO memory visible to main

**Check**:
```bash
# Verify no cross-path in config
cat ~/.openclaw/openclaw.json | jq .agents.main.memorySearch.extraPaths
# Should NOT contain workspace-ceo
```

**Fix**: Remove any cross-path configuration

### 6.3 Skills Not Loading

**Symptom**: Shared skills not available

**Check**:
```bash
# Verify skill directory
ls ~/.openclaw/shared/skills/

# Verify config
cat ~/.openclaw/openclaw.json | jq .agents.ceo.skills.load.extraDirs
```

**Fix**: Ensure skills.load.extraDirs is configured

---

## 7. Timeline

| Phase | Duration | Tasks |
|-------|----------|-------|
| Backup | 5 min | Backup config and workspaces |
| Create | 10 min | Create shared directory and docs |
| Configure | 5 min | Update openclaw.json |
| Restart | 2 min | Restart OpenClaw |
| Verify | 10 min | Validate access and isolation |
| Commit | 5 min | Git commit and push |

**Total**: ~40 minutes
