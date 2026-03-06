# Trust Anchor v2.1 Handoff Document

**Release Date**: 2026-03-06
**Status**: FROZEN — No modifications without version bump

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Execution Policy v2.1                     │
│                   "Trust Anchor" Architecture                │
└─────────────────────────────────────────────────────────────┘

Gate A Signer ──────┐
Gate B Signer ──────┼──→ Final Aggregator ──→ State Authority
Gate C Signer ──────┘         │                      │
                              │                      │
                    receipt-signer           ┌──────┴──────┐
                          │                  │             │
                          ▼                  ▼             ▼
                    verify-and-close    finalize-response  done-guard
                                              │
                                              ▼
                                        safe-message
                                              │
                                              ▼
                                         [OUTPUT]
```

**Key Insight**: Receipt ≠ State Transition. Signature chain proves *intent*, State Authority proves *execution*.

---

## 2. Receipt Trust Model

### 2.1 Core Fields (Signed)

Only these fields are included in HMAC signature:

```json
{
  "task_id": "string",
  "gate": "A|B|C|final",
  "status": "ready_to_close|closed|failed",
  "ts": "ISO8601",
  "signer_id": "string"
}
```

**Excluded**: `checks`, `issues`, `evidence` — these are append-only, not trust-critical.

### 2.2 Signature Chain

```
receipt-signer (HMAC-SHA256)
    │
    ├─→ gate-a-signer (signer_id="gate-a", independent key)
    ├─→ gate-b-signer (signer_id="gate-b", independent key)
    ├─→ gate-c-signer (signer_id="gate-c", independent key)
    │
    └─→ final-aggregator
            │
            └─→ state-authority (state machine arbiter)
```

### 2.3 Verification

```bash
# Verify a receipt
receipt-signer verify <receipt.json>

# Expected output:
{
  "valid": true,
  "signer_id": "gate-a",
  "core_fields_intact": true
}
```

---

## 3. Signer Authority Boundaries

| Signer | Can Sign | Cannot Sign | Scope |
|--------|----------|-------------|-------|
| `gate-a-signer` | Gate A receipts | Gate B/C/final | Contract validation |
| `gate-b-signer` | Gate B receipts | Gate A/C/final | E2E testing |
| `gate-c-signer` | Gate C receipts | Gate A/B/final | Preflight check |
| `final-aggregator` | Final receipts | Gate A/B/C | Aggregation only |
| `receipt-signer` | Any receipt | State transitions | Generic HMAC |

**Critical Rule**: `final-aggregator` cannot sign gate receipts. It can only aggregate existing signed receipts.

---

## 4. State Authority Rules

### 4.1 State Machine

```
initialized → in_progress → ready_to_close → closed
                                │
                                └─→ failed
```

### 4.2 Transition Guards

| Transition | Requirement | Enforcement |
|------------|-------------|-------------|
| `→ ready_to_close` | All gates passed | `final-aggregator` check |
| `ready_to_close → closed` | Final receipt signed | `state-authority` verify |
| `initialized → closed` | ❌ BLOCKED | State authority rejects |
| `ready_to_close → closed` (no receipt) | ❌ BLOCKED | State authority rejects |

### 4.3 State Authority API

```python
class StateAuthority:
    def can_transition(self, current_state, target_state, receipt):
        if current_state == "initialized" and target_state == "closed":
            return False, "Cannot skip ready_to_close"
        if not self.verify_receipt(receipt):
            return False, "Invalid receipt signature"
        return True, "Transition allowed"
