# Materialized State v0 — Field Mapping

## Purpose

This document freezes the v0 field contract for `materialized_state`.

It distinguishes three field classes:

1. **canonical-derived**
2. **continuity-derived**
3. **advisory-only**

This split is mandatory.

---

## Class 1 — canonical-derived

These are execution-facing fields.

Rule:
- future source of truth = ledger / run truth
- in v0 prototype, canonical may be absent
- if canonical is absent, conservative fallback to `SESSION-STATE.md` is allowed
- advisory-only sources must never override these fields

| Field | v0 Source | Future Primary Source | Fallback | Notes |
|---|---|---|---|---|
| `identity.task_id` | empty | ledger/run truth | none | keep empty if unavailable |
| `identity.run_id` | empty | ledger/run truth | none | keep empty if unavailable |
| `identity.branch` | `SESSION-STATE.md` | ledger/run truth / repo truth | empty | continuity-derived fallback |
| `execution.objective` | `SESSION-STATE.md` | ledger/run truth | empty + warning | never guess from summaries |
| `execution.phase` | `SESSION-STATE.md` | ledger/run truth | `unknown` + warning | execution-facing |
| `execution.current_step` | `SESSION-STATE.md` next-step first item | ledger/run truth | empty | conservative derivation only |
| `execution.execution_status` | derived from phase/blocker | ledger/run truth | `unknown` | must remain conservative |
| `execution.blockers` | `SESSION-STATE.md` | ledger/run truth | empty list | no guess from free text |
| `execution.active_children` | empty in v0 | ledger/run truth / receipts | empty list | do not synthesize |
| `execution.verification.pending` | empty in v0 | ledger/run truth / verifier | empty list | do not infer |
| `execution.key_files` | `SESSION-STATE.md` | ledger/run truth / repo evidence | empty list | safe continuity field |

---

## Class 2 — continuity-derived

These are bridge fields sourced from live continuity documents.

Rule:
- continuity-derived fields may populate materialized_state when canonical truth is absent or not yet wired
- they still remain lower authority than future canonical truth

| Field | Source | Allowed? | Notes |
|---|---|---:|---|
| `execution.objective` | `SESSION-STATE.md` | yes | temporary bridge input |
| `execution.phase` | `SESSION-STATE.md` | yes | temporary bridge input |
| `execution.current_step` | `SESSION-STATE.md` | yes | conservative derivation |
| `execution.blockers` | `SESSION-STATE.md` | yes | only explicit blocker section |
| `execution.key_files` | `SESSION-STATE.md` | yes | explicit key files section |
| `identity.branch` | `SESSION-STATE.md` | yes | allowed bridge field |

---

## Class 3 — advisory-only

These fields are reasoning support only.

Rule:
- advisory-only fields may help prompt assembly later
- advisory-only fields must never overwrite execution-facing fields
- advisory-only fields must remain safe to drop

| Field | Source | Notes |
|---|---|---|
| `reasoning.current_focus` | `working-buffer.md` | current focus only |
| `reasoning.immediate_plan` | `working-buffer.md` | direct list extraction only |
| `reasoning.reasoning_targets` | empty in v0 | do not aggressively infer yet |
| `reasoning.uncertainties` | `working-buffer.md` | explicit uncertainty section only |
| `reasoning.priority_artifact_refs` | generated | refs only, not authority |

---

## Forbidden Inputs for v0 Main Input Path

The following are forbidden as primary inputs in v0:

- `handoff.md`
- capsule files
- summary outputs
- distill outputs
- archive outputs

They may appear in future low-trust auxiliary channels, but not in the v0 primary derivation path.

---

## Override Rule

### Allowed
- canonical-derived may override continuity-derived
- continuity-derived may fill canonical gaps only when canonical is absent
- advisory-only may fill advisory-only fields

### Forbidden
- advisory-only overriding canonical-derived fields
- summary-like sources overriding continuity-derived or canonical-derived fields
- guessed values replacing missing execution-facing fields

---

## Conservative Degradation Rule

When a required execution-facing field cannot be derived safely:

- emit empty string / empty list / `unknown`
- add warning
- do not guess from nearby prose

That rule is preferred over “looking helpful but wrong.”
