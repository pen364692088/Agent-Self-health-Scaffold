# Task: MVP11-T05 Homeostasis Workspace Integration

Modify `/home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion/emotiond/workspace.py`

## Requirements

1. Add homeostasis-driven candidates to CandidatePool:
   - rest/recover (when energy low)
   - simplify_plan (when compute_pressure high)
   - seek_info (when uncertainty high)
   - defer_high_risk (when risk_exposure high)

2. Modify Arbitrator to include homeostasis signal in scoring:
   - `score = base_score + homeostasis_adjustment`
   - homeostasis_adjustment based on signal.urgency and signal.suggested_actions

3. Add feature flag:
   - `ENABLE_HOMEOSTASIS` (default: True)
   - When False, skip homeostasis candidates and adjustment

4. Log homeostasis_state and homeostasis_delta in arbitration result

## Reference

Read existing workspace.py at `/home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion/emotiond/workspace.py`
Use HomeostasisManager from `emotiond.homeostasis`

## Create test

File: `/home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion/tests/mvp11/test_homeostasis_affects_focus.py`

Test:
- Different homeostasis states lead to different focus choices
- Recovery candidates appear when stressed
- Feature flag works correctly
