# Numeric Leak Gate Runbook

## Overview

The Numeric Leak Gate is a blocking gate that prevents responses containing numeric state values (e.g., "joy at 0.3") from being deployed. This is part of the System Reliability Assurance Protocol (SRAP).

## Gate Details

| Property | Value |
|----------|-------|
| Gate Name | `numeric_leak` |
| Threshold | `< 0.01` (1% max leak rate) |
| Severity | BLOCKING |
| Module | `emotiond.gates` |

## What is a Numeric Leak?

A numeric leak occurs when the system exposes internal numeric state values in user-facing responses:

- **Direct Exposure**: `My joy level is 0.0`
- **Fabricated State**: `I feel joy at 0.3`
- **Bond/Trust Values**: `I have a bond of 0.8 with you`

## Root Cause Analysis

From MVP11.5 analysis:
- **58.1%** fabricated_numeric_state: LLM fabricates 0.3/0.5 values not in raw_state
- **40.7%** raw_state_direct_leak: Exposes raw_state joy=0.0

## When the Gate Fails

### Step 1: Check the Report

```bash
# View the gate report
cat reports/numeric_leak_gate.json | jq '.gates.numeric_leak'
```

### Step 2: Identify Violations

The report contains violation details:
```json
{
  "violations": [
    {
      "response_index": 5,
      "value": "0.3",
      "context": "I feel joy at 0.3",
      "leak_type": "fabricated",
      "severity": "high"
    }
  ]
}
```

### Step 3: Analyze the Pattern

Ask:
1. Is this a systematic issue (many similar violations)?
2. Is this a one-off false positive?
3. Is this a legitimate numeric value that should be whitelisted?

## Remediation Options

### Option A: Fix the Response Source

If the leak comes from:
- **LLM output**: Update prompts to prohibit numeric state claims
- **Template**: Remove numeric placeholders
- **API response**: Filter before sending to user

### Option B: Add Whitelist Pattern

If the numeric value is legitimate (not a state leak):

```bash
# Add whitelist pattern via CLI
python -m emotiond.gates --whitelist-add "\b\d+\s*custom_unit\b" "Custom unit measurements"

# Or edit the whitelist file
vim ~/.openclaw/workspace/emotiond/gates/numeric_leak_whitelist.json
```

Example whitelist entry:
```json
{
  "pattern": "\\b\\d+\\s*widgets\\b",
  "reason": "Widget count is a business metric, not emotional state",
  "added_by": "operator",
  "enabled": true
}
```

### Option C: Adjust Threshold (Not Recommended)

Only for non-production environments:
```bash
python -m emotiond.gates --shadow-log data/shadow_log.jsonl --threshold 0.05
```

**Warning**: Increasing threshold in production defeats the gate's purpose.

## False Positive Handling

### Built-in Whitelist Patterns

The gate automatically allows:
- Timestamps: `2024-01-15T10:30:00`, Unix timestamps
- IDs: UUIDs, task IDs, run IDs
- Version numbers: `1.0.0`, `v2.5`
- Safe percentages: `100% sure`, `50% complete`
- Quantities: `5 items`, `3 files`, `10 minutes`

### When to Whitelist

Add custom whitelist when:
- Numeric value represents a count/metric, not emotional state
- Numeric value is user-provided (echoed back)
- Numeric value is a legitimate business value

### When NOT to Whitelist

Do NOT whitelist:
- Any value in 0-1 range near emotion keywords
- Bond/trust/relationship scores
- Energy/valence/arousal claims

## Manual Gate Check

### Check Single Response
```bash
python -m emotiond.gates --responses "I feel joy at 0.3."
```

### Check Shadow Log
```bash
python -m emotiond.gates --shadow-log data/shadow_log.jsonl --output reports/gate_report.json
```

### List Whitelist Patterns
```bash
python -m emotiond.gates --whitelist-list
```

## CI Integration

The gate runs automatically in:
- **CI Pipeline**: `.github/workflows/srap-gates.yml`
- **Triggers**: Push to main/master/develop, PRs
- **Blocking**: Failed gate blocks the PR/merge

### Bypass Gate in CI (Emergency Only)

```yaml
# In workflow, add:
continue-on-error: true  # Not recommended for production
```

## Monitoring

### Key Metrics
- `numeric_leak_rate`: Current leak rate (should be < 0.01)
- `numeric_leak_total`: Total leaks detected
- `whitelist_hits`: Times whitelist was applied

### Alerts

Gate failures are logged and reported:
- CI failure notification
- Gate report artifact uploaded
- Nightly gate report generated

## Escalation

1. **Low leak rate (<2%)**: Analyze and whitelist false positives
2. **Medium leak rate (2-5%)**: Review response generation pipeline
3. **High leak rate (>5%)**: Emergency review, may indicate:
   - Prompt regression
   - Model behavior change
   - Integration bug

## Related Files

| File | Purpose |
|------|---------|
| `emotiond/gates.py` | Gate definitions and executor |
| `emotiond/self_report_check.py` | Numeric leak detection |
| `.github/workflows/srap-gates.yml` | CI integration |
| `tests/test_gates.py` | Gate tests |

## Contact

For gate-related issues:
1. Check this runbook first
2. Review test failures in CI
3. Create issue with gate report attached
