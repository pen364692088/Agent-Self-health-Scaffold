# ROOT_CAUSE_FUNCTION_PIN

## Fixed status language
- Config Alignment Gate: PASS
- Phase C / Controlled Validation: PASS
- Phase D / Natural Validation: BLOCKED
- Safeguard bugfix revalidation: FAILED
- Native compaction safeguard bug: OPEN

## Pinned function boundary

### Confirmed outer internal entry
- file: `reply-C5LKjXcC.js`
- function: `compact(params)`
- approx line: `5263`
- role: wrapper entry into compaction runtime

### Confirmed direct implementation entry
- file: `reply-C5LKjXcC.js`
- function: `compactEmbeddedPiSessionDirect(params)`
- approx line: `74319`
- role: real direct compaction implementation

### Confirmed last non-empty handoff
- file: `reply-C5LKjXcC.js`
- function: `session.compact(...)` callsite inside `compactEmbeddedPiSessionDirect`
- approx line: `74713`
- evidence: live Telegram session still carries 342 valid messages at this point

### Confirmed first empty observation
- file: `reply-C5LKjXcC.js`
- function: `compactionSafeguardExtension/session_before_compact`
- approx line: `~72890`
- evidence: `messagesToSummarize = []`, `turnPrefixMessages = []`

## Exact clear condition
Not yet pinned to a single source line assignment.

What is pinned is the **smallest failure window**:
- after `reply-C5LKjXcC.js:74713`
- before safeguard hook execution

So the current best file/function pin is:
- **file**: `reply-C5LKjXcC.js`
- **function region**: internal implementation entered via `session.compact(...)` from `compactEmbeddedPiSessionDirect`
- **approx region**: immediately downstream of the callsite at `74713`, before the safeguard hook sees `preparation`

## Root-cause classification
Current weighting:
1. **not_loaded_into_preparation** — strongest
2. **loaded_then_cleared_by_internal_builder** — possible but weaker

## Why this is closer than editing safeguard again
Because the live Telegram session proves:
- outer stages preserve hundreds of valid role-bearing messages
- the first empty observation is already at the hook boundary
- therefore the loss happens before safeguard semantic checks are even relevant

## Minimal repair point candidate
The minimal real repair point is **inside the internal `session.compact(...)` preparation population path**, specifically the step that should populate:
- `preparation.messagesToSummarize`
- `preparation.turnPrefixMessages`

A real fix should target that builder/population branch, not the safeguard predicate.
