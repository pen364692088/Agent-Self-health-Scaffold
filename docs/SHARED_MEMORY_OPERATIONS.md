# Shared Memory Operations Guide

**Version**: 1.0.0
**Created**: 2026-03-09

---

## 1. Overview

本文档说明共享知识库的日常运维操作。

---

## 2. Quick Reference

### 2.1 同步共享知识

```bash
# 一键同步所有 agent
~/.openclaw/workspace/tools/sync-shared-memory

# 仅同步 main
~/.openclaw/workspace/tools/sync-shared-memory --agent main

# 预览模式（不实际执行）
~/.openclaw/workspace/tools/sync-shared-memory --dry-run
```

### 2.2 添加新共享文档

```bash
# 1. 创建文档
echo "# New Doc" > ~/.openclaw/shared/docs/NEW_DOC.md

# 2. 同步到所有 workspace
~/.openclaw/workspace/tools/sync-shared-memory
```

### 2.3 更新共享文档

```bash
# 直接编辑共享目录中的文件
vim ~/.openclaw/shared/facts/PROJECT_FACTS.md

# 重新索引（让 memory search 生效）
openclaw memory index
```

---

## 3. Directory Structure

```
~/.openclaw/
├── shared/                      # 共享知识库（单一真相来源）
│   ├── docs/                    # 项目文档
│   │   └── PROJECT_OVERVIEW.md
│   ├── facts/                   # 项目事实
│   │   └── PROJECT_FACTS.md
│   ├── runbooks/                # 运维手册
│   │   └── GATE_FLOW.md
│   ├── interfaces/              # 接口契约
│   │   └── API_CONTRACTS.md
│   ├── systems/                 # 系统说明
│   │   └── SYSTEM_MAP.md
│   └── skills/                  # 共享技能
│       └── shared-workflow/SKILL.md
│
├── workspace/                   # main agent
│   ├── memory.md                # 私有记忆（隔离）
│   └── memory/shared/           # 共享知识符号链接
│       ├── PROJECT_FACTS.md -> ~/.openclaw/shared/facts/...
│       └── PROJECT_OVERVIEW.md -> ~/.openclaw/shared/docs/...
│
└── workspace-ceo/               # CEO agent
    ├── MEMORY.md                # 私有记忆（隔离）
    └── memory/shared/           # 共享知识符号链接
        ├── PROJECT_FACTS.md -> ~/.openclaw/shared/facts/...
        └── PROJECT_OVERVIEW.md -> ~/.openclaw/shared/docs/...
```

---

## 4. Content Guidelines

### 4.1 应放入共享层的内容

| 类型 | 例子 |
|------|------|
| 项目事实 | Gate 流程、子代理架构、任务完成协议 |
| 运维手册 | 部署流程、回滚流程、健康检查 |
| 接口契约 | API schema、CLI 参数、事件格式 |
| 系统说明 | 模块边界、依赖关系、ownership |

### 4.2 必须保留私有的内容

| 类型 | 位置 | Owner |
|------|------|-------|
| 会话状态 | SESSION-STATE.md | 各 agent |
| 工作焦点 | working-buffer.md | 各 agent |
| 私有记忆 | MEMORY.md / memory.md | 各 agent |
| 交接摘要 | handoff.md | 各 agent |
| 角色身份 | IDENTITY.md, SOUL.md | 各 agent |

---

## 5. Maintenance Tasks

### 5.1 定期检查

```bash
# 检查共享目录状态
ls -la ~/.openclaw/shared/*/

# 检查符号链接状态
ls -la ~/.openclaw/workspace/memory/shared/
ls -la ~/.openclaw/workspace-ceo/memory/shared/

# 验证隔离
grep -r "PRIVATE_TEST" ~/.openclaw/shared/ 2>/dev/null || echo "OK: No private content in shared"
```

### 5.2 清理失效链接

```bash
# 同步脚本会自动清理
~/.openclaw/workspace/tools/sync-shared-memory
```

### 5.3 重新索引

```bash
# 如果 memory search 找不到共享内容
openclaw memory index

# 或针对特定 agent
openclaw memory index --agent main
openclaw memory index --agent ceo
```

---

## 6. Troubleshooting

### 6.1 某个 agent 找不到共享内容

```bash
# 检查符号链接
ls -la ~/.openclaw/workspace/memory/shared/

# 重新同步
~/.openclaw/workspace/tools/sync-shared-memory --agent <agent_name>

# 重新索引
openclaw memory index --agent <agent_name>
```

### 6.2 共享内容更新后未生效

```bash
# Memory 索引可能过期
openclaw memory index
```

### 6.3 符号链接断裂

```bash
# 删除并重建
rm -rf ~/.openclaw/workspace/memory/shared/*
rm -rf ~/.openclaw/workspace-ceo/memory/shared/*
~/.openclaw/workspace/tools/sync-shared-memory
```

---

## 7. Ownership & Update Rules

| 目录 | Owner | Update Process |
|------|-------|----------------|
| shared/docs/ | Project Team | PR review |
| shared/facts/ | Architecture Lead | Gate approval |
| shared/runbooks/ | Operations | Version control |
| shared/interfaces/ | API Team | Contract test |
| shared/systems/ | Architecture Lead | Review cycle |

---

## 8. Version History

| Date | Version | Change |
|------|---------|--------|
| 2026-03-09 | 1.0.0 | Initial operations guide |
