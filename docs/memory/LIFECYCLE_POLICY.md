# Lifecycle Policy

**Version**: 1.0.0
**Created**: 2026-03-16

---

## Overview

Memory Kernel 的生命周期策略定义了记忆从创建到删除的完整生命周期。

---

## Core Principles

### 1. Full Lifecycle

记忆有完整的生命周期，从 active 到 deleted。

### 2. TTL & Expiration

记忆有时效性，过期后可自动处理。

### 3. Demotion & Archive

记忆可降级或归档，不立即删除。

### 4. Restore Capability

降级或归档的记忆可恢复。

---

## Lifecycle States

| State | Description | Default TTL |
|-------|-------------|-------------|
| active | 活跃使用 | 90 days |
| deprecated | 已弃用 | 30 days |
| archived | 已归档 | 365 days |
| deleted | 已删除 | - |

---

## State Transitions

```
         ┌──────────────┐
         │   active     │
         └──────┬───────┘
           ↓    ↑
    (demote)  (restore)
           ↓    ↑
         ┌──────────────┐
         │  deprecated  │
         └──────┬───────┘
           ↓    ↑
   (archive)  (restore)
           ↓    ↑
         ┌──────────────┐
         │   archived   │
         └──────┬───────┘
           ↓    ↑
    (delete)  (restore, rare)
           ↓
         ┌──────────────┐
         │   deleted    │ (terminal)
         └──────────────┘
```

---

## Valid Transitions

| From | To | Action |
|------|-----|--------|
| active | deprecated | demote |
| active | archived | archive |
| deprecated | active | restore |
| deprecated | archived | archive |
| archived | active | restore |
| archived | deleted | delete |

---

## TTL Configuration

```python
config = TTLConfig(
    active_days=90,      # 活跃状态默认 TTL
    deprecated_days=30,  # 弃用状态默认 TTL
    archived_days=365,   # 归档状态默认 TTL
)
```

---

## Operations

### Demote

降级记忆，通常因为：
- 使用频率低
- 重要性下降
- 内容过时

```python
success, error = manager.demote(
    memory_id="mem_001",
    demoted_by="manager",
    reason="Low usage frequency",
)
```

### Archive

归档记忆，通常因为：
- 长期未使用
- 不再相关
- 历史保留

```python
success, error = manager.archive(
    memory_id="mem_001",
    archived_by="manager",
    reason="No longer relevant",
)
```

### Restore

恢复记忆，通常因为：
- 重新需要
- 误操作恢复
- 重要性回升

```python
success, error = manager.restore(
    memory_id="mem_001",
    restored_by="manager",
    reason="Needed again",
)
```

---

## Lifecycle Record

```python
@dataclass
class LifecycleRecord:
    memory_id: str
    state: LifecycleState
    created_at: datetime
    last_used: Optional[datetime]
    expires_at: Optional[datetime]
    use_count: int
    transitions: List[LifecycleTransition]
```

---

## Expiration Check

```python
expired = manager.check_expiration()

for memory_id in expired:
    # 处理过期记忆
    manager.demote(memory_id, demoted_by="system", reason="Expired")
```

---

## Usage Tracking

```python
# 记录使用
manager.record_usage("mem_001")

# 影响生命周期
# - 更新 last_used
# - 增加 use_count
# - 可能延长 TTL
```

---

## API Reference

### LifecycleManager

```python
manager = LifecycleManager(
    ttl_config=TTLConfig(active_days=60),
)

# 注册新记忆
record = manager.register(memory)

# 转换状态
success, error = manager.transition(
    memory_id="mem_001",
    to_state=LifecycleState.DEPRECATED,
    transitioned_by="manager",
    reason="Old version",
)

# 检查过期
expired = manager.check_expiration()

# 按状态列出
deprecated = manager.list_by_state(LifecycleState.DEPRECATED)
```

---

## Metrics

| Metric | Description |
|--------|-------------|
| total | 总记忆数 |
| by_state | 按状态分布 |
| expired | 过期数 |

---

## Best Practices

1. **Set appropriate TTL** - 根据内容类型设置 TTL
2. **Monitor expiration** - 定期检查过期记忆
3. **Document transitions** - 记录状态转换原因
4. **Consider restore** - 归档前考虑是否需要恢复
5. **Clean up deleted** - 定期清理已删除记忆

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-03-16 | Initial version |
