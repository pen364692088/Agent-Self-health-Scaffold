# 子代理回调修复任务

## 目标
将"子代理完成"从聊天展示事件，改成父 session 的显式回传事件。

## 具体任务

### T1: 配置修改 - 给子代理开 sessions_send
修改 `~/.openclaw/openclaw.json`:
```json
{
  "tools": {
    "subagents": {
      "tools": {
        "allow": ["sessions_send", "sessions_history", "read", "write", "edit", "exec", "process"]
      }
    }
  }
}
```

### T2: 创建子代理回调模板
创建 `~/.openclaw/workspace/templates/subagent_callback_task.md`:
- 包含 parentSessionKey
- 包含 task_id
- 要求完成后 `sessions_send(parentSessionKey, payload)`
- 要求 announce 阶段输出 ANNOUNCE_SKIP

### T3: 重构 subagent-completion-handler
将 `~/.openclaw/workspace/tools/subagent-completion-handler` 改为:
- 接收结构化 payload
- 校验 task_id 和 child 归属
- 拉取 child transcript/artifacts
- 写入 task ledger
- 决定 next step

### T4: 创建 task ledger
创建 `~/.openclaw/workspace/tools/task-ledger`:
- task_id
- parent_session_key
- child_session_key
- state (spawned|running|completed|failed)
- started_at / completed_at
- result_path
- next_action

## 验收标准
1. 子代理有 sessions_send 权限
2. spawn task 模板包含回传要求
3. handler 能处理结构化 payload
4. ledger 记录任务状态
5. E2E 测试通过
