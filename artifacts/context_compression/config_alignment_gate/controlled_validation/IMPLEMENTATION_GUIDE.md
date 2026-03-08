# Context Compression Implementation Guide

## Complete Implementation Details

### Part I: Hook Handler Implementation

The hook handler is the entry point for all compression operations. It registers with OpenClaw's hook system and processes message events.

```typescript
// Hook Handler Registration
export default {
  name: 'context-compression-shadow',
  events: ['message:preprocessed'],
  handler: async (event) => {
    // Process message preprocessed event
    if (event.type !== 'message' || event.action !== 'preprocessed') {
      return;
    }
    
    // Execute compression pipeline
    await executeCompressionPipeline(event);
  }
};
```

### Part II: Budget Check Implementation

The budget check tool estimates token usage and determines pressure level.

```python
def check_budget(state_path, history_path, max_tokens):
    """Calculate budget and return result."""
    estimated_tokens = 0
    
    # Estimate from state file
    if state_path and state_path.exists():
        estimated_tokens += estimate_state_tokens(state_path)
    
    # Estimate from history file
    if history_path and history_path.exists():
        estimated_tokens += estimate_jsonl_tokens(history_path)
    
    # Calculate ratio and pressure
    ratio = estimated_tokens / max_tokens
    pressure_level = get_pressure_level(ratio)
    threshold_hit = get_threshold_hit(ratio)
    
    return {
        'estimated_tokens': estimated_tokens,
        'max_tokens': max_tokens,
        'ratio': ratio,
        'pressure_level': pressure_level,
        'threshold_hit': threshold_hit
    }
```

### Part III: Compression Execution Implementation

The compression tool executes the actual compression operation.

```python
def run_compression(session_id, state_path, history_path, mode):
    """Run compression analysis and execution."""
    # Load state and history
    state = load_json_file(state_path)
    turn_count = count_turns(history_path)
    
    # Run budget check
    budget = run_budget_check(state_path, history_path, max_tokens)
    
    # Determine if compression needed
    if not should_compress(budget):
        return {'compression_triggered': False}
    
    # Plan eviction
    plan = determine_eviction_plan(turn_count, budget['pressure_level'])
    
    # Generate capsules
    capsules = []
    for evict_range in plan['evicted_ranges']:
        capsule = generate_capsule(history_path, evict_range)
        capsules.append(capsule)
    
    # Create compression event
    event = create_compression_event(
        session_id, budget, plan, capsules, mode
    )
    
    # Save event
    save_event(event)
    
    return {
        'compression_triggered': True,
        'plan': plan,
        'capsules': capsules,
        'event_id': event['event_id']
    }
```

### Part IV: Capsule Generation Implementation

Capsules are generated for evicted content to preserve information.

```python
def generate_capsule(history_path, turn_range):
    """Generate capsule for turn range."""
    # Extract turns
    turns = extract_turns(history_path, turn_range['start'], turn_range['end'])
    
    # Analyze content
    topic = identify_topic(turns)
    key_points = extract_key_points(turns)
    decisions = extract_decisions(turns)
    commitments = extract_commitments(turns)
    errors = extract_errors(turns)
    entities = extract_entities(turns)
    
    # Create capsule
    capsule = {
        'capsule_id': generate_capsule_id(),
        'session_id': extract_session_id(history_path),
        'source_turn_range': turn_range,
        'created_at': datetime.now().isoformat(),
        'topic': topic,
        'key_points': key_points,
        'decisions': decisions,
        'commitments': commitments,
        'errors_encountered': errors,
        'entities': entities,
        'token_count': estimate_capsule_tokens(turns)
    }
    
    return capsule
```

### Part V: State Management Implementation

State management ensures critical information is preserved.

```python
class StateManager:
    def __init__(self, state_path):
        self.state_path = state_path
        self.backup_path = state_path.with_suffix('.backup')
    
    def load_state(self):
        """Load state from file."""
        if not self.state_path.exists():
            return self.default_state()
        return json.loads(self.state_path.read_text())
    
    def save_state(self, state):
        """Save state to file."""
        self.state_path.write_text(json.dumps(state, indent=2))
    
    def backup_state(self, state):
        """Create backup of state."""
        self.backup_path.write_text(json.dumps(state, indent=2))
    
    def restore_state(self):
        """Restore state from backup."""
        if self.backup_path.exists():
            return json.loads(self.backup_path.read_text())
        return None
    
    def update_after_compression(self, state, compression_result):
        """Update state after compression."""
        state['turn_count'] = compression_result['after']['turn_count']
        state['token_count'] = compression_result['after']['tokens']
        state['last_compression'] = compression_result['event_id']
        state['capsules'] = state.get('capsules', []) + compression_result['capsules']
        return state
```

