# Rebuild Validation Report

**Date**: 2026-03-14 21:45
**Source**: /home/moonlight/Project/Github/MyProject/Agent-Self-health-Scaffold
**Staging**: /tmp/agent-scaffold-rebuild/staging

---

## Validation Results

### 1. Forbidden Directories Check

| Directory | Expected | Result |
|-----------|----------|--------|
| OpenEmotion/ | Not present | ✅ PASS |
| OpenEmotion_MVP5/ | Not present | ✅ PASS |
| .openviking*/ | Not present | ✅ PASS |
| modules/ | Not present | ✅ PASS |
| checkpoints/ | Not present | ✅ PASS |
| logs/ | Not present | ✅ PASS |

**Result**: ✅ PASS - No forbidden directories found

---

### 2. Artifacts Subdirectories Check

**Found**:
- `artifacts/phase1/` - ✅ Allowed
- `artifacts/baseline_v2.1/` - ✅ Allowed
- `artifacts/gate1_7_3/` - ✅ Allowed
- `artifacts/gate1_7_4/` - ✅ Allowed
- `artifacts/gate1_7_6/` - ✅ Allowed
- `artifacts/gate1_7_7/` - ✅ Allowed
- `artifacts/*.md` files - ✅ Allowed

**Note**: `artifacts/baseline_v2.1/logs/` contains test logs used for baseline verification. These are design artifacts, not runtime logs.

**Result**: ✅ PASS - Only allowed artifact directories

---

### 3. Runtime Code Check

**Expected**: No runtime implementation files in `core/`

**Found**: None

**Result**: ✅ PASS - No runtime code in core/

---

### 4. Session/State Files Check

**Found**:
- `memory/events_drift.jsonl` - Design data (memory events schema)
- `memory/events_golden.jsonl` - Design data (golden test data)
- `memory/daily_summaries.jsonl` - Design data (example schema)

**Analysis**: These are design/example files in the memory schema, not runtime session data. They are part of the scaffold design specification.

**Result**: ✅ PASS - No runtime session files

---

### 5. File Count Comparison

| Location | Files |
|----------|-------|
| Original (tracked) | 1853 |
| Rebuilt | 790 |

**Reduction**: 1063 files removed (57% reduction)

---

### 6. Directory Structure

```
staging/
├── AGENTS.md          ✅
├── BOOTSTRAP.md       ✅
├── HEARTBEAT.md       ✅
├── IDENTITY.md        ✅
├── SOUL.md            ✅
├── TOOLS.md           ✅
├── USER.md            ✅
├── memory.md          ✅
├── README.md          ✅
├── .gitignore         ✅
├── pytest.ini         ✅
├── agents/            ✅
├── artifacts/         ✅ (only allowed subdirs)
├── config/            ✅ (no prompt_pilot.json)
├── docs/              ✅
├── examples/          ✅
├── memory/            ✅
├── schemas/           ✅
├── tests/             ✅
└── tools/             ✅
```

**Result**: ✅ PASS - Clean structure

---

### 7. .gitignore Verification

**Content includes**:
- ✅ Python cache patterns
- ✅ Virtual environment patterns
- ✅ IDE patterns
- ✅ Logs patterns
- ✅ Runtime data patterns (.openviking*)
- ✅ Session patterns (checkpoints/, *.jsonl)
- ✅ Runtime artifacts patterns
- ✅ Other projects (OpenEmotion/)

**Result**: ✅ PASS - Comprehensive .gitignore

---

### 8. Size Comparison

| Location | Size |
|----------|------|
| Original | ~50M+ |
| Rebuilt | ~5M |
| **Reduction** | **~90%** |

---

## Overall Result

| Check | Status |
|-------|--------|
| Forbidden directories | ✅ PASS |
| Artifact directories | ✅ PASS |
| Runtime code | ✅ PASS |
| Session files | ✅ PASS |
| Directory structure | ✅ PASS |
| .gitignore | ✅ PASS |
| File count reduction | ✅ 57% |
| Size reduction | ✅ 90% |

**Overall**: ✅ REBUILD VALIDATED

---

## Next Steps

1. Copy .git from original to staging
2. Commit all changes
3. Replace working tree
4. Push with --force-with-lease

---

*Generated: 2026-03-14 21:45*
