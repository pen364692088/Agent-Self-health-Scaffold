# Root Cause Analysis: Why No Automatic Compression at 111% Context

## Summary
Current live session reached 221k/200k (111%) with 0 compactions because:
**OpenClaw core does not have context compression integration.**

## Evidence Chain

### 1. Policy File Exists But Not Loaded
- `runtime_compression_policy.json` exists at `artifacts/context_compression/config_alignment_gate/`
- Policy content is correct (thresholds: 0.75/0.85/0.92)
- **But**: `openclaw.json` has `runtime_compression_policy: null`
- **Result**: Policy not loaded into OpenClaw runtime

### 2. No Hook Integration in OpenClaw Core
- Searched OpenClaw `dist/` directory for:
  - `context-budget` - NOT FOUND
  - `context-compress` - NOT FOUND  
  - `runtime_compression` - NOT FOUND
  - `preAssemble` / `promptAssemble` - NOT FOUND
- **Result**: OpenClaw has no code to call compression tools

### 3. Compression Events Are Manual Only
- All entries in `artifacts/compression_events/` are from manual tool invocation
- Timestamps match user-initiated commands, not automatic triggers
- **Result**: No automatic compression path exists

### 4. Config Alignment Gate Misleading
- Gate document claims "OpenClaw 运行时读取并应用策略 ✅"
- This is a documentation claim, not verified in code
- The actual integration step was never completed

### 5. Session Started Before Policy
- Session created: 2026-03-08T15:32:09 (CST)
- Config Alignment Gate closed: 2026-03-08T00:45:00 (CST)
- Gateway restarted: 2026-03-08T16:58:59 (CST)
- **But**: Even with restart, policy not loaded because OpenClaw doesn't read it

## Root Cause Classification

**Primary**: Integration Gap
- Tools exist but are NOT integrated into OpenClaw core
- This is not "stale runtime" or "stale session"
- This is **missing integration code**

**Secondary**: Config Not Wired
- `openclaw.json` does not reference `runtime_compression_policy.json`
- No code path in OpenClaw to read this config

## The Gap

```
Policy File Exists (✅)  →  OpenClaw Reads It (❌)  →  Hooks Execute (❌)
```

## What Would Be Needed

1. **OpenClaw core modification** to:
   - Read `runtime_compression_policy.json` on startup
   - Register pre-assemble hook
   - Call `context-budget-check` before each prompt
   - Call `context-compress` when threshold exceeded

2. **Alternative**: OpenClaw native compaction feature
   - OpenClaw may have its own compaction system
   - But it's not connected to our tools
   - And it's not triggered at 0.85 threshold

## Answer to F Questions

1. **Has current live session loaded new runtime compression policy?**
   - NO. Policy file exists but OpenClaw doesn't read it.

2. **Has current live session executed pre-assemble budget-check?**
   - NO. No such hook exists in OpenClaw core.

3. **Has current live session executed guardrail 2A judgment?**
   - NO. No such mechanism exists in OpenClaw core.

4. **What is the root cause of no automatic compression?**
   - **Integration gap**: Tools exist but are not integrated into OpenClaw.
   - NOT "stale session" or "stale config".
   - The integration step was documented as done but never coded.

5. **What fix is needed?**
   - **Code change required**: Integrate compression tools into OpenClaw core
   - OR wait for OpenClaw native compaction (if exists)
   - Restarting gateway/session will NOT help
   - Refreshing config will NOT help
   - The integration code simply doesn't exist

---

## UPDATE: OpenClaw Native Compaction Found

After deeper investigation, OpenClaw **does have native compaction**:

### Evidence
- `compaction` config schema exists in `auth-profiles-*.js`
- `autoCompactionCount` logic exists in `reply-C5LKjXcC.js`
- `sessions.compact` API exists
- Default mode is `"safeguard"`

### The Real Problem
**OpenClaw's `openclaw.json` has `compaction: null`**

This means:
1. Compaction feature exists but is not configured
2. Default mode "safeguard" should apply, but something is blocking it
3. Our custom `runtime_compression_policy.json` is **not related** to OpenClaw's native compaction

### Two Separate Systems
1. **OpenClaw Native Compaction**
   - Controlled by `openclaw.json` → `compaction` key
   - Has `mode`, `reserveTokens`, `keepRecentTokens`, etc.
   - Currently: `null` (not configured)

2. **Custom Context Compression Tools**
   - `tools/context-budget-check`
   - `tools/context-compress`
   - `runtime_compression_policy.json`
   - These are **never integrated** into OpenClaw

### The Gap Explained
We created a **parallel compression system** (custom tools + policy)
that was **never wired into OpenClaw**.

Meanwhile, OpenClaw's **native compaction** exists but is either:
- Not triggered (wrong conditions?)
- Not configured properly
- Blocked by some setting

### Revised Root Cause

**Primary**: OpenClaw native compaction not triggering
- Why? Need to investigate trigger conditions
- Config shows `compaction: null`

**Secondary**: Custom compression tools not integrated
- These are separate from native compaction
- Were never meant to be the primary mechanism

### Next Steps
1. Check OpenClaw native compaction trigger conditions
2. Configure `compaction` in `openclaw.json` if needed
3. Investigate why `autoCompactionCount` stayed at 0
