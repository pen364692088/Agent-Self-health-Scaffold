# Session State

**Purpose**: 恢复主骨架 - 稳定且关键的信息

**Baseline**: v1.1.1 STABLE (FROZEN)  
**Updated**: 2026-03-08T08:31:00-06:00

---

## Current Objective
实现 Session Reuse / Thread Affinity v1.0 的可运行决策层，并补齐 route probe / diff，能用证据区分 sessionKey 变化与 runtime session 变化。

## Current Phase
✅ Phase 4: local decision layer complete
✅ Phase 5: upstream attachment points identified
✅ Phase 6: route probe / diff implemented

## Current Branch / Workspace
- Branch: openviking-l2-bugfix
- Workspace: ~/.openclaw/workspace

---

## Scope Status

| Item | Status | Notes |
|------|--------|-------|
| Binding registry | ✅ DONE | runtime path defined |
| Decision log | ✅ DONE | runtime path defined |
| Reason enums | ✅ DONE | fixed enum set |
| TTL policy | ✅ DONE | conservative defaults |
| Decision function | ✅ DONE | `decide_session_for_inbound` |
| Continuity handoff | ✅ DONE | `recovery_needed` + recovery hook |
| Local validation | ✅ DONE | 11 tests passing |
| Upstream route identification | ✅ DONE | authoritative hook points found in installed OpenClaw dist |
| Route probe / diff | ✅ DONE | `tools/session-route-probe` |
| Core router source patch | ⏳ PENDING | source tree not present in workspace repo |

---

## Latest Evidence
- Probe tool derives route/session key using installed OpenClaw `session-key` dist module
- Probe tool inspects runtime session matches via `openclaw sessions --json` with `sessions.json` fallback
- Current direct-telegram probe result:
  - derived `session_key = agent:main:main`
  - runtime match exists for `agent:main:main`
  - `reused_channel_slot = true`
  - `new_runtime_session_created = false`

This means the latest observed direct-message case is **not evidence of bottom-layer channel slot churn**.
It leans toward a higher-layer runtime/UI/session-surface distinction unless route inputs differ in another case.

## Files Added This Round
- `tools/session-route-probe`
- `docs/session_reuse/ROUTE_PROBE.md`
- `tests/session_reuse/test_session_route_probe.py`

## Next Actions
1. Capture two real probes for the “last night” vs “wake-up” comparison
2. Diff them with `tools/session-route-probe diff`
3. Determine whether the problematic case is:
   - route/sessionKey change
   - runtime rotation above stable key
   - UI/session-surface presentation issue
4. If source tree becomes available, patch `resolveAgentRoute(input)` integration there

## Blockers
- Only dist build is locally available for authoritative router internals; no clean source module to patch in workspace repo
- Historical “last night” probe was not captured at the time, so exact A/B diff still needs a second real sample

---

## Rollout Status

**Mode**: Local decision layer + upstream locator + route probe complete  
**Scope**: Pre-source integration  
**Rollback Ready**: YES
