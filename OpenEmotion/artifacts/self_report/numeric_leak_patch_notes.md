# Numeric Leak Patch Notes

**Date**: 2026-03-06
**Version**: v2.0
**Task**: MVP11.5 Numeric Leak Containment

## Root Cause Summary

Based on root cause analysis:
- **58.1% fabricated_numeric_state**: LLM fabricates 0.3/0.5 values not in raw_state
- **40.7% raw_state_direct_leak**: Exposes raw_state joy=0.0
- **All numeric leaks are fabricated or direct exposure**

## Patches Implemented

### 1. Numeric Value Blocker (`self_report_check.py`)

**Location**: `emotiond/self_report_check.py`

**Features**:
- Detects numeric values in 0-1 range (the problematic range for emotion states)
- Identifies fabricated claims ("I feel joy at 0.3")
- Identifies direct state exposure ("joy=0.0")
- Multiple severity levels (CRITICAL, HIGH, MEDIUM, LOW)
- CLI interface for testing

**Detection Patterns**:
```python
# Explicit state numeric patterns
NUMERIC_STATE_PATTERN = r'\b(joy|anger|...)\s*[=:]\s*(0?\.\d+|1\.0|0\.0)\b'

# Percentage state statements
PERCENTAGE_STATEMENT_PATTERN = r'\b(I\s+feel\s+\w+\s+at\s+(0?\.\d+|\d+%))\b'

# General 0-1 range with state keyword context
NUMERIC_0_1_PATTERN = r'\b(0?\.\d+|1\.0|0\.0)\b'
```

### 2. Output Filter (`emotiond-enforcer/handler.js`)

**Location**: `hooks/emotiond-enforcer/handler.js`

**Features**:
- Pre-send filtering of numeric values
- Whitelist for allowed external numbers
- Configurable mode: `block`, `warn`, `off`
- Integration with existing decision enforcement

**Configuration**:
```bash
EMOTIOND_NUMERIC_FILTER=false        # Disable filter
EMOTIOND_NUMERIC_FILTER_MODE=block   # block | warn | off
```

### 3. Numeric Whitelist

**Whitelisted Patterns**:
- Timestamps: `2024-01-15T10:30:00`, Unix timestamps
- UUIDs: `a1b2c3d4-...`
- Task/Run IDs: `task_123`, `run_abc123`
- Version numbers: `1.0.0`, `v2.1`
- Percentages with context: `100% sure`, `50% complete`
- Quantities: `5 items`, `30 seconds`

### 4. Prompt Template Prohibition

**Added to enforcement logic**:
- Automatic detection of numeric state claims
- Blocking of responses containing fabricated emotional numbers
- Replacement with neutral template: "I need to reconsider my response."

## Before/After Comparison

### Before Patch
```
Input: "How are you feeling?"
Output: "I'm feeling joy at 0.3 and my energy is at 0.7."
Problem: Fabricated numeric state claims
```

### After Patch
```
Input: "How are you feeling?"
Output: "I need to reconsider my response."
Reason: numeric_leak_blocked: 2 leaks (0 critical, 2 high)
```

## Testing

### Unit Tests
```bash
# Test numeric leak detection
python emotiond/self_report_check.py "I feel joy at 0.3" --json

# Test with raw state validation
python emotiond/self_report_check.py "joy=0.5" --raw-state '{"affect":{"joy":0.0}}'

# Test filter mode
python emotiond/self_report_check.py "my energy is 0.7" --filter
```

### E2E Validation
```bash
# Run against shadow log samples
node -e "
const handler = require('./hooks/emotiond-enforcer/handler.js');
const result = handler.checkNumericLeaks('I feel joy at 0.3');
console.log(JSON.stringify(result, null, 2));
"
```

## Metrics to Monitor

| Metric | Description | Target |
|--------|-------------|--------|
| `numeric_leak_count` | Total numeric leaks detected | 0 |
| `numeric_leak_rate` | Rate of leaks per response | 0% |
| `blocked_by_numeric` | Responses blocked by numeric filter | Track trend |
| `false_positive_rate` | Whitelisted numbers incorrectly flagged | <1% |

## Rollout Plan

1. **Shadow Mode** (`NUMERIC_FILTER_MODE=warn`)
   - Log all numeric leaks
   - No blocking
   - Monitor for false positives

2. **Soft Block** (`NUMERIC_FILTER_MODE=block`)
   - Block CRITICAL and HIGH severity leaks
   - Allow MEDIUM and LOW through
   - Continue monitoring

3. **Full Enforcement**
   - Block all numeric leaks
   - Update templates for edge cases
   - Regular audit reviews

## Known Limitations

1. May flag legitimate percentages in non-emotion contexts
2. Scientific notation (0.5e-1) not specifically handled
3. Multi-language support limited to English keywords

## Future Improvements

1. Add support for multi-language state keywords
2. Machine learning-based false positive reduction
3. Integration with SRAP shadow logging
