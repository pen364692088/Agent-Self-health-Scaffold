# Live Session Runtime Audit

## A. Current Live Session Runtime

### A1. Process Information
- **Gateway PID**: 3650954
- **Process**: openclaw-gateway
- **Start Time**: 2026-03-08T16:58:59-05:00
- **Uptime**: ~2 hours
- **OpenClaw Version**: 2026.3.7
- **Node Version**: 22.22.0

### A2. Session Information
- **Session ID**: ee931bff-6fce-4682-930e-44f23cb8382a
- **Created**: 2026-03-08T15:32:09-06:00
- **Current Tokens**: 221k / 200k (111%)
- **Compactions**: 0
- **Agent**: main
- **Channel**: telegram

### A3. Config Status
- **Config File**: ~/.openclaw/openclaw.json
- **Last Modified**: 2026-03-08T16:58:00-05:00
- **runtime_compression_policy**: **null** (not loaded)

### A4. Policy File Status
- **Policy File**: artifacts/context_compression/config_alignment_gate/runtime_compression_policy.json
- **Exists**: YES
- **Content**: Valid (thresholds: 0.75/0.85/0.92)
- **Loaded by OpenClaw**: **NO**

## B. Main Chain Execution Check

### B1. Hook Registration
- **preAssemble hook**: NOT FOUND in OpenClaw core
- **promptAssemble hook**: NOT FOUND in OpenClaw core
- **context-budget-check integration**: NOT FOUND
- **context-compress integration**: NOT FOUND

### B2. Hook Execution Traces
- **Budget check traces**: Manual only (not automatic)
- **Compression traces**: Manual only (not automatic)
- **Guardrail 2A traces**: NONE (mechanism doesn't exist)

### B3. Breakpoint Location
The break is at **integration level**:
- Tools exist in workspace
- Policy file exists
- **But OpenClaw core has no code to use them**

## C. Session Binding Check

### C1. Session Age
- Session created BEFORE Config Alignment Gate closed
- Gateway restarted AFTER Gate closed
- **But restart doesn't help** - policy not integrated

### C2. Stale State Analysis
- NOT stale session
- NOT stale runtime
- NOT stale config
- **Missing integration code**

## D. Why 111% Without Compaction

### D1. Threshold Crossing
- Current ratio: 1.11 (111%)
- Threshold for enforced: 0.85
- **Should have triggered**: YES
- **Actually triggered**: NO

### D2. Root Cause
OpenClaw core **does not check** context ratio against thresholds.
The `session_status` command shows compaction count, but there's no
automatic mechanism to trigger it.

### D3. External vs Internal
- **External tools** (context-compress): Create capsules, don't affect live prompt
- **Internal mechanism**: Doesn't exist

## E. Conclusion

This is not a "stale runtime" or "stale session" issue.
This is a **missing integration** issue.

The compression tools and policy files exist in the workspace,
but OpenClaw core does not have code to:
1. Read the policy file
2. Check context ratio
3. Call compression tools
4. Enforce thresholds

The "Config Alignment Gate PASSED" status refers to the policy file
being created, not to OpenClaw actually using it.
