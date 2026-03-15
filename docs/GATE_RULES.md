# Gate Rules - Hard Fail vs Soft Fail

## Gate A: Contract

### Hard Fail (阻断收口)
- task_state.json 不存在
- TASK.md 不存在
- ledger.jsonl 不存在
- 任何 step_packet 缺失
- 成功步骤的 result.json 缺失

### Soft Fail (警告)
- evidence/ 目录缺失
- handoff/ 目录缺失

### 完整性规则
如果有任何 check.passed=false，Gate A 整体 passed=false

---

## Gate B: E2E

### Hard Fail (阻断收口)
- 任何步骤状态不是 success
- SUMMARY.md 不存在
- 任何成功步骤缺少 evidence

### Soft Fail (警告)
- (当前无 soft fail 项)

### SUMMARY.md 规则
**SUMMARY.md 是必需产物**，必须存在于 `final/SUMMARY.md`

内容要求：
- 任务目标
- 完成的步骤列表
- Evidence 位置
- Gate 结果
- 最终状态

### 完整性规则
如果有任何 check.passed=false，Gate B 整体 passed=false

---

## Gate C: Integrity

### Hard Fail (阻断收口)
- task_state.json 无法解析
- task_state 缺少必需字段
- ledger 无事件
- task_state.status == "completed" 但 ledger 无 task_completed 事件
- 任何成功步骤缺少 evidence 和 handoff

### Soft Fail (警告)
- task_state.status 不是 "completed" 时缺少 task_completed 事件

### 完整性规则
如果有任何 check.passed=false，Gate C 整体 passed=false

---

## 全局完整性规则

**禁止出现矛盾状态**：
- `all_passed=true` 时，不允许任何 `check.passed=false`
- 如果检测到矛盾，整体收口被阻断

```python
# 完整性校验逻辑
def verify_integrity(gate_report):
    if gate_report['all_passed']:
        for gate in gate_report['gates'].values():
            for check in gate['checks']:
                if not check.get('passed', True):
                    return False, "CONTRADICTION: all_passed=true but check failed"
    return True, "OK"
```

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1 | 2026-03-15 | 初始规则定义，修复完整性校验 |
