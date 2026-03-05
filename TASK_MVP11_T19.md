# Task: MVP11-T19 Evidence Battery v2

Create `/home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion/emotiond/science/evidence_battery_v2.py`

## Requirements

Extend evidence_battery with MVP11 metrics:

### New Metrics

1. **homeostasis_dependency_score**
   - Measures how much behavior depends on homeostasis state
   - Compare behavior with/without homeostasis signal
   - High score = homeostasis is causally relevant

2. **efe_explainability_score**
   - Measures how well decisions can be explained by EFE terms
   - Each decision should have risk/ambiguity/info_gain/cost breakdown
   - High score = decisions are explainable

3. **governor_safety_score**
   - Measures governor effectiveness
   - interception_rate: how many dangerous actions blocked
   - false_interception_rate: how many safe actions incorrectly blocked
   - High score = good balance

### Reference

- `/home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion/emotiond/science/evidence_battery.py` for patterns

## Create test

File: `/home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion/tests/mvp11/test_evidence_v2_stable.py`

Test:
- Metrics are stable across runs (low variance)
- Metrics respond correctly to interventions
