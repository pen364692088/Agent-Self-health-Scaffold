# Restore Decision Document

**Date**: 2026-03-14 22:21

---

## Decision Framework

Each candidate path evaluated against:
1. **Contract**: Listed in README/docs as Scaffold component?
2. **Reference**: Imported by tests/tools/main flow?
3. **Responsibility**: OpenClaw extension vs runtime temp data?

---

## Decisions

### 1. core/task_ledger.py
- **Restore**: ✅ YES
- **Basis**: README "P0 build order" #1 - task ledger
- **Reference**: tests/ledger/test_task_ledger.py imports it
- **Responsibility**: Core scaffold component

### 2. core/state_materializer.py
- **Restore**: ✅ YES
- **Basis**: README "P0 build order" #2 - state materializer
- **Reference**: tests/ledger/test_state_materializer.py imports it
- **Responsibility**: Core scaffold component

### 3. core/reconciler/
- **Restore**: ✅ YES
- **Basis**: Recovery orchestration component
- **Reference**: tests/reconciler/test_reconciler.py imports it
- **Responsibility**: Core scaffold component

### 4. core/canonical_adapter.py
- **Restore**: ✅ YES
- **Basis**: Canonical adapter for state management
- **Reference**: Part of core state management
- **Responsibility**: Core scaffold component

### 5. core/materialized_state_v0.py
- **Restore**: ✅ YES
- **Basis**: Materialized state implementation
- **Reference**: Related to state materializer
- **Responsibility**: Core scaffold component

### 6. core/prompt_pilot_runner.py
- **Restore**: ✅ YES
- **Basis**: Prompt pilot runner
- **Reference**: Part of pilot system
- **Responsibility**: Core scaffold component

### 7. core/prompt_preview.py
- **Restore**: ✅ YES
- **Basis**: Prompt preview functionality
- **Reference**: Part of preview system
- **Responsibility**: Core scaffold component

### 8. core/recovery_preview.py
- **Restore**: ✅ YES
- **Basis**: Recovery preview functionality
- **Reference**: Part of recovery system
- **Responsibility**: Core scaffold component

### 9. openviking/
- **Restore**: ✅ YES
- **Basis**: OpenViking local tooling extensions
- **Reference**: Imported by multiple tests
- **Responsibility**: OpenClaw extension (not temp data)

### 10. runtime/
- **Restore**: ✅ YES
- **Basis**: Runtime components (orchestrator, executor, rebuilder)
- **Reference**: tests/orchestration/, tests/recovery/, tests/restart/, tests/transcript/
- **Responsibility**: Core scaffold components per README

---

## Correctly Excluded (No Restore)

### OpenEmotion/
- **Restore**: ❌ NO
- **Basis**: Unrelated project, not in README
- **Reference**: No imports from Scaffold
- **Responsibility**: Separate project

### .openviking-data-local-ollama/
- **Restore**: ❌ NO
- **Basis**: Runtime data directory
- **Reference**: Not imported, just data
- **Responsibility**: Runtime temp data

### checkpoints/
- **Restore**: ❌ NO
- **Basis**: Session checkpoints
- **Reference**: Not core code
- **Responsibility**: Runtime session data

### logs/
- **Restore**: ❌ NO
- **Basis**: Log files
- **Reference**: Not core code
- **Responsibility**: Runtime logs

### skills/
- **Restore**: ❌ NO
- **Basis**: Installed skills
- **Reference**: Should be in workspace
- **Responsibility**: Not part of Scaffold source

### artifacts/* (except allowed)
- **Restore**: ❌ NO
- **Basis**: Runtime artifacts
- **Reference**: Not core code
- **Responsibility**: Runtime generated

---

## Summary

| Decision | Count |
|----------|-------|
| Restore | 10 paths |
| Exclude | 6+ categories |

**All restore decisions**: Based on README contract, test references, and OpenClaw extension responsibility.

---

*Generated: 2026-03-14 22:21*
