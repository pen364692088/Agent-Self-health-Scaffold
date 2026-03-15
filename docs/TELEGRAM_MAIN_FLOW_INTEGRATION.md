# Telegram Main Flow Integration Contract

## 状态
**Version**: v1.0.0-draft
**Status**: DRAFT
**Created**: 2026-03-15
**Target Repository**: Agent-Self-health-Scaffold

---

## 1. 概述

本文档定义 Telegram 版 OpenClaw 与 Agent-Self-health-Scaffold 统一主流程的集成契约。

### 1.1 核心原则

1. **统一主链**: Telegram 消息必须接入统一主流程，不得绕开
2. **默认安全**: 默认模式为 `guarded-auto`，非 `full-auto`
3. **幂等优先**: 同一 update 只处理一次
4. **真相落地**: 所有状态必须持久化，不依赖内存
5. **可熔断**: 必须有 kill switch，可一键停止自动推进

---

## 2. 消息流向

```
Telegram Update
      ↓
┌─────────────────────────────────────────────────────┐
│             Telegram Ingress Adapter                 │
│  - update 去重                                       │
│  - 标准化为 MessageEvent                             │
│  - 提取 metadata (chat_id, user_id, etc.)           │
└─────────────────────────────────────────────────────┘
      ↓
┌─────────────────────────────────────────────────────┐
│              Idempotency Layer                       │
│  - 检查 update_id 是否已处理                         │
│  - 防止重复建任务/重复发送结果                        │
└─────────────────────────────────────────────────────┘
      ↓
┌─────────────────────────────────────────────────────┐
│           Intent Classifier                         │
│  - 判断消息类型: chat / task / control              │
│  - 提取意图和实体                                    │
└─────────────────────────────────────────────────────┘
      ↓
┌─────────────────────────────────────────────────────┐
│          Message-to-Task Router                     │
│  - chat → 直接回复                                  │
│  - new_task → 创建 dossier, 进入主流程               │
│  - continue_task → 关联已有任务                      │
│  - control → 路由到控制面                           │
└─────────────────────────────────────────────────────┘
      ↓
┌─────────────────────────────────────────────────────┐
│          Auto Start Controller                      │
│  - 检查当前模式 (shadow/guarded-auto/full-auto)     │
│  - 决定是否自动建任务                                │
│  - 决定是否自动推进                                  │
└─────────────────────────────────────────────────────┘
      ↓
┌─────────────────────────────────────────────────────┐
│               Risk Gate                             │
│  - 评估操作风险等级                                  │
│  - 低风险 → 自动执行                                │
│  - 高风险 → 暂停等待确认                            │
└─────────────────────────────────────────────────────┘
      ↓
┌─────────────────────────────────────────────────────┐
│      Checkpointed Step Loop (v2/v3-A/v3-B)          │
│  - step_scheduler                                   │
│  - step_executor                                    │
│  - parent_child_orchestrator                        │
└─────────────────────────────────────────────────────┘
      ↓
┌─────────────────────────────────────────────────────┐
│         Telegram Status Bridge                      │
│  - 回传状态给用户                                    │
│  - 与 task truth 保持一致                           │
└─────────────────────────────────────────────────────┘
```

---

## 3. 消息类型定义

### 3.1 MessageEvent Schema

```json
{
  "event_id": "string (UUID)",
  "event_type": "telegram_message",
  "timestamp": "ISO8601",
  "source": {
    "platform": "telegram",
    "chat_id": "string",
    "user_id": "string",
    "username": "string?",
    "message_id": "string",
    "thread_id": "string?",
    "reply_to_message_id": "string?",
    "update_id": "string"
  },
  "content": {
    "text": "string",
    "entities": [
      {
        "type": "bot_command|mention|hashtag|etc",
        "offset": "number",
        "length": "number"
      }
    ],
    "attachments": [
      {
        "type": "photo|document|audio|video|etc",
        "file_id": "string",
        "file_name": "string?"
      }
    ]
  },
  "context": {
    "is_private_chat": "boolean",
    "is_group_chat": "boolean",
    "is_reply": "boolean",
    "has_command": "boolean"
  }
}
```

### 3.2 意图分类

| Intent | 描述 | 示例 |
|--------|------|------|
| `chat` | 普通对话 | "你好", "今天天气怎么样" |
| `new_task` | 新任务请求 | "帮我整理 docs 目录" |
| `continue_task` | 继续已有任务 | "继续之前的任务", reply to task message |
| `control` | 控制命令 | `/status`, `/pause`, `/resume` |
| `approval` | 审批响应 | "/approve", "/reject" |

### 3.3 消息路由规则

