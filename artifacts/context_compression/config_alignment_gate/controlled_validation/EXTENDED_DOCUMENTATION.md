# Context Compression Extended Documentation

## Part E: Implementation Details

### E.1 Hook Handler Architecture

The hook handler is implemented as a TypeScript module that integrates with OpenClaw's hook system. The handler listens for `message.preprocessed` events and executes the compression pipeline when threshold conditions are met.

#### Handler Registration

```typescript
// Hook registration in HOOK.md
{
  "name": "context-compression-shadow",
  "events": ["message:preprocessed"],
  "requires": {
    "bins": ["python3"]
  }
}
```

#### Handler Entry Point

```typescript
const handler = async (event: any) => {
  // Validate event type
  if (event.type !== 'message' || event.action !== 'preprocessed') {
    return;
  }

  // Initialize processing
  const sessionKey = event.sessionKey || 'unknown';
  const counters = readCounters();
  const mode = getCompressionMode();

  // Execute compression pipeline
  await processCompressionPipeline(sessionKey, counters, mode);
};
```

### E.2 Tool Integration Layer

The tool integration layer provides a unified interface for calling Python tools from the TypeScript handler.

#### Tool Execution

```typescript
async function runTool(
  toolPath: string,
  args: string[]
): Promise<{ stdout: string; stderr: string; exitCode: number }> {
  return new Promise((resolve) => {
    const proc = spawn('python3', [toolPath, ...args], {
      cwd: WORKSPACE,
      env: { ...process.env }
    });

    let stdout = '';
    let stderr = '';

    proc.stdout.on('data', (data) => {
      stdout += data.toString();
    });

    proc.stderr.on('data', (data) => {
      stderr += data.toString();
    });

    proc.on('close', (code) => {
      resolve({ stdout, stderr, exitCode: code || 0 });
    });

    proc.on('error', (error) => {
      resolve({ stdout: '', stderr: error.message, exitCode: 1 });
    });
  });
}
```

### E.3 Counter Management

The counter management system provides atomic read/write operations for tracking compression metrics.

#### Counter Schema

```typescript
interface Counters {
  // Scope metrics
  enforced_sessions_total: number;
  enforced_low_risk_sessions: number;
  bypass_sessions_total: number;
  sessions_skipped_by_scope_filter: number;

  // Trigger chain
  budget_check_call_count: number;
  sessions_evaluated_by_budget_check: number;
  sessions_over_threshold: number;
  compression_opportunity_count: number;
  enforced_trigger_count: number;
  retrieve_call_count: number;

  // Safety
  real_reply_corruption_count: number;
  active_session_pollution_count: number;
  rollback_event_count: number;
  hook_error_count: number;
  kill_switch_triggers: number;

  // Continuity
  old_topic_continuity_signal: number;
  open_loop_preservation_signal: number;
  user_correction_stability_signal: number;

  last_updated: string;
}
```

#### Atomic Write

```typescript
function writeCounters(counters: Counters): void {
  counters.last_updated = new Date().toISOString();
  
  const output = {
    status: 'active',
    mode: 'light_enforced',
    enforced_counters: counters,
    safety_status: {
      kill_switch_available: true,
      replay_guardrail_active: true
    },
    last_updated: counters.last_updated
  };
  
  writeFileSync(COUNTERS_FILE, JSON.stringify(output, null, 2));
}
```

### E.4 Session File Discovery

The session file discovery system locates the correct session file for a given session key.

#### Discovery Algorithm

```typescript
function findRecentSessionFile(sessionKey: string): string | null {
  const parts = sessionKey.split(':');
  let sessionId = parts[parts.length - 1];

  // Try direct match
  if (sessionId && sessionId !== 'unknown' && sessionId !== 'direct') {
    const sessionFile = join(SESSIONS_DIR, `${sessionId}.jsonl`);
    if (existsSync(sessionFile)) {
      return sessionFile;
    }
  }

  // Fallback to most recent
  const files = readdirSync(SESSIONS_DIR)
    .filter((f: string) => f.endsWith('.jsonl') && !f.includes('.deleted'))
    .map((f: string) => ({
      name: f,
      time: statSync(join(SESSIONS_DIR, f)).mtime.getTime()
    }))
    .sort((a: any, b: any) => b.time - a.time);

  if (files.length > 0) {
    return join(SESSIONS_DIR, files[0].name);
  }

  return null;
}
```

### E.5 Error Recovery

The error recovery system handles failures gracefully and logs rollback events.

#### Rollback Logging

```typescript
function logRollback(reason: string, sessionKey: string, details: any = {}): void {
  const event = {
    timestamp: new Date().toISOString(),
    reason,
    session_key: sessionKey,
    details
  };
  appendFileSync(ROLLBACK_LOG, JSON.stringify(event) + '\n');
}
```

#### Kill Switch Check

```typescript
function isKillSwitchTriggered(): boolean {
  if (!existsSync(KILL_SWITCH_FILE)) {
    return false;
  }
  const content = readFileSync(KILL_SWITCH_FILE, 'utf-8');
  return content.includes('KILL_SWITCH_TRIGGERED: true');
}
```

## Part F: Testing Framework

### F.1 Unit Tests

#### Token Estimation Tests

