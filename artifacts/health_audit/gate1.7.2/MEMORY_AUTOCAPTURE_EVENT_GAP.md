# Memory AutoCapture Event Gap

**日期**: 2026-03-09 23:15 CST

---

## Gap 定位

### 事件流

```
用户发送消息
    ↓
Gateway 接收
    ↓
before_agent_start 触发
    ↓
memory-lancedb recall 执行 ✅
    ↓
LLM 处理
    ↓
agent 生成回复
    ↓
回复发送给用户
    ↓
??? agent_end 应该在这里触发 ???
    ↓
memory-lancedb capture 未执行 ❌
```

---

## Gap 分析

### 代码层面

**触发点** (`compact-D3emcZgv.js`):
```javascript
if (hookRunner?.hasHooks("agent_end")) hookRunner.runAgentEnd({...})
```

**检查点**:
```javascript
function hasHooks(hookName) {
    return registry.typedHooks.some((h) => h.hookName === hookName);
}
```

**注册点** (`memory-lancedb/index.ts`):
```javascript
api.on("agent_end", async (event) => {...})
```

---

### Gap 原因

**假设 1**: `hasHooks("agent_end")` 返回 false
- 这意味着 `registry.typedHooks` 中没有 `hookName === "agent_end"` 的记录
- 说明 `api.on("agent_end")` 没有成功添加到 typedHooks

**假设 2**: 注册时序问题
- memory-lancedb 在 hookRunner 初始化之后才注册
- 导致 hasHooks 检查时 typedHooks 还没有 agent_end

**假设 3**: KNOWN_TYPED_HOOK_NAMES 不包含 agent_end
- 注册时被忽略（unknown typed hook ignored）

---

## 验证方法

1. 添加调试日志到 `api.on()` 注册过程
2. 检查 `KNOWN_TYPED_HOOK_NAMES` 定义
3. 检查 `registry.typedHooks` 内容

---

## 结论

**Gap 类型**: listener gap

**Gap 位置**: `api.on("agent_end")` → `registry.typedHooks`

**根因**: 注册未生效或被忽略