```python
class MessageRouter:
    def route(self, event: MessageEvent) -> RouteDecision:
        # 1. 控制命令优先
        if event.has_command():
            return RouteDecision(type="control", command=event.extract_command())
        
        # 2. 审批响应
        if event.is_reply() and self.is_pending_approval(event.reply_to):
            return RouteDecision(type="approval", task_id=self.extract_task_id(event.reply_to))
        
        # 3. 继续已有任务
        if event.is_reply() and self.is_task_message(event.reply_to):
            return RouteDecision(type="continue_task", task_id=self.extract_task_id(event.reply_to))
        
        # 4. 显式继续命令
        if self.match_continue_pattern(event.text):
            task_id = self.find_recent_task(event.user_id)
            if task_id:
                return RouteDecision(type="continue_task", task_id=task_id)
        
        # 5. 新任务判断
        if self.is_task_like(event.text):
            return RouteDecision(type="new_task", objective=event.text)
        
        # 6. 默认为普通聊天
        return RouteDecision(type="chat")
```

---

## 4. 运行模式

### 4.1 模式定义

| 模式 | 行为 |
|------|------|
| `shadow` | 只观测，不执行高风险操作 |
| `guarded-auto` | 低风险自动执行，高风险等待确认 |
| `full-auto` | 全自动执行（禁止默认启用） |

### 4.2 模式切换

```python
class ModeController:
    def can_switch_to(self, current: str, target: str) -> bool:
        # shadow → guarded-auto: 允许
        # guarded-auto → full-auto: 需要显式确认
        # full-auto → guarded-auto: 允许
        # any → shadow: 允许
        pass
```

### 4.3 Feature Flags

| Flag | 默认值 | 描述 |
|------|--------|------|
| `telegram.main_flow_enabled` | `true` | 是否启用主流程接入 |
| `telegram.auto_start_mode` | `guarded-auto` | 自动启动模式 |
| `telegram.high_risk_requires_approval` | `true` | 高风险操作是否需要确认 |
| `telegram.allow_background_resume` | `true` | 是否允许后台恢复 |
| `telegram.kill_switch_enabled` | `false` | 熔断开关 |

---

## 5. 幂等性保证

### 5.1 幂等键

```python
def idempotency_key(event: MessageEvent) -> str:
    return f"telegram:{event.source.chat_id}:{event.source.message_id}:{event.source.update_id}"
```

### 5.2 幂等状态存储

```json
{
  "key": "telegram:8420019401:12651:12345678",
  "status": "processed",
  "task_id": "task_20260315_12345678",
  "processed_at": "2026-03-15T12:00:00Z",
  "result_sent": true
}
```

### 5.3 幂等检查流程

```
1. 收到 update
2. 生成幂等键
3. 检查幂等状态
   - 已处理且结果已发送 → 跳过
   - 已处理但结果未发送 → 重发结果
   - 未处理 → 继续处理
4. 处理完成后记录幂等状态
```

---

## 6. 风险门禁

### 6.1 风险等级定义

| 等级 | 描述 | 示例 |
|------|------|------|
| `low` | 低风险，可自动执行 | 读取文件、生成报告 |
| `medium` | 中等风险，需警告 | 修改非关键文件 |
| `high` | 高风险，需确认 | 删除文件、git push |
| `critical` | 严重风险，禁止自动 | 删除整个目录、修改系统配置 |

### 6.2 风险判定规则

```python
class RiskGate:
    HIGH_RISK_PATTERNS = [
        r"rm\s+-rf",
        r"git\s+push\s+--force",
        r"DROP\s+TABLE",
        r"DELETE\s+FROM",
        r"truncate",
        r"chmod\s+777",
        r">\s*/dev/sd",
    ]
    
    CRITICAL_PATTERNS = [
        r"rm\s+-rf\s+/",
        r"dd\s+if=",
        r"mkfs",
    ]
    
    def assess(self, operation: Operation) -> RiskAssessment:
        # 检查模式匹配
        for pattern in self.CRITICAL_PATTERNS:
            if re.search(pattern, operation.command):
                return RiskAssessment(level="critical", reason="Dangerous operation")
        
        for pattern in self.HIGH_RISK_PATTERNS:
            if re.search(pattern, operation.command):
                return RiskAssessment(level="high", reason="High-risk pattern matched")
        
        # 检查文件操作
        if operation.affects_critical_files():
            return RiskAssessment(level="high", reason="Modifies critical files")
        
        return RiskAssessment(level="low")
```

### 6.3 风险处理策略

