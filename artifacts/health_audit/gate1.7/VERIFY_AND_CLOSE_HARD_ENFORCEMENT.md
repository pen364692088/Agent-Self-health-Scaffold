# verify-and-close Hard Enforcement

**日期**: 2026-03-09 22:28 CST

---

## 目标

关闭任务前必须经过 verify-and-close，不允许 message tool 直接绕过。

---

## 实现方案

### 1. 创建 enforce-task-completion 工具

**功能**:
- 检测消息是否包含完成关键词
- 检查任务是否有 receipt
- 决定 ALLOW 或 BLOCK

**完成关键词**:
- 完成, 已完成, 全部完成, 可以交付, 验收通过
- closed, complete, done, finished, delivered
- ✅, 🎉, 交付

---

### 2. Probe 验证

#### Probe A: 正常通过路径

**测试任务**: test-gate1-6（有 receipt）

**测试消息**: "任务已完成，验收通过"

**结果**:
```json
{
  "action": "ALLOW",
  "receipt_status": {
    "has_all": true,
    "found": {
      "contract": true,
      "e2e": true,
      "preflight": true,
      "final": true
    }
  },
  "has_completion_intent": true
}
```

**结论**: ✅ 有 receipt 允许发送

---

#### Probe B: 绕过尝试路径

**测试任务**: nonexistent-task（无 receipt）

**测试消息**: "任务已完成，验收通过"

**结果**:
```json
{
  "action": "BLOCK",
  "receipt_status": {
    "has_all": false
  },
  "has_completion_intent": true
}
```

**结论**: ✅ 无 receipt 阻断发送

---

### 3. SOUL.md 更新

**旧规则**:
```
verify-and-close → finalize-response → safe-message → 输出给用户
```

**新规则**:
```
verify-and-close → finalize-response → enforce-task-completion → 输出给用户
```

---

## 最终判断

# enforced via tool

**说明**:
- 工具层强制执行 ✅
- 主流程需要手动调用工具 ⚠️
- 未修改 OpenClaw 核心 ❌

---

## 限制

1. 无法修改 OpenClaw 内置 message tool
2. 需要 agent 自觉使用 enforce-task-completion
3. 文本输出仍可绕过

---

## 建议

1. **短期**: 所有完成类输出前调用 enforce-task-completion
2. **中期**: 集成到 safe-message 中
3. **长期**: 向 OpenClaw 提交 feature request
