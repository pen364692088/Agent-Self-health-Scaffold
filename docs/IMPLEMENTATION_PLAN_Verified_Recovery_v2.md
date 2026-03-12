# Implementation Plan - Verified Recovery v2

## Intent
Turn the self-health scaffold into a verified recovery system for key operational paths.

The central engineering rule is simple:

> Do not widen coverage faster than you improve recovery truth.

---

## Plan Overview

### Phase P0 - Recovery kernel first
Build the semantics and evidence model before attaching more components.

Work items:
- recovery lifecycle policy
- before/after snapshots
- verdict engine

Expected outcome:
- all future recovery actions share one state model
- no action can claim success without evidence
- insufficient evidence is explicit

Risks if skipped:
- fake recovery success
- action logging without outcome truth
- hard-to-debug repair loops

---

### Phase P1 - Attach only critical paths
Integrate the small number of components that represent workflow survival.

Priority order:
1. heartbeat
2. callback-worker
3. mailbox-worker
4. systemd services

Engineering note:
This phase should favor component-specific probes over generic host-level telemetry.

Expected outcome:
- real workflow failures become visible
- incidents have evidence tied to critical chain health
- recovery actions can be validated against the right targets

---

### Phase P2 - Replace placeholder actions with real recovery actions
Only add a few Level A actions, but make them trustworthy.

Initial target actions:
- restart_service
- restart_worker
- clear_stale_lock
- rerun_health_check
- rotate_logs

Action requirements:
- idempotent
- whitelisted
- bounded retry
- cooldown protected
- evidence producing
- verdict producing

Expected outcome:
- self-heal stops being a shell around intent
- recovery attempts become measurable interventions

---

### Phase P3 - Add storm controls before scaling further
Prevent the system from harming itself under repeated faults.

Required mechanisms:
- incident fingerprint
- dedup window
- retry ceiling
- cooldown
- escalation threshold

Expected outcome:
- no alert spam for the same fault
- no infinite self-heal loops
- cleaner audit trail
- clearer operator attention path

---

### Phase P4 - Prove the system under fault injection
Do not stop at smoke tests.

Minimum test matrix:
- heartbeat stale
- worker down
- service failed
- stale lock
- repeated same incident
- unchanged verdict case
- degraded verdict case

Expected outcome:
- recovery logic validated against controlled failures
- no need to rely on narrative claims about resilience

---

## Suggested Implementation Sequence

### Milestone 1
- VR2-001
- VR2-002
- VR2-003

Ship condition:
- a single Level A action can produce full recovery lifecycle evidence

### Milestone 2
- VR2-004
- VR2-005
- VR2-006

Ship condition:
- critical path probes produce incidents and comparable snapshots

### Milestone 3
- VR2-007
- VR2-008

Ship condition:
- at least 3 real Level A actions run with whitelist + cooldown + verdict

### Milestone 4
- VR2-009
- VR2-010

Ship condition:
- repeated failure no longer causes repair storms

### Milestone 5
- VR2-011
- VR2-012
- VR2-013

Ship condition:
- fault-injection coverage exists
- gates consume recovery truth
- operator summary is generated

---

## Architecture Notes

### Recovery record must be first-class
Recommended fields:
- `recovery_id`
- `incident_id`
- `component`
- `action`
- `started_at`
- `snapshot_before_path`
- `snapshot_after_path`
- `verdict`
- `rollback_needed`
- `escalation_state`
- `attempt_number`
- `cooldown_applied`

### Verdict rules must be deterministic
No free-form subjective completion criteria.

Prefer:
- status transitions
- timestamp freshness
- queue depth deltas
- process/service state transitions
- explicit failure indicators

Avoid:
- vague prose summaries standing in for recovery truth

### Insufficient evidence is a real outcome
Do not collapse `insufficient_evidence` into success.

This protects the system from optimistic false positives.

---

## Operational Boundaries
Still forbidden in v2:
- auto Level B execution
- auto Level C execution
- prompt/router/governance mutation
- destructive actions without explicit human direction
- unlimited retry behavior

---

## Success Criteria
v2 is successful if a human can inspect the system and answer, with evidence:
- what failed
- what recovery action ran
- what the before/after state was
- whether it recovered, stayed unchanged, or degraded
- whether further recovery was suppressed or escalated

If those answers are not explicit, the system is not yet Verified Recovery.
