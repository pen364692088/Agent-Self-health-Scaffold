
---

# 17. finalize-response 强制检查层 (2026-03-06 新增)

## 问题背景

即使有了 `verify-and-close` 和 `done-guard`，agent 仍然可能在输出层"忘记"调用这些工具。

## 解决方案

**不要靠 agent 自己决定何时检查。**

把"发最终总结"这个动作本身包起来：

```
finalize_response -> done-guard -> allow/block
```

## 工具

**finalize-response** - 自动检查包装器
```bash
# 检查文本 + receipts
finalize-response --task-id <id> --summary "..."

# 从文件检查
finalize-response --task-id <id> --file output.md

# 只检查 receipts
finalize-response --task-id <id>
```

输出:
- `ALLOW` - 安全输出
- `BLOCK` - 必须先调用 verify-and-close

## 强制规则

**任何"任务完成"类回复，必须先过 finalize-response。**

也就是说，agent 的正常工作流应该是：

1. 完成实现
2. 调用 `verify-and-close --task-id <id>`
3. 构造总结文本
4. 调用 `finalize-response --task-id <id> --summary "..."`
5. 如果 ALLOW，才输出给用户

如果 finalize-response 返回 BLOCK，则：
- 必须先调用 verify-and-close
- 或者修改总结文本，移除伪完成表述

---

# 18. 测试封口 (2026-03-06 完成)

## 测试套件

位置: `tests/test_execution_policy.py`

### Round 1: 正常路径
- test_verify_and_close_happy_path - 验证完整流程
- test_receipt_field_stability - 验证 receipt 字段稳定性

### Round 2: 故障路径
- test_done_guard_blocks_fake_done_without_receipts - 缺 receipt 阻断
- test_missing_single_receipt_blocked - 缺单个 receipt 阻断
- test_fake_completion_text_blocked - 伪完成文本阻断
- test_invalid_state_transition_blocked - 非法状态迁移阻断

### Round 3: 人测失败回退
- test_human_failed_forces_repairing - human_failed 强制 repairing
- test_repairing_cannot_skip_to_close - repairing 不能跳 reverify
- test_reverify_required_after_repair - 修复后必须 reverify

**状态: 9/9 测试通过**

---

# 19. 一句话总结 (v2.0)

**不要再要求 agent "记得调用工具"；要让 agent 除了调用统一收尾入口之外，没有任何合法完成路径。**

**更关键的是：不要靠 agent 自己决定何时检查；要把检查固化在输出层。**

