# Materialized State v0 — Conflict Rules

## Purpose

This document freezes conservative conflict handling for `materialized_state` v0.

Primary rule:

> When in doubt, degrade conservatively: empty value + warning.

---

## Source Priority

```text
canonical-derived
> continuity-derived
> advisory-only
> summary-like
```

Where:

- canonical-derived = future ledger / run truth
- continuity-derived = `SESSION-STATE.md`
- advisory-only = `working-buffer.md`
- summary-like = handoff / capsule / summary / distill

---

## Conflict Rule 1 — canonical vs continuity

If canonical and continuity disagree:

- keep canonical value
- record warning
- keep `field_sources` pointing to canonical source

v0 note:
- canonical is not yet wired into the prototype, but the rule is frozen now

---

## Conflict Rule 2 — continuity vs advisory

If `SESSION-STATE.md` conflicts with `working-buffer.md` on any execution-facing meaning:

- keep continuity-derived execution field
- advisory-only text must not override it
- if needed, surface disagreement in `warnings`

Example:
- `SESSION-STATE.md` says phase = `INPROGRESS`
- `working-buffer.md` sounds like blocked or complete
- result: keep execution phase from `SESSION-STATE.md`

---

## Conflict Rule 3 — advisory-only fields cannot promote themselves

If `working-buffer.md` contains text that looks like:

- completion claim
- blocker claim
- phase change
- child status claim

then v0 materializer must **not** promote that text into:

- `execution.phase`
- `execution.execution_status`
- `execution.blockers`
- `execution.active_children`

Instead:
- keep execution-facing fields unchanged
- optionally add warning in future versions

---

## Conflict Rule 4 — missing beats guessed

If a field cannot be safely derived from an explicit source pattern:

- leave it empty / unknown
- add warning
- never synthesize from vague nearby prose

Examples:
- no explicit objective header -> empty objective + warning
- no explicit uncertainty section -> empty uncertainties
- no active child machine-readable source -> empty active_children

---

## Conflict Rule 5 — summary-like artifacts are non-authoritative

If a summary-like artifact disagrees with continuity or canonical inputs:

- ignore summary-like value for v0 main derivation
- do not emit execution-facing override
- keep warning optional

v0 main input path does not consume summary-like artifacts at all.

---

## Conflict Rule 6 — provenance must remain explicit

Whenever a field is derived from a source:

- `field_sources` should record it when nontrivial
- warnings should explain missing or downgraded execution-facing fields

This keeps the derived view auditable.

---

## Conflict Rule 7 — no second live state

`materialized_state` output must not be treated as:

- a hand-maintained continuity file
- a write-back target for operators
- a replacement for `SESSION-STATE.md` / `working-buffer.md`

It remains generated output under `artifacts/` only.
