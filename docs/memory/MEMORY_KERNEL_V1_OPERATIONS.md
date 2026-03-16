# Memory Kernel v1 Operations

**Version**: 1.0.0
**Date**: 2026-03-16

---

## Overview

本文档描述 Memory Kernel v1 的运维操作指南。

---

## Quick Start

### 1. 初始化

```python
from core.memory.memory_service import MemoryService
from core.memory.memory_capture import CaptureEngine
from core.memory.memory_candidate_store import CandidateStore
from core.memory.memory_recall import RecallEngine
from core.memory.memory_promotion import PromotionManager

# 初始化候选存储
candidate_store = CandidateStore()

# 初始化捕获引擎
capture_engine = CaptureEngine()

# 初始化晋升管理器
promotion_manager = PromotionManager(candidate_store=candidate_store)

# 初始化召回引擎
recall_engine = RecallEngine()
```

### 2. 捕获记忆

```python
from core.memory.memory_capture import CaptureMetadata, CaptureReason, SourceRef

metadata = CaptureMetadata(
    capture_reason=CaptureReason(
        reason="User decision",
        category="manual"
    ),
    source_ref=SourceRef(path="session/2026-03-16.md"),
    scope=MemoryScope.GLOBAL,
    importance=0.8,
    confidence=0.9,
    authority_level="high",
)

candidate = capture_engine.capture(
    title="New Rule",
    content="All API endpoints must be versioned",
    metadata=metadata,
)

if candidate:
    candidate_store.add(candidate)
```

### 3. 审核候选

```python
# 批准
candidate_store.approve(
    candidate_id=candidate.id,
    reviewed_by="manager",
    review_notes="Verified"
)

# 或拒绝
candidate_store.reject(
    candidate_id=candidate.id,
    reviewed_by="manager",
    review_notes="Outdated"
)
```

### 4. 晋升记忆

```python
from contract.memory.types import TruthKnowledgeRetrieval

success, record, reasons = promotion_manager.promote(
    candidate_id=candidate.id,
    promoted_by="manager",
    review_notes="Promoted to knowledge layer",
    target_tkr_layer=TruthKnowledgeRetrieval.KNOWLEDGE,
)

if success:
    print(f"Promoted to: {record.memory_id}")
else:
    print(f"Failed: {reasons}")
```

### 5. 召回记忆

```python
# 基本召回
result = recall_engine.recall(query="API versioning", top_k=10)

for record in result.records:
    print(f"{record.title}: {record.content}")

# 查看 trace
if result.trace:
    print(f"Total scanned: {result.trace.total_scanned}")
    print(f"Returned: {result.trace.returned_count}")
```

---

## Operations

### Capture Operations

#### 查看候选列表

```python
# 所有候选
candidates = candidate_store.list()

# 按状态过滤
pending = candidate_store.list(status="pending")
approved = candidate_store.list(status="approved")
```

#### 统计信息

```python
stats = capture_engine.get_statistics()
print(f"Total: {stats['total']}")
print(f"By status: {stats['by_status']}")
```

### Promotion Operations

#### 检查门槛

```python
passed, reasons = promotion_manager.check_gates(candidate_id)
if not passed:
    print(f"Gates not passed: {reasons}")
```

#### 查看晋升历史

```python
history = promotion_manager.get_promotion_history()
for record in history:
    print(f"{record.promotion_id}: {record.candidate_id} → {record.memory_id}")
```

#### 回滚晋升

```python
success, error = promotion_manager.rollback(
    memory_id="mem_001",
    rolled_back_by="manager",
    rollback_reason="Error found",
)
```

### Recall Operations

#### 按任务类型召回

```python
from core.memory.memory_recall_policy import RecallPolicyManager

policy_manager = RecallPolicyManager()

# 自动检测任务类型
should_recall = policy_manager.should_recall("how to implement API?")

# 应用策略
filtered = policy_manager.apply_policy(records, query)
```

#### 预算控制

```python
from core.memory.memory_budget import BudgetManager

budget_manager = BudgetManager()
filtered, usage = budget_manager.enforce_budget(records)

print(f"Used tokens: {usage.used_tokens}")
print(f"Truncated: {usage.truncated}")
print(f"Rejected: {usage.rejected}")
```

### Lifecycle Operations

#### 降级记忆

```python
from core.memory.memory_lifecycle import LifecycleManager

lifecycle_manager = LifecycleManager()

success, error = lifecycle_manager.demote(
    memory_id="mem_001",
    demoted_by="manager",
    reason="Low usage",
)
```

#### 归档记忆

```python
success, error = lifecycle_manager.archive(
    memory_id="mem_001",
    archived_by="manager",
    reason="No longer relevant",
)
```

#### 恢复记忆

```python
success, error = lifecycle_manager.restore(
    memory_id="mem_001",
    restored_by="manager",
    reason="Needed again",
)
```

#### 检查过期

```python
expired = lifecycle_manager.check_expiration()
for memory_id in expired:
    print(f"Expired: {memory_id}")
```

