# Auto-Compaction Policy v1.0

## Overview

This document defines the automatic compression trigger policy for the OpenClaw context compression system. It specifies when compression should be triggered, the compression modes, cooldown periods, and hysteresis logic.

---

## Trigger Thresholds

### Normal Compression

| Parameter | Value |
|-----------|-------|
| **Trigger Ratio** | `>= 0.80` |
| **Target Ratio** | `0.55 - 0.65` |
| **Mode** | Standard summarization + handoff |
| **Priority** | Normal |

**Behavior**:
- When context ratio reaches 0.80 (80%), prepare for compression
- Requires all blockers to be resolved (see COMPACTION_BLOCKERS.md)
- Compress to target ratio 0.55-0.65
- Log decision with reason and blockers checked

### Emergency Compression

| Parameter | Value |
|-----------|-------|
| **Trigger Ratio** | `>= 0.90` |
| **Target Ratio** | `0.45 - 0.55` |
| **Mode** | Aggressive summarization |
| **Priority** | Critical |
| **Cooldown Bypass** | Yes |

**Behavior**:
- When context ratio reaches 0.90 (90%), immediate compression required
- May bypass certain blockers (see bypass conditions below)
- Compress to target ratio 0.45-0.55
- Must persist critical state before compression
- Log as emergency event

---

## Cooldown Mechanism

### Purpose
Prevent rapid repeated compressions that could destabilize the session.

### Rules

| Condition | Minimum Interval |
|-----------|------------------|
| Normal → Normal | 30 minutes |
| Emergency → Normal | 15 minutes |
| Emergency → Emergency | 10 minutes |

### Cooldown State File

Location: `artifacts/context_compression/cooldown_state.json`

```json
{
  "last_compaction_time": "2026-03-09T14:30:00Z",
  "last_compaction_mode": "normal",
  "compaction_count": 3,
  "session_id": "agent:main:..."
}
```

### Cooldown Bypass (Emergency Only)

Emergency compression may bypass cooldown if:
1. Ratio >= 0.95 (imminent overflow)
2. Critical task in progress that cannot be paused
3. User explicitly requested bypass

**Bypass requires**:
- Log justification
- Force flag in trigger-policy
- Post-compression audit

---

## Hysteresis Logic

### Purpose
Prevent oscillation between states when ratio hovers near thresholds.

### State Transitions

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   0.75      0.80       0.85      0.90       0.95           │
│    │         │          │         │          │              │
│    ▼         ▼          ▼         ▼          ▼              │
│   ────────────────────────────────────────────────          │
│    ↑                    ↑                    ↑              │
│    │                    │                    │              │
│  Exit                  Exit                Enter            │
│  Warning             Emergency            Emergency         │
│  (from                (from              (from              │
│  warning)            emergency)          warning)           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Hysteresis Thresholds

| Transition | Threshold | Explanation |
|------------|-----------|-------------|
| Normal → Warning | ratio >= 0.80 | Enter warning zone |
| Warning → Normal | ratio < 0.75 | Must drop 5% below trigger to exit |
| Warning → Emergency | ratio >= 0.90 | Escalate to emergency |
| Emergency → Warning | ratio < 0.85 | Must drop 5% below emergency to exit |

### State Machine

```python
# Simplified state machine
def determine_action(current_ratio, previous_zone, cooldown_state):
    # Check cooldown first (unless emergency)
    if cooldown_state.in_cooldown and current_ratio < 0.90:
        return "none", "in_cooldown"
    
    # Emergency zone
    if current_ratio >= 0.90:
        return "emergency", "ratio_threshold_exceeded"
    
    # Warning zone with hysteresis
    if previous_zone == "warning":
        if current_ratio < 0.75:
            return "none", "exited_warning_zone"
        elif current_ratio >= 0.80:
            return "normal", "ratio_threshold_exceeded"
        else:
            return "none", "hysteresis_hold"
    
    if current_ratio >= 0.80:
        return "normal", "ratio_threshold_exceeded"
    
    return "none", "below_threshold"
```

---

## Decision Flow

```
                    ┌─────────────────┐
                    │  Get Ratio      │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ ratio >= 0.90?  │
                    └────────┬────────┘
                             │
              ┌──────────────┴──────────────┐
              │ Yes                         │ No
              ▼                             ▼
     ┌────────────────┐            ┌────────────────┐
     │ EMERGENCY      │            │ ratio >= 0.80? │
     │ Bypass blockers│            └────────┬───────┘
     │ Force compress │                     │
     └────────────────┘          ┌──────────┴──────────┐
                                 │ Yes                 │ No
                                 ▼                     ▼
                        ┌────────────────┐    ┌──────────────┐
                        │ Check blockers │    │ NO ACTION    │
                        └────────┬───────┘    └──────────────┘
                                 │
                        ┌────────▼────────┐
                        │ All resolved?   │
                        └────────┬────────┘
                                 │
                    ┌────────────┴────────────┐
                    │ Yes                     │ No
                    ▼                         ▼
           ┌────────────────┐        ┌──────────────────┐
           │ NORMAL         │        │ BLOCKED          │
           │ Compress       │        │ Report blockers  │
           └────────────────┘        └──────────────────┘
```

---

## Compaction Target Calculation

### Normal Compression
```python
def calculate_normal_target(current_ratio):
    """
    Calculate target ratio for normal compression.
    
    Target: 0.55 - 0.65 (aim for 0.60)
    """
    target = 0.60
    min_target = 0.55
    max_target = 0.65
    
    # If already below target, no compression needed
    if current_ratio <= target:
        return None
    
    return target
```

### Emergency Compression
```python
def calculate_emergency_target(current_ratio):
    """
    Calculate target ratio for emergency compression.
    
    Target: 0.45 - 0.55 (aim for 0.50)
    """
    target = 0.50
    min_target = 0.45
    max_target = 0.55
    
    # If already below target, no compression needed
    if current_ratio <= target:
        return None
    
    return target
```

---

## Logging Requirements

Every trigger decision must be logged:

```json
{
  "timestamp": "2026-03-09T14:30:00Z",
  "event": "trigger_decision",
  "ratio": 0.82,
  "previous_zone": "normal",
  "action": "normal",
  "reason": "ratio_threshold_exceeded",
  "blockers": [],
  "cooldown_remaining": null,
  "session_id": "agent:main:..."
}
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-03-09 | Initial policy definition |