```python
def test_token_estimation():
    # Test empty string
    assert estimate_tokens('') == 0
    
    # Test single character
    assert estimate_tokens('a') == 1
    
    # Test typical sentence
    text = "Hello, world!"
    assert estimate_tokens(text) == len(text) // 4
    
    # Test long text
    text = "a" * 1000
    assert estimate_tokens(text) == 250
```

#### Pressure Level Tests

```python
def test_pressure_levels():
    # Normal range
    assert get_pressure_level(0.50) == 'normal'
    assert get_pressure_level(0.70) == 'light'
    assert get_pressure_level(0.71) == 'light'
    
    # Standard range
    assert get_pressure_level(0.85) == 'standard'
    assert get_pressure_level(0.90) == 'standard'
    
    # Strong range
    assert get_pressure_level(0.92) == 'strong'
    assert get_pressure_level(0.95) == 'strong'
    assert get_pressure_level(1.00) == 'strong'
```

#### Threshold Detection Tests

```python
def test_threshold_detection():
    # Below thresholds
    assert get_threshold_hit(0.50) is None
    assert get_threshold_hit(0.74) is None
    
    # Light threshold
    assert get_threshold_hit(0.75) == 'light'
    assert get_threshold_hit(0.80) == 'light'
    
    # Standard threshold
    assert get_threshold_hit(0.85) == 'standard'
    assert get_threshold_hit(0.90) == 'standard'
    
    # Strong threshold
    assert get_threshold_hit(0.92) == 'strong'
    assert get_threshold_hit(0.95) == 'strong'
```

### F.2 Integration Tests

#### Budget Check Integration

```python
def test_budget_check_integration():
    # Create test session
    test_dir = Path(tempfile.mkdtemp())
    test_file = test_dir / "test.jsonl"
    
    # Write test data
    with open(test_file, 'w') as f:
        for i in range(10):
            f.write(json.dumps({
                "type": "message",
                "message": {
                    "role": "user",
                    "content": [{"type": "text", "text": f"Message {i}"}]
                }
            }) + "\n")
    
    # Run budget check
    result = check_budget(None, test_file, 100000)
    
    # Verify
    assert "estimated_tokens" in result
    assert "ratio" in result
    assert result["estimated_tokens"] > 0
    
    # Cleanup
    shutil.rmtree(test_dir)
```

#### Compression Integration

```python
def test_compression_integration():
    # Create test files
    test_dir = Path(tempfile.mkdtemp())
    test_state = test_dir / "state.json"
    test_history = test_dir / "history.jsonl"
    
    # Write test data
    with open(test_state, 'w') as f:
        json.dump({"session_id": "test"}, f)
    
    with open(test_history, 'w') as f:
        for i in range(100):
            f.write(json.dumps({
                "type": "message",
                "message": {
                    "role": "user" if i % 2 == 0 else "assistant",
                    "content": [{"type": "text", "text": f"Turn {i}: " + "x" * 500}]
                }
            }) + "\n")
    
    # Run compression
    result = run_compression(
        session_id="test",
        state_path=test_state,
        history_path=test_history,
        capsules_path=None,
        events_path=None,
        mode="shadow",
        dry_run=True
    )
    
    # Verify
    assert "compression_triggered" in result
    if result["compression_triggered"]:
        assert "before" in result
        assert "after" in result
        assert result["before"]["ratio"] > result["after"]["ratio"]
    
    # Cleanup
    shutil.rmtree(test_dir)
```

### F.3 End-to-End Tests

#### Full Pipeline Test

```python
def test_full_pipeline():
    """Test complete compression pipeline from message to completion."""
    
    # Setup
    session_id = "test_e2e_session"
    
    # Step 1: Create session with initial turns
    create_session(session_id, turns=50)
    
    # Step 2: Verify initial state
    budget = run_budget_check(session_id)
    assert budget["pressure_level"] == "normal"
    
    # Step 3: Add more turns to trigger compression
    add_turns(session_id, count=100)
    
    # Step 4: Verify compression triggered
    budget = run_budget_check(session_id)
    assert budget["ratio"] >= 0.85
    
    # Step 5: Execute compression
    result = run_compression(session_id)
    assert result["compression_triggered"] == True
    
    # Step 6: Verify post-compression state
    budget = run_budget_check(session_id)
    assert budget["ratio"] < 0.75
    
    # Step 7: Verify safety
    counters = read_counters()
    assert counters["real_reply_corruption_count"] == 0
    assert counters["active_session_pollution_count"] == 0
```

## Part G: Deployment Checklist

### G.1 Pre-Deployment

- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Configuration validated
- [ ] Kill switch tested
- [ ] Rollback procedure documented
- [ ] Monitoring configured
- [ ] Alert thresholds set

### G.2 Deployment Steps

1. Backup current configuration
2. Update hook handler
3. Update tool chain
4. Update configuration files
5. Restart hooks
6. Verify functionality
7. Monitor metrics

### G.3 Post-Deployment

- [ ] Verify compression working
- [ ] Monitor safety counters
- [ ] Check audit logs
- [ ] Verify evidence preservation
- [ ] Document any issues

---

**Document Version**: 1.0
**Last Updated**: 2026-03-08T03:06:00-06:00
**Purpose**: Extended Documentation for Controlled Validation
