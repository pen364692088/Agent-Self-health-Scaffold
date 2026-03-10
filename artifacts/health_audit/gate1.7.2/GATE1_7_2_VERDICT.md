# Gate 1.7.2 Verdict

**日期**: 2026-03-09 23:15 CST
**任务**: Agent Lifecycle Event Trace for memory-lancedb

---

## 最终结论

# listener gap

---

## 证据

### 1. hooks:loader 注册的 hooks

```
boot-md -> gateway:startup
bootstrap-extra-files -> agent:bootstrap
command-logger -> command
session-memory -> command:new, command:reset
compaction-archive -> after_compaction
context-compression-shadow -> message:preprocessed
emotiond-bridge -> message:received
emotiond-enforcer -> message:sending
```

**agent_end 不在列表中**

---

### 2. memory-lancedb hooks 状态

| Hook | 状态 | 日志证据 |
|------|------|----------|
| before_agent_start (recall) | ✅ 触发 | 200+ 条日志 |
| agent_end (capture) | ❌ 从未触发 | 0 条日志 |

---

### 3. 根因分析

**代码路径**:
```
compact-D3emcZgv.js:
  if (hookRunner?.hasHooks("agent_end")) hookRunner.runAgentEnd({...})
```

**hasHooks 实现**:
```javascript
function hasHooks(hookName) {
    return registry.typedHooks.some((h) => h.hookName === hookName);
}
```

**memory-lancedb 注册**:
```javascript
api.on("agent_end", async (event) => {...})
```

**问题**:
- `api.on()` 注册的 hooks 应该添加到 `registry.typedHooks`
- 但 `hasHooks("agent_end")` 返回 false
- 说明 `api.on("agent_end")` 没有成功注册

---

## 判断依据

| 选项 | 是否成立 | 证据 |
|------|----------|------|
| A. agent_end 根本没有发出 | ❌ | 代码中有 `hookRunner.runAgentEnd()` |
| B. agent_end 发出了，但插件没有收到 | ✅ | before_agent_start 正常，agent_end 不工作 |
| C. reply 路径绕过了标准 lifecycle | ❌ | lifecycle 正常 |
| D. 事件名/版本/注册点不一致 | ⚠️ | 可能是注册点问题 |
| E. 其他 | ❌ | 已定位 |

**最终判断**: **B. listener gap**

agent_end 事件可能被触发，但 memory-lancedb 的 listener 没有被正确注册。

---

## 最小修复建议

### 方案 1: 检查 KNOWN_TYPED_HOOK_NAMES

确保 `agent_end` 在已知的 typed hook 名字列表中。

### 方案 2: 添加调试日志

在 memory-lancedb 的 `api.on("agent_end")` 注册后添加日志：
```javascript
api.on("agent_end", async (event) => {
  api.logger.info("memory-lancedb: agent_end hook triggered");
  // ...
});
```

### 方案 3: 使用 hooks:loader 注册

创建 `~/.openclaw/hooks/memory-lancedb-capture/handler.ts`：
```typescript
export default async function handler(event, ctx) {
  // autoCapture 逻辑
}
```

---

## 下一步

1. 检查 OpenClaw 版本和 memory-lancedb 插件兼容性
2. 向 OpenClaw 提交 bug report
3. 或使用 hooks:loader 方式注册作为 workaround
