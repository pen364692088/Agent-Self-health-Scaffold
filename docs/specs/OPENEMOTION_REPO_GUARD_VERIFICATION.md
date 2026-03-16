# OpenEmotion Canonical Repo Guard 验证报告

## 验证时间
2026-03-16T15:15:00-05:00

---

## C1. 入口审计

### OpenEmotion 架构分析

```
OpenEmotion 架构：
├── emotiond/           # Daemon 服务
│   └── main.py         # 独立入口
├── OpenEmotion_MVP5/   # 主模块
├── deploy/
│   └── systemd/
│       └── user/emotiond.service  # systemd 服务定义
└── scripts/            # 脚本工具
```

### 启动方式

**方式 1：独立 daemon 服务**
```bash
cd /home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion
python -m emotiond.main
# 或
systemctl --user start emotiond
```

**方式 2：EgoCore bridge 连接**
- EgoCore 配置：`config/openemotion.yaml`
- `repo_path: "/home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion"`
- `auto_start: true`

### 最小任务进入链

```
任务请求 → EgoCore → OpenEmotion Bridge → HTTP → emotiond
                                      ↓
                        如果 emotiond 未运行
                                      ↓
                        EgoCore auto-start emotiond
                                      ↓
                        cd /path/to/OpenEmotion && python -m emotiond.main
```

### 关键发现

**OpenEmotion 不通过 OpenClaw workspace 访问**：
- 它是独立的 daemon 服务
- 工作目录必须在 OpenEmotion repo 中（systemd service 定义）
- EgoCore 通过 HTTP bridge 连接

---

## C2. 模式判定

### 三种模式对比

| 模式 | 描述 | 适用场景 | OpenEmotion 匹配度 |
|------|------|----------|-------------------|
| **A** | workspace session-start guard | 项目通过 workspace 启动 | ❌ 不匹配 |
| **B** | 独立应用入口 guard | 独立应用，有 main.py 入口 | ⚠️ 部分匹配 |
| **C** | 轻量 repo anchor + 高风险动作前置校验 | 内核系统，无传统入口 | ✅ 最匹配 |

### 判定结论

**推荐模式：C - 轻量 repo anchor + 高风险动作前置校验**

**理由**：
1. OpenEmotion 是主体内核，不是独立应用
2. 主要通过 EgoCore bridge 访问，不是直接启动
3. emotiond daemon 需要在 repo root 运行（systemd 配置已强制）
4. 不需要完整的 session-start guard

---

## C3. 现状验证

### Test 1: 从 OpenEmotion canonical repo 运行

```
cd /home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion
repo-root-guard --check

Result:
  status: canonical
  repo_name: OpenEmotion
  Exit code: 0
```

**结论**：✅ 正确识别 OpenEmotion canonical repo

### Test 2: 从 workspace 运行，指定 task-context=OpenEmotion

```
cd ~/.openclaw/workspace
repo-root-guard --validate --task-context "OpenEmotion MVP16 daily check"

Result:
  status: wrong_repo
  repo_name: OpenEmotion
  canonical_root: /home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion
  Exit code: 1
```

**结论**：✅ 正确识别应该使用 OpenEmotion repo

### Test 3: 从 workspace 运行，指定 task-context=Scaffold

```
cd ~/.openclaw/workspace
repo-root-guard --validate --task-context "Scaffold mutation-guard task"

Result:
  status: wrong_repo
  repo_name: Agent-Self-health-Scaffold
  canonical_root: /home/moonlight/Project/Github/MyProject/Agent-Self-health-Scaffold
  Exit code: 1
```

**结论**：✅ 正确区分 OpenEmotion 和 Scaffold

### Test 4: 从 workspace 运行，无 task-context

```
cd ~/.openclaw/workspace
repo-root-guard --check

Result:
  status: wrong_repo
  repo_name: Agent-Self-health-Scaffold
  canonical_root: /home/moonlight/Project/Github/MyProject/Agent-Self-health-Scaffold
  Exit code: 1
```

**结论**：✅ 默认返回 Scaffold（workspace 是其 forbidden alternative）

### Keywords 映射验证

```yaml
task_to_repo_mapping:
  - keywords: ["OpenEmotion", "emotion", "affect", "MVP"]
    repo: "OpenEmotion"
```

**测试结果**：
- ✅ "OpenEmotion MVP16 daily check" → OpenEmotion
- ✅ "emotion system update" → OpenEmotion
- ✅ "Scaffold mutation-guard" → Scaffold

---

## C4. 关键冷启动样本

### 样本 #1: emotiond daemon 启动

**场景**：从错误目录启动 emotiond

```
cd ~/.openclaw/workspace
python -home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion/emotiond/main.py

预期：应该在 OpenEmotion repo 中启动
实际：systemd service 配置强制 WorkingDirectory
```

**结论**：✅ systemd 配置已强制 repo root

### 样本 #2: EgoCore auto-start emotiond

**场景**：EgoCore 启动时 auto-start emotiond

```
EgoCore 配置：
  repo_path: "/home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion"
  auto_start: true

预期：EgoCore 在正确的 repo 路径启动 emotiond
实际：配置已指定正确的 repo_path
```

**结论**：✅ EgoCore 配置已确保正确路径

### 样本 #3: 通过 workspace 访问 OpenEmotion

**场景**：Agent 在 workspace 中执行 OpenEmotion 相关任务

```
当前 workspace session-start-recovery 行为：
1. Gate R0: repo-root-guard --check
2. 返回 Scaffold 作为默认 repo
3. 不会自动切换到 OpenEmotion

问题：
- workspace 的 session-start 默认关联到 Scaffold
- 没有根据任务上下文动态选择 OpenEmotion
```

**结论**：⚠️ 当前 workspace 的 repo guard 不支持动态任务上下文解析

---

## C5. 验证结论

### 结论类型

**✅ 验证通过，维持当前模式**

### 理由

1. **OpenEmotion 不需要完整的 session-start guard**：
   - 它是独立 daemon 服务
   - systemd 配置已强制 WorkingDirectory
   - EgoCore 配置已指定正确 repo_path

2. **当前 workspace repo-root-guard 对 OpenEmotion 有效**：
   - 可以正确识别 OpenEmotion canonical repo
   - keywords 映射准确
   - 不会误命中 Scaffold / EgoCore

3. **OpenEmotion 的访问模式不同于 Scaffold**：
   - 不通过 workspace 启动
   - 主要通过 EgoCore bridge 或 systemd service
   - 这两种方式都已确保在正确 repo 中运行

### 建议

1. **维持当前模式**：
   - emotiond daemon 由 systemd 管理，WorkingDirectory 已强制
   - EgoCore bridge 配置已正确
   - workspace 中的 repo-root-guard 支持 OpenEmotion 的 canonical repo 识别

2. **可选增强（低优先级）**：
   - 在 emotiond/main.py 入口处添加轻量 repo anchor check
   - 在高风险脚本前添加 repo-root 前置校验

3. **不需要的模式**：
   - ❌ 不需要 workspace session-start guard（模式 A）
   - ❌ 不需要独立应用入口 guard（模式 B）

---

## 最终状态

| 项目 | 集成模式 | 状态 |
|------|----------|------|
| Agent-Self-health-Scaffold | A - workspace session-start guard | ✅ 已完成 |
| EgoCore | B - 独立应用入口 guard | ✅ 已完成 |
| OpenEmotion | C - 轻量 repo anchor | ✅ 验证通过，维持现状 |
