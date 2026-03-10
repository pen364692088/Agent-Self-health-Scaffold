# Bug: isolated session with announce delivery hijacks primary session route

## Summary

When a subagent/cron task runs with `sessionTarget=isolated` and `delivery.mode=announce`, and the user replies to the announcement message, OpenClCore incorrectly rebinds the primary session route to the isolated session.

This causes subsequent user messages to be routed to the isolated session instead of the primary/main session, breaking session continuity silently.

---

## Minimal Reproduction

### Steps

1. Create a main/default session with Telegram binding
2. Spawn a subagent/cron task with:
   - `sessionTarget: "isolated"`
   - `delivery.mode: "announce"`
   - `delivery.target: "telegram:direct:<user_id>"`
3. The subagent sends an announcement to the user
4. User replies to the announcement
5. **Bug**: The reply rebinds the primary route to the isolated session

### Expected Behavior

User reply to isolated session announcement should NOT rebind the primary session route. The isolated session should remain isolated.

### Actual Behavior

The primary route (`agent:main:telegram:direct:<user_id>`) is rebound to the isolated session ID.

---

## Root Cause Analysis

**Location**: OpenClCore reply-routing logic

**Issue**: The reply-routing mechanism does not respect `sessionTarget=isolated` when processing user replies to announcement messages.

When a user replies to an announcement from an isolated session:
1. OpenClCore receives the reply
2. It looks up the "last session" for this route
3. The announcement delivery updated the route to point to the isolated session
4. The reply is routed to the isolated session
5. **The primary route binding is permanently changed**

---

## Impact

- **Severity**: High (P0)
- **Scope**: All deployments using `isolated` sessions with `announce` delivery
- **User Impact**: Session continuity broken silently, subsequent messages go to wrong session

---

## Mitigation Layer (Implemented)

We have implemented a protection layer in OpenClaw (not OpenClCore):

### 1. Detection & Recovery
- **route-rebind-guard**: Manual detection and recovery
- **route-rebind-guard-heartbeat**: Automatic periodic check (heartbeat integration)
- **route-write-guard**: Real-time monitoring with <1ms recovery (inotify)

### 2. Audit Trail
All route rebind events logged to `logs/route_rebind_audit.jsonl`

### 3. E2E Tests
All 6 behavioral E2E tests passing:
- Hijack detection + restore cycle ✅
- Normal reply not false positive ✅
- Multiple isolated concurrent scenario ✅
- Restore persistence ✅
- Recovery speed <100ms ✅ (actual: 0.62ms)
- Continuous hijack protection ✅

### Limitations
- Cannot prevent OpenClCore from making the wrong rebind
- Recovery happens after the rebind (though within 1ms)
- Requires additional tooling in OpenClaw layer

---

## Proposed Fix (OpenClCore)

The reply-routing logic should:

1. **Check sessionTarget before rebinding**:
   ```typescript
   if (session.sessionTarget === 'isolated') {
     // Do NOT rebind primary route
     // Route reply to isolated session only
     return;
   }
   ```

2. **Separate announcement routes from primary routes**:
   - Announcements from isolated sessions should use temporary routes
   - User replies should route back to the primary session
   - Not create permanent bindings

3. **Add route binding guard**:
   - Before any route rebind, verify target session is not isolated
   - Log warnings when attempting to rebind to isolated session

---

## Environment

- OpenClaw version: (current)
- OpenClCore version: (current)
- Platform: Linux
- Channel: Telegram

---

## Related

- Mitigation implementation: `~/.openclaw/workspace/tools/route-rebind-guard*`
- E2E tests: `tests/test_route_rebind_guard_e2e.py`
- Audit logs: `logs/route_rebind_audit.jsonl`

---

## Labels

- bug
- P0
- session-continuity
- routing
- isolated-session
