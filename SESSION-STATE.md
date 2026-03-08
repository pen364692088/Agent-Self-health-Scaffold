# Session State

**Purpose**: 恢复主骨架 - 稳定且关键的信息

**Baseline**: v1.1.1 STABLE (FROZEN)  
**Updated**: 2026-03-08T08:54:00-06:00

---

## Current Objective
继续推进 session-route-probe，优先做真实 A/B diff，用证据区分 route input 变化、runtime rotation、以及仅表面展示差异。

## Current Phase
✅ Phase 4: local decision layer complete
✅ Phase 5: upstream attachment points identified
✅ Phase 6: route probe / diff implemented
✅ Phase 7: real A/B diff completed

## Current Branch / Workspace
- Branch: openviking-l2-bugfix
- Workspace: ~/.openclaw/workspace

---

## Scope Status

| Item | Status | Notes |
|------|--------|-------|
| Binding registry / decision layer | ✅ DONE | `tools/session_reuse_lib.py`, `tools/session-route` |
| Upstream authoritative hook identification | ✅ DONE | `resolveAgentRoute`, `buildAgentSessionKey` |
| Probe enriched runtime fields | ✅ DONE | runtime/session file/surface placeholders |
| Diff enriched judgments | ✅ DONE | session_key/runtime/file/layer/cause |
| Two real samples | ✅ DONE | `7886` vs `7913` |
| A/B diff report | ✅ DONE | `artifacts/session_reuse/v1_0/AB_DIFF_REPORT.md` |
| Core router source patch | ⏳ PENDING | source tree not present in workspace repo |

---

## Latest Evidence

### Real sample A
- inbound_event_id: `telegram:7886`
- session_key: `agent:main:main`
- runtime_session_id: `20b82894-a9f6-40ef-acf0-b1e9362bf08d`
- session_file: `20b82894-a9f6-40ef-acf0-b1e9362bf08d.jsonl`

### Real sample B
- inbound_event_id: `telegram:7913`
- session_key: `agent:main:main`
- runtime_session_id: `20b82894-a9f6-40ef-acf0-b1e9362bf08d`
- session_file: `20b82894-a9f6-40ef-acf0-b1e9362bf08d.jsonl`

### A/B conclusion
- `session_key_changed = false`
- `runtime_session_changed = false`
- `session_file_changed = false`
- `suspected_layer = surface-only-or-none`
- `suspected_cause = surface_only_or_same_session`

## Direct Interpretation
For this real same-chat pair, there is **no evidence** of:
- route input / sessionKey churn
- runtime session-id rotation
- runtime session-file rotation

So this sampled pair points most strongly to:
- only surface presentation difference
- or no actual session rotation at all

## Files Added / Updated This Round
- `tools/session-route-probe`
- `docs/session_reuse/ROUTE_PROBE.md`
- `tests/session_reuse/test_session_route_probe.py`
- `artifacts/session_reuse/probe/real_samples/*.json`
- `artifacts/session_reuse/v1_0/AB_DIFF_REPORT.md`

## Test Status
- `pytest -q tests/session_reuse/test_session_route_probe.py tests/session_reuse/test_session_reuse_v1.py`
- ✅ 12 passed

## Next Actions
1. Capture another real pair when a future “wake-like new session” symptom is observed live
2. Run probe immediately at that moment for higher confidence evidence
3. If a future pair shows stable `session_key` but changed higher-layer ids, inspect UI/control-plane wrapper lifecycle
4. If a future pair shows changed `session_key`, trace exact route input drift

## Blockers
- Historical wake-up symptom was not probed at the moment it happened, so current A/B result is limited to today’s available real samples
- No clean authoritative upstream source tree in workspace for direct router integration

---

## Rollout Status

**Mode**: Decision layer + route probe + real A/B diff complete  
**Scope**: Evidence collection before upstream source integration  
**Rollback Ready**: YES
