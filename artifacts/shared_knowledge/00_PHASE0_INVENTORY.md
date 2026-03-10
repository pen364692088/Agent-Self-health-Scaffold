# Phase 0: 现状盘点报告

**Created**: 2026-03-09T20:35:00Z

---

## 1. Agent 结构盘点

### 1.1 CEO Agent

| Item | Path | Notes |
|------|------|-------|
| Agent Dir | `~/.openclaw/agents/ceo/` | 独立 |
| Workspace | `~/.openclaw/workspace-ceo/` | 独立 |
| Sessions | `~/.openclaw/agents/ceo/sessions/` | 独立 |
| Persona | 无 (IDENTITY.md 空) | 待配置 |
| MEMORY.md | 无 | 待创建 |
| Skills | 无 | 需要挂载 |

### 1.2 Main Agent

| Item | Path | Notes |
|------|------|-------|
| Agent Dir | `~/.openclaw/agents/main/` | 独立 |
| Workspace | `~/.openclaw/workspace/` | 独立 |
| Sessions | `~/.openclaw/agents/main/sessions/` | 独立 |
| Persona | SOUL.md + IDENTITY.md | 已配置 |
| memory.md | 有 | 已配置 |
| Skills | 30+ skills | 已配置 |

### 1.3 绑定关系

| Telegram Account | Agent ID | Workspace |
|------------------|----------|-----------|
| manager | main | workspace/ |
| ceo | ceo | workspace-ceo/ |

---

## 2. 共享层现状

### 2.1 当前状态: **无共享层**

- 无 shared 目录
- 无共享 skills 配置
- 无共享 docs 配置

### 2.2 问题

1. CEO 和 main 各自独立，无共同知识层
2. 项目公共知识分散在 main workspace
3. 规范、runbook、接口说明无共享访问
4. 新 agent 启动需要重新教

---

## 3. 现有知识分布

### 3.1 Main Workspace 知识资产

| Category | Location | Count | Should Share |
|----------|----------|-------|--------------|
| 根级规则 | `*.md` | ~20 | ✅ 共享 |
| POLICIES | `POLICIES/*.md` | 24 | ✅ 共享 |
| Docs | `docs/**/*.md` | ~20 | ✅ 共享 |
| Skills | `skills/*/SKILL.md` | 30+ | ✅ 部分共享 |
| Memory | `memory.md` | 1 | ❌ 私有 |
| Session State | `SESSION-STATE.md` | 1 | ❌ 私有 |
| Working Buffer | `working-buffer.md` | 1 | ❌ 私有 |

### 3.2 高频重复教学内容 (候选共享)

| Content | Location | Reason |
|---------|----------|--------|
| AGENTS.md | workspace/ | 会话连续性协议 |
| SOUL.md | workspace/ | 核心行为规范 |
| TOOLS.md | workspace/ | 工具使用规则 |
| HEARTBEAT.md | workspace/ | 心跳行为协议 |
| EXECUTION_POLICY | POLICIES/ | 任务完成协议 |
| GATES_CONFIG | POLICIES/ | Gate A/B/C 流程 |
| SUBAGENT_INBOX | docs/ | 子代理架构 |
| CONTEXT_COMPRESSION | POLICIES/ | 压缩策略 |

---

## 4. 候选共享内容分类

### 4.1 必须共享 (共享层)

| Content | Category | Priority |
|---------|----------|----------|
| Gate A/B/C 流程 | runbooks | P0 |
| 子代理架构 | systems | P0 |
| 任务完成协议 | policies | P0 |
| 会话连续性协议 | runbooks | P0 |
| 工具使用规则 | interfaces | P1 |
| 压缩策略 | policies | P1 |
| 自健康策略 | policies | P1 |

### 4.2 可选共享 (视需要)

| Content | Category | Notes |
|---------|----------|-------|
| 部分 skills | skills | 工作流类可共享 |
| 项目检查规范 | runbooks | 跨 agent 通用 |

### 4.3 必须私有

| Content | Owner | Reason |
|---------|-------|--------|
| memory.md | 各 agent | 私有记忆 |
| SESSION-STATE.md | 各 agent | 当前状态 |
| working-buffer.md | 各 agent | 工作焦点 |
| handoff.md | 各 agent | 交接摘要 |
| IDENTITY.md | 各 agent | 角色身份 |

---

## 5. 技术可行性

### 5.1 OpenClaw 配置能力

| Feature | Supported | Method |
|---------|-----------|--------|
| 共享 docs | ✅ | `memorySearch.extraPaths` |
| 共享 skills | ✅ | `skills.load.extraDirs` |
| 独立 workspace | ✅ | 默认行为 |
| 独立 agentDir | ✅ | 默认行为 |

### 5.2 配置位置

```
~/.openclaw/openclaw.json
  - agents[].memorySearch.extraPaths
  - agents[].skills.load.extraDirs
```

---

## 6. 推荐实施路径

### Phase 1: 目录设计
- 创建 `~/.openclaw/shared/` 目录结构
- 定义共享内容边界

### Phase 2: 配置草案
- 设计 CEO/main 的 extraPaths 配置
- 设计 skills.load.extraDirs 配置

### Phase 3: 样板文档
- 迁移高频共享内容到 shared 目录
- 创建至少 1 个共享 skill

### Phase 4: 验证
- CEO 能检索共享内容
- main 能检索共享内容
- 私有内容隔离

### Phase 5: 文档交付
- 架构说明
- 配置说明
- 迁移步骤
- 验证报告

---

## 7. 风险初步评估

| Risk | Level | Mitigation |
|------|-------|------------|
| 私有内容泄露 | Low | 明确边界，不共享私有文件 |
| 配置冲突 | Medium | 使用 extraPaths 而非替换 |
| 检索优先级 | Medium | 文档明确检索顺序 |
| 回滚复杂度 | Low | 配置可回滚 |

---

## 8. 下一步

1. **立即**: 创建共享目录结构
2. **Phase 1**: 设计目录布局
3. **Phase 2**: 配置草案
4. **Phase 3-5**: 实施验证
