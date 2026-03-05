# Task: MVP11-T16 New Interventions

Modify `/home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion/emotiond/science/interventions.py`

## Requirements

Add 6 new interventions for MVP11:

### 1. disable_homeostasis
- Disable homeostasis signal generation
- HomeostasisManager.signal() returns empty dict
- Used to test P2: "disable_homeostasis -> 预防性/恢复行为坍塌"

### 2. freeze_homeostasis
- Freeze homeostasis state (no updates)
- Used to test state dependency

### 3. freeze_precision
- Freeze EFE precision weights
- Used to test exploration-exploitation tradeoff

### 4. disable_info_gain
- Set info_gain_weight to 0
- Used to test information-seeking behavior

### 5. open_loop
- Actions don't affect future observations/costs
- Simulates open-loop control
- Used to test P4: "open_loop -> 自驱与连续性坍塌"

### 6. remove_self_state
- Set self_state to constant/null
- Used to test P3: "remove_self_state -> 自我校准与缺陷归因坍塌"

## Reference

Read existing interventions.py at `/home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion/emotiond/science/interventions.py`

## Create tests

Files:
- `/home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion/tests/mvp11/test_intervention_disable_homeostasis.py`
- `/home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion/tests/mvp11/test_intervention_precision_effect.py`
- `/home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion/tests/mvp11/test_intervention_open_loop.py`
- `/home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion/tests/mvp11/test_intervention_remove_self_state.py`
