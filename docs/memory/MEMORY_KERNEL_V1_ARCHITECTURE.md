# Memory Kernel v1 Architecture

**Version**: 1.0.0
**Date**: 2026-03-16

---

## System Architecture

### Layer Overview

```
┌────────────────────────────────────────────────────────────────┐
│                      Application Layer                          │
│  (OpenClaw Agent, CEO, Manager, etc.)                          │
└───────────────────────────┬────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────────┐
│                    Integration Layer                            │
│  OpenClaw Bridge (Shadow Only)                                 │
└───────────────────────────┬────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────────┐
│                     Recall Layer                                │
│  ┌──────────────────┐  ┌──────────────────┐                    │
│  │ RecallEngine     │  │ RecallPolicy     │                    │
│  │ - Approved Only  │  │ - Task Triggers  │                    │
│  │ - Fail-Open      │  │ - Budget Control │                    │
│  └──────────────────┘  └──────────────────┘                    │
└───────────────────────────┬────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────────┐
│                     Query Layer                                 │
│  ┌──────────────────┐  ┌──────────────────┐                    │
│  │ MemoryService    │  │ MemorySearch     │                    │
│  │ - Keyword Search │  │ - Scope Filter   │                    │
│  │ - Metadata       │  │ - Top-K Recall   │                    │
│  └──────────────────┘  └──────────────────┘                    │
│  ┌──────────────────┐  ┌──────────────────┐                    │
│  │ MemoryRanker     │  │ MemoryScope      │                    │
│  │ - Authority-Aware│  │ - Global/Projects│                    │
│  │ - Freshness      │  │ - Domains        │                    │
│  └──────────────────┘  └──────────────────┘                    │
└───────────────────────────┬────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────────┐
│                   Promotion Layer                               │
│  ┌──────────────────┐  ┌──────────────────┐                    │
│  │ PromotionManager │  │ LifecycleManager │                    │
│  │ - Hard Gates     │  │ - TTL            │                    │
│  │ - Rollback       │  │ - Demote/Archive │                    │
│  └──────────────────┘  └──────────────────┘                    │
│  ┌──────────────────┐                                          │
│  │ ConflictResolver │                                          │
│  │ - Detection      │                                          │
│  │ - Resolution     │                                          │
│  └──────────────────┘                                          │
└───────────────────────────┬────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────────┐
│                    Capture Layer                                │
│  ┌──────────────────┐  ┌──────────────────┐                    │
│  │ CaptureEngine    │  │ CandidateStore   │                    │
│  │ - Whitelist      │  │ - Pending        │                    │
│  │ - Noise Filter   │  │ - Approved       │                    │
│  │ - Deduplication  │  │ - Rejected       │                    │
│  └──────────────────┘  └──────────────────┘                    │
└───────────────────────────┬────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────────┐
│                   Foundation Layer                              │
│  ┌──────────────────┐  ┌──────────────────┐                    │
│  │ SourceMapper     │  │ Types            │                    │
│  │ - File → Record  │  │ - MemoryRecord   │                    │
│  │ - Asset Map      │  │ - MemoryScope    │                    │
│  └──────────────────┘  │ - MemoryTier     │                    │
│                        └──────────────────┘                    │
└────────────────────────────────────────────────────────────────┘
```

---

## Data Flow

### Capture Flow

```
Source → CaptureEngine → Validation → Dedup → Noise Filter → CandidateStore
                                                                          ↓
                                                              Review → Promotion
```

### Recall Flow

```
Query → Task Detection → Policy Check → Budget Allocation
                                              ↓
                                        Approved Only → Search → Filter → Rank
                                                                           ↓
                                                                    Trace Output
```

---

## Core Components

### 1. Types (contract/memory/types.py)

```python
- MemoryScope: GLOBAL, PROJECTS, DOMAINS
- MemoryTier: HOT, WARM, COLD, ARCHIVE
- MemorySourceKind: SESSION_LOG, DECISION_LOG, etc.
- MemoryContentType: RULE, FACT, PREFERENCE
- TruthKnowledgeRetrieval: TRUTH, KNOWLEDGE, RETRIEVAL
- MemoryRecord: 核心记忆记录
- MemoryPolicy: 策略定义
```

### 2. Capture Engine (core/memory/memory_capture.py)

```python
class CaptureEngine:
    - capture(title, content, metadata) → CandidateRecord
    - is_noise(content) → bool
    - is_duplicate(content_hash) → bool
    - validate_metadata(metadata) → List[str]
```

### 3. Candidate Store (core/memory/memory_candidate_store.py)

```python
class CandidateStore:
    - add(candidate) → bool
    - approve(candidate_id, reviewed_by) → bool
    - reject(candidate_id, reviewed_by) → bool
    - promote(candidate_id, target_layer) → PromotionResult
```

### 4. Memory Service (core/memory/memory_service.py)

