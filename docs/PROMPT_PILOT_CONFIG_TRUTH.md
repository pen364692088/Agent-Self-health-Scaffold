# Prompt Pilot Config Truth

**Generated**: 2026-03-14
**Purpose**: Clarify source-of-truth relationships in prompt_pilot.json

---

## The Problem

Prior to this document, `config/prompt_pilot.json` had two fields representing sample count:
- `effective_sample_count` (root level)
- `metrics.effective_samples` (nested)

This created ambiguity about which is authoritative for gate decisions.

---

## Resolution

### Authoritative Field

**`metrics.effective_samples`** is the AUTHORITATIVE source for:
- Gate decisions (Shadow → Pilot, Pilot → Decision)
- Status display
- Stop condition checks

### Derived Field

**`effective_sample_count`** (root level) is DERIVED from `metrics.effective_samples` for:
- Display convenience
- Quick reference
- Backward compatibility

### Why This Matters

1. **Gate decisions** use `metrics.effective_samples`
2. **Runner updates** write to `metrics.effective_samples`
3. **Display tools** can use either (they should be synchronized)

---

## Field Categories

### Authoritative (Gate Decisions)

| Field | Location | Used For |
|-------|----------|----------|
| `metrics.effective_samples` | metrics object | Gate threshold check |
| `metrics.avg_match_rate` | metrics object | Stop condition check |
| `metrics.avg_conflict_rate` | metrics object | Stop condition check |
| `metrics.avg_fallback_rate` | metrics object | Stop condition check |
| `metrics.avg_provenance_completeness` | metrics object | Stop condition check |

### Configuration (Static)

| Field | Location | Purpose |
|-------|----------|---------|
| `pilot_enabled` | root | Master switch |
| `pilot_mode` | root | Current mode (shadow/pilot) |
| `dual_gate.*.min_samples` | dual_gate object | Gate threshold |
| `stop_conditions.*` | stop_conditions object | Violation thresholds |
| `allowed_events` | root | Task type whitelist |

### Derived/Display (Not for decisions)

| Field | Location | Source |
|-------|----------|--------|
| `effective_sample_count` | root | Derived from metrics.effective_samples |
| `pilot_start_time` | root | Set on enable, not updated |
| `metrics.avg_*` | metrics object | Running averages |

### Operational (Runtime)

| Field | Location | Purpose |
|-------|----------|---------|
| `pilot_start_time` | root | Track observation period |
| `metrics.total_calls` | metrics object | Total invocation count |
| `metrics.recent_stop_condition_hits` | metrics object | Audit trail |

---

## Update Rules

### When Runner Updates Metrics

```
1. Increment metrics.total_calls
2. If effective sample: increment metrics.effective_samples
3. Update running averages (avg_match_rate, etc.)
4. Sync effective_sample_count = metrics.effective_samples
```

### When Gate Check Runs

```
1. Read metrics.effective_samples (NOT effective_sample_count)
2. Compare against dual_gate.shadow_to_pilot.min_samples
3. Check stop_conditions against metrics.avg_* values
4. Return eligibility status
```

### When Status Displays

```
1. Show metrics.effective_samples as "Effective Samples"
2. Can also show effective_sample_count (should match)
3. If mismatch: warn and use metrics.effective_samples
```

---

## Comments Added to Config

The updated `config/prompt_pilot.json` includes these clarifying comments:

```json
{
  "_comment_metrics": "=== METRICS (AUTHORITATIVE SOURCE) ===",
  "_comment_metrics_note": "metrics.effective_samples is the AUTHORITATIVE count for gate decisions",
  "_comment_display_note": "effective_sample_count at root level is DERIVED from metrics.effective_samples for display only",
  
  "metrics": {
    "effective_samples": 0  // <-- AUTHORITATIVE
  },
  
  "effective_sample_count": 0  // <-- DERIVED for display
}
```

---

## Verification

To verify synchronization:

```bash
# Check that both values match
jq '{effective_samples: .metrics.effective_samples, effective_sample_count: .effective_sample_count}' config/prompt_pilot.json

# Expected output:
# {
#   "effective_samples": 0,
#   "effective_sample_count": 0
# }
```

---

## File: docs/PROMPT_PILOT_CONFIG_TRUTH.md
