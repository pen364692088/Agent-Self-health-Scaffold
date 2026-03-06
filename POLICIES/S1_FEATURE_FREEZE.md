# S1 Feature Freeze Policy

**Version**: v1.0
**Effective**: 2026-03-06 11:46 CST
**Status**: ACTIVE

---

## Core Rule

**S1 期间除 blocker 修复外，禁止功能变更。**

---

## Why Feature Freeze?

S1 是证据采集阶段，不是开发阶段。

**问题**：样本期数据会被污染，最后不知道指标变化到底是因为：
- 压缩策略本身
- capsule 质量
- prompt assemble
- 还是中途改了规则

**解决方案**：冻结实现，收集证据。

---

## Allowed Changes

| 类型 | 是否允许 | 说明 |
|------|---------|------|
| Blocker 修复 | ✅ 允许 | 影响数据收集的严重问题 |
| 数据收集工具 | ✅ 允许 | 不影响压缩逻辑的观测工具 |
| 文档更新 | ✅ 允许 | 不影响运行时行为 |
| 压缩策略变更 | ❌ 禁止 | 会污染数据 |
| 新检索规则 | ❌ 禁止 | 会污染数据 |
| 新压缩规则 | ❌ 禁止 | 会污染数据 |
| 参数调整 | ❌ 禁止 | 会污染数据 |

---

## Blocker Definition

**Blocker** = 影响数据收集或导致系统不可用的严重问题。

示例：
- context-retrieve 无法启动
- capsule 无法创建
- 数据丢失
- 崩溃/死锁

非 Blocker：
- 指标不达标
- 收益不够高
- 理论优化空间

---

## Violation Tracking

如果必须违反冻结规则：

```bash
# 必须记录
echo '{"date": "2026-03-06", "change": "...", "reason": "...", "expected_impact": "..."}' \
  >> artifacts/context_compression/freeze_violations.jsonl
```

**要求**：
1. 必须记录变更内容
2. 必须说明理由
3. 必须预测影响
4. 必须在报告中标注

---

## Exit Condition

S1 功能冻结解除条件：

```yaml
exit_conditions:
  - Gate 1 passed
  - OR:
      - S1 abandon
      - Critical blocker requires architecture change
```

---

## Enforcement

**自动检测**（建议）：
```bash
# 检查关键文件是否有变更
git diff --stat HEAD -- \
  tools/context-budget-check \
  tools/capsule-builder \
  tools/context-compress \
  tools/context-retrieve \
  tools/prompt-assemble
```

**人工审计**：
每次周报时检查是否有违反冻结规则的变更。

---

**Keywords**: `feature-freeze` `controlled-validation` `evidence-collection`
