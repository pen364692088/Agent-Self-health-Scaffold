# Context Compression - Final Content Before Candidate Zone

## Approaching Candidate Zone

**Current Position**: 147k/200k (74%)
**Distance to 0.75**: ~3k tokens
**Status**: About to enter candidate zone

## What Happens at 0.75

When the budget ratio reaches 0.75:

1. **State Transition**: idle → candidate
2. **Trace Mode**: Switch to HIGH granularity
3. **Monitoring**: Increase observation frequency
4. **Logging**: Capture detailed state transitions

## Candidate Zone Behavior

In the candidate zone (0.75-0.85):

- System monitors context growth closely
- State machine tracks transitions
- Trace granularity increased
- Evidence preparation begins

## Next Milestone: 0.85

After candidate zone, at 0.85:

- State transition: candidate → pending
- Guardrail 2A activates
- Trigger capture mode begins
- Evidence capture starts

## Validation Criteria at 0.85

Three things must be verified simultaneously:

1. **Guardrail 2A Hit**: Budget ratio >= 0.85
2. **Action Taken**: forced_standard_compression
3. **Timing**: Before prompt assembly

## System Ready

All systems are ready for candidate zone entry:

- [x] Configuration verified
- [x] Tools tested
- [x] Evidence directory prepared
- [x] Trace file initialized
- [ ] Candidate zone reached
- [ ] Trigger zone reached
- [ ] Compression captured

## Current Configuration

```
Context Window: 200k tokens
Threshold Enforced: 0.85
Threshold Strong: 0.92
Mode: light_enforced
Critical Rule: 不允许跨过 0.85 后继续拖延
```

## Final Documentation

This completes the documentation for the context ramp to candidate zone. The system is prepared to:

1. Enter candidate zone at 0.75
2. Monitor state transitions
3. Continue to trigger zone at 0.85
4. Capture compression event
5. Verify all success criteria

---

**Document Version**: Final
**Last Updated**: 2026-03-08T04:05:00-06:00
**Purpose**: Final Content Before Candidate Zone Entry
