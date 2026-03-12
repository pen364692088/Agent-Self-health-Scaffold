# PILOT_SOAK_REPORT

## Soak Window
- **Start**: 2026-03-08T18:00:00Z
- **Current**: 2026-03-08T18:05:00Z
- **Duration**: Initial cycle only (full soak in progress)

## Observations

### Capability Status
- Total checked: 6
- Healthy: 1 (recovery_summary_generation)
- Missing: 4 (heartbeat, callback, health_summary, incident)
- Degraded: 1 (mailbox - stuck with no_progress)

### Incidents Generated
- Total: 5 capability incidents
- Critical: 1 (heartbeat missing)
- High: 3 (callback, mailbox, incident)
- Medium: 1 (health_summary)

### Proposals Generated
- Total: 4
- Deduped: 1
- Cooldown active: 0

### Gate Status
- Gate A: PASS
- Gate B: PASS
- Gate C: PASS

### Main Loop Impact
- Scheduler runs completed without error
- No timeout or budget exceeded
- Lock contention: none
- Execution time: < 1s for full cycle

## Storm Detection
- Incident storm: NO (< 10 incidents in 1h)
- Proposal storm: NO (< 5 proposals in 6h)
- Summary storm: NO

## Noise Evaluation
- Incident dedup: Working
- Proposal dedup: Working (1 suppressed)
- Summary frequency: Appropriate (hourly)

## Findings
1. Most capabilities missing due to no worker status files
2. Forgetting guard correctly detected missing capabilities
3. Proposals generated appropriately for high-severity issues
4. Gate validates correctly

## Recommendations
1. Ensure workers output status files to artifacts/self_health/state/
2. Consider reducing capability check frequency for missing items
3. Monitor for incident/proposal storms over next 24h
