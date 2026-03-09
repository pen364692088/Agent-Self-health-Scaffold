# ROOT_FIX_DESIGN

## Scope
Root fix for the degenerate empty-preparation path in `prepareCompaction(...)`.

## Frozen status
- Config Alignment Gate: PASS
- Phase C / Controlled Validation: PASS
- Phase D / Natural Validation: BLOCKED
- Safeguard bugfix revalidation: FAILED
- Native compaction safeguard bug: OPEN

## What this fix targets
This fix targets the **semantic origin** of the failure, not only the immediate downstream symptom.

- Immediate failure point: safeguard receives `messagesToSummarize=[]` and `turnPrefixMessages=[]`
- Semantic origin: `prepareCompaction(pathEntries, settings)` default-initializes both arrays empty and can return them still empty when the cut-point degenerates to:
  - `firstKeptEntryIndex === boundaryStart`
  - `isSplitTurn === false`

## Chosen strategy
**Option B (hotfix with precise reason code)**

Instead of silently returning a normal-looking preparation object with both arrays empty, `prepareCompaction(...)` now raises a precise upstream error:

- `invalid_cut_point_empty_preparation`

This preserves safeguard as the last insurance layer while removing its accidental burden as root-cause recognizer.

## Why Option B now
Option A (reselect cut-point) is semantically better long-term, but it is riskier because it changes compaction selection behavior.

Option B is the smallest safe fix because it:
1. eliminates the silent empty-preparation path
2. emits an exact upstream reason
3. prevents the system from misreporting the situation as a safeguard/message-shape issue
4. keeps the actual compaction strategy unchanged

## Implementation summary
### In `prepareCompaction(...)`
- keep the existing source loops
- after both arrays are built, detect the degenerate case:
  - `messagesToSummarize.length === 0`
  - `turnPrefixMessages.length === 0`
  - and `usageMessages` still contains real conversation history
- throw `InvalidCutPointEmptyPreparationError` with code:
  - `invalid_cut_point_empty_preparation`

### In `agent-session.js`
- catch that precise error in manual compaction path
- catch that precise error in auto-compaction path
- surface the exact reason instead of letting the flow collapse into a generic empty preparation/safeguard symptom

## Questions answered
### 1. Immediate failure point or semantic origin?
Both, but primarily **semantic origin**.

We fix the builder output itself, not just the downstream presentation.

### 2. Why live Telegram hits `firstKeptEntryIndex === boundaryStart && !isSplitTurn`?
Best current explanation: the cut-point lands exactly at the start of the compactable segment, and the branch is classified as non-split-turn, so both population loops become empty.

### 3. Should this combination be viewed as legal or degenerate?
**Degenerate / invalid for compaction preparation** when real history candidates still exist.

If real historical messages exist but both preparation arrays are empty, that is not a meaningful compaction input.

### 4. Why controlled path usually avoids it?
Controlled cases likely have either:
- summarizeable history before the kept region, or
- a split-turn boundary,
so at least one population path loads real messages.

### 5. Can safeguard remain?
**Yes.**

But after this fix, safeguard is restored to being only a final insurance layer, not the place where the real root cause is diagnosed.
