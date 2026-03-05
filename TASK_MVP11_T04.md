# Task: MVP11-T04 Homeostasis Module

Create `/home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion/emotiond/homeostasis.py`

## Requirements

Define HomeostasisState dataclass with 6 dimensions:
- energy_budget: float (0-1) - Available energy/resources
- compute_pressure: float (0-1) - Computational load
- error_pressure: float (0-1) - Error/failure rate
- memory_pressure: float (0-1) - Memory usage pressure
- risk_exposure: float (0-1) - Current risk level
- uncertainty: float (0-1) - Epistemic uncertainty

Implement:
1. `HomeostasisState` dataclass with setpoints for each dimension
2. `HomeostasisManager` class:
   - `update_from_outcome(outcome: Dict)` - Update state based on action outcome
   - `signal() -> Dict` - Generate broadcast signal for workspace arbitration
   - `get_deviation()` - Compute deviation from setpoints
   - `get_recovery_candidates()` - Generate recovery candidates when stressed

Reference existing `/home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion/emotiond/drive_homeostasis.py` for patterns.

## Key Design Points

1. Each dimension has:
   - current value
   - setpoint (optimal value)
   - weight (importance)
   - recovery_rate

2. Update rules:
   - energy_budget decreases with actions, recovers over time
   - compute_pressure increases with complex tasks
   - error_pressure increases on failures
   - memory_pressure increases with large context
   - risk_exposure tracks action risks
   - uncertainty decreases with info-seeking

3. Signal generation:
   - Return dict with: status, urgency, affected_dimensions, suggested_actions
   - Used by workspace arbitration to adjust scores

## Create test

File: `/home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion/tests/mvp11/test_homeostasis_update_rules.py`

Test:
- State updates correctly from outcomes
- Signal generation works
- Recovery candidates are generated when stressed
- Deviation computation is correct
