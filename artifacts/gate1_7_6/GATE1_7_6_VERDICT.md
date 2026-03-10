# GATE1_7_6_VERDICT

Date: 2026-03-10

## Allowed verdict
narrowed further but no positive sample yet

## Reason
### What is now proven
- `shouldCapture()` itself accepts valid memory-like inputs
- positive samples exist for preference, instruction, profile fact, and proof token formats
- current runtime path reaches autoCapture handler
- current runtime path feeds wrapper-contaminated text into `shouldCapture()`
- that text is rejected by source guards, not by category/importance/similarity

### What is not yet proven
- a full end-to-end positive autoCapture write in the current normal path
- `embedding_ok`
- `write_ok`
- `row_count +1`
- recall hit for `AUTOCAPTURE-PROOF-001`

## Root cause narrowed to
Current minimal blocker:
- `rejected_by_source=true`
- because input contains `<relevant-memories>` wrapper content

Not blocked by:
- trigger regex strictness alone
- category classification
- importance threshold
- similarity threshold inside `shouldCapture()`

## Short version
The policy is not globally too strict.
The normal path is currently evaluating the wrong text.

## Practical next step
Fix source isolation before policy relaxation:
- evaluate raw user text only
- exclude or strip recalled wrapper content before `shouldCapture()`
