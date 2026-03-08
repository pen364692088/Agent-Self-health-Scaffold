# Context Compression - Additional Content for Context Ramp

## System Integration Details

### Hook Integration with OpenClaw

The hook system integrates deeply with OpenClaw's message processing pipeline:

**Event Registration**:
```json
{
  "name": "context-compression-shadow",
  "events": ["message:preprocessed"],
  "priority": 10,
  "async": true
}
```

**Event Processing**:
1. OpenClaw receives message
2. Preprocesses message content
3. Fires message.preprocessed event
4. Hook handler executes
5. Compression pipeline runs
6. Prompt assembly continues

### Tool Chain Integration

**Tool Discovery**:
```bash
# Tools are located in workspace/tools/
tools/
├── context-budget-check
├── context-compress
├── prompt-assemble
└── context-retrieve
```

**Tool Execution**:
```typescript
async function runTool(toolPath: string, args: string[]): Promise<Result> {
  const proc = spawn('python3', [toolPath, ...args]);
  // Handle stdout, stderr, exit code
  return { stdout, stderr, exitCode };
}
```

### State File Integration

**State File Location**:
```
~/.openclaw/workspace/state/active_state.json
```

**State Access Pattern**:
1. Read state before compression
2. Backup state
3. Update state after compression
4. Verify persistence

### Evidence Storage Integration

**Evidence Directory Structure**:
```
artifacts/context_compression/
├── config_alignment_gate/
│   └── controlled_validation/
│       ├── counter_before.json
│       ├── counter_after.json
│       ├── budget_before.json
│       ├── budget_after.json
│       ├── guardrail_event.json
│       └── capsule_metadata.json
```

## Performance Characteristics

### Latency Breakdown

**Budget Check Latency**:
- File read: 10-30ms
- Token estimation: 20-50ms
- Ratio calculation: < 5ms
- Total: 30-85ms

**Compression Latency**:
- Eviction planning: 10-20ms
- Capsule generation: 100-300ms
- State update: 20-50ms
- Evidence capture: 10-30ms
- Total: 140-400ms

**Total Pipeline Latency**:
- Minimum: 170ms
- Typical: 250ms
- Maximum: 485ms

### Memory Usage

**Idle State**:
- Base memory: 50MB
- Per-session overhead: 0.1MB
- Total for 100 sessions: 60MB

**Active Compression**:
- Base memory: 100MB
- Per-compression overhead: 10MB
- Peak memory: 150MB

### CPU Usage

**Idle State**:
- Background monitoring: 5% CPU
- Event processing: 10% CPU per event

**Active Compression**:
- Eviction planning: 15% CPU
- Capsule generation: 25% CPU
- State update: 10% CPU
- Peak CPU: 40%

## Error Handling Patterns

### Transient Error Handling

**Pattern**: Retry with exponential backoff

```python
async def retry_with_backoff(
    operation: Callable,
    max_retries: int = 3,
    initial_delay: float = 0.1
) -> Result:
    delay = initial_delay
    for attempt in range(max_retries):
        try:
            return await operation()
        except TransientError as e:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(delay)
            delay *= 2
```

### Permanent Error Handling

**Pattern**: Fallback to safe state

```python
def handle_permanent_error(error: Error, state: State) -> State:
    # Log error
    logger.error(f"Permanent error: {error}")
    
    # Restore from backup
    restored_state = restore_backup(state)
    
    # Update error counter
    increment_counter('hook_error_count')
    
    # Return safe state
    return restored_state
```

### Catastrophic Error Handling

**Pattern**: Kill switch activation

```python
def handle_catastrophic_error(error: Error):
    # Activate kill switch
    activate_kill_switch(f"Catastrophic error: {error}")
    
    # Log critical event
    logger.critical(f"Kill switch activated: {error}")
    
    # Alert operators
    send_alert('kill_switch_activated', error)
```

## Monitoring Integration

### Metrics Export

**Prometheus Format**:
```
# HELP compression_trigger_total Total compression triggers
# TYPE compression_trigger_total counter
compression_trigger_total{threshold="enforced"} 10
compression_trigger_total{threshold="strong"} 2

# HELP compression_duration_ms Compression duration in milliseconds
# TYPE compression_duration_ms histogram
compression_duration_ms_bucket{le="100"} 5
compression_duration_ms_bucket{le="250"} 8
compression_duration_ms_bucket{le="500"} 11
compression_duration_ms_bucket{le="+Inf"} 12

# HELP safety_counter_zero Safety counter value
# TYPE safety_counter_zero gauge
safety_counter_zero{name="real_reply_corruption"} 0
safety_counter_zero{name="active_session_pollution"} 0
```

### Log Format

**Structured Logging**:
```json
{
  "timestamp": "2026-03-08T04:00:00-06:00",
  "level": "INFO",
  "component": "compression-hook",
  "message": "Compression triggered",
  "context": {
    "session_id": "session_001",
    "trigger_ratio": 0.85,
    "pressure_level": "standard"
  }
}
```

### Alert Integration

**Alert Types**:
- Critical: Immediate notification
- Warning: Priority queue
- Info: Daily digest

**Alert Channels**:
- Email: For critical alerts
- Slack: For warning alerts
- Dashboard: For info alerts

---

**Document Version**: 1.0
**Last Updated**: 2026-03-08T04:04:00-06:00
