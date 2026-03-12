# PILOT_SOAK_POLICY

## Purpose
Define soak validation parameters for pilot instance.

## Soak Window
- **Duration**: 24 hours
- **Start**: 2026-03-08T18:00:00Z
- **End**: 2026-03-09T18:00:00Z

## Observation Schedule
| Time | Check Type |
|------|------------|
| Hourly | Quick capability check |
| Every 6h | Full capability check + forgetting guard |
| Every 1h | Summary generation |
| Every 6h | Gate validation |

## Metrics Collection
- scheduler_runs_total
- capability_healthy_count
- capability_degraded_count
- capability_missing_count
- incident_total
- proposal_total
- deduped_proposal_count
- main_loop_delay_ms

## Success Criteria
- No incident storm (>10 same-type incidents in 1h)
- No proposal storm (>5 same-type proposals in 6h)
- Main loop delay < 500ms
- Gate A/B/C all PASS

## Failure Criteria
- Main loop crash
- Infinite recursion detected
- Execution budget exceeded 3+ times
- Incident/proposal storm detected

## Reporting
- Soak report generated at end of window
- Final verdict based on metrics
- Rollout recommendation based on verdict
