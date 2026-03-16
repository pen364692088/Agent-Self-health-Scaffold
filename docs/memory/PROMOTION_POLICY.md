# Promotion Policy

**Version**: 1.0.0
**Created**: 2026-03-16

---

## Overview

Memory Kernel 的晋升策略定义了 candidate 如何成为 approved 记忆。

---

## Core Principles

### 1. Hard Gates Required

candidate -> approved 必须通过硬门槛，不可绕过。

### 2. Review Required

所有晋升必须经过审核。

### 3. Rollback Capability

错误晋升可撤销。

---

## Promotion Flow

```
Candidate → Gate Check → Review → Promote → Active Memory
                                     ↓
                              Rollback (if error)
```

---

## Hard Gates

| Gate | Requirement | Default |
|------|-------------|---------|
| review_required | 必须经过审核 | True |
| min_confidence | 最低置信度 | 0.7 |
| min_importance | 最低重要性 | 0.5 |
| no_severe_conflicts | 无严重冲突 | True |
| source_verified | 来源已验证 | False |
| min_tags | 最少标签数 | 1 |

### Gate Check

```python
gate = PromotionGate(
    review_required=True,
    min_confidence=0.7,
    min_importance=0.5,
)

passed, reasons = gate.check(candidate)
```

---

## Promotion Process

### Step 1: Gate Check

检查候选是否满足所有门槛。

### Step 2: Conflict Detection

检测候选与现有记忆的冲突。

### Step 3: Review

人工审核候选内容。

### Step 4: Promote

执行晋升，创建正式记忆。

### Step 5: Record

记录晋升历史，支持回滚。

---

## Rollback

### When to Rollback

- 发现晋升错误
- 记忆内容有误
- 严重冲突未解决

### Rollback Process

```python
success, error = manager.rollback(
    memory_id="mem_001",
    rolled_back_by="manager",
    rollback_reason="Content error found",
)
```

### Rollback Effects

1. 记忆从正式列表中移除
2. 候选状态更新为 "rollback"
3. 晋升记录标记为已回滚
4. 保留回滚历史

---

## Promotion Record

```python
@dataclass
class PromotionRecord:
    promotion_id: str
    candidate_id: str
    memory_id: str
    promoted_at: datetime
    promoted_by: str
    review_notes: Optional[str]
    rolled_back: bool
    gates_passed: List[str]
```

---

## API Reference

### PromotionManager

```python
manager = PromotionManager(
    candidate_store=store,
    gate=PromotionGate(min_confidence=0.8),
)

# 检查门槛
passed, reasons = manager.check_gates("cand_001")

# 晋升
success, record, reasons = manager.promote(
    candidate_id="cand_001",
    promoted_by="manager",
    review_notes="Verified and approved",
)

# 回滚
success, error = manager.rollback(
    memory_id="mem_001",
    rolled_back_by="manager",
    rollback_reason="Error found",
)
```

---

## Metrics

| Metric | Description |
|--------|-------------|
| total_promotions | 总晋升数 |
| active_memories | 活跃记忆数 |
| rolled_back | 回滚数 |
| rollback_rate | 回滚率 |

---

## Best Practices

1. **Set appropriate gates** - 根据场景设置门槛
2. **Always review** - 不要跳过审核
3. **Document reason** - 记录晋升原因
4. **Monitor rollback rate** - 监控回滚率
5. **Handle conflicts first** - 先解决冲突再晋升

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-03-16 | Initial version |
