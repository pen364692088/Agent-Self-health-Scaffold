# Session State

**Purpose**: 恢复主骨架 - 稳定且关键的信息

**Baseline**: v1.1.1 STABLE (FROZEN)  
**Updated**: 2026-03-08T08:52:00-06:00

---

## Current Objective
实现 Session Reuse / Thread Affinity v1.0 的可运行决策层，并明确 OpenClaw 上游 authoritative route 挂点，确保后续能在正确层接入复用策略。

## Current Phase
✅ Phase 4: local decision layer complete
✅ Phase 5: upstream attachment points identified

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
| Local validation | ✅ DONE | 9 tests passing |
| Upstream route identification | ✅ DONE | authoritative hook points found in installed OpenClaw dist |
| Core router source patch | ⏳ PENDING | source tree not present in workspace repo |

---

## New Findings
- `recordInboundSession()` is not the session-selection hook.
- Real transport-level decision point is upstream at:
  - `resolveAgentRoute(input)`
  - `buildAgentSessionKey(params)`
- If `sessionKey` remains stable, OpenClaw channel/session storage should naturally reuse the same slot.
- User-observed “new session” may therefore be happening above the channel-store layer unless the route inputs themselves changed.

## Evidence
- `docs/session_reuse/UPSTREAM_ATTACHMENT.md`
- `tools/inspect-openclaw-session-route`

## Next Actions
1. Compare real inbound events to derived `sessionKey` over time
2. Determine whether observed “new session” means changed `sessionKey` or higher-layer runtime session creation
3. If source tree becomes available, patch `resolveAgentRoute(input)` integration there
4. Keep avoiding direct minified-dist patching as the primary path

## Blockers
- Only dist build is locally available for authoritative router internals; no clean source module to patch in workspace repo

---

## Rollout Status

**Mode**: Local decision layer + upstream locator complete  
**Scope**: Pre-source integration  
**Rollback Ready**: YES
