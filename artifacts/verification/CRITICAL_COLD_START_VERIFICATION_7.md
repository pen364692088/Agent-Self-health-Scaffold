# 关键冷启动样本 #7 验证报告

## 验证时间
2026-03-16T17:15:00-05:00

## 验证目标
验证 Session-Start Canonical Repo Guard 是否正确集成到 session-start 入口层

## 验证场景
1. /new 新会话
2. 无人工干预
3. 第一次 Scaffold 相关任务
4. 先验证 repo root
5. 实际执行仅发生在 `/home/moonlight/Project/Github/MyProject/Agent-Self-health-Scaffold`

---

## 验证结果：✅ PASS

### STEP 1: 从默认 workspace 启动
```
Current directory: /home/moonlight/.openclaw/workspace
```

### STEP 2: 执行 session-start-recovery
```
Output:
{
  "repo_guard": "BLOCKED",
  "status": "wrong_repo",
  "current_dir": "/home/moonlight/.openclaw/workspace",
  "canonical_root": "/home/moonlight/Project/Github/MyProject/Agent-Self-health-Scaffold",
  "repo_name": "Agent-Self-health-Scaffold",
  "action_required": "cd /home/moonlight/Project/Github/MyProject/Agent-Self-health-Scaffold"
}

Exit code: 2
```

**验证点**：
- ✅ Repo-Root Guard 在 session-start 入口层执行
- ✅ 正确检测到 wrong repo
- ✅ 返回 block 消息和 action required
- ✅ Exit code 为 2（blocked）

### STEP 3: 执行切换
```
Action: cd /home/moonlight/Project/Github/MyProject/Agent-Self-health-Scaffold
New directory: /home/moonlight/Project/Github/MyProject/Agent-Self-health-Scaffold
```

### STEP 4: 在 canonical repo 中重新执行 session-start-recovery
```
Output:
✅ Session state recovered
  ✅ branch: main
  ✅ blocker: 无

Exit code: 0
```

**验证点**：
- ✅ 在 canonical repo 中，repo-root-guard 返回 status: "canonical"
- ✅ Session state 成功恢复
- ✅ Exit code 为 0（success）

### STEP 5: 在 canonical repo 中执行 Scaffold 任务
```
Verification:
- docs/memory/CANONICAL_OBJECT_REGISTRY.yaml: ✅ Present
- tools/repo-root-guard: ✅ Present
- tools/session-start-recovery: ✅ Present
- git remote: git@github.com:pen364692088/Agent-Self-health-Scaffold.git

repo-root-guard --check:
{
  "status": "canonical",
  "current_dir": "/home/moonlight/Project/Github/MyProject/Agent-Self-health-Scaffold",
  "canonical_root": "/home/moonlight/Project/Github/MyProject/Agent-Self-health-Scaffold",
  "repo_name": "Agent-Self-health-Scaffold"
}
```

---

## 实现摘要

### 新增文件

| 文件 | 路径 | 用途 |
|------|------|------|
| canonical_repos.yaml | config/canonical_repos.yaml | 定义唯一合法 repo root |
| repo-root-guard | tools/repo-root-guard | Repo root 验证工具 |
| SESSION-STATE.md | SESSION-STATE.md | 迁移到 canonical repo |

### 修改文件

| 文件 | 变更 |
|------|------|
| session-start-recovery | v1.1.1 → v1.2.0，添加 Gate R0: Repo Root Guard |

### Gate Sequence

```
Gate R0: Repo Root Guard (MANDATORY)
  ↓ 如果 wrong repo → BLOCK (exit code 2)
  ↓ 如果 canonical repo → 继续
Gate R1: Session State Recovery
  ↓
Gate R2: Task Reclaimer
  ↓
Continue with task execution
```

---

## 用户强制要求验证

| 要求 | 状态 | 说明 |
|------|------|------|
| 不接受 "remote 相同即 workspace 正确" | ✅ | 通过 canonical_root 路径精确匹配 |
| 在 session-start 入口前置接入 | ✅ | Gate R0 是 main() 第一个检查 |
| 错误 workspace 时 block/切正 | ✅ | 返回 block 消息 + action required |
| repo-root validation 是硬前置 | ✅ | Exit code 2，不继续任何操作 |
| 实际执行仅发生在 canonical repo | ✅ | 验证步骤 5 确认 |

---

## Commit

```
ed8867e fix(session-start): Gate R0 - Repo Root Guard integration
```

## 推送状态
✅ 已推送到 origin/main

---

## 结论

**关键冷启动样本 #7: PASS**

Repo-Root Preflight 已成功集成到 session-start 入口层：
1. ✅ 在 session-start-recovery main() 第一行执行
2. ✅ 正确检测 wrong repo 并 block
3. ✅ 返回明确的 action required
4. ✅ 在 canonical repo 中可正常继续
5. ✅ 所有 Scaffold 任务在 canonical repo 中执行
