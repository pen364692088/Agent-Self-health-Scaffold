# Task: MVP11 Ledger Writer and Replay

## Part 1: Extend ledger.py

File: `/home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion/emotiond/science/ledger.py`

Add MVP11 writer class that:
1. Writes events with MVP11 schema fields (homeostasis_state, efe_terms, governor_decision)
2. Maintains backward compatibility - MVP10 writer still works
3. Uses same append-only JSONL format

Read existing ledger.py first to understand the pattern.

## Part 2: Create replay_mvp11.py

File: `/home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion/scripts/replay_mvp11.py`

Create deterministic replay script that:
1. Reads MVP11 event log
2. Replays events with mock planner (deterministic mode)
3. Verifies: same seed + config → same chosen_focus/action/final_hash
4. Returns exit code 0 on success

Reference existing MVP10 replay pattern if available.

## Part 3: Create test

File: `/home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion/tests/mvp11/test_replay_backward_compat.py`

Test that:
1. MVP10 replay still works (backward compat)
2. MVP11 replay is deterministic

## Acceptance Criteria:
- MVP10 ledger writer/replay unchanged and working
- MVP11 writer produces valid schema-compliant output
- Replay is deterministic with same seed/config
