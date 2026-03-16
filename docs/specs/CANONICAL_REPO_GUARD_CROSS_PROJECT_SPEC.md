# Canonical Repo Guard 跨项目规范 v1.0

## 文档信息
- **版本**: v1.0
- **日期**: 2026-03-16
- **状态**: 规范抽象完成，待推广
- **基线项目**: Agent-Self-health-Scaffold

---

## 0. 目的

定义跨项目可复用的 Canonical Repo Guard 规范，防止新会话启动时 repo/workspace 漂移。

**核心问题**：新会话 / 新任务 / 新入口下，系统是否会先命中唯一合法 repo root，而不是先掉进默认 workspace 或错误目录。

---

## 1. 三个核心变量

### A. canonical_repo_root

**定义**：每个项目唯一合法仓库根目录。

**约束**：
- 必须是绝对路径
- 必须是 git 仓库根目录
- 不能是 symbolic link
- 不能是 workspace 或 worktree

**判定逻辑**：
```
current_dir == canonical_repo_root OR current_dir starts with canonical_repo_root + "/"
```

### B. session_start_entry

**定义**：每个项目"新会话 / 会话恢复 / 启动前置"的真正入口点。

**类型**：
1. **OpenClaw Workspace 模式**：通过 `~/.openclaw/workspace-{name}/tools/session-start-recovery` 启动
2. **独立 Repo 模式**：项目有自己的 `tools/session-start-recovery` 或等价入口
3. **脚本执行模式**：项目通过脚本直接执行，需要在前置脚本中加入 repo guard

**判定标准**：
- 该入口是否在新会话/新任务时最先被调用
- 该入口是否能阻断后续执行

### C. wrong_repo_policy

**定义**：若未命中 canonical repo root，系统的行为。

**可选值**：
- `block`：直接阻断，返回错误消息，要求手动切换
- `switch_then_continue`：自动切换到 canonical repo 并继续执行

**默认优先**：`block` > `switch_then_continue`

**原因**：block 更可审计、更稳。

---

## 2. Gate 层级设计

```
Gate R0: Canonical Repo Guard (session-start 入口层)
  ↓
Gate R1: Session State Recovery
  ↓
Gate R2: Task Reclaimer
  ↓
Gate M0: Mutation Preflight (项目内执行层)
  ↓
Task Execution
```

### Gate R0 vs Gate M0

| Gate | 层级 | 触发时机 | 作用 |
|------|------|----------|------|
| R0 | session-start 入口层 | 新会话/会话恢复 | 防止启动时 repo 漂移 |
| M0 | 项目内执行层 | mutation/test/git | 防止执行时 repo 漂移 |

**优先级**：R0 > M0

**原因**：入口层拦截比执行层拦截更早、更彻底。

---

## 3. 行为规范

### 正确行为
```
/new 新会话
  ↓
session-start-entry
  ↓
Gate R0: Repo Root Guard
  ↓ current_dir == canonical_repo_root?
  ├─ YES → Continue to Gate R1
  └─ NO  → BLOCK (exit code 2) + action required
           return {"action_required": "cd <canonical_repo_root>"}
```

### 禁止行为
- ❌ 在 wrong repo 中继续执行任务
- ❌ 跳过 Gate R0 直接恢复 session state
- ❌ 在 wrong repo 中进行 mutation/test/git 操作
- ❌ 用 "remote 相同" 替代 "canonical repo root 正确"

---

## 4. 证据链字段

每次 repo guard 检查必须记录：

```json
{
  "timestamp": "ISO8601",
  "event": "repo_guard_check",
  "current_dir": "/path/to/current",
  "canonical_root": "/path/to/canonical",
  "repo_name": "PROJECT_NAME",
  "status": "canonical | wrong_repo | blocked",
  "can_auto_switch": true | false,
  "action_taken": "allow | block | switch"
}
```

---

## 5. 回归测试集合

### 必须覆盖的场景

