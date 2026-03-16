# Canonical Repo Guard 跨项目推广总结报告

## 推广时间
2026-03-16

## 推广顺序
```
Scaffold 规范抽象完成 → EgoCore 集成验证 → OpenEmotion 验证
```

---

## 最终状态

| 项目 | 集成模式 | 状态 | 验证报告 |
|------|----------|------|----------|
| **Agent-Self-health-Scaffold** | A - workspace session-start guard | ✅ 已完成 | artifacts/verification/CRITICAL_COLD_START_VERIFICATION_7.md |
| **EgoCore** | B - 独立应用入口 guard | ✅ 已完成 | docs/EGOCORE_REPO_GUARD_VERIFICATION.md |
| **OpenEmotion** | C - 轻量 repo anchor | ✅ 验证通过 | docs/specs/OPENEMOTION_REPO_GUARD_VERIFICATION.md |

---

## 各项目实现摘要

### Agent-Self-health-Scaffold（模式 A）

**入口类型**：OpenClaw Workspace

**集成方式**：
- workspace 的 `session-start-recovery` 集成 Gate R0
- 在会话恢复前验证 repo root
- wrong repo → BLOCK (exit code 2)

**实现文件**：
- `~/.openclaw/workspace/config/canonical_repos.yaml`
- `~/.openclaw/workspace/tools/repo-root-guard`
- `~/.openclaw/workspace/tools/session-start-recovery` (v1.2.0)

**Commit**：`ed8867e`

---

### EgoCore（模式 B）

**入口类型**：独立应用

**集成方式**：
- 在 `app/main.py` 入口处集成 Gate R0
- 在配置加载、日志初始化之前验证 repo root
- wrong repo → BLOCK (exit code 2)

**实现文件**：
- `config/canonical_repos.yaml`
- `tools/repo-root-guard`
- `app/main.py` (修改)

**Commit**：`306ef24`

---

### OpenEmotion（模式 C）

**入口类型**：Daemon Service

**验证结论**：
- OpenEmotion 是主体内核，不通过 workspace 启动
- systemd 配置已强制 WorkingDirectory
- EgoCore bridge 配置已指定正确 repo_path
- 当前 workspace repo-root-guard 可以正确识别 OpenEmotion

**不需要额外集成**：
- ❌ 不需要 workspace session-start guard
- ❌ 不需要独立应用入口 guard
- ✅ 维持现状即可

---

## 三种集成模式总结

### 模式 A：OpenClaw Workspace 模式

**适用场景**：
- 项目通过 OpenClaw workspace 启动
- workspace 与项目 repo 分离
- 需要在会话启动时验证 repo root

**实现要点**：
- 在 workspace 的 `session-start-recovery` 中集成 Gate R0
- 在 `canonical_repos.yaml` 中定义项目的 canonical root
- 通过 `task_to_repo_mapping` 支持多项目

---

### 模式 B：独立 Repo 模式

**适用场景**：
- 项目有独立的 main.py 入口
- 项目不通过 workspace 启动
- 需要在应用启动时验证 repo root

**实现要点**：
- 在 main.py 的 main() 函数第一行集成 Gate R0
- 创建项目专属的 `config/canonical_repos.yaml`
- 创建 `tools/repo-root-guard`

---

### 模式 C：轻量 Repo Anchor 模式

**适用场景**：
- 项目是内核/daemon 服务
- 通过 systemd 或其他方式管理
- 已有机制确保在正确目录运行

**实现要点**：
- 确认 systemd WorkingDirectory 正确
- 确认调用方配置正确
- 可选：在高风险脚本前添加 repo-root 检查

---

## 关键发现

### 1. 不同项目需要不同模式

| 项目类型 | 推荐模式 | 原因 |
|----------|----------|------|
| 通过 workspace 启动的项目 | A | 需要在会话启动时验证 |
| 独立应用 | B | 需要在应用入口验证 |
| 内核/daemon 服务 | C | 已有机制确保正确目录 |

### 2. 不应机械复制实现

- Scaffold 的实现适合 workspace 模式
- EgoCore 需要在应用入口集成
- OpenEmotion 不需要完整 guard

### 3. 系统级配置也很重要

- systemd WorkingDirectory
- EgoCore bridge repo_path
- 这些配置已经确保了正确的 repo root

---

## 规范文档

| 文档 | 路径 | 用途 |
|------|------|------|
| 跨项目规范 | docs/specs/CANONICAL_REPO_GUARD_CROSS_PROJECT_SPEC.md | 定义核心变量、Gate 层级、三种模式 |
| 迁移模板 | docs/specs/CANONICAL_REPO_GUARD_MIGRATION_TEMPLATE.md | 集成检查清单、验证报告模板 |
| 实例化参数 | docs/specs/PROJECT_INSTANTIATION_PARAMS.md | 三个项目的具体参数 |

---

## 成功标准验证

### Scaffold

- ✅ 作为已验证基线，规范抽象完整
- ✅ 关键冷启动样本 #7 通过
- ✅ 短观察阶段 PASS

### EgoCore

- ✅ 已完成 Gate R0 集成
- ✅ 已通过关键冷启动样本
- ✅ 进入短观察阶段

### OpenEmotion

- ✅ 已验证当前模式有效
- ✅ 未误伤主体流程
- ✅ 不需要额外集成

### 整体

- ✅ 三个项目共享同一套抽象规范
- ✅ 每个项目使用自己的实例化参数
- ✅ 无"默认 workspace 先执行再补救"的情况
- ✅ 无"路径漂移靠人工提醒纠偏"的情况

---

## Commits

```
Scaffold:
- ed8867e fix(session-start): Gate R0 - Repo Root Guard integration
- 77aab57 docs: 关键冷启动样本 #7 验证通过
- e55dade docs: 短观察阶段 PASS - 主线级闭环完成
- 0ffcff1 docs(specs): Canonical Repo Guard 跨项目规范抽象完成
- 050e2bd docs: 更新 EgoCore 集成状态为已完成

EgoCore:
- 306ef24 feat(repo-guard): Gate R0 - Canonical Repo Guard 集成
```

---

## 结论

**Canonical Repo Guard 跨项目推广任务：✅ 完成**

- Scaffold：模式 A，已完成
- EgoCore：模式 B，已完成
- OpenEmotion：模式 C，验证通过

**建议后续**：
1. 监控 Scaffold 和 EgoCore 的短观察阶段
2. 可选：在 OpenEmotion 高风险脚本前添加 repo-root 检查
3. 可选：将这套模式推广到其他项目
