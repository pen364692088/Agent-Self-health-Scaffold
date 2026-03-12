# GATE_SELF_HEALTH_WIRING

## Purpose
Define how Gate A/B/C validates self-health objects.

## Gate A - Contract Integrity
Validates:
- Capability registry completeness
- Schema compliance (capability, proposal)
- Policy file existence and version
- Capability_id uniqueness
- Verification_mode legality

Gate A MUST reject:
- Missing capability registry
- Invalid schema instances
- Duplicate capability_ids

## Gate B - E2E Capability Paths
Verifies critical paths:
- heartbeat_cycle_execution
- callback_delivery
- mailbox_consumption
- incident_recording
- summary_generation

Gate B MUST:
- Use real/synthetic verification, not config-only
- Output per-capability and per-path status
- Distinguish "not checked" from "checked and failed"

## Gate C - Preflight & Boundary
Validates:
- Preflight capability state readable
- Doctor vs capability state consistency
- Proposal boundary (still proposal_only)
- Level B/C not incorrectly opened
- Summary metric consistency
- Cooldown/dedup/retry ceiling effectiveness

## Gate Output
Gate results MUST include:
- gate_contract_status: PASS/FAIL
- gate_e2e_status: PASS/FAIL/PARTIAL
- gate_preflight_status: PASS/FAIL
- capability_health_status: healthy/stale/degraded/missing
- proposal_boundary_status: valid/violation

## Integration
Gate results flow to:
- artifacts/self_health/gate_reports/
- Unified health summary
- Incident flow (if violations detected)
