# Memory Rehydration Pack

**Generated**: 2026-03-10 06:03 CST
**Mode**: Lite (Essentials Only)

---

## 1. Long-Term Stable Preferences

| Preference | Value | Source |
|------------|-------|--------|
| Dark mode | Preferred | memory_recall |
| AUTOCAPTURE-PROOF-001 | Stored (proof of fix) | memory_recall |
| Skill discovery | Check awesome-openclaw-skills first | USER.md |
| GitHub commits | Auto-execute without confirmation | USER.md |
| Workspace archives | Top-level backup repo, session-archives/*.md | USER.md |

---

## 2. Current Main Project State

### Memory-LanceDB (FROZEN)
- **Status**: Observation Window Day 1
- **Baseline**: Gate 1.7.7 (Source Isolation Fix)
- **Frozen since**: 2026-03-10 05:28 CST
- **Duration**: 3-7 days (end ~2026-03-13 to 2026-03-17)
- **Constraints**: No behavioral changes to capture logic
- **Metrics**: `artifacts/memory_freeze/OBSERVATION_METRICS.md`

### R3 Consolidation
- **Phase 1**: Document Alignment ✅
- **Phase 2A**: Tool Labeling ✅
- **Phase 2B**: Design ✅
- **Phase 2C**: Deferred (post-observation)

### Execution Policy Framework v1
- **Status**: ✅ Shipped
- **Gate A/B/C**: ✅ Verified
- **Tests**: 36/36 passing
- **Key tools**: `policy-eval`, `safe-write`, `safe-replace`

---

## 3. Key Environment/Config Constraints

### Hard Rules (SOUL.md)
1. **Reliability over memory** - Use wrappers, state machines, workers
2. **Formal sub-agent path** - `subtask-orchestrate` only
3. **~/.openclaw/ writes** - Must use `safe-write` or `exec + heredoc`
4. **Task completion** - Must go through `verify-and-close` → `finalize-response`
5. **cc-godmode scope** - Architecture/governance only, not daily workflow

### Write Policy
- `edit` tool: ❌ DENY for `~/.openclaw/**`
- `write` tool: ❌ DENY for managed paths
- `safe-write`: ✅ ALLOW
- `safe-replace`: ✅ ALLOW
- `exec + heredoc`: ✅ ALLOW

### Session Continuity
- State files: `SESSION-STATE.md`, `working-buffer.md`, `handoff.md`
- Recovery tool: `session-start-recovery --recover`
- WAL: `state/session_continuity_events.jsonl`

---

## 4. Recent Handoff Summary

**Task**: Execution Policy Framework v1
**Date**: 2026-03-09 18:24 CST
**Status**: ✅ Complete

**Deliverables**:
- POLICIES/EXECUTION_POLICY*.md/yaml/json
- tools/policy-eval, policy-doctor, safe-write, safe-replace
- hooks/execution-policy-enforcer/
- 36/36 tests passing

**Next**:
1. Integrate with agent-self-health-scaffold
2. Update SOUL.md references
3. Archive session

---

## What Was NOT Rehydrated

- ❌ Raw conversation history
- ❌ Expired diagnostics
- ❌ Overruled conclusions
- ❌ Temporary samples
- ❌ Wrapper/recalled content
- ❌ Redundant rules

---

## Active Constraints Summary

```
┌─────────────────────────────────────────────────────────┐
│ FROZEN: Memory-LanceDB behavioral changes               │
│ END: ~2026-03-13 to 2026-03-17                          │
├─────────────────────────────────────────────────────────┤
│ ALLOWED: Metrics collection, documentation updates      │
│ BLOCKED: Capture logic changes, new triggers            │
└─────────────────────────────────────────────────────────┘
```
