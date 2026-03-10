# memory-lancedb AutoCapture Debug

**日期**: 2026-03-09 22:45 CST

---

## AutoCapture 触发流程

```
对话开始
    │
    ├─→ 用户发送消息
    │       │
    │       └─→ agent 处理
    │               │
    │               └─→ agent 响应
    │                       │
    │                       └─→ 对话继续...
    │
    └─→ 对话结束
            │
            └─→ 触发 agent_end 事件
                    │
                    ├─→ 检查 event.success
                    ├─→ 提取 user 消息
                    ├─→ 应用 shouldCapture 过滤
                    ├─→ 获取 embedding
                    ├─→ 检查重复
                    └─→ 存储到 LanceDB
```

---

## 调试发现

### 1. agent_end 事件

**状态**: 未触发

**日志证据**:
```
// 没有 agent_end 相关日志
// 只有 context-compression Processing complete
```

### 2. 用户消息条件

**检查项**:
| 条件 | 状态 |
|------|------|
| 消息存在 | ✅ 多条用户消息 |
| role = 'user' | ✅ 确认 |
| 长度 10-500 | ✅ 符合 |
| 过滤条件 | ✅ 不包含过滤内容 |

### 3. 成功条件

**问题**: 不确定 `event.success` 是否为 `true`

---

## 建议的调试日志增强

### 在 memory-lancedb/index.ts 中添加

```typescript
api.on("agent_end", async (event) => {
  api.logger.info(`memory-lancedb: agent_end triggered, success=${event.success}`);
  
  if (!event.success || !event.messages || event.messages.length === 0) {
    api.logger.info(`memory-lancedb: capture skipped, success=${event.success}, messages=${event.messages?.length || 0}`);
    return;
  }

  // ... 现有代码 ...
  
  if (toCapture.length === 0) {
    api.logger.info(`memory-lancedb: no capturable content after filter`);
    return;
  }

  api.logger.info(`memory-lancedb: capturing ${toCapture.length} items`);
  // ...
});
```

---

## 当前诊断状态

| 检查项 | 状态 | 说明 |
|--------|------|------|
| agent_end 触发 | ❌ | 无日志 |
| event.success | ? | 未知 |
| 消息过滤 | ✅ | 条件符合 |
| embedding 服务 | ✅ | Ollama 正常 |
| LanceDB 初始化 | ✅ | initialized |

---

## 结论

**问题**: agent_end 事件未触发，导致 autoCapture 无法执行

**需要**: 确认 Gateway 如何触发 agent_end 事件
