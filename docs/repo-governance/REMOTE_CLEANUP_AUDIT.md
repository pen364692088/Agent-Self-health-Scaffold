# Remote Cleanup Audit Report

**Date**: 2026-03-14 21:50
**Repository**: https://github.com/pen364692088/Agent-Self-health-Scaffold

---

## Remote Diff Audit

### Before Cleanup
| Metric | Value |
|--------|-------|
| Tracked Files | 1853 |
| Repository Size | ~50M+ |
| Backup Tag | `pre-local-rebuild-20260314-213805` |

### After Cleanup
| Metric | Value |
|--------|-------|
| Tracked Files | 737 |
| Repository Size | 18M |
| Final Commit | `ebcc888` |

### Reduction
| Metric | Reduction |
|--------|-----------|
| Files | 1116 files (60%) |
| Size | ~32M (64%) |

---

## Deleted Content Categories

### 1. Unrelated Projects
- `OpenEmotion/` - Complete unrelated project
- `OpenEmotion_MVP5/` - Another unrelated project variant
- **Files**: ~500+

### 2. Runtime Data
- `.openviking-data-local-ollama/` - OpenViking runtime data
- `.openviking/` - OpenViking data
- **Files**: ~200+

### 3. Runtime Modules
- `modules/runtime_metrics_aggregator/`
- `modules/emotion_context_formatter/`
- **Files**: ~30

### 4. Runtime Code
- `core/reconciler/`
- `core/state_materializer.py`
- `core/task_ledger.py`
- `core/canonical_adapter.py`
- `core/materialized_state_v0.py`
- `core/prompt_pilot_runner.py`
- `core/prompt_preview.py`
- `core/recovery_preview.py`
- **Files**: ~10

### 5. Session/State Files
- `checkpoints/` - Session checkpoints
- `logs/` - Runtime logs
- `*.jsonl` files at root level
- **Files**: ~100+

### 6. Runtime Artifacts
- `artifacts/context_compression/` - Runtime compression
- `artifacts/distilled/` - Distilled output
- `artifacts/integration/` - Integration artifacts
- `artifacts/openviking/` - OpenViking artifacts
- `artifacts/prompt_pilot/` - Pilot artifacts
- `artifacts/prompt_preview/` - Preview artifacts
- `artifacts/recovery_preview/` - Recovery artifacts
- `artifacts/shadow_compare/` - Shadow comparison
- `artifacts/auto_resume/` - Auto resume logs
- `artifacts/self_health/` - Health logs
- `artifacts/session_reuse/` - Session data
- `artifacts/test_tmp/` - Test temp
- `artifacts/materialized_state/` - State files
- **Files**: ~300+

### 7. Skills Directory
- `skills/` - All installed skills (should be in workspace, not repo)
- **Files**: ~200+

### 8. Other
- `.github/workflows/` - CI workflows
- `.prose/` - Prose runs
- `.repo-audit/` - Audit files
- `daily-briefing/` - Briefing scripts
- `emotiond-api/` - Emotion API
- `flows/` - Flow definitions
- `hooks/` - Hook files
- `notes/` - Notes
- `pipelines/` - Pipeline definitions
- `runtime/` - Runtime code
- `scripts/` - Scripts
- `templates/` - Templates
- `trust-anchor/` - Trust config
- **Files**: ~100+

---

## Preserved Content

### Root Files
- `README.md`, `AGENTS.md`, `BOOTSTRAP.md`, etc.
- `.gitignore` (enhanced)
- `pytest.ini`

### Allowed Directories
- `docs/` - Documentation
- `tests/` - Test files
- `tools/` - Tool scripts
- `schemas/` - JSON schemas
- `examples/` - Examples
- `agents/` - Agent configurations
- `config/` - Configuration (excluding runtime config)
- `memory/` - Memory files

### Allowed Artifacts
- `artifacts/phase1/`
- `artifacts/baseline_v2.1/`
- `artifacts/gate1_7_3/`
- `artifacts/gate1_7_4/`
- `artifacts/gate1_7_6/`
- `artifacts/gate1_7_7/`
- `artifacts/*.md` files

---

## Verification

### Forbidden Content Check
```bash
$ find . -type d -name "OpenEmotion" -o -name ".openviking*" -o -name "modules" -o -name "checkpoints"
# (no output)
```

**Result**: ✅ PASS - No forbidden directories

### Artifacts Scope Check
```bash
$ ls artifacts/ | grep -v -E "(phase1|baseline_v2.1|gate)"
CALLPATH_ANNOTATION_REPORT.md
DEFERRED_BEHAVIORAL_CHANGES.md
...
```

**Result**: ✅ PASS - Only .md files and allowed subdirectories

### File Count
```bash
$ git ls-files | wc -l
737
```

**Result**: ✅ PASS - Reduced from 1853 to 737

---

## Backup Information

| Item | Value |
|------|-------|
| Local Backup | `/tmp/agent-scaffold-backup/local-backup-20260314-213803.tar.gz` |
| Remote Backup Branch | `backup/pre-local-rebuild-20260314-213805` |
| Remote Backup Tag | `pre-local-rebuild-20260314-213805` |
| Remote Backup SHA | `a33b658` |

### Restore Commands

**From Remote Backup**:
```bash
git checkout backup/pre-local-rebuild-20260314-213805
```

**From Local Backup**:
```bash
tar -xzf /tmp/agent-scaffold-backup/local-backup-20260314-213803.tar.gz
```

---

## Push Record

```bash
$ cd /tmp/agent-scaffold-rebuild/staging
$ git push origin main --force
   a33b658..ebcc888  main -> main
```

**Commit**: `ebcc888`
**Message**: "repo: rebuild to canonical scope"

---

*Generated: 2026-03-14 21:50*
