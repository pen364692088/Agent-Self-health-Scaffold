# Capture Policy

**Version**: 1.0.0
**Created**: 2026-03-15

---

## Overview

Memory Kernel 的捕获策略定义了如何捕获新记忆，确保只有高质量的候选才能进入系统。

---

## Core Principles

### 1. Capture is Candidate, Not Authority

捕获的内容只是候选，不是权威知识。必须经过审核和提升才能成为正式记忆。

### 2. Whitelist Only

只捕获白名单来源的内容，避免噪音污染。

### 3. Explicit Promotion

候选必须显式提升为正式记忆，不能自动晋升。

---

## Capture Flow

```
Source → CaptureEngine → Validation → Deduplication → Noise Filter → CandidateStore
                                                                          ↓
                                                              Manual Review → Promotion
```

---

## Required Fields

每条捕获必须包含以下元数据：

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| capture_reason | CaptureReason | 捕获原因 | ✅ |
| source_ref | SourceRef | 来源引用 | ✅ |
| scope | MemoryScope | 作用域 | ✅ |
| importance | float | 重要性 [0.0, 1.0] | ✅ |
| confidence | float | 置信度 [0.0, 1.0] | ✅ |
| authority_level | str | 权威等级 | ✅ |

### CaptureReason

```python
@dataclass
class CaptureReason:
    reason: str  # 原因描述
    category: str  # 分类：auto/manual/suggestion
    triggered_by: Optional[str] = None  # 触发者
```

### SourceRef

```python
@dataclass
class SourceRef:
    path: str  # 文件路径
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    context: Optional[str] = None
    session_id: Optional[str] = None
    timestamp: Optional[datetime] = None
```

---

## Whitelist Configuration

### Allowed Sources

| Source Kind | Description |
|-------------|-------------|
| SESSION_LOG | 会话日志 |
| DECISION_LOG | 决策日志 |
| TECHNICAL_NOTE | 技术笔记 |

### Allowed Content Types

| Content Type | Description |
|--------------|-------------|
| RULE | 规则 |
| FACT | 事实 |
| PREFERENCE | 偏好 |

### Thresholds

| Threshold | Default | Description |
|-----------|---------|-------------|
| min_confidence | 0.5 | 最低置信度 |
| min_importance | 0.3 | 最低重要性 |

---

## Noise Filtering Rules

以下内容被视为噪音，不进行捕获：

1. **Empty content** - 空内容
2. **Too short** - 少于 10 个字符
3. **Whitespace only** - 仅包含空白字符
4. **Below thresholds** - 置信度或重要性低于阈值
5. **Missing required fields** - 缺少必填字段

---

## Deduplication

使用内容哈希（SHA256）进行去重：

```python
def compute_content_hash(content: str) -> str:
    normalized = content.strip().lower()
    return hashlib.sha256(normalized.encode()).hexdigest()[:16]
```

如果内容哈希已存在，则拒绝捕获。

---

## Candidate States

| State | Description | Transitions |
|-------|-------------|-------------|
| pending | 待审核 | → approved, rejected, promoted |
| approved | 已批准 | → promoted |
| rejected | 已拒绝 | 终态 |
| promoted | 已提升 | 终态 |

---

## Promotion Criteria

提升候选为正式记忆需要：

1. **状态检查**: 候选状态为 pending 或 approved
2. **审核者**: 指定审核者
3. **目标层级**: 指定 T/K/R 层级
4. **审核备注**: 可选的审核备注

### Promotion Flow

```python
result = store.promote(
    candidate_id="cand_20260315_abc123",
    target_tkr_layer=TruthKnowledgeRetrieval.KNOWLEDGE,
    reviewed_by="manager",
    review_notes="Verified and approved"
)
```

---

## API Reference

### CaptureEngine

```python
engine = CaptureEngine(
    whitelist=CaptureWhitelist(),
    noise_threshold_chars=10,
    dedup_similarity_threshold=0.9,
)

# 捕获
candidate = engine.capture(
    title="New Rule",
    content="All API endpoints must be versioned",
    metadata=CaptureMetadata(
        capture_reason=CaptureReason(
            reason="User decision",
            category="manual"
        ),
        source_ref=SourceRef(path="session/2026-03-15.md"),
        scope=MemoryScope.GLOBAL,
        importance=0.8,
        confidence=0.9,
        authority_level="high",
    ),
)
```

### CandidateStore

```python
store = CandidateStore()

# 添加候选
store.add(candidate)

# 批准
store.approve(candidate_id, reviewed_by="manager")

# 拒绝
store.reject(candidate_id, reviewed_by="manager", review_notes="Outdated")

# 提升
result = store.promote(
    candidate_id=candidate_id,
    target_tkr_layer=TruthKnowledgeRetrieval.KNOWLEDGE,
    reviewed_by="manager",
)
```

---

## Metrics

| Metric | Description |
|--------|-------------|
| total_candidates | 总候选数 |
| by_status | 按状态分布 |
| promoted_memories | 提升的记忆数 |

---

## Best Practices

1. **Always provide source_ref** - 确保可追溯
2. **Set realistic confidence** - 不要高估置信度
3. **Review before promotion** - 审核后再提升
4. **Add review_notes** - 记录审核理由

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-03-15 | Initial version |