```

---

## 5. Baseline Directory Structure

```
artifacts/baseline_v2.1/
├── happy_path/
│   ├── baseline_happy_001_gate_a_receipt.json
│   ├── baseline_happy_001_gate_b_receipt.json
│   ├── baseline_happy_001_gate_c_receipt.json
│   └── baseline_happy_001_final_receipt.json
├── attack_samples/
│   ├── attack_tamper_gate_a_original.json
│   └── attack_tamper_gate_a_tampered.json
├── logs/
├── BASELINE_SUMMARY.md
└── metrics_snapshot.json
```

**Retention Policy**: Baseline samples are immutable. Do not delete.

---

## 6. Blocked Attack Surfaces

| Attack | Vector | Blocked By | Test |
|--------|--------|------------|------|
| Receipt Tampering | Modify `status` field | HMAC signature | `attack_tamper_gate_a` |
| Gate Forgery | Sign gate B with gate A key | Independent signer keys | Adversarial test #3 |
| State Bypass | Skip `ready_to_close` | State Authority | Adversarial test #7 |
| Aggregator Forgery | Create final without gate receipts | Aggregator constraints | Adversarial test #5 |
| Receipt Replay | Use old receipt | Timestamp + task_id check | Adversarial test #9 |

---

## 7. Outstanding Gap: Native Message Hook

### 7.1 Current State

```
safe-message → output-interceptor → finalize-response → done-guard
```

**Problem**: This chain is at agent layer, not OpenClaw core. Theoretical bypass exists if:
- Agent directly calls `message` tool without going through `safe-message`
- Malicious agent code constructs raw Telegram API calls

### 7.2 Target Architecture

```
message tool (OpenClaw core)
    │
    ├─→ Pre-send hook (policy check)
    │       │
    │       └─→ execution-policy middleware
    │
    └─→ Send to channel (Telegram/Discord/etc.)
```

### 7.3 Integration Points (Need OpenClaw Core Support)

1. **MessageToolMiddleware** - Interface for pre-send hooks
2. **PolicyEnforcer** - Execution Policy as registered middleware
3. **Hook Priority** - Policy hook runs before channel adapter

### 7.3 Current Status (Updated 2026-03-06)

**✅ Native hook infrastructure EXISTS and is FUNCTIONAL.**

OpenClaw has a `message:sending` hook system already in use by `emotiond-enforcer`:

```
~/.openclaw/hooks/emotiond-enforcer/
├── handler.js      # Pre-send middleware (WORKING)
├── hook.json       # Configuration
└── HOOK.md         # Documentation
```

**What's Working**:
- Hook intercepts `message:sending` events
- Can modify `event.context.text` to change response
- Audit logging to `emotiond/enforcement_audit.jsonl`

**What's Missing**:
- Integration with Execution Policy v2.1 Trust Anchor chain
- Receipt signer verification in hook
- State Authority approval before send

### 7.4 Implementation Path

| Step | Owner | Effort | Status |
|------|-------|--------|--------|
| 1. Create execution-policy-enforcer hook | Agent dev | 1-2 hours | 🟡 READY |
| 2. Wire to receipt-signer + state-authority | Agent dev | 2-3 hours | 🟡 READY |
| 3. Shadow mode testing | Agent dev | 3-7 days | ⏳ PENDING |
| 4. Enable enforcement mode | Agent dev | 1 day | ⏳ PENDING |

**Estimated Timeline**: 1 day implementation + observation period

**Detailed Plan**: See `docs/releases/NATIVE_HOOK_INTEGRATION.md`

---

## 8. Version History

| Version | Date | Changes |
|---------|------|---------|
| v2.1 | 2026-03-06 | Trust Anchor architecture, signer separation, state authority |
| v2.0 | 2026-03-05 | Gate structure, adversarial testing |
| v1.0 | 2026-03-04 | Basic verify-and-close |

---

## 9. Contact & Escalation

- **Policy Owner**: Agent developer (this workspace)
- **Technical Questions**: See `docs/EXECUTION_POLICY.md`
- **Baseline Questions**: See `artifacts/baseline_v2.1/BASELINE_SUMMARY.md`
- **OpenClaw Core**: https://github.com/openclaw/openclaw

---

**FROZEN**: This document represents v2.1 architecture baseline. Any changes require version bump to v2.2+.
