# Context Compression - Final Content Blocks

## Block 1: System Architecture Summary

The context compression system provides automatic token management for long-running OpenClaw sessions. The system operates through a pipeline of tools coordinated by a TypeScript hook handler.

### Architecture Components

1. **Hook Handler**: Event-driven coordinator
2. **Budget Checker**: Token estimation engine
3. **Compression Engine**: Context reduction system
4. **State Manager**: Persistence layer
5. **Evidence Collector**: Audit trail generator

### Data Flow

```
Message → Hook → Budget → Decision → Compression → State → Evidence → Prompt
```

## Block 2: Threshold Strategy

The threshold strategy defines when and how compression occurs:

### Threshold Levels

- **0.75**: Candidate zone entry
- **0.85**: Enforced compression trigger
- **0.92**: Strong compression trigger

### Critical Rule

At ratio >= 0.85, compression MUST execute before next prompt assembly. This rule prevents context overflow and maintains response quality.

## Block 3: State Transitions

The state machine manages compression lifecycle:

### States

1. **idle**: Normal operation
2. **candidate**: Monitoring active
3. **pending**: Compression required
4. **executing**: Compression in progress
5. **completed**: Success
6. **failed**: Error occurred
7. **rollback**: Recovery in progress

### Transitions

- idle → candidate: ratio >= 0.75
- candidate → pending: ratio >= 0.85
- pending → executing: compression start
- executing → completed: success
- executing → failed: error
- failed → rollback: recovery start

## Block 4: Safety Systems

Multiple safety systems protect data integrity:

### Kill Switch

Emergency shutdown capability that immediately stops all compression operations.

### Safety Counters

Track potential violations:
- real_reply_corruption_count
- active_session_pollution_count

Both must remain at zero.

### Scope Filter

Only processes low-risk sessions:
- single_topic_daily_chat
- non_critical_task
- simple_tool_context

## Block 5: Evidence Chain

Complete audit trail for each compression:

### Required Evidence

1. counter_before.json
2. counter_after.json
3. budget_before.json
4. budget_after.json
5. guardrail_event.json
6. capsule_metadata.json

### Validation

- All files present
- Timestamps consistent
- Counter deltas correct
- Budget changes valid

## Block 6: Performance Targets

System performance must meet these targets:

### Latency

- Budget check: < 100ms
- Compression: < 500ms
- Total: < 1000ms

### Success Rate

- Compression success: > 99%
- Evidence capture: 100%
- Safety preservation: 100%

## Block 7: Configuration Reference

Complete configuration specification:

```json
{
  "context_window": 200000,
  "threshold_enforced": 0.85,
  "threshold_strong": 0.92,
  "mode": "light_enforced",
  "critical_rule": "不允许跨过 0.85 后继续拖延"
}
```

## Block 8: Validation Criteria

Phase C passes when all criteria met:

1. Trigger at 0.85 (not 0.92)
2. Guardrail 2A hit
3. action_taken = forced_standard_compression
4. pre_assemble_compliant = yes
5. post_compression_ratio < 0.75
6. Safety counters = 0
7. Evidence complete

## Block 9: Monitoring Requirements

Continuous monitoring of:

### System Health

- Active sessions
- Compression rate
- Error rate
- Latency

### Safety Status

- Kill switch state
- Safety counters
- Rollback frequency

## Block 10: Operational Guidelines

### Daily

- Check counters
- Review logs
- Verify evidence

### Weekly

- Analyze trends
- Clean evidence
- Update docs

### Monthly

- Full audit
- Performance review
- Capacity planning

---

**Document Version**: Final
**Last Updated**: 2026-03-08T03:58:00-06:00
**Purpose**: Final Content Blocks for Candidate Zone Entry
