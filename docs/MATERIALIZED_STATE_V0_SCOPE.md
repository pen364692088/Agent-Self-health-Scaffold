# Materialized State v0 - Scope and Boundaries

**Version**: v0
**Status**: Feature Frozen
**Created**: 2026-03-14
**Updated**: 2026-03-14
**Phase**: Phase 2.6 COMPLETE (Shadow Mode)

---

## Overview

`core/materialized_state_v0.py` 提供从 SESSION-STATE.md 和 working-buffer.md 物化状态的独立模块。设计为可复用组件，支持 CLI 工具、prompt assembly、recovery flows 和测试。

Phase 2.4 新增 `core/canonical_adapter.py`，提供只读 shadow 接入 canonical sources。

Phase 2.5 新增 `core/prompt_preview.py`，提供 shadow prompt preview 和 dual-run comparison。

Phase 2.6 新增 `core/recovery_preview.py`，提供 shadow recovery preview 和与主 recovery flow 的对比。

---

## v0 Scope (FROZEN)

### 输入
- `SESSION-STATE.md` (根级)
- `working-buffer.md` (根级)
- Git branch (repo evidence)

### 输出
- `MaterializedState` dataclass
- JSON-serializable dictionary

### 字段
- `objective` - 当前任务目标
- `phase` - 当前阶段
- `branch` - 当前分支
- `blocker` - 当前阻塞项
- `next_step` - 下一步动作
- `next_actions` - 动作列表

### 特性
- Schema validation (`schemas/materialized_state.v0.schema.json`)
- Field-level conflict resolution with priority
- Uncertainty flag for missing critical fields
- Canonical-ready adapter seam (stub)

---

## Phase 2.4: CanonicalAdapter Shadow Mode

### 新增模块
`core/canonical_adapter.py` - 只读 shadow 接入 canonical sources。

### Canonical Sources
- `TASK_LEDGER.jsonl` - 任务事件日志
- `state/durable_execution/RUN_STATE.json` - Durable run state
- `artifacts/run_ledger/*.jsonl` - Run event streams

### Shadow Compare 功能
```bash
materialize-state --shadow-compare
```

### Shadow Mode 约束
- **只读**: 不修改任何 canonical source
- **Shadow only**: 不替代 bridge state
- **Provenance preserved**: 所有冲突保留来源信息
- **No silent override**: 不静默覆盖任何值

---

## Phase 2.5: Prompt Preview Shadow Mode

### 新增模块
`core/prompt_preview.py` - MaterializedState-driven prompt preview。

### Prompt Preview 功能
```bash
materialize-state --prompt-preview
materialize-state --prompt-preview --compare-with-main
```

### Prompt Preview 约束
- **Shadow mode**: 不替代 main prompt chain
- **No authority**: MaterializedState 不是 prompt authority
- **Conflicts NOT included**: 冲突字段不静默进入 prompt
- **Explicit warnings**: Missing blocker 触发显式警告

### Prompt Layers
1. **Resident Layer**: objective, phase, branch, blocker
2. **Action Layer**: next_step, next_actions
3. **Metadata Layer**: sources_checked, field_sources_summary

---

## Phase 2.6: Recovery Preview Shadow Mode

### 新增模块
`core/recovery_preview.py` - MaterializedState + CanonicalAdapter recovery preview。

### Recovery Preview 功能
```bash
materialize-state --recovery-preview
materialize-state --recovery-preview --compare-with-main
```

生成：
- JSON preview: `artifacts/recovery_preview/recovery_preview_*.json`
- Markdown summary: `artifacts/recovery_preview/recovery_preview_*.md`
- Recovery compare (if requested): `artifacts/recovery_preview/recovery_compare_*.json`

### Recovery Preview 约束
- **Shadow mode**: 不替代 main recovery chain
- **No authority**: MaterializedState 不是 recovery authority
- **No real recovery**: 不触发真实恢复动作
- **Conflicts tracked, not used**: 冲突字段追踪但不静默使用
- **Explicit warnings**: Missing blocker 触发显式警告

### Recovery Fields
- `objective` - 当前任务目标
- `phase` - 当前阶段
- `next_step` - 下一步动作
- `blocker` - 当前阻塞项

### Recovery Comparison
比较 main recovery 与 shadow preview：
- Field differences (objective, phase, next_step, blocker)
- Phase comparison
- Next step comparison
- Blocker comparison
- Warnings comparison
- Provenance comparison
- Recommendations

---

## Explicitly NOT in v0

以下功能明确不在 v0 范围内：

1. **不接 recovery 主链** - RecoveryPreview 是 shadow only，不替代 main recovery chain
2. **不接 canonical 主链** - CanonicalAdapter 是 shadow only，不替代 bridge state
3. **不接 handoff/capsule/summary/distill** - 不读取这些文件作为输入
4. **不新增第二套 live state** - 只读，不写回
5. **不写回 continuity 源文件** - Read-only boundary
6. **不让 canonical shadow 替代 bridge** - Shadow compare 仅用于 observability
7. **不让 shadow preview 替代 main chains** - 仅用于 comparison
8. **不静默包含冲突字段** - 冲突必须明确标记
9. **不触发真实恢复动作** - Recovery preview 是 read-only

---

## CLI Tool

`tools/materialize-state` 提供 CLI 接口：

```bash
# 基本用法
materialize-state --json

# Shadow compare with canonical
materialize-state --shadow-compare

# Prompt preview (shadow mode)
materialize-state --prompt-preview
materialize-state --prompt-preview --compare-with-main

# Recovery preview (shadow mode)
materialize-state --recovery-preview
materialize-state --recovery-preview --compare-with-main

# Schema 验证
materialize-state --json --schema-validate

# 健康检查
materialize-state --health

# 查看追踪字段
materialize-state --fields
```

---

## Contract Tests

### MaterializedState v0
`tests/core/test_materialized_state_v0.py` (30 tests)

### CanonicalAdapter
`tests/core/test_canonical_adapter.py` (26 tests)

### PromptPreview
`tests/core/test_prompt_preview.py` (31 tests)

### RecoveryPreview
`tests/core/test_recovery_preview.py` (29 tests)

**Total: 116 tests**

---

## Source Priority

冲突解决优先级（高到低）：

| Source | Priority |
|--------|----------|
| repo_evidence | 100 |
| wal_entry | 90 |
| handoff_md | 80 |
| session_state_md | 70 |
| working_buffer_md | 60 |

---

## Uncertainty Flag

`uncertainty_flag = True` 当：
- `objective` 字段缺失或为空

---

## Files Created/Modified

| File | Description |
|------|-------------|
| `core/materialized_state_v0.py` | 核心模块 (Phase 2.3) |
| `core/canonical_adapter.py` | Canonical adapter shadow mode (Phase 2.4) |
| `core/prompt_preview.py` | Prompt preview shadow mode (Phase 2.5) |
| `core/recovery_preview.py` | Recovery preview shadow mode (Phase 2.6) |
| `schemas/materialized_state.v0.schema.json` | JSON Schema |
| `tests/core/test_*.py` | Contract tests (116) |
| `tools/materialize-state` | CLI wrapper |
| `docs/MATERIALIZED_STATE_V0_SCOPE.md` | 本文档 |

---

## Next Steps (Future Phases)

1. **Phase 2.7**: Add handoff/capsule input sources
2. **Phase 2.8**: Merge canonical into bridge state (with explicit conflict resolution)
3. **Phase 3**: Task execution kernel

这些步骤在 v0 中明确不做。
