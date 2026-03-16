# Memory Kernel Index

**Version**: v1.0.0
**Date**: 2026-03-16
**Status**: Released

---

## Overview

Memory Kernel v1 是一个分层记忆管理系统，支持多类型记忆捕获、候选存储、升级审批、生命周期管理和有限召回。

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Memory Kernel v1                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Capture   │→ │  Candidate  │→ │  Promotion  │        │
│  │   (M4a)     │  │    Store    │  │    (M4b)    │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│         │                                    │              │
│         ▼                                    ▼              │
│  ┌─────────────┐                    ┌─────────────┐        │
│  │   Recall    │                    │  Lifecycle  │        │
│  │   (M5a/M5b) │                    │    (M4b)    │        │
│  └─────────────┘                    └─────────────┘        │
│         │                                    │              │
│         ▼                                    ▼              │
│  ┌─────────────────────────────────────────────────┐      │
│  │            Approved Knowledge Store              │      │
│  └─────────────────────────────────────────────────┘      │
│                          │                                  │
│                          ▼                                  │
│  ┌─────────────────────────────────────────────────┐      │
│  │         Bridge Integration (G1-G3.5)             │      │
│  └─────────────────────────────────────────────────┘      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Core Components

### Capture (M4a)

| File | Description |
|------|-------------|
| `core/memory/memory_capture.py` | 记忆捕获系统 |
| `core/memory/memory_candidate_store.py` | 候选存储 |
| `docs/memory/CAPTURE_POLICY.md` | 捕获策略 |

**Key Features**:
- 多源捕获 (decision_log, rule, technical_note, etc.)
- 自动去重
- 候选存储
- 捕获元数据追踪

### Promotion (M4b)

| File | Description |
|------|-------------|
| `core/memory/memory_promotion.py` | 升级审批系统 |
| `core/memory/memory_lifecycle.py` | 生命周期管理 |
| `core/memory/memory_conflict.py` | 冲突检测与解决 |
| `docs/memory/PROMOTION_POLICY.md` | 升级策略 |
| `docs/memory/LIFECYCLE_POLICY.md` | 生命周期策略 |

**Key Features**:
- 升级门控 (min_confidence=0.7, min_importance=0.5)
- 生命周期状态 (active → deprecated → archived → deleted)
- TTL 支持
- 冲突检测与自动/手动解决

### Recall (M5a/M5b)

| File | Description |
|------|-------------|
| `core/memory/memory_recall.py` | 召回引擎 |
| `core/memory/memory_recall_policy.py` | 召回策略 |
| `core/memory/memory_budget.py` | 预算控制 |
| `docs/memory/M5A_TASK_DEFINITION.md` | M5a 定义 |
| `docs/memory/M5B_TASK_DEFINITION.md` | M5b 定义 |

**Key Features**:
- 任务类型触发
- 预算控制
- Approved-only 召回
- Canary limited recall

### Bridge Integration (G1-G3.5)

| Phase | File | Description |
|-------|------|-------------|
| G1 | `integration/memory/openclaw_bridge.py` | Shadow 模式 |
| G2 | `integration/memory/openclaw_bridge_canary.py` | Canary Assist |
| G3 | `integration/memory/openclaw_bridge_mainline_limited.py` | Limited Mainline |

**Key Features**:
- 只读接入
- 建议参与
- 任务类型限制
- 会话级限流
- Fail-open 100%

---

## Type System

### Memory Record

```python
@dataclass
class MemoryRecord:
    id: str
    source_file: str
    source_kind: MemorySourceKind
    content_type: MemoryContentType
    scope: MemoryScope
    tkr_layer: TruthKnowledgeRetrieval
    title: str
    content: str
    tags: List[str]
    confidence: float
    importance: float
    created_at: datetime
    # ... more fields
```

### Truth-Knowledge-Retrieval (TKR)

| Layer | Description | Priority |
|-------|-------------|----------|
| truth | Absolute truths | Highest |
| knowledge | Derived knowledge | Medium |
| retrieval | Context-specific | Lowest |

### Memory Scope

| Scope | Description |
|-------|-------------|
| global | All projects |
| projects | Specific projects |
| local | Single context |

---

## Test Coverage

| Module | Tests | Status |
|--------|-------|--------|
| Types | 19 | ✅ |
| Recall | 35 | ✅ |
| Capture | 45 | ✅ |
| Controlled Recall | 46 | ✅ |
| Promotion | 33 | ✅ |
| Canary Recall | 28 | ✅ |
| Bridge Shadow | 17 | ✅ |
| Bridge Canary | 24 | ✅ |
| Bridge Mainline | 23 | ✅ |
| **Total** | **270** | ✅ |

---

## Documentation

### Release Documents

| Document | Location |
|----------|----------|
| v1 Overview | `docs/memory/MEMORY_KERNEL_V1_OVERVIEW.md` |
| v1 Architecture | `docs/memory/MEMORY_KERNEL_V1_ARCHITECTURE.md` |
| v1 Operations | `docs/memory/MEMORY_KERNEL_V1_OPERATIONS.md` |
| v1 Limitations | `docs/memory/MEMORY_KERNEL_V1_LIMITATIONS.md` |

### Policy Documents

| Policy | Location |
|--------|----------|
| Capture Policy | `docs/memory/CAPTURE_POLICY.md` |
| Promotion Policy | `docs/memory/PROMOTION_POLICY.md` |
| Lifecycle Policy | `docs/memory/LIFECYCLE_POLICY.md` |

### Task Definitions

| Task | Location |
|------|----------|
| M3 | `docs/memory/M3_TASK_DEFINITION.md` |
| M4a | `docs/memory/M4A_TASK_DEFINITION.md` |
| M5a | `docs/memory/M5A_TASK_DEFINITION.md` |
| M4b | `docs/memory/M4B_TASK_DEFINITION.md` |
| M5b | `docs/memory/M5B_TASK_DEFINITION.md` |

### Acceptance Reports

| Phase | Location |
|-------|----------|
| M0-M2 | `artifacts/acceptance/MEMORY_KERNEL_M0_M2_ACCEPTANCE.md` |
| M3 | `artifacts/acceptance/MEMORY_KERNEL_M3_ACCEPTANCE.md` |
| M4a | `artifacts/acceptance/MEMORY_KERNEL_M4A_ACCEPTANCE.md` |
| M5a | `artifacts/acceptance/MEMORY_KERNEL_M5A_ACCEPTANCE.md` |
| M4b | `artifacts/acceptance/MEMORY_KERNEL_M4B_ACCEPTANCE.md` |
| M5b | `artifacts/acceptance/MEMORY_KERNEL_M5B_ACCEPTANCE.md` |
| v1 Pack | `artifacts/memory/MEMORY_KERNEL_V1_ACCEPTANCE_PACK.md` |

---

## Metrics

| Metric | Value |
|--------|-------|
| Total Tests | 270 |
| Total Files | 75+ |
| Total Lines | ~21,000 |
| Noise Filter Rate | 100% |
| Dedup Rate | 100% |
| Recall Hit Rate | 75% |
| A/B Improvement | +13%~+19% |

---

## Version History

| Version | Date | Description |
|---------|------|-------------|
| v1.0.0 | 2026-03-16 | Initial release with M0-M5b + G1-G3.5 |

---

**Last Updated**: 2026-03-16T01:48:00Z
