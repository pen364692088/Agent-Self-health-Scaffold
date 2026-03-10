# Boundaries and Rules

**Version**: 1.0.0  
**Created**: 2026-03-09

---

## 1. Boundary Definition

### 1.1 Shared Boundary

**Path**: `~/.openclaw/shared/`

**Access**:
- CEO: Read-only
- main: Read-write

**Content Types**:
- 项目公共知识
- 操作手册
- 接口规范
- 项目事实
- 系统架构
- 共享技能

### 1.2 Private Boundaries

| Agent | Private Workspace | Private AgentDir |
|-------|------------------|------------------|
| CEO | `~/.openclaw/workspace-ceo/` | `~/.openclaw/agents/ceo/` |
| main | `~/.openclaw/workspace/` | `~/.openclaw/agents/main/` |

---

## 2. Sharing Rules

### 2.1 What CAN Be Shared

| Content | Path | Reason |
|---------|------|--------|
| 项目概览 | shared/docs/PROJECT_OVERVIEW.md | 全局视角 |
| Gate 流程 | shared/runbooks/GATE_FLOW.md | 标准流程 |
| API 契约 | shared/interfaces/API_CONTRACTS.md | 接口定义 |
| 项目事实 | shared/facts/PROJECT_FACTS.md | 真相来源 |
| 系统架构 | shared/systems/SYSTEM_MAP.md | 技术架构 |
| 共享技能 | shared/skills/ | 工作流复用 |

### 2.2 What MUST NOT Be Shared

| Content | Path | Reason |
|---------|------|--------|
| 私有记忆 | workspace*/MEMORY.md | 隔离 |
| 会话状态 | workspace*/SESSION-STATE.md | 隔离 |
| 工作缓冲 | workspace*/working-buffer.md | 隔离 |
| 交接摘要 | workspace*/handoff.md | 隔离 |
| 身份定义 | workspace*/IDENTITY.md | 隔离 |
| 用户偏好 | workspace*/USER.md | 隔离 |

---

## 3. Access Control Matrix

### 3.1 File Access

| File | CEO Read | CEO Write | main Read | main Write |
|------|----------|-----------|-----------|------------|
| shared/docs/* | ✅ | ❌ | ✅ | ✅ |
| shared/runbooks/* | ✅ | ❌ | ✅ | ✅ |
| shared/interfaces/* | ✅ | ❌ | ✅ | ✅ |
| shared/facts/* | ✅ | ❌ | ✅ | ✅ |
| shared/systems/* | ✅ | ❌ | ✅ | ✅ |
| shared/skills/* | ✅ | ❌ | ✅ | ✅ |
| workspace-ceo/* | ✅ | ✅ | ❌ | ❌ |
| workspace/* | ❌ | ❌ | ✅ | ✅ |

### 3.2 Directory Access

| Directory | CEO Access | main Access |
|-----------|------------|-------------|
| ~/.openclaw/shared/ | Read | Read-Write |
| ~/.openclaw/workspace-ceo/ | Full | None |
| ~/.openclaw/workspace/ | None | Full |
| ~/.openclaw/agents/ceo/ | Full | None |
| ~/.openclaw/agents/main/ | None | Full |

---

## 4. Update Rules

### 4.1 Who Can Update

| Content Type | Updater | Reviewer |
|--------------|---------|----------|
| docs/ | main | CEO |
| runbooks/ | main | CEO |
| interfaces/ | main | - |
| facts/ | main | - |
| systems/ | main | CEO |
| skills/ | main | - |

### 4.2 Update Process

1. **Draft**: main 创建草稿
2. **Review**: 需要评审的内容由 CEO 审核
3. **Commit**: 评审通过后提交
4. **Announce**: 通知所有 agent 更新

---

## 5. Isolation Guarantees

### 5.1 Memory Isolation

**Guarantee**: CEO 的私有记忆不会被 main 检索到

**Implementation**:
- CEO memory: `workspace-ceo/MEMORY.md`
- main memory: `workspace/memory.md`
- 两个路径不在对方的 `extraPaths` 中

### 5.2 Session Isolation

**Guarantee**: CEO 的会话状态不会被 main 访问

**Implementation**:
- CEO sessions: `agents/ceo/sessions/`
- main sessions: `agents/main/sessions/`
- 两个目录完全独立

### 5.3 Workspace Isolation

**Guarantee**: CEO 的 workspace 完全独立于 main

**Implementation**:
- CEO workspace: `workspace-ceo/`
- main workspace: `workspace/`
- 无共享路径

---

## 6. Conflict Resolution

### 6.1 Same File Update

如果 CEO 和 main 尝试更新同一共享文件：

1. main 拥有写权限，CEO 无写权限
2. 冲突不会发生

### 6.2 Reference Conflict

如果共享内容引用私有内容：

1. 共享内容不应引用私有内容
2. 如果必须引用，使用抽象描述
3. 具体实现留在私有区域

---

## 7. Audit Trail

### 7.1 Change Log

所有共享内容变更记录在 git:

```bash
cd ~/.openclaw
git log --oneline shared/
```

### 7.2 Access Log

Agent 访问日志记录在 session logs:

```bash
# CEO 访问
ls ~/.openclaw/agents/ceo/sessions/

# main 访问
ls ~/.openclaw/agents/main/sessions/
```

---

## 8. Compliance Checklist

### 8.1 Before Sharing

- [ ] 内容是否属于项目公共知识？
- [ ] 内容是否包含敏感信息？
- [ ] 内容是否引用私有内容？

### 8.2 After Sharing

- [ ] 文件权限是否正确？
- [ ] 配置是否生效？
- [ ] 是否能回滚？

### 8.3 Periodic Review

- [ ] 共享内容是否仍然准确？
- [ ] 是否有过期内容需要归档？
- [ ] 隔离是否仍然有效？
