# Restore Candidates Analysis

**Date**: 2026-03-14 22:20
**Current Commit**: `a367c2b` (with partial restore)
**Backup Point**: `a33b658`
**Original Backup**: `pre-cleanup-20260314-2121`

---

## Phase 1: Diff Analysis

### Files in backup but not in current (deleted during cleanup)

```bash
git diff --name-status a367c2b a33b658 | grep "^D" | wc -l
```

**Result**: 0 files (already restored)

### Files already restored

| Path | Status | Category |
|------|--------|----------|
| `core/task_ledger.py` | ✅ Restored | Must Restore |
| `core/state_materializer.py` | ✅ Restored | Must Restore |
| `core/reconciler/` | ✅ Restored | Must Restore |
| `core/canonical_adapter.py` | ✅ Restored | Must Restore |
| `core/materialized_state_v0.py` | ✅ Restored | Must Restore |
| `core/prompt_pilot_runner.py` | ✅ Restored | Must Restore |
| `core/prompt_preview.py` | ✅ Restored | Must Restore |
| `core/recovery_preview.py` | ✅ Restored | Must Restore |
| `openviking/` | ✅ Restored | Must Restore |
| `runtime/` | ✅ Restored | Must Restore |

---

## Classification

### 1. Must Restore (Already Done)

These are confirmed Scaffold core components:

- `core/task_ledger.py` - Task ledger (P0 core per README)
- `core/state_materializer.py` - State materializer (P0 core per README)
- `core/reconciler/` - Reconciler for recovery decisions
- `core/canonical_adapter.py` - Canonical adapter
- `core/materialized_state_v0.py` - Materialized state v0
- `core/prompt_pilot_runner.py` - Prompt pilot runner
- `core/prompt_preview.py` - Prompt preview
- `core/recovery_preview.py` - Recovery preview
- `openviking/` - OpenViking local tooling extensions
- `runtime/` - Runtime components (job_orchestrator, recovery-orchestrator, restart_executor, transcript_rebuilder)

### 2. Correctly Deleted (No Restore)

These were correctly identified as pollution:

- `OpenEmotion/` - Unrelated project
- `OpenEmotion_MVP5/` - Unrelated project variant
- `.openviking-data-local-ollama/` - Runtime data
- `checkpoints/` - Session checkpoints
- `logs/` - Runtime logs
- `skills/` - Installed skills (should be in workspace)
- `artifacts/context_compression/` - Runtime artifacts
- `artifacts/distilled/` - Runtime artifacts
- `artifacts/integration/` - Runtime artifacts
- `artifacts/openviking/` - Runtime artifacts
- `artifacts/prompt_pilot/` - Runtime artifacts
- `artifacts/prompt_preview/` - Runtime artifacts
- `artifacts/recovery_preview/` - Runtime artifacts
- `artifacts/shadow_compare/` - Runtime artifacts
- `artifacts/auto_resume/` - Runtime artifacts
- `artifacts/self_health/` - Runtime artifacts
- `artifacts/session_reuse/` - Runtime artifacts
- `artifacts/test_tmp/` - Runtime artifacts
- `artifacts/materialized_state/` - Runtime artifacts

### 3. Already Present (No Action)

- `docs/` - Documentation
- `tests/` - Tests
- `tools/` - Tool scripts
- `schemas/` - Schemas
- `examples/` - Examples
- `agents/` - Agent configurations
- `config/` - Configuration
- `memory/` - Memory files
- `artifacts/phase1/` - Phase 1 artifacts
- `artifacts/baseline_v2.1/` - Baseline artifacts
- `artifacts/gate*/` - Gate artifacts

---

## Summary

| Category | Count | Status |
|----------|-------|--------|
| Must Restore | 10 paths | ✅ All restored |
| Correctly Deleted | 20+ paths | ✅ Stay deleted |
| Already Present | 8+ dirs | ✅ No action |

**Conclusion**: Core code has been restored. Ready for validation.

---

*Generated: 2026-03-14 22:20*
