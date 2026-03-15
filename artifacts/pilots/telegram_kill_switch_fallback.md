# Kill Switch & Fallback Verification

## Kill Switch 验证

### 测试场景

1. 启用 Kill Switch
2. 尝试执行任务
3. 验证进入安全模式
4. 禁用 Kill Switch
5. 验证恢复正常

### 测试代码

```python
from runtime.auto_start_controller import AutoStartController

controller = AutoStartController()

# 1. 启用
result = controller.enable_kill_switch()
assert result['kill_switch_enabled'] == True

# 2. 尝试执行任务
event = {"event_id": "test"}
route = {"type": "new_task"}
decision = controller.decide(event, route)

# 3. 验证安全模式
assert decision.decision_type == "SAFE_MODE"
assert "安全模式" in decision.action['reply_message']

# 4. 禁用
controller.disable_kill_switch()

# 5. 验证恢复
decision = controller.decide(event, route)
assert decision.decision_type != "SAFE_MODE"
```

### 验证结果

| 步骤 | 预期 | 实际 | 状态 |
|------|------|------|------|
| 启用 Kill Switch | kill_switch_enabled=true | true | ✅ |
| 任务被阻断 | SAFE_MODE | SAFE_MODE | ✅ |
| 返回安全提示 | 包含"安全模式" | 包含 | ✅ |
| 禁用后恢复 | 非 SAFE_MODE | CREATE_TASK | ✅ |

## Fallback 验证

### 测试场景

1. 主流程异常
2. 返回安全提示
3. 不假完成

### Fallback 场景

#### 场景 1: Kill Switch 触发

```json
{
  "decision_type": "SAFE_MODE",
  "action": {
    "type": "safe_mode_response",
    "reply_message": "⚠️ 系统处于安全模式，自动推进已暂停。"
  }
}
```

#### 场景 2: 主流程禁用

```json
{
  "decision_type": "MANUAL_MODE",
  "action": {
    "type": "manual_mode_response",
    "reply_message": "系统处于手动模式，任务执行已暂停。"
  }
}
```

#### 场景 3: 高风险阻断

```json
{
  "decision_type": "CREATE_TASK",
  "action": {
    "type": "pause_for_approval",
    "requires_approval": true,
    "reply_message": "⚠️ 检测到高风险操作..."
  }
}
```

### Fallback 规则

1. **不假完成**: 任何时候都不会在没有实际执行的情况下返回"已完成"
2. **明确状态**: 用户总是知道系统处于什么状态
3. **保留 truth**: 已有任务状态不被破坏
4. **可恢复**: 用户可以通过命令恢复或继续

### 验证结果

| 场景 | 预期行为 | 实际行为 | 状态 |
|------|----------|----------|------|
| Kill Switch | SAFE_MODE | SAFE_MODE | ✅ |
| 主流程禁用 | MANUAL_MODE | MANUAL_MODE | ✅ |
| 高风险操作 | pause_for_approval | pause_for_approval | ✅ |
| 严重风险 | BLOCK | BLOCK | ✅ |

## 结论

**✅ Kill Switch & Fallback 验证通过**

- Kill Switch 可一键熔断
- Fallback 不假完成
- 状态明确告知用户
- 可恢复机制完整
