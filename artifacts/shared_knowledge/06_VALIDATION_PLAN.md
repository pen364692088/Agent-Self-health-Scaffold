# Validation Plan

**Version**: 1.0.0  
**Created**: 2026-03-09

---

## 1. Validation Overview

本文档定义共享知识库架构的验证计划。

### 1.1 Validation Goals

1. CEO 能检索 shared facts
2. main 能检索同一事实
3. CEO 私有 MEMORY.md 不会被 main 看到
4. main 私有 memory.md 不会被 CEO 看到

### 1.2 Validation Scope

| Scenario | Validated By |
|----------|--------------|
| Shared access | Manual + Automated |
| Private isolation | Manual + Automated |
| Config correctness | Automated |
| Rollback | Manual |

---

## 2. Test Scenarios

### Scenario 1: CEO Reads Shared Facts

**Purpose**: 验证 CEO 能访问 shared/facts/

**Steps**:
1. CEO agent 启动
2. 发起查询: "项目的 Gate 流程是什么？"
3. 验证能检索到 shared/facts/PROJECT_FACTS.md 内容

**Expected Result**:
- CEO 能检索到共享事实
- 检索结果包含 shared/facts/ 内容

**Validation Command**:
```bash
# As CEO agent
grep -r "Gate" ~/.openclaw/shared/facts/
```

### Scenario 2: main Reads Shared Facts

**Purpose**: 验证 main 能访问 shared/facts/

**Steps**:
1. main agent 启动
2. 发起相同查询: "项目的 Gate 流程是什么？"
3. 验证能检索到同一事实

**Expected Result**:
- main 能检索到共享事实
- 检索结果与 CEO 一致

**Validation Command**:
```bash
# As main agent
grep -r "Gate" ~/.openclaw/shared/facts/
```

### Scenario 3: CEO Private Memory Isolated

**Purpose**: 验证 CEO 私有记忆不被 main 访问

**Steps**:
1. 创建 CEO 私有记忆: `workspace-ceo/MEMORY.md`
2. 添加独特内容: "CEO_PRIVATE_TEST_12345"
3. main agent 查询该内容
4. 验证 main 无法检索到

**Expected Result**:
- main 搜索路径不包含 `workspace-ceo/`
- main 无法检索到 CEO 私有内容

**Validation Command**:
```bash
# Check main config
cat ~/.openclaw/openclaw.json | jq '.agents.main.memorySearch.extraPaths[]'
# Should NOT contain workspace-ceo
```

### Scenario 4: main Private Memory Isolated

**Purpose**: 验证 main 私有记忆不被 CEO 访问

**Steps**:
1. 确认 main 私有记忆: `workspace/memory.md`
2. 添加独特内容: "MAIN_PRIVATE_TEST_67890"
3. CEO agent 查询该内容
4. 验证 CEO 无法检索到

**Expected Result**:
- CEO 搜索路径不包含 `workspace/`
- CEO 无法检索到 main 私有内容

**Validation Command**:
```bash
# Check CEO config
cat ~/.openclaw/openclaw.json | jq '.agents.ceo.memorySearch.extraPaths[]'
# Should NOT contain workspace (without -ceo)
```

### Scenario 5: Shared Skills Access

**Purpose**: 验证共享技能可加载

**Steps**:
1. 创建共享技能: `shared/skills/shared-workflow/SKILL.md`
2. CEO agent 启动
3. 验证技能可用

**Expected Result**:
- CEO 能加载共享技能
- main 能加载共享技能

**Validation Command**:
```bash
ls ~/.openclaw/shared/skills/shared-workflow/SKILL.md
```

---

## 3. Automated Validation Script

