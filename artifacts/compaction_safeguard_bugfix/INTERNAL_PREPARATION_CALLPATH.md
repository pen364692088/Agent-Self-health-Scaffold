# INTERNAL_PREPARATION_CALLPATH

## Confirmed internal call chain

For the live Telegram session `agent:main:telegram:direct:8420019401`, the confirmed chain is:

1. `reply-C5LKjXcC.js:5263`
   - `async compact(params)`
   - Session wrapper entry
   - Dynamically imports `compactEmbeddedPiSessionDirect` from `compact.runtime-DsDWWmcn.js`

2. `compact.runtime-DsDWWmcn.js:5`
   - re-exports `compactEmbeddedPiSessionDirect` from `reply-C5LKjXcC.js`
   - not a real implementation layer; forwarding only

3. `reply-C5LKjXcC.js:74319`
   - `async function compactEmbeddedPiSessionDirect(params)`
   - real direct compaction implementation

4. `reply-C5LKjXcC.js:74619-74645` (approx)
   - visible outer preparation stages:
     - `sanitizeSessionHistory`
     - `validateTurns`
     - `limitHistoryTurns`
     - `sanitizeToolUseResultPairing`
   - all remain non-empty for live Telegram session

5. `reply-C5LKjXcC.js:74713`
   - `const result = await compactWithSafetyTimeout(() => session.compact(params.customInstructions));`
   - this is the **handoff into the unresolved internal builder path**

6. inside internal `session.compact(...)`
   - preparation is built
   - `session_before_compact` hook is emitted
   - safeguard sees:
     - `messagesToSummarize = []`
     - `turnPrefixMessages = []`

7. `reply-C5LKjXcC.js` safeguard hook
   - `compactionSafeguardExtension/session_before_compact`
   - first observable empty state

## Last non-empty vs first empty

### Last non-empty stage
- file: `reply-C5LKjXcC.js`
- function: `compactEmbeddedPiSessionDirect`
- code region: ~`74645`
- stage: `safeguard_handoff`
- count: `342 -> 342` (latest live sample)

### First empty stage
- file: `reply-C5LKjXcC.js`
- function: `compactionSafeguardExtension/session_before_compact`
- code region: safeguard hook body
- observed state:
  - `messageCount = 0`
  - `turnPrefixCount = 0`
  - `reasonCode = upstream_empty_candidate_set`

## Empty assignment point
**Not yet directly observed as a source line assignment**, but the boundary is now tight:

- after `reply-C5LKjXcC.js:74713` handoff
- before safeguard hook execution

This means the empty preparation is produced **inside the internal implementation of `session.compact(...)`**, not by the outer wrapper and not by the safeguard predicate.

## Strongest current interpretation
Weighting:
- **High confidence**: `not_loaded_into_preparation`
- **Medium/low confidence**: `loaded_then_cleared_by_internal_builder`

Why:
- outer handoff contains hundreds of valid message objects with roles/content
- safeguard receives both arrays empty at first observation point
- no visible intermediate stage shows a non-empty `messagesToSummarize` or `turnPrefixMessages`
- that pattern fits "never populated into preparation" better than "populated then cleared", though the latter is not fully excluded without deeper internal write-trace
