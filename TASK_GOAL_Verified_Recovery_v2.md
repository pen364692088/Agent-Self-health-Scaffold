# TASK_GOAL_Verified_Recovery_v2

## Background
Current state is **Agent Self-Health Scaffold v1**.

v1 proves the scaffold is real:
- health state exists
- incident flow exists
- self-heal boundary exists
- proposal-only safety rail exists
- audit trail exists

But v1 does **not** yet prove that recovery actually works under real faults.

---

## Phase Positioning

This phase is:
- **Verified Recovery v2**

This phase is not:
- broad monitoring expansion for its own sake
- automatic Level B/C execution
- a claim that the system is already resilient under repeated failure

---

## Core Goal
Upgrade self-health from:
- can observe
- can report
- can execute limited actions

To:
- can recover key paths
- can verify whether recovery succeeded
- can escalate safely when recovery did not succeed

---

## Hard Constraint
Do **not** expand many new checks before the recovery verifier is stable and fault-injection-tested.

Reason:
More probes without verified recovery only creates the illusion of progress.

Priority order:
1. recovery lifecycle
2. before/after evidence
3. verdict engine
4. key-path coverage
5. real Level A actions
6. storm prevention
7. fault-injection + gates + reporting

---

## Non-Goals
v2 must **not** do the following:
- auto-execute Level B actions
- auto-execute Level C actions
- mutate core governance files automatically
- rewrite router / prompt / memory policy automatically
- perform destructive actions automatically
- optimize for wide component coverage ahead of recovery truthfulness

---

## Execution Order

### P0 - Recovery Closure Kernel

#### VR2-001 Recovery lifecycle model
**Goal**: every recovery attempt becomes a first-class lifecycle, not a one-off action.

**Deliverables**:
- `POLICIES/AGENT_RECOVERY_LIFECYCLE.md`
- recovery record schema extension
- state flow definition:
  - `detected -> snapshot_before -> action -> snapshot_after -> verdict -> escalate/archive`

**Acceptance**:
- every self-heal has a unique `recovery_id`
- before/action/after/verdict are persisted
- audit entries can reconstruct one complete recovery chain

#### VR2-002 Before/after snapshot mechanism
**Goal**: create machine-readable state baselines around each recovery action.

**Deliverables**:
- `tools/agent-health-snapshot`
- snapshot schema covering at least:
  - component
  - status
  - key metrics
  - probe timestamp
  - failure indicators
- `artifacts/self_health/state/recovery_snapshots/`

**Acceptance**:
- every Level A action generates before + after snapshots
- snapshots are machine-readable JSON
- missing probe evidence yields `insufficient_evidence`, never silent success

#### VR2-003 Verdict engine
**Goal**: automatically decide whether recovery actually worked.

**Deliverables**:
- `tools/agent-recovery-verify`
- verdict enum:
  - `recovered`
  - `unchanged`
  - `degraded`
  - `insufficient_evidence`
- `rollback_needed` decision field

**Acceptance**:
- every Level A recovery attempt produces a verdict
- verdict rules are deterministic and explainable
- `unchanged` and `degraded` trigger escalation logic

---

### P1 - Key Path Coverage

#### VR2-004 Heartbeat coverage
**Goal**: model heartbeat as a real health component, not generic liveness.

**Deliverables**:
- heartbeat probe
- metrics:
  - `last_seen`
  - `lag`
  - `consecutive_failures`
  - `last_successful_cycle`
- fault rules for stale / delayed / repeatedly failed heartbeat

**Acceptance**:
- stopped heartbeat is detected
- excessive lag is detected
- repeated failures are detectable and evidence-backed

#### VR2-005 Callback-worker / mailbox-worker coverage
**Goal**: cover the critical workflow chain before wider metrics.

**Deliverables**:
- callback-worker probe
- mailbox-worker probe
- stuck / backlog / crash / no-output detection

**Acceptance**:
- distinguish “process alive but chain stuck” from “process dead”
- emit component-level incidents
- outputs are usable by Level A recovery verification

