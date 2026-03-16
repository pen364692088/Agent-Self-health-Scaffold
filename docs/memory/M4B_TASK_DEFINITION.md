# M4b: Promotion & Lifecycle Governance

**Status**: In Progress
**Branch**: feature/memory-kernel-m4b
**Started**: 2026-03-16T00:12:00Z

---

## Objective

建立 candidate -> approved 的硬门槛，增加 lifecycle / TTL / demotion / archive、conflict resolution、approve / reject / rollback 路径，保证错误晋升可撤销。

---

## Core Principles

1. **Hard Gate for Promotion** - candidate -> approved 需要硬门槛
2. **Lifecycle Management** - 记忆有完整的生命周期
3. **TTL & Expiration** - 记忆有时效性
4. **Demotion & Archive** - 记忆可降级或归档
5. **Conflict Resolution** - 处理记忆冲突
6. **Rollback Capability** - 错误晋升可撤销

---

## Deliverables

| File | Description |
|------|-------------|
| core/memory/memory_promotion.py | 晋升管理器 |
| core/memory/memory_lifecycle.py | 生命周期管理 |
| core/memory/memory_conflict.py | 冲突解决 |
| docs/memory/PROMOTION_POLICY.md | 晋升策略文档 |
| docs/memory/LIFECYCLE_POLICY.md | 生命周期策略文档 |
| tests/memory/test_memory_promotion.py | 晋升测试 |
| tests/memory/test_memory_lifecycle.py | 生命周期测试 |
| tests/memory/test_memory_conflict.py | 冲突测试 |

---

## Promotion Flow

```
Candidate → Review → Approve/Reject → Promote → Rollback (if needed)
                                                    ↓
                                              Demote/Archive
```

---

## Promotion Criteria

### Hard Gates

| Gate | Requirement |
|------|-------------|
| review_required | 必须经过审核 |
| min_confidence | 置信度 ≥ 0.7 |
| min_importance | 重要性 ≥ 0.5 |
| no_conflicts | 无严重冲突 |
| source_verified | 来源已验证 |

---

## Lifecycle States

| State | Description | TTL |
|-------|-------------|-----|
| active | 活跃使用 | 90 days |
| deprecated | 已弃用 | 30 days |
| archived | 已归档 | 无限 |
| deleted | 已删除 | - |

---

## Lifecycle Transitions

```
active → deprecated (demotion)
active → archived (archive)
deprecated → active (restore)
deprecated → archived (archive)
archived → active (restore, rare)
```

---

## Conflict Types

| Type | Description | Resolution |
|------|-------------|------------|
| contradiction | 内容矛盾 | 标记冲突，需人工裁定 |
| overlap | 内容重叠 | 合并或保留较新的 |
| supersession | 新记录取代旧记录 | 标记被取代 |

---

## Rollback

错误晋升可撤销：
- 记录晋升历史
- 支持回滚到晋升前状态
- 保留回滚记录

---

## Test Requirements

### Promotion Tests
- test_promotion_with_all_gates
- test_promotion_missing_gate
- test_promotion_conflict_blocked
- test_rollback_basic
- test_rollback_with_dependencies

### Lifecycle Tests
- test_lifecycle_transition
- test_ttl_expiration
- test_demotion
- test_archive
- test_restore

### Conflict Tests
- test_conflict_detection
- test_conflict_resolution_auto
- test_conflict_resolution_manual

---

## Acceptance Criteria

1. 所有测试通过
2. 硬门槛生效
3. 生命周期完整
4. 冲突可检测和解决
5. 回滚可用

---

## Constraints

- 不接 OpenClaw 主流程
- 不进入 M5b fully-on
- 独立分支/提交/测试/验收
- 无 process debt

---

**Updated**: 2026-03-16T00:12:00Z
