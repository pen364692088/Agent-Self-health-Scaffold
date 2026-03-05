# Task: MVP11-T17 no-report v2 Suite

Create /home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion/emotiond/science/no_report_tasks_v2.py

## Requirements

Create no-report task suite for MVP11 with 4 causal predictions:

### P1: disable_broadcast -> 跨模块整合/长程规划坍塌
- Test that without broadcast, long-range planning and cross-module integration fails
- Measure: planning_depth, cross_module_coherence

### P2: disable_homeostasis -> 预防性/恢复行为坍塌
- Test that without homeostasis, preventive and recovery behaviors disappear
- Measure: recovery_actions, preventive_actions

### P3: remove_self_state -> 自我校准与缺陷归因坍塌
- Test that without self-state, self-calibration and deficit attribution fail
- Measure: self_deficit_attribution, calibration_accuracy

### P4: open_loop -> 自驱与连续性坍塌
- Test that in open-loop mode, self-driven behavior and continuity fail
- Measure: self_driven_actions, continuity_score

## Reference

- /home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion/emotiond/science/no_report_tasks.py for patterns
- Use interventions from emotiond.science.interventions

## Create test

File: /home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion/tests/mvp11/test_no_report_v2_matrix.py

Test:
- Each prediction has threshold for "collapse"
- Normal mode passes, intervention mode shows collapse
