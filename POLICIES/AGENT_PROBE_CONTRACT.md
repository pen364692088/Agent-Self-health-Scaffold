# AGENT_PROBE_CONTRACT

## Purpose
Provide one minimal, shared contract for component probes used by verified recovery.

## Required Fields
- `probe_name`
- `component`
- `status`
- `observed_at`
- `evidence`
- `metrics`
- `failure_indicators`
- `recoverability_hint`

## Status Vocabulary
Allowed component probe statuses:
- `ok`
- `warning`
- `error`
- `failed`
- `unknown`

## Recoverability Hint
Allowed values:
- `none`
- `rerun_health_check`
- `restart_worker`
- `restart_service`
- `needs_human_attention`

## Rules
1. Every probe must emit machine-readable JSON.
2. `failure_indicators` must be explicit, not implied by prose.
3. `evidence` should preserve raw facts used for judgment.
4. Component-specific probes may add fields, but the core contract must remain stable.
