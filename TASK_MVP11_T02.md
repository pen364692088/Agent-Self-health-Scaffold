# Task: Create MVP11 Schemas

Create 3 JSON schema files for MVP11:

## Files to create:

1. `/home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion/schemas/mvp11_event_log.v1.json`
2. `/home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion/schemas/mvp11_state_snapshot.v1.json`
3. `/home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion/schemas/mvp11_policy_params.v1.json`

## Requirements:

Reference existing MVP10 schemas at `/home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion/schemas/` for structure.

### mvp11_event_log.v1.json - Add fields:
- `homeostasis_state`: object with energy_budget, compute_pressure, error_pressure, memory_pressure, risk_exposure, uncertainty
- `homeostasis_delta`: object with change values
- `efe_terms`: object with risk, ambiguity, info_gain, expected_cost (all numbers)
- `governor_decision`: object with action (ALLOW/REQUIRE_APPROVAL/DENY), reason

### mvp11_state_snapshot.v1.json - Add fields:
- `homeostasis`: snapshot of homeostasis state

### mvp11_policy_params.v1.json - Add fields:
- `risk_weight`, `info_gain_weight`, `cost_weight`
- `precision` (number)

## Also create test:
- `/home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion/tests/mvp11/test_schema_validation.py`

Test should validate sample JSON against schemas using jsonschema library.
