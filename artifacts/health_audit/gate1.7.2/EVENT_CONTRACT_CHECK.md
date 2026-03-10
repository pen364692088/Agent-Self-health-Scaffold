# Event Contract Check

**日期**: 2026-03-09 23:15 CST

---

## Hook 事件合约

### 已知 Typed Hooks (从代码推断)

```javascript
// 从 hasHooks 调用推断
"before_compaction"
"after_compaction"
"before_tool_call"
"after_tool_call"
"before_message_write"
"tool_result_persist"
"before_prompt_build"
"before_agent_start"
"llm_input"
"agent_end"  // ← 这个应该支持
"llm_output"
"before_model_resolve"
"subagent_delivery_target"
"subagent_ended"
"subagent_spawned"
"before_reset"
"session_end"
```

---

## 事件名检查

### memory-lancedb 使用的 hook

| Hook 名 | 是否在已知列表 | 状态 |
|---------|---------------|------|
| before_agent_start | ✅ 是 | ✅ 工作 |
| agent_end | ✅ 是 | ❌ 不工作 |

---

## 注册点检查

### hooks:loader 注册的 hooks

| Hook 名 | 事件 | 注册源 |
|---------|------|--------|
| boot-md | gateway:startup | 文件系统 |
| bootstrap-extra-files | agent:bootstrap | 文件系统 |
| command-logger | command | 文件系统 |
| session-memory | command:new, command:reset | 文件系统 |
| compaction-archive | after_compaction | 文件系统 |
| context-compression-shadow | message:preprocessed | 文件系统 |
| emotiond-bridge | message:received | 文件系统 |
| emotiond-enforcer | message:sending | 文件系统 |

### memory-lancedb 注册的 hooks

| Hook 名 | 注册源 | 状态 |
|---------|--------|------|
| before_agent_start | api.on() | ✅ 工作 |
| agent_end | api.on() | ❌ 不工作 |

---

## 合约一致性

### 检查项

| 检查项 | 状态 | 说明 |
|--------|------|------|
| 事件名正确 | ✅ | "agent_end" 是有效的 hook 名 |
| 注册方式正确 | ⚠️ | api.on() 对 before_agent_start 有效 |
| 触发条件满足 | ? | 无法直接验证 |
| 参数格式正确 | ? | 无法直接验证 |

---

## 结论

**事件合约**: 正常

**问题**: 不是事件名或合约问题，是注册机制问题

**推断**: `api.on("agent_end")` 注册未生效
