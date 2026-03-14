# Prompt Pilot Operations Runbook

## Quick Reference

### Status Check
```bash
tools/prompt-pilot-control --status
```

### Gate Check (Dual Gate)
```bash
# Check if eligible to switch from shadow to pilot
tools/prompt-pilot-control --check-gate
```

### Enable Pilot
```bash
# Pre-flight check first
tools/prompt-pilot-preflight

# Enable in shadow mode (REQUIRED first step)
tools/prompt-pilot-control --enable --mode shadow

# Monitor until gate conditions met (NOT time-based!)
tools/prompt-pilot-control --check-gate

# When gate passes, switch to pilot mode
tools/prompt-pilot-control --set-mode pilot
```

### Disable Pilot
```bash
# Immediate disable
tools/prompt-pilot-control --disable

# With reason
tools/prompt-pilot-control --disable --reason "conflict rate exceeded"
```

---

## Dual Gate Mechanism (IMPORTANT)

### Gate 1: Shadow → Pilot

**You CANNOT switch to pilot based on time alone.**

| Condition | Requirement | Current |
|-----------|-------------|---------|
| Effective Samples | ≥ 20 | Check with --check-gate |
| Max Observation | ≤ 7 days | Time limit |
| Match Rate | ≥ 80% | Quality gate |
| Conflict Rate | ≤ 5% | Safety gate |
| Fallback Rate | ≤ 10% | Stability gate |

**To check eligibility**:
```bash
tools/prompt-pilot-control --check-gate
```

**Output when NOT eligible**:
```
Samples: 15 / 20 required
  Status: ❌ INSUFFICIENT
```

**Output when eligible**:
```
✅ ELIGIBLE FOR PILOT
You can now run:
  tools/prompt-pilot-control --set-mode pilot
```

### Gate 2: Pilot → Decision

| Condition | Requirement |
|-----------|-------------|
| Effective Samples | ≥ 30 |
| Max Observation | ≤ 14 days |

**Possible Decisions**:
- `expand_prompt_pilot` - All metrics good
- `continue_pilot_and_patch_gaps` - Minor issues
- `escalate_to_phase_3` - Major issues

### Effective Sample Definition

A sample is "effective" only if ALL conditions met:
1. ✅ Task type in allowed list (recovery_success, task_ready_to_close, gate_completed)
2. ✅ Actually executed through pilot path
3. ✅ No configuration errors
4. ✅ Success = True
5. ✅ Conflict count = 0
6. ✅ Provenance completeness ≥ 50%

---

## Daily Operations

### Morning Check (Daily)
```bash
# 1. Check status
tools/prompt-pilot-control --status

# 2. Check gate progress
tools/pilot-pilot-control --check-gate

# 3. Review violations
# (shown in status output)
```

### Gate Progress Monitoring
```bash
# Check if ready to switch modes
tools/prompt-pilot-control --check-gate

# Sample output:
# Samples: 18 / 20 required
#   Status: ❌ INSUFFICIENT
# 
# Continue shadow mode until 20 samples collected.
```

---

## Incident Response

### Conflict Rate Spike

**Symptoms**: Conflict rate > 5%

**Response**:
1. Check recent changes to state files
2. Review conflict details
3. If persistent, disable pilot:
   ```bash
   tools/prompt-pilot-control --disable --reason "conflict rate spike"
   ```
4. Investigate root cause

### Match Rate Drop

**Symptoms**: Match rate < 80%

**Response**:
1. Check if state files are being updated correctly
2. Review shadow vs main comparison
3. If persistent, disable pilot
4. Check for data quality issues

### Fallback Rate High

**Symptoms**: Fallback rate > 10%

**Response**:
1. Check fallback reasons
2. If persistent, stay in shadow mode
3. Do NOT switch to pilot until resolved

---

## Rollback Procedure

### Manual Rollback
```bash
# 1. Disable pilot
tools/prompt-pilot-control --disable --reason "manual rollback"

# 2. Verify main chain is working
# (Run a test task)

# 3. Document reason
echo "$(date): Rollback - <reason>" >> artifacts/prompt_pilot/rollback_log.txt
```

### Auto Rollback
- Triggered when stop condition violated
- Logs to metrics.jsonl with error field
- Pilot disabled in config

---

## Monitoring Dashboard

### Key Metrics to Watch

| Metric | Healthy | Warning | Critical |
|--------|---------|---------|----------|
| Match Rate | 85-100% | 80-85% | < 80% |
| Conflict Rate | 0-3% | 3-5% | > 5% |
| Missing Rate | 0-2% | 2-5% | > 5% |
| Fallback Rate | 0-5% | 5-10% | > 10% |
| Error Rate | 0% | 0-1% | > 1% |

### Gate Progress Metrics

| Metric | Purpose |
|--------|---------|
| effective_samples | Count toward gate threshold |
| days_elapsed | Time toward max observation |
| eligible_for_pilot | Boolean gate status |

---

## Post-Pilot Decision

### Before Making Decision

Run gate check and verify:
```bash
tools/prompt-pilot-control --check-gate
tools/prompt-pilot-control --status
```

### Decision Criteria

| Decision | When |
|----------|------|
| `expand_prompt_pilot` | All metrics pass, ≥30 samples |
| `continue_pilot_and_patch_gaps` | 1-2 metrics slightly off |
| `escalate_to_phase_3` | Multiple metrics failing |

---

## Configuration Reference

### config/prompt_pilot.json

| Key | Type | Description |
|-----|------|-------------|
| pilot_enabled | bool | Master switch |
| pilot_mode | string | "shadow" or "pilot" |
| dual_gate.shadow_to_pilot.min_samples | int | Gate threshold (20) |
| dual_gate.shadow_to_pilot.max_days | int | Max observation (7) |
| metrics.effective_samples | int | **AUTHORITATIVE** sample count |

### Stop Conditions

| Condition | Default | Description |
|-----------|---------|-------------|
| max_conflict_rate | 0.05 | Max 5% conflicts |
| max_missing_rate | 0.05 | Max 5% missing fields |
| min_match_rate | 0.80 | Min 80% match |
| max_token_overhead | 0.30 | Max 30% token increase |
| max_fallback_rate | 0.10 | Max 10% fallbacks |
| max_manual_override_rate | 0.05 | Max 5% overrides |
| min_provenance_completeness | 0.95 | Min 95% completeness |

---

## Key Points to Remember

### ⚠️ Gate is NOT Time-Based

- ❌ WRONG: "Wait 1-2 weeks then switch to pilot"
- ✅ RIGHT: "Wait for ≥20 effective samples AND all conditions pass"

### ⚠️ Authority is ALWAYS main_chain

- Pilot can INFLUENCE prompt assembly
- Pilot can INFLUENCE context selection
- Pilot CANNOT decide task close
- Pilot CANNOT decide gate pass
- Final authority is ALWAYS main_chain

### ⚠️ Recovery is NEVER Live

- RecoveryPreview is shadow only
- No recovery pilot mode
- No recovery live mode

---

## Support

- **Current Status**: `CURRENT_STATUS.md`
- **Logs**: `artifacts/prompt_pilot/metrics.jsonl`
- **Config**: `config/prompt_pilot.json`
- **Design**: `PHASE_2_9_DESIGN.md`
- **Tools**: `tools/prompt-pilot-*`
