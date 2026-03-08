# Evidence Freeze Declaration

**Declared**: 2026-03-08T00:07:00-06:00
**Status**: FROZEN
**Scope**: Milestone B Natural Traffic Validation

---

## Purpose

保护证据链完整性，等待首个自然 trigger。

---

## Frozen Items

| Category | Items | Reason |
|----------|-------|--------|
| **Metrics** | 采样逻辑、命名、计数口径 | 证据链一致性 |
| **Thresholds** | trigger threshold = 0.85 | DoD 要求默认配置 |
| **Scoring** | capsule scoring formula | 对比基准 |
| **Schema** | capsule structure, evidence format | 可比性 |
| **Directories** | 证据目录结构 | 追溯链 |

---

## Forbidden During Freeze

- ❌ 修改 trigger threshold
- ❌ 修改 counter 命名/计数逻辑
- ❌ 修改 capsule schema
- ❌ 重命名/移动证据文件
- ❌ 添加"顺手优化"

---

## Allowed During Freeze

- ✅ 记录观察数据
- ✅ 运行健康检查
- ✅ 准备模板（不动实现）
- ✅ 文档更新

---

## Exit Condition

首个自然 trigger 完成证据封板后，解除冻结。

---

## Current Metrics Baseline

```
budget_ratio: ~0.825
hot_zone_threshold: 0.84
trigger_threshold: 0.85
distance_to_hot_zone: ~0.015
distance_to_trigger: ~0.025
```

---

## Duration

**Indefinite** until natural trigger captured.

---

*Evidence freeze declared: 2026-03-08T00:07:00-06:00*
