# PREPARE_COMPACTION_REGRESSION_TESTS

## Coverage
Four required classes are covered in `tests/prepare_compaction_regression_test.mjs`.

### A. live-like regression
- condition:
  - `firstKeptEntryIndex === boundaryStart`
  - `isSplitTurn === false`
  - real history exists
- expected:
  - throw `invalid_cut_point_empty_preparation`

### B. valid non-split path
- condition:
  - `firstKeptEntryIndex > boundaryStart`
- expected:
  - `messagesToSummarize` fills normally

### C. valid split-turn path
- condition:
  - `isSplitTurn === true`
- expected:
  - `turnPrefixMessages` fills normally

### D. truly empty history
- condition:
  - no real history
- expected:
  - no false safeguard-style semantic
  - empty result shape remains distinguishable from the degenerate real-history case

## Test run
```bash
node artifacts/compaction_safeguard_bugfix/tests/prepare_compaction_regression_test.mjs
```

## Result
- PASS A live-like regression
- PASS B valid non-split path
- PASS C valid split-turn path
- PASS D truly empty history

## Note
These tests intentionally validate the root-cause code region semantics directly, instead of depending on unstable end-to-end cut-point heuristics.
That makes the regression coverage deterministic for the degenerate empty-preparation condition.
