# Directory Layout

**Version**: 1.0.0  
**Created**: 2026-03-09

---

## 1. Shared Directory Structure

```
~/.openclaw/shared/
├── docs/                           # 项目文档
│   └── PROJECT_OVERVIEW.md         # 项目概览
├── runbooks/                       # 操作手册
│   └── GATE_FLOW.md               # Gate A/B/C 流程
├── interfaces/                     # 接口规范
│   └── API_CONTRACTS.md           # API 契约
├── facts/                          # 项目事实
│   └── PROJECT_FACTS.md           # 项目事实库
├── systems/                        # 系统架构
│   └── SYSTEM_MAP.md              # 系统地图
└── skills/                         # 共享技能
    └── shared-workflow/            # 共享工作流技能
        └── SKILL.md
```

---

## 2. Directory Purpose

### 2.1 docs/

**Purpose**: 存放项目级文档，提供全局视角

| File | Content | Owner |
|------|---------|-------|
| PROJECT_OVERVIEW.md | 项目背景、目标、范围 | main |

**Update Rule**: 评审后更新

### 2.2 runbooks/

**Purpose**: 存放操作手册，标准化流程

| File | Content | Owner |
|------|---------|-------|
| GATE_FLOW.md | Gate A/B/C 流程说明 | main |

**Update Rule**: 流程变更时更新

### 2.3 interfaces/

**Purpose**: 存放接口规范，定义契约

| File | Content | Owner |
|------|---------|-------|
| API_CONTRACTS.md | API 契约定义 | main |

**Update Rule**: API 变更时更新

### 2.4 facts/

**Purpose**: 存放项目事实，作为真相来源

| File | Content | Owner |
|------|---------|-------|
| PROJECT_FACTS.md | 项目事实库 | main |

**Update Rule**: 事实变更时更新

### 2.5 systems/

**Purpose**: 存放系统架构，提供技术视角

| File | Content | Owner |
|------|---------|-------|
| SYSTEM_MAP.md | 系统架构图 | main |

**Update Rule**: 架构变更时更新

### 2.6 skills/

**Purpose**: 存放共享技能，提供工作流

| Directory | Content | Owner |
|-----------|---------|-------|
| shared-workflow/ | 共享工作流技能 | main |

**Update Rule**: 技能变更时更新

---

## 3. Owner Responsibility

### 3.1 Owner Definition

| Owner | Responsibility |
|-------|---------------|
| main | 主维护者，负责更新和评审 |
| CEO | 消费者，可读取但不能修改 |

### 3.2 Update Rules

| Category | Trigger | Reviewer |
|----------|---------|----------|
| docs | 项目重大变更 | CEO + main |
| runbooks | 流程变更 | CEO + main |
| interfaces | API 变更 | main |
| facts | 事实变更 | main |
| systems | 架构变更 | CEO + main |
| skills | 技能变更 | main |

---

## 4. Naming Conventions

### 4.1 File Naming

- 使用 `UPPER_SNAKE_CASE.md`
- 文件名应描述内容
- 避免缩写

### 4.2 Directory Naming

- 使用 `lowercase/`
- 目录名应描述类别
- 单数形式优先

---

## 5. Permissions

### 5.1 File Permissions

```bash
# Shared files
chmod 644 ~/.openclaw/shared/**/*.md

# Directories
chmod 755 ~/.openclaw/shared/*/
```

### 5.2 Access Control

| Agent | Read | Write |
|-------|------|-------|
| CEO | ✅ | ❌ |
| main | ✅ | ✅ |

---

## 6. Backup Strategy

### 6.1 Git Tracking

```bash
cd ~/.openclaw
git add shared/
git commit -m "Update shared knowledge"
git push
```

### 6.2 Version History

- 所有变更通过 git 追踪
- 使用语义化版本标签
- 保留历史版本

---

## 7. Cleanup Rules

### 7.1 Deprecated Content

```bash
# Move to archive instead of delete
mv ~/.openclaw/shared/docs/OLD_FILE.md ~/.openclaw/shared/docs/archive/
```

### 7.2 Archive Policy

- 过期内容移至 `archive/` 子目录
- 保留 90 天后删除
- 重要历史记录保留 git 标签
