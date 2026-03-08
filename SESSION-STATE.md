# Session State

**Purpose**: 恢复主骨架 - 稳定且关键的信息

**Baseline**: v1.1.1 STABLE (FROZEN)  
**Updated**: 2026-03-08T09:07:00-06:00

---

## Current Objective
完成现场取证工具 `capture-wake-session-diff`，然后将 Session Reuse / Thread Affinity v1.0 切换到观察态，等待下一次真实 wake-like incident。

## Current Phase
✅ Phase 4: local decision layer complete
✅ Phase 5: upstream attachment points identified
✅ Phase 6: route probe / diff implemented
✅ Phase 7: real A/B diff completed
✅ Phase 8: one-shot incident capture tooling complete
🟡 Observation State: waiting for next real wake-like incident

## Current Branch / Workspace
- Branch: openviking-l2-bugfix
- Workspace: ~/.openclaw/workspace

---

## Scope Status

| Item | Status | Notes |
|------|--------|-------|
| Decision layer | ✅ DONE | session reuse v1.0 local logic |
| Route probe | ✅ DONE | enriched runtime/session fields |
| Diff judgments | ✅ DONE | route/runtime/file/layer/cause |
| Real A/B report | ✅ DONE | `artifacts/session_reuse/v1_0/AB_DIFF_REPORT.md` |
| Incident capture tool | ✅ DONE | `tools/capture-wake-session-diff` |
| Observation mode | ✅ DONE | wait for next real incident |
| Automatic repair/intervention | ❌ INTENTIONALLY NOT DONE | evidence only |

---

## New Capability

### Tool
`tools/capture-wake-session-diff`

### Purpose
One-shot incident forensics only:
1. capture current probe
2. choose latest or explicit baseline
3. run diff automatically
4. generate incident report
5. classify conclusion as:
   - `confirmed`
   - `likely`
   - `inconclusive`

### Explicit non-goals
- no auto-fix
- no session mutation
- no continuity mutation
- no runtime intervention

---

## Latest Incident Capture Result
Command executed against current Telegram direct chat with explicit baseline `normal_continuation_7886.json`.

### Result
- `level = likely`
- verdict: `Likely surface-only presentation difference or no actual session rotation.`

### Diff summary
- `session_key_changed = false`
- `runtime_session_changed = false`
- `session_file_changed = false`
- `suspected_layer = surface-only-or-none`
- `suspected_cause = surface_only_or_same_session`

### Evidence
- current probe: `artifacts/session_reuse/incidents/current_probe_20260308T140600Z.json`
- incident report: `artifacts/session_reuse/incidents/incident_report_20260308T140600Z.md`

## Test Status
- `pytest -q tests/session_reuse/test_capture_wake_session_diff.py tests/session_reuse/test_session_route_probe.py tests/session_reuse/test_session_reuse_v1.py`
- ✅ 13 passed

## Observation Policy
Session Reuse / Thread Affinity v1.0 is now in **observation mode**.
Next action is not more abstraction; it is to wait for the next real wake-like symptom and run `tools/capture-wake-session-diff` immediately.

## Next Actions
1. When the next wake-like incident happens, run:
   ```bash
   tools/capture-wake-session-diff --chat-id telegram:8420019401 --account-id manager --dm-scope per-channel-peer --inbound-event-id <message_id>
   ```
2. Review incident report classification
3. Only escalate to route/runtime investigation if a future capture yields `confirmed` or stronger `likely` evidence for a non-surface layer

## Blockers
- Still no authoritative upstream source tree in workspace for direct router integration
- Higher-layer surface ids remain null in current samples

---

## Rollout Status

**Mode**: Observation  
**Evidence path**: Ready  
**Intervention path**: Deliberately disabled
