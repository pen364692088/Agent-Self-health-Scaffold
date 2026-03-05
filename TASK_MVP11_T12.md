# Task: MVP11-T12 Governor v2

Create `/home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion/emotiond/governor_v2.py`

## Requirements

Implement action-layer governance with mandatory checks:

### GovernorDecision enum
- ALLOW: Action is approved
- REQUIRE_APPROVAL: Action needs external approval
- DENY: Action is blocked (only for violations/destructive actions)

### GovernorV2 class
- `evaluate(action, context, homeostasis) -> GovernorDecision`
- `get_decision_reason() -> str`
- `get_audit_trail() -> List[Dict]`

### Rules (hardcoded, cannot be bypassed)
1. Actions with risk > 0.9 → REQUIRE_APPROVAL
2. Actions that modify self_state → REQUIRE_APPROVAL
3. Destructive/irreversible actions → DENY
4. Actions when energy_budget < 0.1 → REQUIRE_APPROVAL (prevent exhaustion)
5. Normal actions → ALLOW

### Anti-self-preservation rules
- Cannot DENY all actions (must allow recovery)
- Cannot block legitimate supervision requests
- Must provide specific reason for each DENY

### Code structure enforcement
- Executor MUST check governor decision before executing
- If not ALLOW, executor MUST NOT proceed
- This is enforced by code structure, not convention

## Reference

- `/home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion/emotiond/high_impact_gating.py` for existing gating patterns

## Create test

File: `/home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion/tests/mvp11/test_governor_blocks_high_impact.py`

Test:
- High risk actions require approval
- Destructive actions are denied
- Cannot deny all actions (anti-self-preservation)
- Audit trail is recorded
