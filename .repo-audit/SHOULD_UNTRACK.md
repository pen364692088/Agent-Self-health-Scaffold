# SHOULD_UNTRACK.md

**Generated**: 2026-03-13
**Repository**: Agent-Self-health-Scaffold

## Summary
- **Total files to untrack**: ~2,187 (out of 3,871)
- **Primary categories**: Runtime artifacts, logs, caches, processed events

---

## Category 1: Logs (13 files)

### Rationale
Log files are machine-generated, contain runtime information, and grow over time. They should be generated locally and not shared.

### Files to untrack
```
logs/callback-auto-20260305.log
logs/callback-auto-20260306.log
logs/callback-worker.log
logs/event-queue-20260305.log
logs/event-queue-20260306.log
logs/policy_violations.jsonl
logs/route_guard_heartbeat.jsonl
logs/route_rebind_audit.jsonl
logs/s1-validator-daily.log
logs/s1-validator-hourly.log
logs/s1-validator-scan.log
logs/session-cleanup.log
logs/session_cleanup_20260309.log
```

### Impact: None - logs are regenerated on each run

---

## Category 2: Reports (77 files)

### Rationale
Generated reports are outputs from tool runs, not source material. They can be regenerated.

### Directories to untrack
- `reports/tool_doctor/` - Tool doctor outputs
- `reports/schema_validation/` - Validation outputs
- `reports/smart_stable/` - Comparison reports
- `reports/orchestrator/` - Orchestrator logs
- `reports/subtasks/` - Subtask processing

### Impact: None - reports are regenerated

---

## Category 3: Processed Events (59 files)

### Rationale
`events/processed/` contains already-handled events. These are transient runtime state.

### Directory to untrack
```
events/processed/
```

### Impact: None - processed events are historical artifacts

---

## Category 4: Mailbox (15 files)

### Rationale
`mailbox/out/` contains outgoing messages that have been delivered. These are runtime artifacts.

### Directory to untrack
```
mailbox/out/
```

### Impact: None - mailbox is transient

---

## Category 5: Artifacts - Runtime Generated (~2,013 files)

### Rationale
The `artifacts/` directory contains extensive runtime-generated content including:
- Context compression validation samples
- OpenViking archive entries
- Self-health recovery snapshots
- Capability incidents and proposals
- Gate reports and probe results

### Subdirectories to untrack
```
artifacts/context_compression/sessions/
artifacts/context_compression/validation/samples/
artifacts/context_compression/validation/reports/
artifacts/openviking/archive/
artifacts/openviking/ops_runs/
artifacts/self_health/state/
artifacts/self_health/incidents/
artifacts/self_health/proposals/
artifacts/self_health/probes/
artifacts/self_health/probe_tests/
artifacts/self_health/runtime/
artifacts/self_health/coverage_audit/soak/
artifacts/self_health/locks/
artifacts/self_health/gate_reports/
artifacts/self_health/capability_incidents/
artifacts/openviking-l2-fix/
artifacts/execution_policy/
artifacts/monitoring/
artifacts/health_audit/
artifacts/receipts/
artifacts/session_recovery/
artifacts/session_reuse/incidents/
artifacts/session_reuse/probe/
```

### Files to KEEP tracked in artifacts/
- `artifacts/*/IMPLEMENTATION_SUMMARY.md` - Documentation
- `artifacts/*/README.md` - Documentation
- `artifacts/shared_knowledge/` - Shared knowledge base

### Impact: Low - artifacts are regenerable outputs

---

## Category 6: Memory Runtime State (~20 files)

### Rationale
Memory `.json` and `.jsonl` files are local caches and indices.

### Files to untrack
```
memory/.bootstrap_state.json
memory/.dedup_cache.json
memory/daily_summaries.jsonl
memory/entry_state.json
memory/events.log
memory/regression_cron.log
memory/regression_report.json
memory/reports/daily/
memory/review_queue.json
memory/sweeper_stats.json
memory/sweeper_stats_prev.json
memory/tests/retrieval_regression.json
memory/tuning_recommendations.json
memory/use_link_audit.json
memory/golden_fixtures/
memory/.locks/
```

### Impact: None - these are local caches

---

## Category 7: State Directory (11 files)

### Rationale
`state/` contains runtime state that should be local.

### Directory to untrack
```
state/
```

### Impact: None - state is regenerated

---

## Category 8: Integration Traces (10 files)

### Rationale
Telegram traces contain conversation data and session IDs.

### Directory to untrack
```
integrations/openclaw/traces/
```

### Impact: None - traces are local logs

---

## Category 9: PID and Lock Files (9 files)

### Rationale
PID and lock files are machine-specific and should never be tracked.

### Files to untrack
```
.callback-worker.pid
.workflow.lock
artifacts/self_health/locks/full.lock
artifacts/self_health/locks/gate.lock
artifacts/self_health/locks/quick.lock
memory/.locks/sweeper.lock
reports/subtasks/.inbox.lock
state/locks/continuity_events.lock
```

### Impact: None - these are temporary locks

---

## Category 10: Session Archives (2 files)

### Rationale
Session archives are historical session data.

### Directory to untrack
```
session-archives/
```

### Impact: None - archives are local history

---

## Category 11: Other Runtime Files

### Files to untrack
```
.last_session_id
output.txt
openclawnode-autostart.log
antfarm-dashboard.log
```

### Impact: None

---

## Total Summary

| Category | Count | Action |
|----------|-------|--------|
| Logs | 13 | `git rm -r --cached logs/` |
| Reports | 77 | `git rm -r --cached reports/` |
| Events processed | 59 | `git rm -r --cached events/processed/` |
| Mailbox | 15 | `git rm -r --cached mailbox/out/` |
| Artifacts runtime | ~2,000 | Selective removal |
| Memory runtime | 20 | Selective removal |
| State | 11 | `git rm -r --cached state/` |
| Traces | 10 | `git rm -r --cached integrations/openclaw/traces/` |
| PID/Lock | 9 | Individual removal |
| Session archives | 2 | `git rm -r --cached session-archives/` |
| Other | 4 | Individual removal |
| **Total** | **~2,187** | |
