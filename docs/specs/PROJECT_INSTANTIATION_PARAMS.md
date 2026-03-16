# 项目实例化参数

## 已验证项目

### Agent-Self-health-Scaffold

```yaml
project_name: "Agent-Self-health-Scaffold"
canonical_repo_root: "/home/moonlight/Project/Github/MyProject/Agent-Self-health-Scaffold"
git_remote: "git@github.com:pen364692088/Agent-Self-health-Scaffold.git"

session_start_entry:
  type: "openclaw_workspace"
  path: "/home/moonlight/.openclaw/workspace/tools/session-start-recovery"
  
wrong_repo_policy: "block"

forbidden_alternatives:
  - path: "/home/moonlight/.openclaw/workspace"
    reason: "workspace 是 OpenClaw 默认工作区，不是 Scaffold 项目仓库"

integration_mode: "A - OpenClaw Workspace 模式"
status: "✅ 已完成"
verification: "artifacts/verification/CRITICAL_COLD_START_VERIFICATION_7.md"
```

---

## 待集成项目

### EgoCore

```yaml
project_name: "EgoCore"
canonical_repo_root: "/home/moonlight/Project/Github/MyProject/EgoCore"
git_remote: "https://github.com/pen364692088/EgoCore.git"

session_start_entry:
  type: "independent_repo"  # 独立应用
  path: "/home/moonlight/Project/Github/MyProject/EgoCore/app/main.py"
  
wrong_repo_policy: "block"

forbidden_alternatives:
  - path: "/home/moonlight/.openclaw/workspace"
    reason: "OpenClaw 默认 workspace，不是 EgoCore 项目仓库"
  - path: "/home/moonlight/Project/Github/MyProject/Agent-Self-health-Scaffold"
    reason: "Scaffold 项目仓库，不是 EgoCore"

integration_mode: "B - 独立 Repo 模式"
status: "✅ 已完成"
verification: "docs/EGOCORE_REPO_GUARD_VERIFICATION.md"
commit: "306ef24"

# 特殊说明
notes: |
  EgoCore 是独立 Telegram Agent Runtime
  通过 python app/main.py 启动
  Gate R0 已集成在应用入口处
```

### OpenEmotion

```yaml
project_name: "OpenEmotion"
canonical_repo_root: "/home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion"
git_remote: "git@github.com:pen364692088/OpenEmotion.git"

session_start_entry:
  type: "openclaw_workspace"  # 主要通过 workspace 访问
  path: "/home/moonlight/.openclaw/workspace/tools/session-start-recovery"
  
wrong_repo_policy: "block"

forbidden_alternatives:
  - path: "/home/moonlight/.openclaw/workspace"
    reason: "OpenClaw 默认 workspace，不是 OpenEmotion 项目仓库"

integration_mode: "A - OpenClaw Workspace 模式"
status: "🔜 待集成"

# 特殊说明
notes: |
  OpenEmotion 更偏主体核心系统
  当前主要通过 OpenClaw workspace 访问
  已在 workspace 的 canonical_repos.yaml 中定义
  但 session-start 的 repo guard 可能需要细化判断逻辑
```

---

## 集成模式对照

| 项目 | 模式 | 入口类型 | 集成方式 |
|------|------|----------|----------|
| Agent-Self-health-Scaffold | A | OpenClaw Workspace | workspace 的 session-start-recovery 已集成 |
| EgoCore | B | 独立应用 | 需要在 app/main.py 中集成 repo guard |
| OpenEmotion | A | OpenClaw Workspace | 已定义，需验证判断逻辑 |

---

## 下一步

### Phase B: EgoCore 集成
1. 在 EgoCore 创建 `config/canonical_repos.yaml`
2. 创建 `tools/repo-root-guard`（复制并修改）
3. 在 `app/main.py` 开头集成 repo guard
4. 验证：正确 repo = allow, 错误 repo = block

### Phase C: OpenEmotion 验证
1. 验证 workspace 的 repo-root-guard 是否能正确识别 OpenEmotion 任务
2. 验证 keywords 映射是否准确
3. 运行关键冷启动样本验证
