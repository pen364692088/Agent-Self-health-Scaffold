# AGENT_MAIN_LOOP_INTEGRATION

## Purpose
Define how self-health integrates into OpenClaw main loop for continuous operation.

## Core Principle
Tools should run continuously and automatically, not manually.

## Trigger Modes
- `quick_check`: Light capability verification (every heartbeat cycle)
- `full_check`: Complete verification including forgetting guard (every N cycles)
- `summary_refresh`: Generate summaries (every N hours)

## Frequencies
| Task | Quick Mode | Full Mode |
|------|-----------|-----------|
| capability_check | every cycle | every 6 cycles |
| forgetting_guard | every 6 cycles | every 12 cycles |
| capability_summary | every 1h | every 6h |
| proposal_summary | every 1h | every 6h |
| recovery_summary | every 1h | every 6h |

## Safety Contract
1. Failures MUST NOT crash main loop
2. No infinite recursion (summary cannot trigger summary)
3. No incident/proposal storms (dedup + cooldown)
4. Single-run lock per task type
5. Execution budget: max 30s per quick check, 120s per full check

## Reentry Protection
- Each task type has a lock file
- Lock includes: task_type, started_at, pid
- Stale lock (>5min) can be cleared
- Concurrent runs are blocked, not queued

## Error Handling
- Soft failure: log and continue
- Hard failure: escalate to incident
- Never throw uncaught exception in main loop
