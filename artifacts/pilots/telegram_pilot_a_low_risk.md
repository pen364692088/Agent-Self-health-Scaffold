# Pilot A: Low Risk Auto Task

## 任务描述

**输入**: Telegram 消息 "帮我整理 docs 目录"
**预期**: 自动创建任务、自动推进、自动完成

## 处理流程

### Step 1: Ingress 标准化

```json
{
  "event_id": "304a157b-97e8-42d4-bf5c-bac330f5f6d8",
  "event_type": "telegram_message",
  "source": {
    "chat_id": "8420019401",
    "user_id": "8420019401",
    "message_id": "12345",
    "update_id": "99999"
  },
  "content": {
    "text": "帮我整理 docs 目录"
  }
}
```

### Step 2: 路由决策

```json
{
  "type": "new_task",
  "confidence": 0.7,
  "reason": "Task keywords matched (score: 2)",
  "objective": "帮我整理 docs 目录"
}
```

### Step 3: 风险评估

```json
{
  "risk_level": "low",
  "reason": "No risk patterns matched",
  "action": {
    "type": "execute",
    "message": "Low risk operation, proceeding automatically"
  }
}
```

### Step 4: 自动启动决策

```json
{
  "decision_type": "CREATE_TASK",
  "mode": "guarded-auto",
  "action": {
    "type": "auto_proceed",
    "requires_approval": false,
    "reply_message": "✅ 已创建任务并开始执行\n\n任务 ID: task_xxx\n\n使用 /status 查看进度"
  }
}
```

## 验证结果

| 检查项 | 结果 |
|--------|------|
| 消息正确标准化 | ✅ PASS |
| 正确路由为 new_task | ✅ PASS |
| 风险评估为 low | ✅ PASS |
| 自动执行决策正确 | ✅ PASS |
| 不需要审批 | ✅ PASS |

## 结论

**✅ Pilot A 通过**: 低风险任务正确地被识别为可自动执行，无需人工确认。
