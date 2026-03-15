# Telegram Auto-Start Policy

## 状态
**Version**: v1.0.0-draft
**Status**: DRAFT
**Created**: 2026-03-15

---

## 1. 概述

本文档定义 Telegram 消息的自动启动策略，决定哪些消息触发任务创建和自动推进。

### 1.1 核心原则

1. **不把所有消息当任务**: 普通聊天直接回复，不建 dossier
2. **默认安全**: 高风险操作默认暂停，等待确认
3. **可预测**: 用户能预判系统的行为
4. **可审计**: 所有决策有记录

---

## 2. 自动启动决策流程

```
MessageEvent
      ↓
┌─────────────────────────────────────────────────────┐
│           Auto Start Controller                      │
│                                                      │
│  1. 检查 kill_switch                                 │
│     - 如果启用 → 返回 SAFE_MODE                      │
│                                                      │
│  2. 检查 main_flow_enabled                           │
│     - 如果禁用 → 返回 MANUAL_MODE                    │
│                                                      │
│  3. 确定消息类型                                     │
│     - chat → DIRECT_REPLY                            │
│     - control → CONTROL_ROUTING                      │
│     - task → 继续检查                                │
│                                                      │
│  4. 检查当前模式                                     │
│     - shadow → OBSERVE_ONLY                          │
│     - guarded-auto → AUTO_WITH_RISK_GATE             │
│     - full-auto → FULL_AUTO                          │
│                                                      │
│  5. 创建决策记录                                     │
│     - 记录决策原因                                   │
│     - 记录下一步动作                                 │
└─────────────────────────────────────────────────────┘
      ↓
   Decision
```

---

## 3. 决策类型

### 3.1 Decision Schema

```json
{
  "decision_id": "string (UUID)",
  "timestamp": "ISO8601",
  "message_event_id": "string",
  "decision_type": "DIRECT_REPLY | CREATE_TASK | CONTINUE_TASK | CONTROL | SAFE_MODE | MANUAL_MODE | BLOCKED",
  "reason": "string",
  "mode": "shadow | guarded-auto | full-auto",
  "risk_level": "low | medium | high | critical",
  "action": {
    "type": "string",
    "task_id": "string?",
    "requires_approval": "boolean",
    "approval_id": "string?"
  },
  "metadata": {}
}
```

### 3.2 决策类型详解

| 类型 | 描述 | 后续动作 |
|------|------|----------|
| `DIRECT_REPLY` | 普通聊天，直接回复 | 不建任务，调用 chat handler |
| `CREATE_TASK` | 新任务请求 | 创建 dossier，进入主流程 |
| `CONTINUE_TASK` | 继续已有任务 | 关联已有 dossier，恢复推进 |
| `CONTROL` | 控制命令 | 路由到控制面处理 |
| `SAFE_MODE` | 熔断状态 | 返回安全提示 |
| `MANUAL_MODE` | 主流程禁用 | 返回手动模式提示 |
| `BLOCKED` | 被阻断 | 返回阻断原因 |

---

## 4. 消息分类规则

### 4.1 任务判定

```python
class TaskClassifier:
    # 明确的任务触发词
    TASK_KEYWORDS = [
        "帮我", "请", "创建", "生成", "实现", "修复",
        "整理", "分析", "重构", "删除", "修改",
        "写一个", "做个", "完成", "处理"
    ]
    
    # 排除词（普通聊天）
    CHAT_KEYWORDS = [
        "你好", "谢谢", "再见", "怎么样", "是什么",
        "可以吗", "吗", "呢"
    ]
    
    def classify(self, text: str, context: MessageContext) -> Classification:
        # 1. 检查是否回复任务消息
        if context.is_reply_to_task:
            return Classification(
                type="continue_task",
                confidence=0.9,
                task_id=context.reply_task_id
            )
        
        # 2. 检查是否控制命令
        if text.startswith('/'):
            return Classification(type="control", confidence=1.0)
        
        # 3. 检查任务关键词
        task_score = sum(1 for kw in self.TASK_KEYWORDS if kw in text)
        chat_score = sum(1 for kw in self.CHAT_KEYWORDS if kw in text)
        
        if task_score > chat_score and task_score > 0:
            return Classification(type="new_task", confidence=0.7)
        
        # 4. 检查文本长度（长文本更可能是任务）
        if len(text) > 200:
            return Classification(type="new_task", confidence=0.6)
        
        # 5. 默认为普通聊天
        return Classification(type="chat", confidence=0.8)
```

### 4.2 置信度阈值

| 置信度 | 行为 |
|--------|------|
| ≥ 0.9 | 直接执行 |
| 0.7 - 0.9 | 执行但记录不确定性 |
| 0.5 - 0.7 | 询问确认 |
| < 0.5 | 按普通聊天处理 |

---

## 5. 模式行为矩阵

### 5.1 shadow 模式