```python
class MemoryService:
    - search(query, scope, filters, top_k) → SearchResult
    - keyword_search(query, top_k) → List[MemoryRecord]
    - search_by_scope(scope) → List[MemoryRecord]
    - advanced_search(...) → SearchResult
```

### 5. Recall Engine (core/memory/memory_recall.py)

```python
class RecallEngine:
    - recall(query, top_k) → RecallResult
    - recall_with_truth_quote(query) → RecallResult
    - set_mode(mode) → void
```

### 6. Promotion Manager (core/memory/memory_promotion.py)

```python
class PromotionManager:
    - check_gates(candidate_id) → (passed, reasons)
    - promote(candidate_id, promoted_by) → (success, record, reasons)
    - rollback(memory_id, rolled_back_by, reason) → (success, error)
```

### 7. Lifecycle Manager (core/memory/memory_lifecycle.py)

```python
class LifecycleManager:
    - register(memory) → LifecycleRecord
    - demote(memory_id, demoted_by, reason) → (success, error)
    - archive(memory_id, archived_by, reason) → (success, error)
    - restore(memory_id, restored_by, reason) → (success, error)
```

### 8. Conflict Resolver (core/memory/memory_conflict.py)

```python
class ConflictResolver:
    - detect_and_resolve(new_record) → (conflicts, unresolved)
    - manual_resolve(conflict_id, strategy, resolved_by) → (success, error)
    - has_blocking_conflicts(conflicts) → bool
```

---

## Data Models

### MemoryRecord

```python
@dataclass
class MemoryRecord:
    id: str
    source_file: str
    source_kind: MemorySourceKind
    content_type: MemoryContentType
    scope: MemoryScope
    scope_qualifier: Optional[str]
    tkr_layer: TruthKnowledgeRetrieval
    title: str
    content: str
    tags: List[str]
    tier: MemoryTier
    status: MemoryStatus
    created_at: datetime
    last_used: Optional[datetime]
    use_count: int
    confidence: float
    importance: float
```

### CandidateRecord

```python
@dataclass
class CandidateRecord:
    id: str
    title: str
    content: str
    metadata: CaptureMetadata
    content_hash: str
    status: str  # pending, approved, rejected, promoted
    captured_at: datetime
    reviewed_at: Optional[datetime]
    promoted_at: Optional[datetime]
```

---

## Configuration

### Capture Whitelist

```yaml
capture_whitelist:
  sources:
    - session_log
    - decision_log
    - technical_note
  content_types:
    - RULE
    - FACT
    - PREFERENCE
  min_confidence: 0.5
  min_importance: 0.3
```

### Promotion Gates

```yaml
promotion_gates:
  review_required: true
  min_confidence: 0.7
  min_importance: 0.5
  no_severe_conflicts: true
  min_tags: 1
```

### TTL Configuration

```yaml
ttl:
  active_days: 90
  deprecated_days: 30
  archived_days: 365
```

### Budget Configuration

```yaml
budget:
  max_tokens: 1000
  max_records: 10
  max_content_length: 500
  truth_ratio: 0.5
  knowledge_ratio: 0.3
  retrieval_ratio: 0.2
```

---

## File Structure

```
Agent-Self-health-Scaffold/
├── contract/memory/
│   ├── types.py              # 核心类型定义
│   └── policies.py           # 策略定义
├── core/memory/
│   ├── source_mapper.py      # 源映射器
│   ├── truth_classifier.py   # Truth 分类器
│   ├── memory_scope.py       # 作用域处理器
│   ├── memory_ranker.py      # 排序器
│   ├── memory_search.py      # 搜索引擎
│   ├── memory_service.py     # 统一服务
│   ├── memory_capture.py     # 捕获引擎
│   ├── memory_candidate_store.py  # 候选存储
│   ├── memory_recall.py      # 召回引擎
│   ├── recall_trace.py       # 召回追踪
│   ├── memory_promotion.py   # 晋升管理
│   ├── memory_lifecycle.py   # 生命周期
│   ├── memory_conflict.py    # 冲突解决
│   ├── memory_recall_policy.py  # 召回策略
│   └── memory_budget.py      # 预算控制
├── tests/memory/
│   ├── test_source_mapper.py
│   ├── test_memory_search.py
│   ├── test_memory_capture.py
│   ├── test_memory_candidate_promotion.py
│   ├── test_memory_recall.py
│   ├── test_memory_recall_trace.py
│   ├── test_memory_promotion.py
│   ├── test_memory_lifecycle.py
│   ├── test_memory_conflict.py
│   ├── test_memory_recall_policy.py
│   └── test_memory_budget.py
└── docs/memory/
    ├── CAPTURE_POLICY.md
    ├── RECALL_POLICY.md
    ├── PROMOTION_POLICY.md
    └── LIFECYCLE_POLICY.md
```

---

## Dependencies

- Python 3.12+
- No external dependencies for core functionality
- Optional: LanceDB (for future vector search)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-03-16 | Initial architecture |
