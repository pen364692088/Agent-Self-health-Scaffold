# Materialized State v0 - Scope and Boundaries

**Version**: v0
**Status**: Feature Frozen
**Created**: 2026-03-14
**Phase**: Phase 2.3 COMPLETE

---

## Overview

`core/materialized_state_v0.py` 提供从 SESSION-STATE.md 和 working-buffer.md 物化状态的独立模块。设计为可复用组件，支持 CLI 工具、prompt assembly、recovery flows 和测试。

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

## Explicitly NOT in v0

以下功能明确不在 v0 范围内：

1. **不接 prompt-assemble** - 独立模块，不与 prompt 组装器集成
2. **不接 recovery** - 不与 recovery 流程集成
3. **不接 canonical 主链** - CanonicalAdapter 是 stub，不连接真实 ledger/run truth
4. **不接 handoff/capsule/summary/distill** - 不读取这些文件作为输入
5. **不新增第二套 live state** - 只读，不写回
6. **不写回 continuity 源文件** - Read-only boundary

---

## Canonical-Ready Adapter Seam

预留了薄层接口供未来扩展：

```python
class CanonicalAdapter:
    """Stub adapter for future canonical ledger integration."""
    
    def connect(self) -> bool:
        """Connect to canonical ledger (stub in v0)."""
        return False
    
    def merge_with_canonical(self, state: MaterializedState) -> MaterializedState:
        """Merge materialized state with canonical state (stub in v0)."""
        return state
```

未来实现时：
- `connect()` 连接到真实 ledger
- `merge_with_canonical()` 合并 canonical state 和 materialized state
- 保持 conflict resolution 逻辑不变

---

## CLI Tool

`tools/materialize-state` 提供 CLI 接口：

```bash
# 基本用法
materialize-state --json

# Schema 验证
materialize-state --json --schema-validate

# 健康检查
materialize-state --health

# 查看追踪字段
materialize-state --fields
```

---

## Contract Tests

`tests/core/test_materialized_state_v0.py` 包含：
- Schema compliance tests
- Field extraction tests
- Conflict resolution tests
- Materialization tests
- Read-only boundary tests
- CLI compatibility tests
- Normalization tests
- Integration tests

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
| `core/materialized_state_v0.py` | 核心模块 (NEW) |
| `schemas/materialized_state.v0.schema.json` | JSON Schema (NEW) |
| `tests/core/test_materialized_state_v0.py` | Contract tests (NEW) |
| `tests/core/fixtures/materialized_state_v0_golden_fixtures.json` | Golden fixtures (NEW) |
| `tools/materialize-state` | CLI wrapper (NEW) |

---

## Compatibility

- 现有 `core/state_materializer.py` (RunStateMaterializer) 保持不变
- 现有 `tests/ledger/test_state_materializer.py` 全部通过
- CLI 输出格式保持向后兼容

---

## Next Steps (Future Phases)

1. **Phase 2.4**: Connect CanonicalAdapter to real ledger
2. **Phase 2.5**: Integrate with prompt-assemble
3. **Phase 2.6**: Integrate with recovery flows
4. **Phase 2.7**: Add handoff/capsule input sources

这些步骤在 v0 中明确不做。
