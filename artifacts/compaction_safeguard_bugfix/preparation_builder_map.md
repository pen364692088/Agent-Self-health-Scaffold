# preparation_builder_map

## Confirmed live path

`index.js` -> `reply-C5LKjXcC.js` -> outer compaction callsite -> `session.compact(...)` -> internal preparation builder -> `compactionSafeguardExtension/session_before_compact`

## What is confirmed

### 1. Who constructs `preparation`
Not the safeguard itself.
`preparation` is already built **inside the internal `session.compact(...)` implementation path** before the `session_before_compact` hook is emitted.

Visible live bundle/file:
- `reply-C5LKjXcC.js`

Visible live wrapper stage:
- outer compaction callsite in `reply-C5LKjXcC.js`
- this wrapper sanitizes / validates / limits / repairs the session history, then calls `session.compact(...)`

### 2. Who fills `messagesToSummarize`
The exact filling line is not exposed in the outer wrapper.
But it is confirmed to happen **after** the visible handoff and **before** `session_before_compact`.
So `messagesToSummarize` originates from the internal preparation builder inside `session.compact(...)`, not from the safeguard extension.

### 3. Who fills `turnPrefixMessages`
Same conclusion as above.
`turnPrefixMessages` is also an internal preparation field produced before the safeguard hook fires.

## Proven boundary

For the real live Telegram session:
- `sessionKey = agent:main:telegram:direct:8420019401`

Visible outer stages all remain non-empty:
- `session_slicing`: 279 -> 285
- `message_normalization`: 285 -> 285
- `turn_extraction`: 285 -> 285
- `pre_compaction_filtering`: 285 -> 285
- `safeguard_handoff`: 285 -> 285

But at the safeguard anchor:
- `messagesToSummarize = 0`
- `turnPrefixMessages = 0`

## Therefore
The emptying does **not** happen in:
- session slicing
- message normalization
- turn extraction
- pre-compaction filtering
- outer handoff

It happens **inside the internal preparation builder between `session.compact(...)` handoff and `session_before_compact` hook emission**.

## Strongest current interpretation
This is much more consistent with:
- `not_loaded_into_preparation`
- or an internal candidate-builder filtering step that zeroes both arrays before the hook

than with:
- safeguard role/content misread
- or outer session trimming
