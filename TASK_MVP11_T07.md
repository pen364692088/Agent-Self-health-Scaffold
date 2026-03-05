# Task: MVP11-T07 EFE Policy Module

Create `/home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion/emotiond/efe_policy.py`

## Requirements

Implement Active-Inference style Expected Free Energy (EFE) policy:

### EFETerms dataclass
- risk: float (0-1) - Expected risk of action
- ambiguity: float (0-1) - Epistemic ambiguity
- info_gain: float (0-1) - Expected information gain
- expected_cost: float (0-1) - Expected resource cost

### EFEPolicy class
Compute EFE terms for candidate actions:
- `compute_efe(candidate, context, homeostasis) -> EFETerms`
- `compute_policy_params(efe_terms) -> PolicyParams`
  - precision: weights for different EFE terms
  - risk_weight, info_gain_weight, cost_weight

### Key formulas
```
EFE = risk * risk_weight - info_gain * info_gain_weight + expected_cost * cost_weight
score = base_utility - EFE + commitments_bonus
```

### Integration
- Use homeostasis state to modulate weights
- High risk_exposure → higher risk_weight
- High uncertainty → higher info_gain_weight
- Low energy_budget → higher cost_weight

## Reference

- `/home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion/emotiond/valence_policy.py` for patterns
- `/home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion/emotiond/drives.py` for drive integration

## Create test

File: `/home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion/tests/mvp11/test_efe_terms_monotonicity.py`

Test:
- Higher risk → higher EFE
- Higher info_gain → lower EFE (exploration bonus)
- Monotonicity: increasing risk monotonically increases EFE
- Weights correctly modulate terms