| 风险等级 | shadow | guarded-auto | full-auto |
|----------|--------|--------------|-----------|
| low | 执行 | 执行 | 执行 |
| medium | 记录 | 警告后执行 | 执行 |
| high | 记录 | 暂停等待确认 | 执行 |
| critical | 记录 | 阻断 | 需要二次确认 |

---

## 7. 控制命令

### 7.1 支持的命令

| 命令 | 描述 | 别名 |
|------|------|------|
| `/status` | 查看当前任务状态 | `/s` |
| `/pause` | 暂停当前任务 | `/stop` |
| `/resume` | 恢复暂停的任务 | `/continue` |
| `/cancel` | 取消当前任务 | `/abort` |
| `/mode` | 切换运行模式 | - |
| `/approve` | 批准高风险操作 | `/yes` |
| `/reject` | 拒绝高风险操作 | `/no` |
| `/kill` | 启用熔断 | `/emergency_stop` |

### 7.2 命令处理流程

```python
class ControlCommandHandler:
    def handle(self, command: str, context: CommandContext) -> CommandResult:
        # 1. 验证权限
        if not self.is_authorized(context.user_id):
            return CommandResult(status="denied", message="Unauthorized")
        
        # 2. 记录审计日志
        self.audit_log(command, context)
        
        # 3. 执行命令
        result = self.execute(command, context)
        
        # 4. 持久化状态变更
        self.persist_state_change(command, result)
        
        return result
```

---

## 8. 状态回传

### 8.1 Telegram Status Bridge 接口

```python
class TelegramStatusBridge:
    def send_status(self, chat_id: str, task_id: str, status: TaskStatus):
        """发送任务状态"""
        pass
    
    def send_progress(self, chat_id: str, task_id: str, step: StepInfo):
        """发送步骤进度"""
        pass
    
    def send_approval_request(self, chat_id: str, task_id: str, operation: Operation):
        """发送审批请求"""
        pass
    
    def send_result(self, chat_id: str, task_id: str, result: TaskResult):
        """发送最终结果"""
        pass
```

### 8.2 状态消息格式

```json
{
  "type": "task_status",
  "task_id": "task_20260315_12345678",
  "status": "running",
  "current_step": "S02",
  "progress": "2/4",
  "message": "正在执行: 生成索引文件",
  "can_approve": false
}
```

---

## 9. Kill Switch

### 9.1 熔断触发条件

1. 手动触发 `/kill` 命令
2. 连续失败超过阈值
3. 异常率超过阈值
4. 外部告警触发

### 9.2 熔断后行为

```python
class KillSwitch:
    def on_trigger(self):
        # 1. 设置 kill_switch_enabled = true
        # 2. 停止所有自动推进
        # 3. 保留手动模式
        # 4. 保留已有 truth
        # 5. 通知用户
        pass
    
    def on_reset(self):
        # 1. 设置 kill_switch_enabled = false
        # 2. 允许恢复自动推进
        # 3. 记录审计日志
        pass
```

---

## 10. 与现有主流程的集成点

### 10.1 v2 Baseline 兼容

- 不修改 `task_state.schema.json` 核心字段
- 不修改 Gate A/B/C 规则
- 不修改 `step_executor` 核心逻辑
- 新增 `telegram_metadata` optional 字段

### 10.2 v3-A Scheduler 兼容

- Telegram 任务进入同一 scheduler 队列
- 不修改 `scheduler_decision.schema.json`
- 新增 `source: telegram` 标记

### 10.3 v3-B Parent-Child 兼容

- Telegram 任务可创建子任务
- 不修改 `parent_child_orchestrator.py` 核心逻辑

---

## 11. 非目标

以下功能不在本次集成范围内：

1. 多 Telegram bot 实例管理
2. Telegram 群组协作功能
3. Telegram 内联按钮（inline buttons）深度集成
4. Telegram 支付集成
5. 语音消息转任务

---

## 12. 验收标准

### Gate A: Contract

- [ ] 本文档审核通过
- [ ] 所有 schema 文件存在且有效
- [ ] Feature flags 定义完整
- [ ] 默认模式为 `guarded-auto`

### Gate B: E2E

- [ ] 低风险任务自动执行闭环
- [ ] 高风险任务正确暂停
- [ ] `/approve` 或 `/reject` 生效
- [ ] `/status` 返回正确状态
- [ ] 不重复建任务

### Gate C: Integrity

- [ ] Telegram 状态与 truth 一致
- [ ] 幂等保护成立
- [ ] Kill switch 生效
- [ ] Fallback 不假完成
- [ ] v2/v3-A/v3-B 测试仍通过

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0.0-draft | 2026-03-15 | 初始契约设计 |
