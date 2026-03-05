# MVP11 Missing Tasks Context

## Project Path
`/home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion`

## T10: Resource Environment

**File to create**: `emotiond/envs/resource_env.py`

**Requirements**:
- Closed-loop resource sandbox
- Each action has cost (time/energy/risk)
- Environment perturbations (tool failure/latency/spike tasks)
- Integration with homeostasis system

**Key Classes**:
```python
class ResourceEnv:
    def __init__(self, config: dict)
    def step(self, action: dict) -> tuple[dict, float, bool, dict]
    def reset(self) -> dict
    def get_state(self) -> dict
```

**Test file**: `tests/mvp11/test_resource_env_dynamics.py`

---

## T11: Executor Integration

**File to create**: `emotiond/executor_mvp11.py`

**Requirements**:
- Integrate with resource_env
- Update homeostasis from outcome
- Feature flag for MVP11 vs MVP10 behavior

**Key integration points**:
```python
from emotiond.envs.resource_env import ResourceEnv
from emotiond.homeostasis import HomeostasisManager

class ExecutorMVP11:
    def execute(self, action: dict, context: dict) -> dict:
        # 1. Check with resource_env for cost
        # 2. Execute action
        # 3. Update homeostasis from outcome
        pass
```

**Test file**: `tests/mvp11/test_executor_updates_homeostasis.py`

---

## T14: Computational Mirror Test v2

**File to create**: `tests/mvp11/test_computational_mirror_v2.py`

**Requirements**:
- Test self-deficit attribution
- Degrade executor capability (slower/higher failure rate)
- Verify system attributes to self_deficit
- Verify adjusts action_space/plan_depth/info-seeking

**Test scenarios**:
1. Normal operation - no self-deficit
2. Degraded capability - self-deficit attribution
3. Recovery after capability restored

---

## T15: Counterfactual Self Model

**File to create**: `emotiond/self_counterfactual.py`

**Requirements**:
- Compare "what if I had fewer resources/lower precision"
- Execute matching strategy when reality matches counterfactual
- Integration with hot_self_model

**Key Classes**:
```python
class CounterfactualSelfModel:
    def generate_counterfactuals(self, current_state: dict) -> list[dict]
    def compare_strategies(self, actual: dict, counterfactual: dict) -> dict
    def select_strategy(self, state: dict) -> dict
```

**Test file**: `tests/mvp11/test_counterfactual_self_planning.py`

---

## Existing Context

### Homeostasis (emotiond/homeostasis.py)
- 6 dimensions: energy, safety, affiliation, certainty, autonomy, fairness
- Methods: update_from_outcome(), signal(), get_deviation()

### EFE Policy (emotiond/efe_policy.py)
- Computes risk, ambiguity, info_gain, cost
- Integration with homeostasis weights

### Governor v2 (emotiond/governor_v2.py)
- ALLOW / REQUIRE_APPROVAL / DENY decisions
- Anti-self-preservation rules

### Hot Self Model (emotiond/hot_self_model.py)
- Existing self-state tracking
- Integration point for counterfactuals
