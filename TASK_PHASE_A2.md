# Phase A.2: E2E Replay Validation Framework

## Context
SELF_REPORT_ALIGNMENT协议已实施。需要验证整条链的确定性：
raw_state → interpreter → contract → LLM → checker

## Goal
构建E2E replay验证框架，验证：
1. 固定raw_state → 固定allowed_claims
2. 固定contract → 固定checker判定
3. 多种表述但同语义时，checker不漏报/乱报

## Architecture

```
raw_state (JSON)
    ↓
self_report_interpreter.py (纯函数)
    ↓
allowed_claims + forbidden_claims
    ↓
contract (JSON)
    ↓
LLM response (多种表述)
    ↓
self_report_consistency_checker.py
    ↓
verdict (OK / VIOLATION)
```

## Implementation Requirements

### File Locations
- `tools/replay_validator.py` - 核心验证器
- `tests/test_e2e_replay.py` - 测试用例

### Core Class
```python
class E2EReplayValidator:
    """Deterministic pipeline validator"""
    
    def __init__(self, interpreter, checker):
        self.interpreter = interpreter
        self.checker = checker
    
    def run_replay(self, raw_state: dict, llm_responses: list[str]) -> ReplayResult:
        """
        Run full pipeline with fixed raw_state.
        Returns: verdict consistency analysis
        """
        
    def verify_determinism(self, raw_state: dict, iterations: int = 10) -> bool:
        """
        Verify: same raw_state always produces same allowed_claims
        """
        
    def verify_semantic_stability(self, contract: dict, responses: list[str]) -> bool:
        """
        Verify: same semantic meaning gets consistent verdict
        """
```

### Test Cases
1. **Determinism Test**: Run interpreter 100 times with same raw_state → all identical
2. **Semantic Stability Test**: 10 different phrasings of same claim → all same verdict
3. **Cross-mode Test**: same response in interpreted vs style_only mode → different verdicts expected

### Acceptance Criteria
- [ ] Determinism: 100 iterations, 0 drifts
- [ ] Semantic stability: 10 phrasings, consistent verdicts
- [ ] Cross-mode: different modes produce expected differences
- [ ] Total test cases ≥ 20

## Project Root
`/home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion`

## Run Tests
```bash
cd /home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion
python3 -m pytest tests/test_e2e_replay.py -v
```