#### VR2-006 systemd service health coverage
**Goal**: upgrade service truth from script heuristics to system service state.

**Deliverables**:
- systemd adapter
- service state probe
- restart result parser

**Acceptance**:
- support at least `active` / `failed` / `restarting`
- restart can be compared before/after
- service evidence flows into incident + audit records

---

### P2 - Real Level A Actions

#### VR2-007 restart_service / restart_worker
**Goal**: replace placeholders with real verified recovery actions.

**Deliverables**:
- `tools/agent-self-heal` support for:
  - `restart_service`
  - `restart_worker`
- whitelist configuration
- cooldown + max retry

**Acceptance**:
- only whitelisted targets can be touched
- repeated triggers inside cooldown are blocked
- execution must automatically run verdict verification

#### VR2-008 clear_stale_lock / rerun_health_check / rotate_logs
**Goal**: add a small number of low-risk, high-value actions.

**Deliverables**:
- `clear_stale_lock`
- `rerun_health_check`
- `rotate_logs`
- precondition / postcondition definition for each

**Acceptance**:
- action refuses execution if preconditions are not met
- result is recorded in recovery log
- postconditions are actually checked

---

### P3 - Anti-Storm Controls

#### VR2-009 Incident fingerprint + dedup
**Goal**: prevent the same fault from flooding incidents.

**Deliverables**:
- fingerprint rules
- dedup window
- merge / suppress policy

**Acceptance**:
- same fault does not spam incident files repeatedly
- suppressed events still appear in audit
- `suppressed_count` is observable

#### VR2-010 Retry ceiling + cooldown + escalation
**Goal**: stop repair loops from turning into recovery storms.

**Deliverables**:
- retry ceiling
- cooldown window
- escalation threshold
- escalation path:
  - `local_recoverable`
  - `needs_proposal`
  - `needs_human_attention`

**Acceptance**:
- repeated failure eventually stops auto-recovery
- system escalates instead of looping forever
- no unlimited retry behavior

---

### P4 - Testing, Gates, Reporting

#### VR2-011 Fault injection tests
**Goal**: prove recovery under controlled fault scenarios.

**Deliverables**:
- `tests/test_agent_verified_recovery.py`
- scenarios including at least:
  - heartbeat stale
  - worker down
  - systemd failed
  - stale lock
  - repeated same incident

**Acceptance**:
- at least 5 fault-injection scenarios
- each verifies before / action / after / verdict
- at least one `unchanged` and one `degraded` branch are explicitly tested

#### VR2-012 Gate A / B / C deep integration
**Goal**: make recovery part of governance, not an outer utility.

**Deliverables**:
- Gate A: contract / whitelist / boundary validation
- Gate B: key-path E2E verification
- Gate C: preflight + doctor + policy consistency

**Acceptance**:
- policy / whitelist / cooldown violations block execution
- gate outputs reflect recovery verdicts
- closeout remains compatible with existing verify-and-close flow

#### VR2-013 Recovery summary and operator reporting
**Goal**: show whether the system actually recovers and where it flakes.

**Deliverables**:
- `artifacts/self_health/VERIFIED_RECOVERY_SUMMARY.md`
- summary fields:
  - incidents total
  - deduped incidents
  - recovery attempts
  - recovered rate
  - unchanged rate
  - degraded count
  - escalated count
  - top flaky components

**Acceptance**:
- generated automatically from logs/audit data
- easy to inspect by humans
- recovery effectiveness is visible, not implied

---

## Definition of Done
Verified Recovery v2 is complete only if all of the following are true:

1. heartbeat, callback-worker, mailbox-worker, and systemd service health are covered
2. at least 3 real Level A actions are executable and verifiable
3. every recovery attempt has before / action / after / verdict / rollback_needed
4. dedup, retry ceiling, cooldown, and escalation are implemented
5. fault-injection tests exist and pass
6. Gate A/B/C integration is in place
7. recovery effectiveness summary is generated
8. v1 safety boundaries remain intact

---

## One-Line Summary
v1 proves the scaffold is right.
v2 must prove the recovery is real.
