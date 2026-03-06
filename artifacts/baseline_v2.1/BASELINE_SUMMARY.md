# Baseline v2.1 Summary

**Frozen**: 2026-03-06 10:30 CST
**Version**: execution-policy-v2.1

---

## Test Results

| Category | Count | Status |
|----------|-------|--------|
| Normal tests | 13 | ✅ PASS |
| Adversarial tests | 9 | ✅ BLOCKED |
| Happy Path | 1 | ✅ PASS |
| Attack Path | 2 | ✅ BLOCKED |

---

## Components

| Component | File | Status |
|-----------|------|--------|
| receipt-signer | tools/receipt-signer | ✅ HEALTHY |
| gate-a-signer | tools/gate-a-signer | ✅ HEALTHY |
| gate-b-signer | tools/gate-b-signer | ✅ HEALTHY |
| gate-c-signer | tools/gate-c-signer | ✅ HEALTHY |
| final-aggregator | tools/final-aggregator | ✅ HEALTHY |
| state-authority | tools/state-authority | ✅ HEALTHY |
| verify-and-close-v2 | tools/verify-and-close-v2 | ✅ HEALTHY |
| safe-message | tools/safe-message | ✅ HEALTHY |

---

## Sample Files

```
happy_path/
├── baseline_happy_001_gate_a_receipt.json   # Gate A signature
├── baseline_happy_001_gate_b_receipt.json   # Gate B signature
├── baseline_happy_001_gate_c_receipt.json   # Gate C signature
└── baseline_happy_001_final_receipt.json    # Aggregated final

attack_samples/
├── attack_tamper_gate_a_original.json       # Before tampering
└── attack_tamper_gate_a_tampered.json       # After tampering (detected)
```

---

## Metrics Snapshot

See `metrics_snapshot.json` for full details.

Key metrics:
- `receipt_verification_latency_ms`: ~2ms
- `state_transition_latency_ms`: ~1ms
- `attack_detection_rate`: 100%

---

## Verification Command

```bash
# Verify all baseline receipts
for f in artifacts/baseline_v2.1/happy_path/*.json; do
  tools/receipt-signer verify "$f" | jq '{file: input_filename, valid}'
done
```

---

## Do Not Modify

This baseline is frozen. For changes, create `baseline_v2.2/`.
