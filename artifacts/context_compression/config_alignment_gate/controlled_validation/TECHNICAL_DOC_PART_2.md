# Context Compression - Additional Technical Documentation Part 2

## Module 5: Evidence Collector Implementation

The evidence collector ensures complete audit trail for all compression operations.

**Evidence Collection Flow**:
1. Pre-compression: Capture current state
2. During compression: Log operations
3. Post-compression: Capture new state
4. Validation: Verify completeness

**Evidence Files**:

**counter_before.json**:
```json
{
  "timestamp": "2026-03-08T04:00:00-06:00",
  "enforced_counters": {
    "enforced_trigger_count": 0,
    "real_reply_corruption_count": 0,
    "active_session_pollution_count": 0
  }
}
```

**budget_before.json**:
```json
{
  "timestamp": "2026-03-08T04:00:00-06:00",
  "estimated_tokens": 170000,
  "max_tokens": 200000,
  "ratio": 0.85,
  "pressure_level": "standard"
}
```

**guardrail_event.json**:
```json
{
  "guardrail_id": "2A",
  "trigger_condition": "budget_ratio >= 0.85",
  "observed_values": {
    "budget_ratio": 0.85,
    "estimated_tokens": 170000
  },
  "action_taken": "forced_standard_compression",
  "timestamp": "2026-03-08T04:00:00-06:00"
}
```

**capsule_metadata.json**:
```json
{
  "capsule_id": "cap_001",
  "session_id": "session_001",
  "source_turn_range": {"start": 1, "end": 50},
  "token_count": 2500,
  "created_at": "2026-03-08T04:00:00-06:00"
}
```

## Module 6: Counter Manager Implementation

The counter manager tracks all system metrics.

**Counter Categories**:

**Scope Counters**:
- `enforced_sessions_total`: Total sessions processed
- `enforced_low_risk_sessions`: Low-risk sessions only
- `bypass_sessions_total`: Sessions bypassed
- `sessions_skipped_by_scope_filter`: Excluded by filter

**Trigger Counters**:
- `budget_check_call_count`: Budget checks performed
- `sessions_evaluated_by_budget_check`: Sessions evaluated
- `sessions_over_threshold`: Sessions exceeding threshold
- `compression_opportunity_count`: Could compress
- `enforced_trigger_count`: Actually compressed
- `retrieve_call_count`: Retrieval operations

**Safety Counters**:
- `real_reply_corruption_count`: Reply corruptions
- `active_session_pollution_count`: Session pollution
- `rollback_event_count`: Rollback events
- `hook_error_count`: Hook errors
- `kill_switch_triggers`: Kill switch activations

**Counter Operations**:
```python
class CounterManager:
    def __init__(self, path: Path):
        self.path = path
    
    def read(self) -> dict:
        if not self.path.exists():
            return self.defaults()
        return json.loads(self.path.read_text())['enforced_counters']
    
    def write(self, counters: dict):
        output = {
            'status': 'active',
            'mode': 'light_enforced',
            'enforced_counters': counters,
            'last_updated': datetime.now().isoformat()
        }
        self.path.write_text(json.dumps(output, indent=2))
    
    def increment(self, key: str, delta: int = 1):
        counters = self.read()
        counters[key] = counters.get(key, 0) + delta
        self.write(counters)
```

## Module 7: Kill Switch Implementation

The kill switch provides emergency shutdown capability.

**Kill Switch File Format**:
```markdown
# Kill Switch Activated

KILL_SWITCH_TRIGGERED: true
Reason: Testing emergency shutdown
Timestamp: 2026-03-08T04:00:00-06:00
ActivatedBy: admin
```

**Kill Switch Check**:
```python
def is_kill_switch_active(kill_switch_path: Path) -> bool:
    if not kill_switch_path.exists():
        return False
    content = kill_switch_path.read_text()
    return 'KILL_SWITCH_TRIGGERED: true' in content
```

**Kill Switch Activation**:
```python
def activate_kill_switch(path: Path, reason: str):
    content = f"""# Kill Switch Activated

KILL_SWITCH_TRIGGERED: true
Reason: {reason}
Timestamp: {datetime.now().isoformat()}
ActivatedBy: admin
"""
    path.write_text(content)
    logger.critical(f"Kill switch activated: {reason}")
```

## Module 8: Scope Filter Implementation

The scope filter determines session eligibility.

**Allowed Session Types**:
```python
ALLOWED_TYPES = [
    'single_topic_daily_chat',
    'non_critical_task',
    'simple_tool_context'
]
```

**Excluded Session Types**:
```python
EXCLUDED_TYPES = [
    'multi_file_debug',
    'high_commitment_task',
    'critical_execution',
    'multi_agent_collaboration',
    'high_risk_scenario'
]
```

**Scope Check**:
```python
def is_session_eligible(session_type: str) -> bool:
    if session_type in EXCLUDED_TYPES:
        return False
    return session_type in ALLOWED_TYPES or session_type == 'unknown'
```

## Module 9: Guardrail System Implementation

The guardrail system provides multiple protection layers.

**Guardrail Definitions**:

**Guardrail 1: Pre-Check Guardrail**:
- Checks session eligibility
- Verifies kill switch status
- Validates configuration

**Guardrail 2A: Threshold Enforcement Guardrail**:
- Monitors budget ratio
- Triggers at 0.85 threshold
- Forces compression before assemble

**Guardrail 2B: Kill Switch Guardrail**:
- Monitors kill switch state
- Blocks compression if active
- Alerts on activation

**Guardrail 2C: Safety Counter Guardrail**:
- Monitors safety counters
- Blocks if non-zero
- Alerts on violation

**Guardrail Event Generation**:
```python
def create_guardrail_event(
    guardrail_id: str,
    trigger_condition: str,
    observed_values: dict,
    action_taken: str
) -> dict:
    return {
        'guardrail_id': guardrail_id,
        'trigger_condition': trigger_condition,
        'observed_values': observed_values,
        'action_taken': action_taken,
        'timestamp': datetime.now().isoformat()
    }
```

## Module 10: Configuration Validator Implementation

The configuration validator ensures correct settings.

**Validation Rules**:

**Threshold Validation**:
```python
def validate_thresholds(thresholds: dict) -> bool:
    enforced = thresholds.get('enforced', 0)
    strong = thresholds.get('strong', 0)
    
    # Must be between 0 and 1
    if not (0 < enforced <= 1 and 0 < strong <= 1):
        return False
    
    # Enforced must be less than strong
    if enforced >= strong:
        return False
    
    return True
```

**Context Window Validation**:
```python
def validate_context_window(context_window: int) -> bool:
    return 1000 <= context_window <= 1000000
```

**Mode Validation**:
```python
def validate_mode(mode: str) -> bool:
    return mode in ['shadow', 'light_enforced', 'full_enforced']
```

**Complete Configuration Validation**:
```python
def validate_config(config: dict) -> tuple[bool, list[str]]:
    errors = []
    
    if not validate_thresholds(config.get('thresholds', {})):
        errors.append('Invalid threshold configuration')
    
    if not validate_context_window(config.get('context_window', 0)):
        errors.append('Invalid context window')
    
    if not validate_mode(config.get('mode', '')):
        errors.append('Invalid mode')
    
    return len(errors) == 0, errors
```

---

**Document Version**: 1.0
**Last Updated**: 2026-03-08T04:03:00-06:00
