# Context Compression - Guardrail System Deep Dive

## Guardrail Architecture

The guardrail system provides multiple layers of protection to ensure safe and correct compression behavior.

### Guardrail Hierarchy

```
Guardrail 1: Pre-Check Guardrail
    ↓
Guardrail 2A: Threshold Enforcement
    ↓
Guardrail 2B: Kill Switch Protection
    ↓
Guardrail 2C: Safety Counter Protection
    ↓
Guardrail 3: Post-Compression Verification
```

---

## Guardrail 1: Pre-Check Guardrail

**Purpose**: Verify system is ready for compression

**Checks**:
1. Is session in allowed scope?
2. Is kill switch inactive?
3. Is feature enabled?
4. Is configuration valid?

**Implementation**:
```python
def pre_check_guardrail(session: Session) -> bool:
    if not is_session_eligible(session.type):
        return False
    
    if is_kill_switch_active():
        return False
    
    if not is_feature_enabled():
        return False
    
    if not is_config_valid():
        return False
    
    return True
```

**Failure Action**: Skip compression, log reason

---

## Guardrail 2A: Threshold Enforcement Guardrail

**Purpose**: Enforce compression at 0.85 threshold

**Trigger Condition**: `budget_ratio >= 0.85`

**Actions**:
1. Detect threshold crossing
2. Log guardrail event
3. Trigger forced_standard_compression
4. Ensure execution before assemble

**Implementation**:
```python
def threshold_enforcement_guardrail(budget: Budget) -> dict:
    if budget.ratio >= 0.85:
        event = {
            'guardrail_id': '2A',
            'trigger_condition': 'budget_ratio >= 0.85',
            'observed_values': {
                'budget_ratio': budget.ratio,
                'estimated_tokens': budget.estimated_tokens
            },
            'action_taken': 'forced_standard_compression'
        }
        log_guardrail_event(event)
        return {'triggered': True, 'event': event}
    return {'triggered': False}
```

**Event Schema**:
```json
{
  "guardrail_id": "2A",
  "guardrail_name": "budget_threshold_enforcement",
  "trigger_condition": "budget_ratio >= 0.85",
  "observed_values": {
    "budget_ratio": 0.85,
    "estimated_tokens": 170000,
    "max_tokens": 200000,
    "compression_state": "pending"
  },
  "action_taken": "forced_standard_compression",
  "execution_result": {
    "success": true,
    "post_compression_ratio": 0.52
  },
  "pre_assemble_compliant": true,
  "timestamp": "2026-03-08T04:00:00-06:00"
}
```

**Critical Rule**: Compression MUST occur before prompt assembly.

---

## Guardrail 2B: Kill Switch Protection

**Purpose**: Allow emergency shutdown

**Trigger Condition**: `KILL_SWITCH_TRIGGERED: true`

**Actions**:
1. Detect kill switch activation
2. Block all compression
3. Alert operators
4. Log activation event

**Implementation**:
```python
def kill_switch_guardrail() -> bool:
    if is_kill_switch_active():
        log_event('kill_switch_active')
        alert_operators('kill_switch_active')
        return False  # Block compression
    return True  # Allow compression
```

**Kill Switch File**:
```markdown
# Kill Switch

KILL_SWITCH_TRIGGERED: true
Reason: Emergency shutdown for investigation
Timestamp: 2026-03-08T04:00:00-06:00
ActivatedBy: admin
```

---

## Guardrail 2C: Safety Counter Protection

**Purpose**: Prevent data corruption

**Trigger Condition**: `safety_counter > 0`

**Monitored Counters**:
- real_reply_corruption_count
- active_session_pollution_count

**Actions**:
1. Check counters before compression
2. Alert if non-zero
3. Block compression if violation
4. Require investigation

**Implementation**:
```python
def safety_counter_guardrail(counters: Counters) -> bool:
    if counters.real_reply_corruption_count > 0:
        log_event('safety_violation', {'type': 'reply_corruption'})
        alert_operators('safety_violation')
        return False  # Block compression
    
    if counters.active_session_pollution_count > 0:
        log_event('safety_violation', {'type': 'session_pollution'})
        alert_operators('safety_violation')
        return False  # Block compression
    
    return True  # Allow compression
```

---

## Guardrail 3: Post-Compression Verification

**Purpose**: Verify compression was successful

**Checks**:
1. Post-compression ratio < 0.75
2. Safety counters still zero
3. Evidence package complete
4. State consistent

**Implementation**:
```python
def post_compression_guardrail(
    before: Budget,
    after: Budget,
    counters: Counters
) -> bool:
    # Verify ratio reduced
    if after.ratio >= 0.75:
        log_event('compression_incomplete')
        return False
    
    # Verify safety
    if counters.real_reply_corruption_count > 0:
        log_event('safety_violation')
        return False
    
    # Verify evidence
    if not verify_evidence_package():
        log_event('evidence_incomplete')
        return False
    
    return True
```

---

## Guardrail Event Flow

```
Compression Request
    ↓
Guardrail 1: Pre-Check
    ↓ [pass]
Guardrail 2B: Kill Switch Check
    ↓ [inactive]
Guardrail 2C: Safety Counter Check
    ↓ [all zero]
Guardrail 2A: Threshold Enforcement
    ↓ [ratio >= 0.85]
Execute Compression
    ↓
Guardrail 3: Post-Compression Verification
    ↓ [pass]
Complete
```

---

## Guardrail Failure Handling

### Pre-Check Failure
- Action: Skip compression
- Log: Reason for skip
- Counter: Increment bypass_sessions_total

### Kill Switch Activation
- Action: Block all operations
- Log: Activation event
- Alert: Immediate notification
- Recovery: Manual deactivation required

### Safety Counter Violation
- Action: Block compression
- Log: Violation details
- Alert: Immediate investigation
- Recovery: Root cause analysis required

### Threshold Not Reached
- Action: Continue monitoring
- Log: Current ratio
- No compression triggered

### Post-Compression Failure
- Action: Initiate rollback
- Log: Failure details
- Counter: Increment rollback_event_count
- Recovery: Restore from backup

---

**Document Version**: 1.0
**Last Updated**: 2026-03-08T04:15:00-06:00
**Purpose**: Guardrail System Deep Dive Documentation
