# Data Quality Note - real_main_agent Samples

## Finding

The 5 real_main_agent samples in the benchmark contain ONLY `time_passed` heartbeat events:

```json
{
  "timestamp": "2026-03-06T04:10:57.024Z",
  "inbound": { "messageId": "6658", "ts": 1772770256000, "dt_seconds": 300 },
  "sent_events": [{ "type": "time_passed", "seconds": 300 }],
  "errors": []
}
```

## Impact

- No conversation content (no decisions, entities, open loops, constraints)
- No tool calls beyond heartbeat
- Only time anchors can be extracted (from timestamps)
- Baseline score = 0.000 (no topic keywords)
- Anchor score = 0.230 (only time anchors contribute)

## Root Cause

These samples appear to be:
1. Heartbeat-only sessions, OR
2. Sampled incorrectly (only captured heartbeat events, not actual conversations)

## Recommendation

1. **For accurate benchmarking**: Replace these samples with real_main_agent samples that contain actual conversation events
2. **For current analysis**: The 0.230 score represents the maximum achievable with time-only anchors
3. **For next phase**: Focus anchor extraction on historical_replay samples which have rich content

## Alternative Interpretation

If these samples ARE representative of real_main_agent sessions (mostly heartbeat), then:
- Anchor-aware ranking won't help (no anchors to extract)
- Need different approach: session-level metadata, cross-session patterns, etc.