| 消息类型 | 行为 | 说明 |
|----------|------|------|
| chat | 直接回复 | 正常处理 |
| new_task | 创建 dossier + 观测 | 不执行高风险操作 |
| continue_task | 观测状态 | 不继续推进 |
| control | 正常处理 | 控制命令不受限 |

### 5.2 guarded-auto 模式

| 消息类型 | 行为 | 说明 |
|----------|------|------|
| chat | 直接回复 | 正常处理 |
| new_task | 创建 dossier + 自动推进 | 高风险需确认 |
| continue_task | 自动恢复推进 | 高风险需确认 |
| control | 正常处理 | 控制命令不受限 |

### 5.3 full-auto 模式

| 消息类型 | 行为 | 说明 |
|----------|------|------|
| chat | 直接回复 | 正常处理 |
| new_task | 创建 dossier + 全自动推进 | 无确认要求 |
| continue_task | 全自动推进 | 无确认要求 |
| control | 正常处理 | 控制命令不受限 |

---

## 6. 自动推进规则

### 6.1 可自动推进的条件

1. **模式允许**: 当前模式不是 `shadow`
2. **未熔断**: `kill_switch_enabled = false`
3. **任务状态**: 任务状态为 `running` 或 `created`
4. **无阻塞**: 没有等待审批的操作

### 6.2 暂停自动推进的条件

1. **高风险操作**: 需要 `/approve`
2. **用户显式暂停**: `/pause` 命令
3. **任务失败**: `failed_retryable` 状态
4. **依赖阻塞**: 缺少必要输入

---

## 7. 后台恢复规则

### 7.1 允许后台恢复的条件

```python
def can_background_resume(task_id: str) -> bool:
    # 1. Feature flag 允许
    if not feature_flags.get("telegram.allow_background_resume"):
        return False
    
    # 2. 任务状态允许
    task = load_task(task_id)
    if task.status not in ("running", "blocked"):
        return False
    
    # 3. 没有活跃会话
    if has_active_session(task_id):
        return False
    
    # 4. 没有等待审批
    if has_pending_approval(task_id):
        return False
    
    return True
```

### 7.2 后台恢复触发

- 定时检查（每 5 分钟）
- 任务状态变更事件
- 用户主动触发 `/resume`

---

## 8. 异常处理

### 8.1 分类失败

```python
def handle_classification_failure(event: MessageEvent):
    # 记录失败
    log_classification_failure(event)
    
    # 返回安全回复
    return """
    我收到了你的消息，但不确定如何处理。
    
    如果你想让我执行某个任务，请明确告诉我，比如：
    "帮我整理 docs 目录"
    
    如果只是想聊天，那我们继续聊！
    """
```

### 8.2 主流程异常

```python
def handle_main_flow_error(event: MessageEvent, error: Exception):
    # 记录错误
    log_error(event, error)
    
    # 进入安全模式
    set_safe_mode(event.chat_id)
    
    # 返回安全提示
    return """
    ⚠️ 主流程出现异常，已进入安全模式。
    
    你的消息已被记录，但自动推进暂时受限。
    
    你可以：
    - 等待恢复
    - 使用 /status 查看状态
    - 使用 /mode 切换模式
    """
```

---

## 9. 审计日志

### 9.1 必须记录的事件

1. 消息分类决策
2. 模式切换
3. 自动推进启动/暂停
4. 风险判定结果
5. 审批请求/响应
6. Kill switch 触发/重置
7. 异常事件

### 9.2 日志格式

```json
{
  "event_id": "string",
  "event_type": "string",
  "timestamp": "ISO8601",
  "chat_id": "string",
  "user_id": "string",
  "message_id": "string",
  "decision": {},
  "mode": "string",
  "risk_level": "string",
  "task_id": "string?",
  "details": {}
}
```

---

## 10. 配置管理

### 10.1 配置来源优先级

1. 环境变量（最高优先级）
2. 配置文件
3. 数据库
4. 默认值（最低优先级）

### 10.2 热更新支持

以下配置支持热更新（无需重启）：

- `telegram.auto_start_mode`
- `telegram.high_risk_requires_approval`
- `telegram.allow_background_resume`

以下配置需要重启：

- `telegram.main_flow_enabled`
- `telegram.kill_switch_enabled`

---

## 11. 安全边界

### 11.1 禁止行为

1. 不在 shadow 模式下执行高风险操作
2. 不在 kill switch 启用时自动推进
3. 不跳过风险判定
4. 不绕开幂等检查
5. 不在未授权时执行控制命令

### 11.2 强制检查

每个自动推进循环必须检查：

1. kill_switch_enabled
2. main_flow_enabled
3. 当前模式
4. 任务状态
5. 风险等级

---

## 12. 验收标准

- [ ] 消息分类准确率 > 90%
- [ ] 低风险任务自动执行率 = 100%
- [ ] 高风险任务暂停率 = 100%
- [ ] 审批命令响应率 = 100%
- [ ] Kill switch 生效延迟 < 1s
- [ ] 异常恢复成功率 > 95%

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0.0-draft | 2026-03-15 | 初始策略设计 |
