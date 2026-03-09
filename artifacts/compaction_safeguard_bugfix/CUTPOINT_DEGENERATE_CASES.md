# CUTPOINT_DEGENERATE_CASES

## Degenerate case under fix

### Case 1: Empty summarize window + non-split turn
Condition:
- `firstKeptEntryIndex === boundaryStart`
- `isSplitTurn === false`
- real history candidates exist in `usageMessages`

Effect before fix:
- `messagesToSummarize = []`
- `turnPrefixMessages = []`
- empty preparation returned silently

Effect after fix:
- throw `invalid_cut_point_empty_preparation`

## Non-degenerate cases

### Case 2: Valid non-split path
Condition:
- `firstKeptEntryIndex > boundaryStart`
- `isSplitTurn === false`

Expected:
- `messagesToSummarize` populated
- `turnPrefixMessages` may remain empty legitimately

### Case 3: Valid split-turn path
Condition:
- `isSplitTurn === true`

Expected:
- `turnPrefixMessages` can populate from the turn prefix region
- `messagesToSummarize` may also populate if summarizeable history exists before `turnStartIndex`

### Case 4: Truly empty / non-compactable history
Condition:
- no meaningful compaction history exists
- or preparation cannot be built at all

Expected:
- no fake safeguard-style explanation
- upstream path remains explicitly non-compactable

## Why this cut-point combination is invalid
The builder contract is: if compaction is being prepared and real history exists, preparation must either:
1. provide summarizeable content, or
2. fail explicitly with an upstream reason

A preparation object containing both arrays empty while real history exists violates that contract.
