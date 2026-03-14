# Continuity Live Source Policy

## Current frozen live continuity sources

The only live continuity sources are:

- `SESSION-STATE.md`
- `working-buffer.md`

## Non-live / archive-only continuity files

The following files are **not** live continuity sources and must not be read by active continuity tools as authoritative state:

- `memory/SESSION-STATE.md`
- `memory/working-buffer.md`

They are retained only as:

- archive
- historical reference
- stop-write candidates

## Explicit authority rule

The following must not be treated as authoritative truth for continuity or recovery state:

- `handoff.md`
- capsule files
- summary outputs
- distill outputs
- `memory/SESSION-STATE.md`
- `memory/working-buffer.md`

## Guardrail

Active continuity tools must read live continuity state only from:

- root `SESSION-STATE.md`
- root `working-buffer.md`

Any reintroduction of `memory/*` as a live continuity source is a policy regression.
