# Phase 5 Scope · Limited Shadow Validation

**Date**: 2026-03-09T11:25:00-06:00
**Phase**: Gate 1 Final Closure
**Mode**: 受控验证（非开放式观察）

---

## 目标定义

**验证 V2 + evaluator v2 在真实压缩场景下，是否支持"从断点继续做事"。**

这不是观察期，是**带退出条件的验证闭环**。

---

## 量化目标

| 指标 | 目标 | 阻断条件 |
|------|------|----------|
| Shadow Agreement Rate | >= 80% | < 70% 暂停 |
| False Positive Rate | < 20% | >= 30% 暂停 |
| Create Action Ambiguity Impact | 不主导 | 成主导失败类型暂停 |

---

## 样本要求

- 来源：真实压缩触发事件（非 replay）
- 数量：最小 10 个有效样本
- 字段：完整可审计

---

## 阶段划分

| Phase | 名称 | 产出 |
|-------|------|------|
| 5A | Shadow Trace 采集 | SHADOW_TRACE.jsonl |
| 5B | Spot-check 复核 | SHADOW_SPOTCHECK_REPORT.md |
| 5C | 歧义专项检查 | CREATE_ACTION_AMBIGUITY_REPORT.md |
| 5D | Gate 1 Final Audit | GATE1_CLOSURE_VERDICT.md |

---

## 退出条件

### 成功退出
- Agreement >= 80%
- FP < 20%
- 无新主导失败模式
- → Gate 1 正式关闭

### 暂停退出
- Agreement < 70%
- FP >= 30%
- Create Action 歧义成主导 blocker
- → 回退修复

---

## 非目标

- ❌ 不继续大改 capsule 主逻辑
- ❌ 不重新设计 evaluator
- ❌ 不做长期监控
- ❌ 不扩展到 Gate 2 问题

---

## 时间边界

- 预计完成：收集 10+ 有效 shadow 样本后
- 超时：若 48 小时内无法收集足够样本，评估是否降低样本要求

---

Created: 2026-03-09 11:25 CST
