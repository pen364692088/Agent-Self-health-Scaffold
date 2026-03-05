# Task: MVP11-T21 Eval Script

Create `/home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion/scripts/eval_mvp11.py`

## Requirements

Create one-click evaluation script for MVP11 with 3 modes:

### Mode: quick
- Core loop test
- Key interventions
- Run time: ~1 minute

### Mode: science
- Intervention matrix (P1-P4)
- no-report v2 tasks
- zombie baseline v2
- evidence battery v2
- posterior v2
- Run time: ~5 minutes

### Mode: replay
- Deterministic replay test
- Verify same seed/config produces same output

## Output
- `artifacts/mvp11/` - run logs, evidence, posterior, summary.md

## AC
- pytest -q all green
- MVP10 eval script still works

## Reference

- `/home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion/scripts/eval_mvp10.py` for patterns
