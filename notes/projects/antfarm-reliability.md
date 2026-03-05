# Project: Antfarm Reliability & Recovery

## Status
Active

## Progress
- Identified recovery gap: stalled runs could end up cancelled, which blocks `workflow resume`.
- Patched local Antfarm Medic logic to mark stalled runs as `failed` for resumable recovery.
- Added manager-side runbook rule: on Medic alert, resume first; stop only when abandoning.

## Current baseline
- Stall handling target behavior: `running` → `failed` (resumable)
- Preferred operator action: `workflow resume <run-id>`
- Avoided path: `workflow stop` unless explicitly abandoning run

## Next milestone
- Validate on a real stalled run that resume continues from failed step without replaying completed stories.
