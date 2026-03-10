# Agent Lifecycle Trace

**日期**: 2026-03-09 23:15 CST

---

## Lifecycle 事件

根据代码分析，OpenClaw Gateway 的 agent lifecycle 事件包括：

```
before_model_resolve
  ↓
before_prompt_build
  ↓
before_agent_start  ← memory-lancedb recall 在这里触发
  ↓
llm_input
  ↓
[LLM 处理]
  ↓
llm_output
  ↓
agent_end  ← memory-lancedb capture 应该在这里触发
```

---

## 实际观测

### before_agent_start

**触发次数**: 200+ 次

**日志证据**:
```
[gateway] memory-lancedb: recall failed: Error: 404 404 page not found
```

**结论**: ✅ 正常工作

---

### agent_end

**触发次数**: 0 次

**日志证据**: 无

**结论**: ❌ 从未触发

---

## 对比分析

| Hook | 注册方式 | 状态 | 说明 |
|------|----------|------|------|
| before_agent_start | api.on() | ✅ | 正常工作 |
| agent_end | api.on() | ❌ | 从未触发 |

**矛盾**: 同样的 `api.on()` 注册方式，一个工作，一个不工作。

---

## 可能原因

1. **注册顺序问题**: agent_end 注册时 hookRunner 已初始化完成
2. **KNOWN_TYPED_HOOK_NAMES**: agent_end 不在已知 hook 名单中
3. **条件检查**: `hasHooks("agent_end")` 返回 false，跳过触发