| 场景 | 预期行为 | 验证方法 |
|------|----------|----------|
| 正确 repo 启动 | allow (exit code 0) | cd canonical_repo; session-start-recovery |
| 错误 repo 启动 | block (exit code 2) | cd wrong_repo; session-start-recovery |
| 默认 workspace 启动 | block (exit code 2) | cd ~/.openclaw/workspace; session-start-recovery |
| 项目内 mutation | repo check before mutation | 在 wrong repo 中尝试 mutation |
| 项目内 test | repo check before test | 在 wrong repo 中尝试 test |
| 项目内 git | repo check before git | 在 wrong repo 中尝试 git commit |

### 关键冷启动样本

**定义**：无人工干预的新会话首次任务。

**验收标准**：
1. /new 新会话
2. 无人工纠偏
3. 第一次项目相关任务
4. 先验证 repo root
5. 实际执行仅发生在 canonical_repo_root

---

## 6. 项目实例化参数

每个项目需要定义以下参数：

```yaml
project_name: "PROJECT_NAME"
canonical_repo_root: "/absolute/path/to/repo"
git_remote: "git@github.com:org/repo.git"

# session_start_entry 取决于项目类型
session_start_entry:
  type: "openclaw_workspace | independent_repo | script_execution"
  path: "/path/to/entry"  # 如果是独立模式

wrong_repo_policy: "block"  # 或 "switch_then_continue"

forbidden_alternatives:
  - path: "/path/to/wrong/workspace"
    reason: "说明为什么这里是禁止的"

regression_tests:
  - correct_repo_allow
  - wrong_repo_block
  - critical_cold_start_sample
```

---

## 7. 集成模式

### 模式 A：OpenClaw Workspace 模式

**适用项目**：通过 OpenClaw workspace 启动的项目

**特点**：
- workspace 作为项目入口
- 项目 repo 与 workspace 可能分离
- 需要在 workspace 的 session-start-recovery 中集成 Gate R0

**实现**：
1. 在 workspace 的 `config/canonical_repos.yaml` 中定义项目
2. 在 workspace 的 `tools/session-start-recovery` 中集成 Gate R0
3. Gate R0 根据任务上下文解析应该使用哪个 canonical repo

### 模式 B：独立 Repo 模式

**适用项目**：有独立 session-start 入口的项目

**特点**：
- 项目有自己的 tools 目录
- 项目有自己的 session-start-recovery 或等价入口
- 项目 repo 本身就是 workspace

**实现**：
1. 复制 repo-root-guard 到项目的 tools 目录
2. 在项目的 session-start 入口中集成 Gate R0
3. 创建项目专属的 canonical_repos.yaml

### 模式 C：脚本执行模式

**适用项目**：通过脚本直接执行，没有 session-start 入口

**特点**：
- 项目通过 scripts 目录中的脚本执行
- 没有会话恢复机制
- 需要在关键脚本前加入 repo guard

**实现**：
1. 在 scripts 目录中创建 repo-guard.sh
2. 在关键脚本开头 source repo-guard.sh
3. 如果 wrong repo，脚本直接退出

---

## 8. 推广顺序

```
Scaffold 规范抽象完成 → EgoCore 集成验证 → OpenEmotion 集成验证
```

**禁止**：两边同时推广。

**原因**：并行扩散会把问题面放大，排障成本更高。

---

## 9. 红线模板

```
凡是涉及 <PROJECT_NAME> 的任何会话启动、恢复、执行、测试、状态更新、git 操作，
必须先通过 Gate R0 canonical repo guard；
未命中唯一合法 repo root 时，一律不得继续。

唯一合法 repo root: <CANONICAL_REPO_ROOT>
禁止替代: <FORBIDDEN_WORKSPACES>
```

---

## 10. 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-03-16 | 初始规范，从 Scaffold 提炼抽象 |

---

## 11. 参考

- 基线实现: `Agent-Self-health-Scaffold`
- 验证报告: `artifacts/verification/CRITICAL_COLD_START_VERIFICATION_7.md`
- 实现规范: `docs/specs/SESSION_START_CANONICAL_REPO_GUARD_SPEC.md`
