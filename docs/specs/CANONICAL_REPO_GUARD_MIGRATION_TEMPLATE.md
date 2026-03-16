# Canonical Repo Guard 迁移模板

## 使用说明

本文档是迁移 Canonical Repo Guard 到新项目的模板。复制此模板并根据项目实际情况填写参数。

---

## 项目信息

```yaml
project_name: ""  # 项目名称，如 "EgoCore", "OpenEmotion"
canonical_repo_root: ""  # 绝对路径，如 "/home/user/projects/EgoCore"
git_remote: ""  # git remote URL，如 "git@github.com:org/repo.git"
```

---

## Session Start Entry 分析

### 问题 1：项目如何启动？

- [ ] OpenClaw Workspace 模式：通过 `~/.openclaw/workspace-{name}` 启动
- [ ] 独立 Repo 模式：项目有自己的 tools/session-start-recovery
- [ ] 脚本执行模式：通过 scripts 目录中的脚本直接执行

### 问题 2：当前入口是什么？

```
# 填写实际的入口路径
session_start_entry:
  type: ""  # openclaw_workspace | independent_repo | script_execution
  path: ""  # 实际入口路径
```

### 问题 3：当前是否存在 repo 漂移风险？

- [ ] 是：曾经发生过在错误 repo 中执行任务
- [ ] 否：当前工作流稳定

---

## 实例化参数

```yaml
# === 必填参数 ===
project_name: ""
canonical_repo_root: ""
git_remote: ""

# === session_start_entry ===
session_start_entry:
  type: ""  # 必须从上述三种模式中选择
  path: ""

# === wrong_repo_policy ===
wrong_repo_policy: "block"  # 推荐 block

# === forbidden_alternatives ===
forbidden_alternatives:
  - path: "/home/moonlight/.openclaw/workspace"
    reason: "OpenClaw 默认 workspace，不是本项目仓库"
  - path: ""  # 添加其他禁止的路径
    reason: ""

# === 回归测试清单 ===
regression_tests:
  - correct_repo_allow
  - wrong_repo_block
  - critical_cold_start_sample
  # 添加项目特定的测试场景
```

---

## 集成检查清单

### Phase 1：仓库定位与入口确认

- [ ] 确认 canonical_repo_root 路径正确
- [ ] 确认 git remote 正确
- [ ] 确认 session_start_entry 实际位置
- [ ] 分析当前是否存在默认 workspace 漂移风险
- [ ] 分析当前 mutation/test/git 是否已有部分 preflight

### Phase 2：Gate R0 集成

- [ ] 在 session_start_entry 前置接入 canonical repo resolve
- [ ] 在 session_start_entry 前置接入 repo root validate
- [ ] 在 session_start_entry 前置接入 wrong repo block
- [ ] 验证：正确 repo = allow
- [ ] 验证：错误 repo = block

### Phase 3：项目内 repo-root preflight（可选）

- [ ] 在 mutation 操作前置校验
- [ ] 在 test 操作前置校验
- [ ] 在 git 操作前置校验
- [ ] 验证：项目内动作不能绕过 repo-root 校验

### Phase 4：回归测试与冷启动验证

- [ ] 正确 repo allow
- [ ] 错误 repo block
- [ ] /new 冷启动首次任务无人工干预验证
- [ ] 状态更新命中 canonical target
- [ ] git 动作不绕过 preflight

### Phase 5：短观察阶段

- [ ] /new 后第一次任务是否先验 repo root
- [ ] 错误 workspace 是否稳定 block
- [ ] 是否存在误拦截
- [ ] 状态更新 / 测试 / git 动作口径是否一致

---

## 验证报告模板

```markdown
# <PROJECT_NAME> Canonical Repo Guard 集成验证报告

## 验证时间
YYYY-MM-DD

## 项目实例化参数
- project_name: 
- canonical_repo_root: 
- session_start_entry: 
- wrong_repo_policy: 

## 验证结果

### STEP 1: 从默认 workspace 启动
```
Current directory: <默认 workspace>
```

### STEP 2: 执行 session-start-recovery
```
Output: 
Exit code: 
```

**验证点**：
- [ ] Repo-Root Guard 在 session-start 入口层执行
- [ ] 正确检测到 wrong repo
- [ ] 返回 block 消息和 action required
- [ ] Exit code 正确

### STEP 3: 切换到 canonical repo
```
Action: cd <canonical_repo_root>
New directory: 
```

### STEP 4: 在 canonical repo 中重新执行
```
Output:
Exit code:
```

**验证点**：
- [ ] 在 canonical repo 中，repo-root-guard 返回 allow
- [ ] Session state 成功恢复（如果有）
- [ ] Exit code 为 0

### STEP 5: 在 canonical repo 中执行项目任务
```
Verification:
- 关键文件检查:
- git remote 验证:
- repo-root-guard 验证:
```

## 结论

- [ ] 关键冷启动样本通过
- [ ] 可以进入短观察阶段
```

---

## 文件清单

集成完成后，项目应包含以下文件（根据模式不同）：

### OpenClaw Workspace 模式
- 在 workspace 的 `config/canonical_repos.yaml` 中添加项目定义
- 无需在项目中创建额外文件

### 独立 Repo 模式
- `config/canonical_repos.yaml` - Canonical repos registry
- `tools/repo-root-guard` - Repo root 验证工具
- `tools/session-start-recovery` (修改) - 集成 Gate R0

### 脚本执行模式
- `scripts/repo-guard.sh` - Repo guard 脚本
- 关键脚本修改（在开头 source repo-guard.sh）

---

## 禁止事项

- ❌ 直接复制 Scaffold 的路径和文件名
- ❌ 在未验证 EgoCore 前同时修改 OpenEmotion
- ❌ 把 OpenEmotion 当成和 Scaffold 一样的执行壳处理
- ❌ 只补文档不接 session-start 入口
- ❌ 用 "remote 相同" 替代 "canonical repo root 正确"
