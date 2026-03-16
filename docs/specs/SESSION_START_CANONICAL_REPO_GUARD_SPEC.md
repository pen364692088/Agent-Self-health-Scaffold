# Session-Start Canonical Repo Guard 规范

## 目的
防止新会话启动时 repo/workspace 漂移，确保所有操作在唯一合法 repo root 中执行。

---

## 适用场景
- 多项目环境（如 EgoCore, OpenEmotion, Agent-Self-health-Scaffold）
- 使用 /new 或会话重置
- 默认 workspace 与项目 repo 不同
- 需要跨会话保持 repo 一致性

---

## 核心组件

### 1. Canonical Repos Registry
**路径**: `config/canonical_repos.yaml`

```yaml
canonical_repos:
  <PROJECT_NAME>:
    canonical_root: "/absolute/path/to/canonical/repo"
    identifiers:
      git_remote: "git@github.com:org/repo.git"
    forbidden_alternatives:
      - path: "/path/to/wrong/workspace"
        reason: "说明为什么这里是禁止的"
    enforcement:
      block_if_wrong_repo: true
      auto_switch_allowed: true
```

### 2. Repo-Root Guard Tool
**路径**: `tools/repo-root-guard`

**功能**:
- 检查当前目录是否在 canonical repo
- 返回 block 或 switch 指令
- Exit code: 0=canonical, 1=可切换, 2=blocked

### 3. Session-Start Recovery Integration
**路径**: `tools/session-start-recovery`

**Gate Sequence**:
```
Gate R0: Repo Root Guard (MANDATORY)
  ↓
Gate R1: Session State Recovery
  ↓
Gate R2: Task Reclaimer
  ↓
Continue with task execution
```

---

## 集成步骤

### Step 1: 创建 Canonical Repos Registry
```bash
mkdir -p config
cat > config/canonical_repos.yaml << 'EOF'
canonical_repos:
  YOUR_PROJECT:
    canonical_root: "/path/to/your/canonical/repo"
    identifiers:
      git_remote: "git@github.com:org/repo.git"
    forbidden_alternatives:
      - path: "/path/to/wrong/workspace"
        reason: "Not the canonical repo"
    enforcement:
      block_if_wrong_repo: true
      auto_switch_allowed: true
EOF
```

### Step 2: 复制 Repo-Root Guard Tool
```bash
cp /home/moonlight/Project/Github/MyProject/Agent-Self-health-Scaffold/tools/repo-root-guard tools/
chmod +x tools/repo-root-guard
```

### Step 3: 更新 Session-Start Recovery
```python
# 在 main() 第一行添加 Gate R0
def main():
    # Gate R0: Repo Root Guard (MANDATORY)
    repo_guard_tool = WORKSPACE / "tools" / "repo-root-guard"
    if repo_guard_tool.exists():
        result = subprocess.run([str(repo_guard_tool), "--check", "--json"], ...)
        if result.returncode != 0:
            # Block and return action required
            sys.exit(2)
    # Continue with normal recovery...
```

### Step 4: 验证
```bash
# 测试 1: 在错误 workspace 启动
cd /wrong/workspace
./tools/session-start-recovery --recover
# 期望: BLOCK + action required

# 测试 2: 在 canonical repo 启动
cd /canonical/repo
./tools/session-start-recovery --recover
# 期望: SUCCESS
```

---

## 行为规范

### 正确行为
1. `/new` 新会话 → session-start-recovery → Gate R0
2. 如果 wrong repo → BLOCK (exit code 2) + action required
3. Agent 切换到 canonical repo
4. 重新执行 session-start-recovery → PASS
5. 继续任务执行

### 禁止行为
- ❌ 在 wrong repo 中继续执行任务
- ❌ 跳过 Gate R0 直接恢复 session state
- ❌ 在 wrong repo 中进行 mutation/test/git 操作

---

## 红线模板

```
凡是涉及 <PROJECT_NAME> 的任何会话启动、恢复、执行、测试、状态更新、git 操作，
必须先通过 Gate R0 canonical repo guard；
未命中唯一合法 repo root 时，一律不得继续。

唯一合法 repo root: <CANONICAL_ROOT>
禁止替代: <FORBIDDEN_WORKSPACES>
```

---

## 复用清单

| 项目 | Canonical Root | 状态 |
|------|----------------|------|
| Agent-Self-health-Scaffold | `/home/moonlight/Project/Github/MyProject/Agent-Self-health-Scaffold` | ✅ 已集成 |
| EgoCore | TBD | 🔜 待集成 |
| OpenEmotion | `/home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion` | 🔜 待集成 |

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-03-16 | 初始规范，关键冷启动样本 #7 验证通过 |

---

## 参考
- 验证报告: `artifacts/verification/CRITICAL_COLD_START_VERIFICATION_7.md`
- 实现示例: `Agent-Self-health-Scaffold` 项目
