# Local Pollution Report

**Date**: 2026-03-14 21:40
**Repository**: /home/moonlight/Project/Github/MyProject/Agent-Self-health-Scaffold

---

## Summary

| Category | Files | Size |
|----------|-------|------|
| Unrelated Projects | ~500+ | 14M+ |
| Runtime Artifacts | ~600+ | 35M+ |
| Session Checkpoints | ~50+ | 28K |
| Runtime Code | ~20+ | 92K |
| Logs | ~100+ | 596K |
| **Total Pollution** | **~1270+** | **~50M+** |

---

## Category 1: Unrelated Projects

### OpenEmotion/
**Size**: 14M
**Status**: Complete unrelated project
**Action**: DELETE

```
OpenEmotion/
├── emotiond/          # Emotion daemon code
├── tests/             # Test files
├── artifacts/         # MVP11 artifacts
├── checkpoints/       # Session checkpoints
├── scripts/           # Scripts
├── integrations/      # OpenClaw integration
└── ...
```

### OpenEmotion_MVP5/
**Status**: Another unrelated project variant
**Action**: DELETE

---

## Category 2: Runtime Artifacts

### artifacts/ (Polluted Subdirectories)

| Subdirectory | Files | Status |
|--------------|-------|--------|
| `context_compression/` | ~100+ | Runtime compression - DELETE |
| `distilled/` | ~10 | Distilled output - DELETE |
| `integration/` | ~5 | Integration artifacts - DELETE |
| `openviking/` | ~50 | OpenViking artifacts - DELETE |
| `prompt_pilot/` | ~5 | Pilot artifacts - DELETE |
| `prompt_preview/` | ~10 | Preview artifacts - DELETE |
| `recovery_preview/` | ~10 | Recovery artifacts - DELETE |
| `shadow_compare/` | ~10 | Shadow artifacts - DELETE |
| `auto_resume/` | ~20 | Resume logs - DELETE |
| `self_health/` | ~50 | Health logs - DELETE |
| `session_reuse/` | ~10 | Session data - DELETE |
| `test_tmp/` | ~20 | Test temp - DELETE |
| `materialized_state/` | ~10 | State files - DELETE |

### Allowed Artifacts (KEEP)
- `artifacts/phase1/` - Phase 1 design artifacts
- `artifacts/baseline_v2.1/` - Baseline design
- `artifacts/gate*/` - Gate design artifacts
- Root level `.md` files in artifacts/

---

## Category 3: Session/State Files

### checkpoints/
**Size**: 28K
**Status**: Session checkpoints
**Action**: DELETE

### Other Session Files
- `memory/TOMBSTONES.jsonl` - DELETE
- `memory/sweeper_config.json` - DELETE

---

## Category 4: Runtime Code

### core/ (Runtime Implementation)
**Size**: 92K
**Status**: Runtime code (belongs to EgoCore)
**Action**: DELETE

**Files**:
```
core/reconciler/__init__.py
core/reconciler/reconciler.py
core/state_materializer.py
core/task_ledger.py
```

**Note**: These are runtime implementation files, not design documents.

---

## Category 5: Logs

### logs/
**Size**: 596K
**Status**: Runtime log files
**Action**: DELETE

---

## Category 6: Untracked Files

Current `git status` shows these untracked files:

```
OpenEmotion/                  # Unrelated project
OpenEmotion_MVP5/            # Unrelated project variant
antfarm-dashboard.log        # Log file
artifacts/distilled/         # Runtime artifacts
artifacts/materialized_state/# State files
artifacts/openviking/        # OpenViking artifacts
artifacts/self_health/       # Health logs
artifacts/session_reuse/     # Session data
artifacts/test_tmp/          # Test temp
checkpoints/                 # Session checkpoints
core/                        # Runtime code
memory/TOMBSTONES.jsonl      # Tombstones
memory/sweeper_config.json   # Config
```

---

## Root Cause Analysis

### Why This Happened

1. **No clear repository boundary definition**
   - Scaffold repo was treated as "dump everything here"
   - No whitelist/blacklist enforcement

2. **OpenClaw workspace confusion**
   - `~/.openclaw/workspace/` points to Agent-Self-health-Scaffold
   - Runtime sessions created files in repo directory
   - Files from other projects (OpenEmotion) were copied

3. **No .gitignore enforcement**
   - Logs, checkpoints, artifacts not properly ignored
   - Runtime data committed by accident

4. **Mixed concerns**
   - Design specs mixed with runtime implementation
   - Scaffold design mixed with EgoCore runtime code

---

## Cleanup Strategy

### Rebuild Approach (Not Incremental Delete)

1. Create clean staging directory OUTSIDE repo
2. Copy ONLY whitelisted content
3. Validate clean result
4. Replace working tree with clean version
5. Commit and push

### Why Rebuild vs Delete

- **Rebuild**: Controlled, verifiable, atomic
- **Delete**: Risk of missing files, partial cleanup, hard to verify

---

## Whitelist for Rebuild

From CANONICAL_SCOPE.md:

```
Allowed:
- README.md, AGENTS.md, BOOTSTRAP.md, etc.
- docs/ (all .md files)
- tests/ (test files)
- tools/ (scripts)
- schemas/
- examples/
- agents/
- config/ (except prompt_pilot.json)
- artifacts/phase1/
- artifacts/baseline_v2.1/
- artifacts/gate*/

Forbidden:
- OpenEmotion/
- OpenEmotion_MVP5/
- .openviking*/
- modules/
- core/ (runtime files)
- checkpoints/
- logs/
- artifacts/* (except allowed)
- *.jsonl at root
- All untracked runtime files
```

---

## Next Steps

1. Create staging directory
2. Initialize clean git repo
3. Copy whitelisted content
4. Generate REBUILT_TREE.txt
5. Validate against CANONICAL_SCOPE.md
6. Replace working tree
7. Force-with-lease push

---

*Generated: 2026-03-14 21:40*
