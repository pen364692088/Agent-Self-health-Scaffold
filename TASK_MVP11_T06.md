# Task: MVP11-T06 Homeostasis Interventions

Modify /home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion/emotiond/science/interventions.py

## Requirements

Add 2 new interventions:

### 1. disable_homeostasis
- Disable homeostasis signal generation
- HomeostasisManager.signal() returns empty dict
- Used to test: "disable_homeostasis -> 预防性/恢复行为坍塌"

### 2. freeze_homeostasis
- Freeze homeostasis state (no updates from outcomes)
- State remains at current values
- Used to test state dependency

## Reference

Read existing interventions.py at /home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion/emotiond/science/interventions.py for patterns.

## Create test

File: /home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion/tests/mvp11/test_intervention_disable_homeostasis.py

Test:
- disable_homeostasis prevents signal generation
- freeze_homeostasis prevents state updates
- Recovery actions decrease when homeostasis disabled
