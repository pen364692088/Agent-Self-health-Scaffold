# Verified Recovery Summary

**Window**: Last 24 hours
**Generated**: 2026-03-11T15:18:16.706342+00:00

## Actions Overview

| Metric | Count |
|--------|-------|
| actions_total | 1 |
| recovery_actions_total | 0 |
| evidence_actions_total | 0 |
| maintenance_actions_total | 1 |
| blocked_by_precondition_total | 0 |

## Verdict Distribution

| Verdict | Count |
|---------|-------|
| recovered | 0 |
| unchanged | 1 |
| degraded | 0 |
| insufficient_evidence | 0 |

## Recovery Effectiveness

- **direct_recovery_total**: 0
- **recovery_effective_rate**: 0.00%

## Risk & Stability

- escalated_total: 1
- cooldown_block_total: 0
- retry_ceiling_hit_total: 0

## Top Flaky Components

_No flaky components in this window._

## clear_stale_lock Details

- lock_removed: 0
- downstream_progress_resumed: 0
- recovery_confirmed: 0

## Notes

- `evidence_actions_total` are excluded from recovery effectiveness.
- `direct_recovery_total` counts only actions that led to `recovered` verdict.
- `clear_stale_lock` details separate lock removal from downstream recovery.