### Conflict Operations

#### 检测冲突

```python
from core.memory.memory_conflict import ConflictResolver

resolver = ConflictResolver()
resolver.detector.load_records(existing_records)

conflicts, unresolved = resolver.detect_and_resolve(new_record)
```

#### 解决冲突

```python
for conflict in unresolved:
    success, error = resolver.manual_resolve(
        conflict_id=conflict.conflict_id,
        strategy=ResolutionStrategy.KEEP_NEWER,
        resolved_by="manager",
    )
```

---

## Monitoring

### Key Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| candidate_total | 候选总数 | Monitor |
| noise_filter_rate | 噪音拦截率 | ≥80% |
| dedup_rate | 去重率 | ≥90% |
| promotion_rate | 晋升通过率 | Monitor |
| recall_hit_rate | 召回命中率 | ≥50% |
| budget_usage | 预算使用率 | Monitor |
| rollback_rate | 回滚率 | <10% |
| conflict_rate | 冲突率 | Monitor |

### Health Checks

```python
# 候选存储健康检查
stats = candidate_store.get_statistics()
if stats["by_status"].get("pending", 0) > 100:
    print("WARNING: Too many pending candidates")

# 晋升健康检查
promo_stats = promotion_manager.get_statistics()
if promo_stats["rollback_rate"] > 0.1:
    print("WARNING: High rollback rate")

# 召回健康检查
recall_stats = recall_engine.get_statistics()
print(f"Approved records: {recall_stats['approved_count']}")
```

---

## Maintenance

### Daily Tasks

1. **检查候选队列**
   ```python
   pending = candidate_store.list(status="pending")
   print(f"Pending candidates: {len(pending)}")
   ```

2. **检查过期记忆**
   ```python
   expired = lifecycle_manager.check_expiration()
   print(f"Expired memories: {len(expired)}")
   ```

3. **检查未解决冲突**
   ```python
   unresolved = resolver.list_unresolved()
   print(f"Unresolved conflicts: {len(unresolved)}")
   ```

### Weekly Tasks

1. **清理已拒绝候选**
   ```python
   rejected = candidate_store.list(status="rejected")
   # 归档或删除
   ```

2. **审查晋升历史**
   ```python
   history = promotion_manager.get_promotion_history()
   # 检查回滚率
   ```

3. **审查召回质量**
   ```python
   # 查看 A/B 测试结果
   ```

### Monthly Tasks

1. **归档旧记忆**
   ```python
   old_records = lifecycle_manager.list_by_state(LifecycleState.DEPRECATED)
   for record in old_records:
       lifecycle_manager.archive(record.id, archived_by="system")
   ```

2. **更新白名单**
   ```yaml
   # 根据实际情况调整 capture whitelist
   ```

3. **调整预算**
   ```yaml
   # 根据使用情况调整 budget 配置
   ```

---

## Troubleshooting

### Issue: 候选无法晋升

**Symptoms**: `check_gates` 返回失败

**Diagnosis**:
```python
passed, reasons = promotion_manager.check_gates(candidate_id)
print(reasons)
```

**Solutions**:
- 检查置信度/重要性是否满足阈值
- 检查是否有未解决的冲突
- 检查候选状态是否为 approved

### Issue: 召回无结果

**Symptoms**: `recall` 返回空列表

**Diagnosis**:
```python
result = recall_engine.recall(query="test")
if result.trace:
    print(f"Total scanned: {result.trace.total_scanned}")
    print(f"Filtered: {result.trace.filtered_count}")
```

**Solutions**:
- 检查是否有 approved 记录
- 检查查询关键词是否匹配
- 检查作用域/层级过滤器

### Issue: 预算超限

**Symptoms**: 大量记录被拒绝

**Diagnosis**:
```python
filtered, usage = budget_manager.enforce_budget(records)
print(f"Rejected: {usage.rejected}")
print(f"Records rejected: {usage.records_rejected}")
```

**Solutions**:
- 增加 max_tokens
- 减少 max_content_length
- 调整层级预算比例

---

## Security

### Access Control

- 所有晋升操作需要 `reviewed_by`
- 所有状态变更需要操作者标识
- 回滚操作需要 `rollback_reason`

### Data Protection

- candidate 不进入 authority knowledge
- Truth 记录只允许精确引用
- 所有操作有 trace 记录

### Audit Trail

```python
# 晋升历史
history = promotion_manager.get_promotion_history()

# 状态转换历史
record = lifecycle_manager.get_record(memory_id)
for transition in record.transitions:
    print(f"{transition.from_state} → {transition.to_state}")
```

---

## Backup & Recovery

### Export

```python
candidate_store.export_to_json("candidates_backup.json")
```

### Import

```python
import json

with open("candidates_backup.json", 'r') as f:
    data = json.load(f)

for item in data["candidates"]:
    candidate = CandidateRecord.from_dict(item)
    candidate_store.add(candidate)
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-03-16 | Initial operations guide |
