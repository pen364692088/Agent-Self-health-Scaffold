# Open Loop Schema

**Version**: 1.0  
**Created**: 2026-03-09

---

## Open Loop 定义

未完成、需要后续跟进的事项。

---

## 必须记录的字段

| 字段 | 说明 |
|------|------|
| description | 事项描述 |
| status | open/in_progress/blocked |
| created_at | 创建时间 |
| blocking_reason | 如果 blocked |
| next_action | 下一步动作 |

---

## Open Loop 检测模式

| 模式 | 示例 |
|------|------|
| TODO | "TODO: 实现登录功能" |
| TBD | "TBD: 确认 API 版本" |
| 待定 | "待用户确认" |
| 尚未 | "尚未实现" |
| 需要 | "需要进一步测试" |

---

## Open Loop Anchor 评分

| 条件 | 加分 |
|------|------|
| 接近断点 | +recency |
| 阻塞后续步骤 | +0.2 |
| 用户明确提及 | +0.1 |

---

## 实现状态

✅ `capsule-builder-v2.py` 已实现：
- Open Loop 模式检测
- 去重
- 评分

---