```bash
#!/bin/bash
# validate_shared_knowledge.sh

set -e

echo "=== Shared Knowledge Validation ==="

# Test 1: Shared directory exists
echo -n "Test 1: Shared directory... "
if [ -d ~/.openclaw/shared ]; then
    echo "PASS"
else
    echo "FAIL"
    exit 1
fi

# Test 2: Shared docs accessible
echo -n "Test 2: Shared docs... "
if [ -f ~/.openclaw/shared/docs/PROJECT_OVERVIEW.md ]; then
    echo "PASS"
else
    echo "FAIL"
    exit 1
fi

# Test 3: Shared facts accessible
echo -n "Test 3: Shared facts... "
if [ -f ~/.openclaw/shared/facts/PROJECT_FACTS.md ]; then
    echo "PASS"
else
    echo "FAIL"
    exit 1
fi

# Test 4: CEO config has extraPaths
echo -n "Test 4: CEO extraPaths... "
CEO_PATHS=$(cat ~/.openclaw/openclaw.json | jq -r '.agents.ceo.memorySearch.extraPaths[]' 2>/dev/null || echo "")
if echo "$CEO_PATHS" | grep -q "shared"; then
    echo "PASS"
else
    echo "FAIL"
    exit 1
fi

# Test 5: main config has extraPaths
echo -n "Test 5: main extraPaths... "
MAIN_PATHS=$(cat ~/.openclaw/openclaw.json | jq -r '.agents.main.memorySearch.extraPaths[]' 2>/dev/null || echo "")
if echo "$MAIN_PATHS" | grep -q "shared"; then
    echo "PASS"
else
    echo "FAIL"
    exit 1
fi

# Test 6: CEO cannot see main workspace
echo -n "Test 6: CEO isolation from main... "
if echo "$CEO_PATHS" | grep -qv "workspace-ceo" && echo "$CEO_PATHS" | grep -qv "workspace/"; then
    echo "PASS"
else
    echo "CHECK"
fi

# Test 7: main cannot see CEO workspace
echo -n "Test 7: main isolation from CEO... "
if echo "$MAIN_PATHS" | grep -qv "workspace-ceo"; then
    echo "PASS"
else
    echo "FAIL"
    exit 1
fi

echo "=== All Tests Passed ==="
```

---

## 4. Validation Checklist

### 4.1 Pre-Validation

- [ ] OpenClaw gateway running
- [ ] CEO agent configured
- [ ] main agent configured
- [ ] Shared directory created

### 4.2 Shared Access Validation

- [ ] CEO can read shared/docs/
- [ ] CEO can read shared/facts/
- [ ] main can read shared/docs/
- [ ] main can read shared/facts/
- [ ] Both get same content

### 4.3 Isolation Validation

- [ ] CEO config has no main workspace path
- [ ] main config has no CEO workspace path
- [ ] CEO memory file not in main paths
- [ ] main memory file not in CEO paths

### 4.4 Skills Validation

- [ ] Shared skills directory exists
- [ ] CEO can load shared skills
- [ ] main can load shared skills

### 4.5 Rollback Validation

- [ ] Config backup exists
- [ ] Rollback procedure documented
- [ ] Rollback tested

---

## 5. Validation Results Template

```markdown
# Validation Report

**Date**: YYYY-MM-DD
**Validator**: Agent Name

## Results

| Scenario | Status | Notes |
|----------|--------|-------|
| CEO reads shared facts | ✅/❌ | |
| main reads shared facts | ✅/❌ | |
| CEO memory isolated | ✅/❌ | |
| main memory isolated | ✅/❌ | |
| Shared skills accessible | ✅/❌ | |

## Issues Found

1. [Description]
2. [Description]

## Recommendations

1. [Recommendation]
2. [Recommendation]

## Sign-off

- [ ] All scenarios pass
- [ ] No blocking issues
- [ ] Ready for production
```

---

## 6. Continuous Validation

### 6.1 Periodic Checks

- Daily: Health check script runs
- Weekly: Full validation suite
- Monthly: Isolation audit

### 6.2 Alerting

- Alert if shared directory missing
- Alert if config changed unexpectedly
- Alert if isolation broken

### 6.3 Monitoring

```bash
# Add to cron
0 * * * * ~/.openclaw/workspace/tools/validate_shared_knowledge.sh
```
