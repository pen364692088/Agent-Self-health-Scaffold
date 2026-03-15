# Static Restore Validation

**Date**: 2026-03-14 22:22

---

## Phase 4: Static Validation

### 1. File Structure Check

```bash
find core -maxdepth 3 | sort
```

**Result**:
```
core/
core/canonical_adapter.py
core/materialized_state_v0.py
core/prompt_pilot_runner.py
core/prompt_preview.py
core/reconciler
core/reconciler/__init__.py
core/reconciler/reconciler.py
core/recovery_preview.py
core/state_materializer.py
core/task_ledger.py
```

✅ All core files present

---

### 2. OpenViking Structure Check

```bash
find openviking -maxdepth 3 | sort
```

**Result**:
```
openviking/
openviking/__init__.py
openviking/chunking
openviking/chunking/__init__.py
openviking/chunking/deterministic_chunker.py
openviking/ingest
openviking/ingest/__init__.py
openviking/ingest/embedding_audit.py
openviking/ingest/index_manifest.py
openviking/ingest/metrics.py
openviking/ops
openviking/ops/__init__.py
openviking/ops/alerting.py
openviking/policy
openviking/policy/__init__.py
openviking/policy/embedding_policy.py
openviking/tokenization
openviking/tokenization/__init__.py
openviking/tokenization/token_counter.py
```

✅ All openviking files present

---

### 3. Runtime Structure Check

```bash
find runtime -maxdepth 3 | sort
```

**Result**:
```
runtime/
runtime/job_orchestrator
runtime/job_orchestrator/job_orchestrator.py
runtime/recovery-orchestrator
runtime/recovery-orchestrator/recovery_apply.py
runtime/recovery-orchestrator/recovery_orchestrator.py
runtime/recovery-orchestrator/recovery_scan.py
runtime/restart_executor
runtime/restart_executor/restart_executor.py
runtime/transcript_rebuilder
runtime/transcript_rebuilder/transcript_rebuilder.py
```

✅ All runtime files present

---

### 4. Import Reference Check

Search for references to restored modules:

```bash
grep -r "from core.task_ledger\|import core.task_ledger" tests/ --include="*.py" | head -5
```

**Result**: ✅ Found in tests/ledger/test_task_ledger.py

```bash
grep -r "from core.state_materializer\|import core.state_materializer" tests/ --include="*.py" | head -5
```

**Result**: ✅ Found in tests/ledger/test_state_materializer.py

```bash
grep -r "from core.reconciler\|import core.reconciler" tests/ --include="*.py" | head -5
```

**Result**: ✅ Found in tests/reconciler/test_reconciler.py

```bash
grep -r "from openviking\|import openviking" tests/ --include="*.py" | head -5
```

**Result**: ✅ Found in multiple test files

---

### 5. No Dangling References

Check for any remaining import errors:

```bash
python3 -c "from core.task_ledger import TaskLedger; print('✅ task_ledger imports OK')"
python3 -c "from core.state_materializer import StateMaterializer; print('✅ state_materializer imports OK')"
python3 -c "from core.reconciler.reconciler import Reconciler; print('✅ reconciler imports OK')"
python3 -c "import openviking; print('✅ openviking imports OK')"
```

**Result**: All imports successful

---

## Summary

| Check | Status |
|-------|--------|
| core/ files present | ✅ |
| openviking/ files present | ✅ |
| runtime/ files present | ✅ |
| Test references found | ✅ |
| No dangling imports | ✅ |

**Static validation**: ✅ PASSED

---

*Generated: 2026-03-14 22:22*
