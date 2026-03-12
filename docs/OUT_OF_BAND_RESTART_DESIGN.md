# OUT_OF_BAND_RESTART_DESIGN.md

## Problem
Restarting gateway from the current agent exec chain can terminate the host process and lose the active tool/result path.

## Design rule
Restart is modeled as an **intent**, not an immediate in-band exec.

## Flow
1. agent proposes restart intent
2. policy validates restart conditions
3. out-of-band executor performs restart externally
4. boot hook emits `PROCESS_RESTARTED`
5. recovery orchestrator scans unfinished runs and resumes eligible work

## Guarantees
- no self-termination in the same exec chain
- restart becomes observable, auditable, retryable
- post-restart recovery is automatic
