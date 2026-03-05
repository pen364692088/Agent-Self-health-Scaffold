# Task: MVP11-T08 EFE Policy Workspace Integration

Modify /home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion/emotiond/workspace.py

## Requirements

1. Import EFEPolicy from emotiond.efe_policy
2. Modify Arbitrator scoring:
   - score = base_utility - EFE + commitments_bonus
   - EFE = risk * risk_weight + ambiguity * ambiguity_weight - info_gain * info_gain_weight + cost * cost_weight
3. valence_policy becomes precision/weight modulation input:
   - High positive valence → increase info_gain_weight
   - High negative valence → increase risk_weight
4. Add feature flag: ENABLE_EFE_POLICY (default: True)
5. Log efe_terms in arbitration result

## Reference

Read existing workspace.py and valence_policy.py.
Use EFEPolicy from efe_policy.py.

## Create test

File: /home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion/tests/mvp11/test_efe_drives_valence_chain.py

Test:
- EFE affects score calculation
- Valence modulates EFE weights
- Log chain: drives/valence/homeostasis -> policy_params -> efe_terms -> score -> focus
