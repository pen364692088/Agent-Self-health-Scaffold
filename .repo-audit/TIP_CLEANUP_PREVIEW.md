# TIP_CLEANUP_PREVIEW.md

**Generated**: 2026-03-13
**Repository**: Agent-Self-health-Scaffold

## Summary

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Total tracked files | 3,871 | 2,194 | -1,677 (-43%) |
| Artifacts files | 2,013 | ~500 | ~-1,500 |
| Logs files | 13 | 0 | -13 |
| Reports files | 77 | 0 | -77 |
| State files | 11 | 0 | -11 |

---

## Files Removed from Git Tracking

### Will disappear from remote after push:
| Category | Count | Example Paths |
|----------|-------|---------------|
| Logs | 13 | `logs/callback-worker.log`, `logs/policy_violations.jsonl` |
| Reports | 77 | `reports/tool_doctor/*.json`, `reports/smart_stable/*.json` |
| Processed events | 59 | `events/processed/*.json` |
| State | 11 | `state/active_state.json`, `state/wal/*.jsonl` |
| Mailbox out | 15 | `mailbox/out/*.md` |
| Session archives | 2 | `session-archives/*.md` |
| Memory runtime | 10+ | `memory/sweeper_stats.json`, `memory/events.log` |
| Artifacts runtime | ~1,500 | `artifacts/self_health/state/*`, `artifacts/openviking/archive/*` |
| PID/Lock files | 2 | `.callback-worker.pid`, `.workflow.lock` |

---

## Files Kept Locally (Not Affected)

All local files remain on disk. They are simply no longer tracked by Git.

```
✅ logs/               → Still exists locally, ignored by Git
✅ reports/            → Still exists locally, ignored by Git
✅ events/processed/   → Still exists locally, ignored by Git
✅ state/              → Still exists locally, ignored by Git
✅ artifacts/          → Still exists locally (partial tracking removed)
✅ memory/*.json       → Still exists locally, ignored by Git
✅ cerebras_config.json → Still exists locally, ignored by Git
```

---

## Files Still Tracked

| Category | Count | Purpose |
|----------|-------|---------|
| Core source (core/, openviking/, runtime/) | ~100 | Application code |
| Tools | ~300 | CLI tools and scripts |
| Tests | ~50 | Test suites |
| Skills | ~200 | Skill definitions |
| Documentation | ~150 | docs/, *.md files |
| Config templates | ~20 | Non-sensitive configs |
| Artifacts docs | ~200 | Implementation summaries, docs |
| Schemas | ~30 | JSON schemas |
| Hooks | ~5 | Git hooks |
| Other | ~1,100 | Mixed (mostly docs) |

---

## Risk Assessment

### Low Risk ✅
- All removed files are runtime-generated
- Can be regenerated on any machine
- No source code affected
- No documentation removed

### Mitigation
- Backup exists at `/home/moonlight/Project/Github/MyProject/Agent-Self-health-Scaffold-backup-20260313-014718/`
- Git bundle at `/home/moonlight/Project/Github/MyProject/Agent-Self-health-Scaffold-precleanup-20260313-014718.bundle`

---

## Commit Preview

```
Files changed: ~1,694
Files deleted from tracking: ~1,677
Files added: .gitignore (updated), cerebras_config.json.template

Commit message:
  chore(repo): untrack local runtime artifacts, harden ignore rules, remove exposed secret

  - Remove logs/, reports/, state/, events/processed/ from tracking
  - Remove artifacts runtime subdirs (state, incidents, probes, etc.)
  - Remove memory/*.json and memory/*.jsonl runtime caches
  - Remove cerebras_config.json (contained API key) from tracking
  - Add cerebras_config.json.template for reference
  - Update .gitignore with comprehensive rules
  - History rewritten to remove exposed API key
```

---

## Post-Push Actions Required

1. ⚠️ **Rotate Cerebras API Key** - Old key was exposed in history (now removed)
2. ✅ Verify remote shows clean state
3. ✅ Verify local files still exist
4. ✅ Run smoke tests to verify application works
