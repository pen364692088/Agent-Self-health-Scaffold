# Materialized State v0 - Scope and Boundaries

**Version**: v0
**Status**: Feature Frozen
**Created**: 2026-03-14
**Updated**: 2026-03-14
**Phase**: Phase 2.4 COMPLETE (Shadow Mode)

---

## Overview

`core/materialized_state_v0.py` 提供从 SESSION-STATE.md 和 working-buffer.md 物化状态的独立模块。设计为可复用组件，支持 CLI 工具、prompt assembly、recovery flows 和测试。

Phase 2.4 新增 `core/canonical_adapter.py`，提供只读 shadow 接入 canonical sources。

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

生成：
- JSON report: `artifacts/shadow_compare/shadow_compare_*.json`
- Markdown summary: `artifacts/shadow_compare/shadow_compare_*.md`

### Shadow Mode 约束
- **只读**: 不修改任何 canonical source
- **Shadow only**: 不替代 bridge state
- **Provenance preserved**: 所有冲突保留来源信息
- **No silent override**: 不静默覆盖任何值

### Compare Report 内容
- **Coverage**: 哪些字段由哪个源覆盖
- **Conflicts**: 值不匹配的字段
- **Fallbacks**: Canonical 有但 bridge 没有的值
- **Warnings**: 缺失字段和冲突警告
- **Provenance**: 每个值的完整来源链

---

## Explicitly NOT in v0

以下功能明确不在 v0 范围内：

1. **不接 prompt-assemble** - 独立模块，不与 prompt 组装器集成
2. **不接 recovery** - 不与 recovery 流程集成
3. **不接 canonical 主链** - CanonicalAdapter 是 shadow only，不替代 bridge state
4. **不接 handoff/capsule/summary/distill** - 不读取这些文件作为输入
5. **不新增第二套 live state** - 只读，不写回
6. **不写回 continuity 源文件** - Read-only boundary
7. **不让 canonical shadow 替代 bridge** - Shadow compare 仅用于 observability

---

## CLI Tool

`tools/materialize-state` 提供 CLI 接口：

```bash
# 基本用法
materialize-state --json

# Shadow compare with canonical
materialize-state --shadow-compare

# 指定输出目录
materialize-state --shadow-compare --output-dir ./reports

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
`tests/core/test_materialized_state_v0.py` (30 tests):
- Schema compliance tests
- Field extraction tests
- Conflict resolution tests
- Materialization tests
- Read-only boundary tests
- CLI compatibility tests
- Normalization tests
- Integration tests

### CanonicalAdapter
`tests/core/test_canonical_adapter.py` (26 tests):
- Read-only boundary tests
- Connection tests
- Field extraction tests
- Shadow comparison tests
- Coverage reporting tests
- Conflict detection tests
- Integration tests
- Merge stub tests

Golden fixtures: `tests/core/fixtures/materialized_state_v0_golden_fixtures.json`

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

不触发 uncertainty 的字段缺失：
- `phase`, `branch`, `blocker`, `next_step`, `next_actions`

---

## Files Created/Modified

| File | Description |
|------|-------------|
| `core/materialized_state_v0.py` | 核心模块 (Phase 2.3) |
| `core/canonical_adapter.py` | Canonical adapter shadow mode (Phase 2.4) |
| `schemas/materialized_state.v0.schema.json` | JSON Schema |
| `tests/core/test_materialized_state_v0.py` | Contract tests (30) |
| `tests/core/test_canonical_adapter.py` | Contract tests (26) |
| `tests/core/fixtures/*_golden_fixtures.json` | Golden fixtures |
| `tools/materialize-state` | CLI wrapper |
| `docs/MATERIALIZED_STATE_V0_SCOPE.md` | 本文档 |

---

## Compatibility

- 现有 `core/state_materializer.py` (RunStateMaterializer) 保持不变
- 现有 `tests/ledger/test_state_materializer.py` 全部通过
- CLI 输出格式保持向后兼容
- Shadow compare 不影响主链路

---

## Next Steps (Future Phases)

1. **Phase 2.5**: Integrate with prompt-assemble
2. **Phase 2.6**: Integrate with recovery flows
3. **Phase 2.7**: Add handoff/capsule input sources
4. **Phase 2.8**: Merge canonical into bridge state (with explicit conflict resolution)

这些步骤在 v0 中明确不做。
