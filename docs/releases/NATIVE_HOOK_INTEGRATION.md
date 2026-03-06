# Native Hook Integration Roadmap

**Status**: Ready for Implementation
**Date**: 2026-03-06

---

## Current State

### What Already Exists

OpenClaw has a native hook system that intercepts `message:sending` events:

```
~/.openclaw/hooks/emotiond-enforcer/
├── handler.js      # Pre-send middleware
├── hook.json       # Configuration
└── HOOK.md         # Documentation
```

**Key Code** (handler.js):
```javascript
const handler = async (event) => {
  if (event.type !== 'message' || event.action !== 'sending') return event;
  
  const targetId = ctx.conversationId || ctx.channelId || 'default';
  const proposedResponse = ctx.text || ctx.message || '';
  
  // ... enforcement logic ...
  
  if (result.enforced) {
    event.context.text = result.finalResponse;  // Modify response
    event.context._enforcement = { ... };        // Audit trail
  }
  
  return event;
};
```

### What's Missing

The current hook only enforces:
1. Emotiond decisions (withdraw/attack/boundary)
2. Numeric leak detection (MVP11.5)

**NOT integrated**:
- Execution Policy v2.1 Trust Anchor chain
- Receipt signer verification
- State Authority approval
- Gate A/B/C enforcement

---

## Integration Options

### Option A: Extend emotiond-enforcer

**Pros**: Single hook, single audit trail
**Cons**: Tight coupling, harder to test independently

**Implementation**:
```javascript
// In handler.js
const { verifyExecutionPolicy } = require('./execution-policy-checker');

const handler = async (event) => {
  // ... existing emotiond checks ...
  
  // NEW: Execution Policy check
  const policyResult = await verifyExecutionPolicy({
    targetId: targetId,
    proposedResponse: proposedResponse,
    sessionId: ctx.sessionId,
    receipt: ctx._receipt  // If present
  });
  
  if (policyResult.block) {
    event.context.text = policyResult.safeResponse;
    event.context._policyBlock = policyResult.reason;
  }
  
  return event;
};
```

### Option B: Separate execution-policy-enforcer hook

**Pros**: Decoupled, independently testable, can be enabled/disabled
**Cons**: Two hooks, potential ordering issues

**Structure**:
```
~/.openclaw/hooks/
├── emotiond-enforcer/      # Existing (emotion checks)
└── execution-policy-enforcer/  # NEW (trust anchor)
    ├── handler.js
    ├── hook.json
    └── execution-policy-checker.js
```

**hook.json**:
```json
{
  "name": "execution-policy-enforcer",
  "version": "1.0.0",
  "type": "pre-send",
  "priority": 50,  // Run BEFORE emotiond-enforcer (lower = earlier)
  "events": ["message:sending"]
}
```

### Recommendation

**Option B** (separate hook) for cleaner architecture:
- Execution Policy is a different concern than emotiond
- Allows independent testing and rollout
- Priority ordering ensures policy check happens first

---

## Implementation Steps

### Step 1: Create hook scaffold
```bash
mkdir -p ~/.openclaw/hooks/execution-policy-enforcer
```

### Step 2: Create hook.json
```json
{
  "name": "execution-policy-enforcer",
  "version": "1.0.0",
  "description": "Enforces Execution Policy v2.1 Trust Anchor before messages are sent",
  "type": "pre-send",
  "priority": 50,
  "handler": "handler.js",
  "config": {
    "policyVersion": "2.1",
    "enforcementMode": "shadow",  // "shadow" | "enforce"
    "auditEnabled": true
  }
}
```

### Step 3: Create handler.js
```javascript
const { StateAuthority } = require('./state-authority');
const { ReceiptSigner } = require('./receipt-signer');

async function verifyExecutionPolicy(context) {
  // Check if message has valid receipt
  if (context._receipt) {
    const valid = ReceiptSigner.verify(context._receipt);
    if (!valid) {
      return {
        block: true,
        reason: 'invalid_receipt_signature',
        safeResponse: 'I need to reconsider my response.'
      };
    }
  }
  
  // Check state authority
  const stateAuth = new StateAuthority();
  const allowed = await stateAuth.canTransition({
    from: context._state || 'in_progress',
    to: 'closed',
    receipt: context._receipt
  });
  
  if (!allowed) {
    return {
      block: true,
      reason: 'state_transition_denied',
      safeResponse: 'I need to reconsider my response.'
    };
  }
  
  return { block: false };
}

const handler = async (event) => {
  if (event.type !== 'message' || event.action !== 'sending') return event;
  
  const ctx = event.context || {};
  const result = await verifyExecutionPolicy(ctx);
  
  if (result.block) {
    event.context.text = result.safeResponse;
    event.context._policyBlock = result.reason;
  }
  
  return event;
};

module.exports = handler;
```

### Step 4: Enable in OpenClaw config
```json
// ~/.openclaw/openclaw.json
{
  "hooks": {
    "internal": {
      "enabled": true,
      "entries": {
        "emotiond-enforcer": { "enabled": true },
        "execution-policy-enforcer": { "enabled": true }
      }
    }
  }
}
```

---

## Testing Strategy

### Unit Tests
```bash
# Test receipt verification
node -e "const h = require('./handler'); console.log(h.verifyExecutionPolicy({...}))"
```

### Integration Tests
```bash
# Send test message, verify hook intercepts
openclaw test-hook execution-policy-enforcer --event message:sending
```

### Shadow Mode
Set `enforcementMode: "shadow"` to log violations without blocking.

---

## Timeline

| Step | Effort | Dependency |
|------|--------|------------|
| Create scaffold | 5 min | None |
| Implement handler.js | 1-2 hours | Step 1 |
| Wire to existing tools | 2-3 hours | Step 2 |
| Testing | 1-2 hours | Step 3 |
| Shadow mode observation | 3-7 days | Step 4 |

**Total**: ~1 day implementation + observation period

---

## Open Questions

1. **Priority ordering**: Should policy check run before or after emotiond?
   - Recommendation: BEFORE (lower priority number = earlier execution)
   
2. **Receipt injection**: How does agent layer pass receipt to message tool?
   - Option: `message` tool accepts `_receipt` in context
   - Alternative: Hook extracts from session state

3. **State Authority backend**: Does hook call Python tools or reimplement in JS?
   - Recommendation: Call Python tools via subprocess for consistency
   - Alternative: Port critical logic to JS for performance

---

## Conclusion

Native hook infrastructure **exists and is functional**. The gap is integration with Execution Policy v2.1 Trust Anchor chain. This is an implementation task, not an architectural blocker.
