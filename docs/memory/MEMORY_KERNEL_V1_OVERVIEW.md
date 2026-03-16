# Memory Kernel v1 Overview

**Version**: 1.0.0
**Release Date**: 2026-03-16
**Status**: Baseline Complete

---

## What is Memory Kernel?

Memory Kernel 是 Agent-Self-health-Scaffold 的记忆管理层，提供统一的记忆存储、检索、晋升和生命周期管理。

---

## Core Capabilities

### 1. Memory Asset Management (M0-M2)

- **Asset Audit**: 盘点 192 文件，分类 6 大类
- **Type System**: 10 核心类型定义
- **Source Mapping**: 文件到 MemoryRecord 映射

### 2. Unified Query Service (M3)

- **Keyword Search**: 关键词搜索
- **Metadata Filter**: 元数据过滤
- **Scope Filter**: 作用域过滤
- **Authority-Aware Ranking**: 权威感知排序
- **Top-K Recall**: Top-K 召回
- **Trace Output**: 追踪输出

### 3. Capture Governance (M4a)

- **Whitelist Only**: 只捕获白名单来源
- **Noise Filtering**: 噪音拦截 (100% 效果)
- **Deduplication**: 去重机制 (100% 效果)
- **Candidate Store**: 候选存储，不进入 authority knowledge

### 4. Controlled Recall (M5a)

- **Approved Only**: 默认只从 approved 召回
- **Shadow/Debug Mode**: candidate 仅 shadow/debug 可见
- **Truth Exact Quote**: Truth 记录只允许精确引用
- **Fail-Open**: 召回失败时主链继续

### 5. Promotion & Lifecycle Governance (M4b)

- **Hard Gates**: candidate -> approved 硬门槛
- **Lifecycle Management**: TTL、demotion、archive、restore
- **Conflict Resolution**: 自动/人工解决冲突
- **Rollback Capability**: 错误晋升可撤销

### 6. Limited Canary Recall (M5b)

- **Task-Type Triggers**: 按任务类型触发 recall
- **Budget Control**: prompt budget 控制
- **A/B Testing**: 有/无 recall 对照实验
- **Quality Metrics**: 质量指标 +13%~+17%

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Memory Kernel v1                         │
├─────────────────────────────────────────────────────────────┤
│  Capture Layer (M4a)                                        │
│  ├── CaptureEngine                                          │
│  ├── CandidateStore                                         │
│  └── Whitelist / Noise Filter / Deduplication              │
├─────────────────────────────────────────────────────────────┤
│  Promotion Layer (M4b)                                      │
│  ├── PromotionManager                                       │
│  ├── LifecycleManager                                       │
│  ├── ConflictResolver                                       │
│  └── Hard Gates / TTL / Rollback                           │
├─────────────────────────────────────────────────────────────┤
│  Query Layer (M3)                                           │
│  ├── MemoryService                                          │
│  ├── MemorySearchEngine                                     │
│  ├── MemoryRanker                                           │
│  └── Scope Filter / Top-K / Trace                          │
├─────────────────────────────────────────────────────────────┤
│  Recall Layer (M5a/M5b)                                     │
│  ├── RecallEngine                                           │
│  ├── RecallPolicyManager                                    │
│  ├── BudgetManager                                          │
│  └── Approved Only / Fail-Open / Budget Control            │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Metrics

| Metric | Value |
|--------|-------|
| Total Tests | 206 |
| Total Files | 50+ |
| Total Lines | 15,000+ |
| Noise Filter Rate | 100% |
| Dedup Rate | 100% |
| Recall Hit Rate | 75% |
| Truth Quote Accuracy | 100% |
| A/B Improvement | +13%~+17% |

---

## Release Phases

| Phase | Description | Status |
|-------|-------------|--------|
| M0-M2 | Asset Audit & Types | ✅ Complete |
| M3 | Unified Query Service | ✅ Complete |
| M4a | Capture Governance | ✅ Complete |
| M5a | Controlled Recall | ✅ Complete |
| M4b | Promotion & Lifecycle | ✅ Complete |
| M5b | Limited Canary Recall | ✅ Complete |
| Shadow Validation | Boundary Verification | ✅ Complete |

---

## Next Steps

1. **R1**: 发布收口 - 整理文档，统一基线
2. **R2**: Soak/Canary 观察窗 - 验证稳定性
3. **G1**: OpenClaw Bridge Shadow - 只读 shadow 接入

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-03-16 | Initial baseline release |

---

**Maintainer**: Manager
**Last Updated**: 2026-03-16T00:40:00Z
