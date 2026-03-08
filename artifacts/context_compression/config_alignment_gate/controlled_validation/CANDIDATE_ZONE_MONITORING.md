# Context Compression - Candidate Zone Monitoring

## Current Status: Candidate Zone Active

**Position**: 150k/200k (75%)
**State**: candidate
**Trace Mode**: HIGH granularity
**Next Target**: 0.85 trigger zone

---

## Candidate Zone Monitoring Protocol

### What We're Monitoring

**State Transitions**:
- Current: candidate
- Next: pending (at 0.85)
- Tracking: All state changes logged

**Budget Growth**:
- Current ratio: 0.75
- Target ratio: 0.85
- Distance: 0.10 (20k tokens)

**System Health**:
- Safety counters: All zero
- Kill switch: Inactive
- Tools: Operational

### Trace Collection

In candidate zone, we collect detailed traces:

```jsonl
{"timestamp":"...","ratio":0.75,"state":"candidate","mode":"HIGH"}
{"timestamp":"...","ratio":0.76,"state":"candidate","mode":"HIGH"}
{"timestamp":"...","ratio":0.77,"state":"candidate","mode":"HIGH"}
...
{"timestamp":"...","ratio":0.85,"state":"pending","mode":"MAX","transition":"candidate→pending"}
```

### Pre-Trigger Preparation

As we approach 0.85:

1. **Evidence Directory**: Ready
2. **Counter Snapshot**: Prepared
3. **Budget Snapshot**: Prepared
4. **Guardrail Monitor**: Active
5. **Event Logger**: Active

---

## Expected Behavior at 0.85

When ratio reaches 0.85:

### State Transition
```
candidate → pending
```

### Trace Mode Switch
```
HIGH → MAXIMUM
```

### Guardrail Activation
```
Guardrail 2A: Budget threshold enforcement
Trigger condition: budget_ratio >= 0.85
Action: forced_standard_compression
```

### Evidence Capture Begin
- counter_before.json
- budget_before.json
- guardrail_event.json (started)

---

## Verification Checklist at 0.85

Three things must be verified simultaneously:

### 1. Guardrail 2A Hit
```json
{
  "guardrail_id": "2A",
  "trigger_condition": "budget_ratio >= 0.85",
  "observed_values": {
    "budget_ratio": 0.85
  }
}
```

### 2. Action Taken
```json
{
  "action_taken": "forced_standard_compression"
}
```

### 3. Pre-Assemble Compliance
```json
{
  "pre_assemble_compliant": true,
  "timing": "before_prompt_assembly"
}
```

---

## System Readiness

| Component | Status |
|-----------|--------|
| Budget Monitor | ✅ Active |
| State Machine | ✅ Tracking |
| Guardrail System | ✅ Armed |
| Evidence Collector | ✅ Ready |
| Trace Logger | ✅ HIGH mode |

---

## Progress Tracking

```
Observe Zone (< 0.75):    ✅ Complete
Candidate Zone (0.75):    ✅ Current
Trigger Zone (0.85):      ⏳ Approaching
Compression Event:        ⏳ Pending
Evidence Package:         ⏳ Pending
```

---

**Document Version**: 1.0
**Last Updated**: 2026-03-08T04:12:00-06:00
**Purpose**: Candidate Zone Monitoring
