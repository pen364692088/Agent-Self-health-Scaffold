# Session Continuity Observability

**Version**: v1.1.1

---

## Key Metrics

### Recovery Metrics

| Metric | Description | Collection |
|--------|-------------|------------|
| recovery_success_count | Successful recoveries | session-start-recovery |
| recovery_uncertainty_count | Recoveries with uncertainty | session-start-recovery |
| recovery_failure_count | Failed recoveries | session-start-recovery |

### Conflict Metrics

| Metric | Description | Collection |
|--------|-------------|------------|
| conflict_resolution_count | Fields with conflicts | session-start-recovery |
| conflict_uncertain_count | Uncertain resolutions | session-start-recovery |

### Persistence Metrics

| Metric | Description | Collection |
|--------|-------------|------------|
| wal_append_count | WAL entries written | state-journal-append |
| handoff_trigger_count | Handoffs created | manual |

### Context Metrics

| Metric | Description | Collection |
|--------|-------------|------------|
| fallback_ratio_count | Fallback mode uses | pre-reply-guard |
| threshold_warning_count | 60-80% warnings | pre-reply-guard |
| threshold_critical_count | >80% criticals | pre-reply-guard |

---

## Health Check

### Quick Check
```bash
session-state-doctor
```

### Full Check
```bash
session-state-doctor --json
python scripts/run_session_continuity_checks.py --gate all
```

---

## Log Locations

| Log | Path |
|-----|------|
| WAL journal | state/wal/session_state_wal.jsonl |
| Recovery summary | artifacts/session_recovery/latest_recovery_summary.json |
| Health reports | artifacts/session_continuity/v1_1_1/ |

---

## Alert Thresholds

| Metric | Warning | Critical |
|--------|---------|----------|
| recovery_success_rate | < 95% | < 90% |
| uncertainty_rate | > 10% | > 20% |
| conflict_rate | > 10% | > 20% |
| WAL size | > 5MB | > 10MB |

---

## Recommended Actions

### On Warning
1. Check session-state-doctor output
2. Review recent recovery summaries
3. Monitor next few sessions

### On Critical
1. Switch to RECOVERY-ONLY mode
2. Investigate root cause
3. Consider rollback if needed