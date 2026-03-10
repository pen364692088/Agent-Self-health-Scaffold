# Callpath Annotation Report

Date: 2026-03-10
Version: 1.0
Purpose: 非行为改变型标记 - 记录调用关系

---

## 调用关系约定

### 符号

| 符号 | 含义 |
|------|------|
| `→` | 直接调用 |
| `⇢` | 可选调用 |
| `↻` | 内部循环 |
| `⚡` | 事件触发 |

---

## 1. 子代理编排调用链

### 主入口: `subtask-orchestrate`

```
subtask-orchestrate run
  → sessions_spawn (OpenClaw API)
    → subagent session
  → write receipt to subagent-inbox/
  ⚡ callback-worker.path triggers
    → callback-worker.service
      → openclaw message send

subtask-orchestrate status
  → read subagent-inbox/
  → parse receipts
  → return status

subtask-orchestrate resume
  → read pending receipts
  → determine next action
  → spawn if needed
```

### 调试入口: `spawn-with-callback`

```
spawn-with-callback
  → sessions_spawn (OpenClaw API)
  → set callback handler
  ⇢ write to subagent-inbox/
```

### 底层入口: `sessions_spawn`

```
sessions_spawn (OpenClaw API)
  → create isolated session
  → run task
  → return result
```

---

## 2. 记忆检索调用链

### 主入口: `session-query`

```
session-query <query>
  → sqlite3 session_index.db
  ⇢ openviking find (fallback)
  → return results
```

### 专用入口: `context-retrieve`

```
context-retrieve
  → capsule retrieval (L1)
  ⇢ openviking find (L2)
  → return context
```

### 自动化入口: `session-start-recovery`

```
session-start-recovery
  → read SESSION-STATE.md
  → read working-buffer.md
  → read handoff.md
  ⇢ session-query (optional)
  → restore state
```

### 底层入口: `openviking find`

```
openviking find <query>
  → query vector index
  → return results
```

---

## 3. 状态写入调用链

### 主入口: `safe-write`

```
safe-write <path> <content>
  → policy-eval --path <path> --tool write
  → if ALLOW:
      → write file atomically
  → if DENY:
      → return error
```

### 主入口: `safe-replace`

```
safe-replace <path> <old> <new>
  → policy-eval --path <path> --tool replace
  → if ALLOW:
      → read file
      → replace content
      → write atomically
  → if DENY:
      → return error
```

### 专用入口: `state-write-atomic`

```
state-write-atomic <path> <content>
  → write to temp file
  → fsync
  → rename to target
  → return success
```

---

## 4. 任务完成调用链

### 主入口: `verify-and-close`

```
verify-and-close --task-id <id>
  → check contract receipt
  → check e2e receipt (optional)
  → check preflight receipt
  → check final receipt
  → if all pass:
      → mark READY_TO_CLOSE
  → else:
      → mark BLOCKED
```

### 强制执行: `enforce-task-completion`

```
enforce-task-completion --task-id <id>
  → verify-and-close --json
  → if not READY_TO_CLOSE:
      → BLOCK output
  → if READY_TO_CLOSE:
      → ALLOW output
```

### 安全消息: `safe-message`

```
safe-message --task-id <id> --message <msg>
  → output-interceptor check
  → verify receipts exist
  → detect pseudo-completion text
  → if ALLOW:
      → message tool send
  → if BLOCK:
      → return error
```

---

## 5. Context Compression 调用链

### 专用入口: `context-compress`

```
context-compress
  → context-budget-check
  → if pressure > threshold:
      → capsule-builder
      → prompt-assemble
      → replace context
```

### S1 专用: `context-retrieve`

```
context-retrieve
  → L1: capsule lookup
  → L2: openviking find
  → merge results
  → return context
```

---

## 6. Execution Policy 调用链

### 主入口: `policy-eval`

```
policy-eval --path <path> --tool <tool>
  → load rules
  → match path pattern
  → match tool
  → return ALLOW/WARN/DENY
```

### Heartbeat 集成

```
HEARTBEAT CHECK
  → probe-execution-policy-v2 --quick
    ↻ log violations
  → continue heartbeat
```

---

## 7. 自动化调用链

### Heartbeat

```
HEARTBEAT (every 30s)
  → session-start-recovery --recover
  → agent-self-health-scheduler --quick
  → probe-execution-policy-v2 --quick
  → route-rebind-guard-heartbeat
  → handle-subagent-complete
  → output HEARTBEAT_OK or ALERT
```

### Cron

```
systemd timer
  → callback-handler --auto-cleanup
  → retrieval-regression-runner
  → session-continuity-daily-check
  → policy-daily-check
```

---

## 调用层级隔离

### 规则

1. **MAIN 工具** 可调用 MAIN/SPECIALIZED/LOW-LEVEL
2. **SPECIALIZED 工具** 可调用 SPECIALIZED/LOW-LEVEL
3. **LOW-LEVEL 工具** 可调用 LOW-LEVEL/系统 API
4. **DEBUG 工具** 可调用任意工具
5. **INTERNAL 工具** 通常被自动化调用

### 禁止跨层调用

- MAIN 不应直接调用 DEPRECATED
- SPECIALIZED 不应直接调用 MAIN（避免循环依赖）
- LOW-LEVEL 不应调用 MAIN/SPECIALIZED

---

## 事件驱动调用

| 事件 | 触发器 | 处理器 |
|------|--------|--------|
| 子代理完成 | `reports/subtasks/` 写入 | `callback-worker` |
| Heartbeat | systemd timer | `HEARTBEAT.md` 流程 |
| Cron | systemd timer | 各 cron 脚本 |
| 文件变更 | inotify | `route-rebind-guard-heartbeat` |

---

## 可观测性建议

### 日志标签

```python
# 推荐的日志格式
logger.info(f"[{TOOL_NAME}] [LAYER:{LAYER}] action={action} result={result}")
```

### 审计标识

```python
# 推荐的审计字段
{
  "tool": "subtask-orchestrate",
  "layer": "main",
  "action": "run",
  "task_id": "xxx",
  "timestamp": "2026-03-10T05:00:00Z"
}
```

---

## 下一步

1. 为 MAIN 工具添加 LAYER 注释
2. 为 DEBUG 工具添加 warning banner
3. 统一日志格式
4. 添加审计标识字段