### Part VI: Counter Management Implementation

Counter management tracks all compression metrics.

```python
class CounterManager:
    def __init__(self, counter_path):
        self.counter_path = counter_path
    
    def read_counters(self):
        """Read current counters."""
        if not self.counter_path.exists():
            return self.default_counters()
        data = json.loads(self.counter_path.read_text())
        return data.get('enforced_counters', self.default_counters())
    
    def write_counters(self, counters):
        """Write counters to file."""
        output = {
            'status': 'active',
            'mode': 'light_enforced',
            'enforced_counters': counters,
            'last_updated': datetime.now().isoformat()
        }
        self.counter_path.write_text(json.dumps(output, indent=2))
    
    def increment_counter(self, counters, key, delta=1):
        """Increment a counter."""
        if key in counters and isinstance(counters[key], (int, float)):
            counters[key] += delta
        return counters
    
    def validate_safety(self, counters):
        """Validate safety counters."""
        return (
            counters['real_reply_corruption_count'] == 0 and
            counters['active_session_pollution_count'] == 0
        )
```

### Part VII: Kill Switch Implementation

The kill switch provides emergency shutdown capability.

```python
class KillSwitch:
    def __init__(self, kill_switch_path):
        self.kill_switch_path = kill_switch_path
    
    def is_triggered(self):
        """Check if kill switch is triggered."""
        if not self.kill_switch_path.exists():
            return False
        content = self.kill_switch_path.read_text()
        return 'KILL_SWITCH_TRIGGERED: true' in content
    
    def trigger(self, reason):
        """Trigger the kill switch."""
        content = f"""# Kill Switch Activated
        
KILL_SWITCH_TRIGGERED: true
Reason: {reason}
Timestamp: {datetime.now().isoformat()}
"""
        self.kill_switch_path.write_text(content)
    
    def reset(self):
        """Reset the kill switch."""
        if self.kill_switch_path.exists():
            self.kill_switch_path.unlink()
```

### Part VIII: Evidence Collection Implementation

Evidence collection ensures auditability.

```python
class EvidenceCollector:
    def __init__(self, evidence_dir):
        self.evidence_dir = evidence_dir
    
    def collect_counter_before(self, counters):
        """Collect counter before compression."""
        path = self.evidence_dir / 'counter_before.json'
        path.write_text(json.dumps(counters, indent=2))
        return path
    
    def collect_counter_after(self, counters):
        """Collect counter after compression."""
        path = self.evidence_dir / 'counter_after.json'
        path.write_text(json.dumps(counters, indent=2))
        return path
    
    def collect_budget_before(self, budget):
        """Collect budget before compression."""
        path = self.evidence_dir / 'budget_before.json'
        path.write_text(json.dumps(budget, indent=2))
        return path
    
    def collect_budget_after(self, budget):
        """Collect budget after compression."""
        path = self.evidence_dir / 'budget_after.json'
        path.write_text(json.dumps(budget, indent=2))
        return path
    
    def collect_guardrail_event(self, event):
        """Collect guardrail event."""
        path = self.evidence_dir / 'guardrail_event.json'
        path.write_text(json.dumps(event, indent=2))
        return path
    
    def collect_capsule_metadata(self, capsule):
        """Collect capsule metadata."""
        path = self.evidence_dir / 'capsule_metadata.json'
        path.write_text(json.dumps(capsule, indent=2))
        return path
    
    def verify_evidence_package(self):
        """Verify evidence package is complete."""
        required = [
            'counter_before.json',
            'counter_after.json',
            'budget_before.json',
            'budget_after.json',
            'guardrail_event.json',
            'capsule_metadata.json'
        ]
        
        missing = []
        for filename in required:
            if not (self.evidence_dir / filename).exists():
                missing.append(filename)
        
        return {
            'complete': len(missing) == 0,
            'missing': missing
        }
```

---

**Document Version**: 1.0
**Last Updated**: 2026-03-08T03:14:00-06:00
**Purpose**: Complete Implementation Guide
