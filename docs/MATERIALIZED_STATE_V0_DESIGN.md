# Materialized State v0 — Minimal Executable Design

## Purpose

`materialized_state` is a **derived, prompt-ready state view**.

It is **not a new authoritative truth source**.

Its job is:

- take higher-trust execution/continuity inputs
- normalize them into a compact, predictable structure
- provide a stable input contract for future prompt assembly and recovery assistance

Its job is **not**:

- to become a new authoritative truth source
- to replace ledger / run truth
- to become a hand-written state file
- to replace `SESSION-STATE.md` or `working-buffer.md` as live bridge files before the main chain is migrated

---

## Authority Rule

Frozen usage order for Phase 2 design:

```text
Ledger / Run Truth
> materialized_state
> SESSION-STATE.md
> working-buffer.md
> summary-like artifacts
```

Where:

- **Ledger / Run Truth** = highest authority, canonical execution truth
- **materialized_state** = derived prompt-ready state
- **SESSION-STATE.md** = live continuity bridge state
- **working-buffer.md** = live working-memory / reasoning-focus bridge
- **summary-like artifacts** = handoff / capsule / summary / distill / archive outputs

### Non-negotiable

`materialized_state` must never:

1. override ledger / run truth
2. be edited manually as if it were source-of-truth
3. become a second live continuity file
4. be filled from summary-like artifacts when higher-trust sources exist

---

## Design Goal

Provide the minimum stable structure needed for future state-driven prompt assembly without changing the current prompt/compression/archive mainline yet.

That means v0 should:

- be small
- be reconstructable
- be explicit about source provenance
- separate authoritative-derived fields from advisory fields
- support missing data gracefully

---

## What v0 Contains

`materialized_state` v0 contains only five groups:

1. **identity**
2. **objective and execution position**
3. **continuity bridge state**
4. **reasoning focus**
5. **provenance + warnings**

It intentionally does **not** include:

- full transcript summaries
- freeform archive distill
- full capsule content
- tool stdout/stderr blobs
- child completion summaries

Those belong elsewhere.

---

## Input Source Priority

## Tier 0 — Canonical (highest authority)

Use when available:

- Task Ledger / Run Ledger
- durable execution state
- reconciliation output
- machine-readable child/task receipts

These sources define:

- task / run identity
- current phase
- current step pointer
- active blockers
- active child runs
- verification status
- true execution status

## Tier 1 — Live bridge continuity state

Use when Tier 0 is absent or incomplete:

- `SESSION-STATE.md`

This may provide:

- objective
- phase
- branch
- blocker
- next step / next actions
- key files

But its data is still lower authority than ledger/run truth.

## Tier 2 — Live working memory

Use only for reasoning focus and advisory context:

- `working-buffer.md`

This may provide:

- current focus
- immediate plan
- uncertainty notes
- reasoning targets
- local constraints phrasing

It must not define execution truth.

## Tier 3 — Summary-like artifacts (lowest authority)

Allowed only as auxiliary hints when higher tiers are missing:

- `handoff.md`
- session capsules
- summary outputs
- distill outputs

These may contribute:

- warnings
- optional hints
- recall candidates

They must not define:

- run status
- task completion
- phase truth
- step truth
- child completion truth

---

## Bridge Relationship with Existing Files

## Relationship to `SESSION-STATE.md`

`SESSION-STATE.md` remains the current live continuity bridge file.

In v0 design:

- `materialized_state` may read from it
- `materialized_state` does not replace it yet
- `materialized_state` does not write back into it
- `materialized_state` should record which fields were sourced from it

## Relationship to `working-buffer.md`

`working-buffer.md` remains the current live working-memory bridge file.

In v0 design:

- `materialized_state` may read current focus / plan / uncertainty from it
- these fields must be marked advisory
- these fields must never override canonical execution fields

## Relationship to `handoff.md`

`handoff.md` is auxiliary only.

In v0 design:

- it can be listed as a low-trust hint source
- it should not populate canonical execution fields if a higher-trust source exists

---

## Field Boundary Rules

## Canonical-derived fields

These must come only from ledger/run truth, or fall back to `SESSION-STATE.md` if canonical truth is absent:

- `task_id`
- `run_id`
- `objective`
- `phase`
- `current_step`
- `blockers`
- `active_children`
- `verification`
- `execution_status`

## Advisory-only fields

These may be populated from `working-buffer.md`:

- `current_focus`
- `reasoning_targets`
- `immediate_plan`
- `uncertainties`
- `priority_artifact_refs`

## Provenance-only fields

These exist to keep derivation auditable:

- `sources`
- `field_sources`
- `warnings`
- `derived_at`
- `schema_version`

---

## v0 Derivation Rules

### Rule 1
If ledger/run truth exists for a field, use it.

### Rule 2
If canonical truth is absent, fall back to `SESSION-STATE.md` for continuity bridge fields.

### Rule 3
Use `working-buffer.md` only for advisory reasoning-focus fields.

### Rule 4
Never upgrade summary-like artifacts into canonical execution fields.

### Rule 5
Every nontrivial field should be traceable through `field_sources`.

### Rule 6
If two higher-priority inputs conflict, keep the higher one and emit a warning.

---

## Output Contract

`materialized_state` v0 should be serializable JSON and safe to regenerate at any time.

It should be treated as:

- ephemeral derived state
- cacheable
- replaceable
- auditable

It should **not** be treated as:

- a hand-maintained markdown truth file
- a durable write target for user edits
- a long-term archive document

---

## Suggested Storage Form

Recommended future path:

- `artifacts/materialized_state/latest.json`

Optional future extension:

- `artifacts/materialized_state/<run_or_session_id>.json`

### Why artifacts/
Because this signals clearly that it is generated output, not a primary human-maintained continuity file.

---

## Minimal Generation Flow (future)

```text
ledger/run truth
 + SESSION-STATE.md
 + working-buffer.md
 + optional low-trust hints
 -> state materializer
 -> materialized_state.json
```

No write-back into continuity sources is required.

---

## v0 Implementation Boundary

This design intentionally does **not** require:

- prompt-assemble changes
- context-compress changes
- archive-with-distill changes
- distill-content changes
- continuity file migration

It is a design contract only.

---

## Acceptance Criteria for v0 Design

1. `materialized_state` is clearly documented as derived, not authoritative.
2. Input source priority is explicit.
3. Canonical-derived vs advisory-only field boundaries are explicit.
4. Bridge relationship with `SESSION-STATE.md` / `working-buffer.md` is explicit.
5. Output can be represented by a small JSON schema.
6. Example instances are enough for future implementation and review.
