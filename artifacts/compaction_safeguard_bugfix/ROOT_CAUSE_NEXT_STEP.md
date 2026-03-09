# ROOT_CAUSE_NEXT_STEP

## Status
- Config Alignment Gate: PASS
- Phase C / Controlled Validation: PASS
- Phase D / Natural Validation: BLOCKED
- Safeguard bugfix revalidation: FAILED
- Native compaction safeguard bug: OPEN

## Confirmed root-cause statement
The current bug is **not** primarily in the safeguard predicate.

For the real live Telegram session at high context pressure, outer visible compaction-prep stages remain non-empty all the way through the visible `session.compact(...)` handoff, but the hook receives:
- `messagesToSummarize = []`
- `turnPrefixMessages = []`

So the actual emptying occurs **inside the internal preparation builder between outer handoff and `session_before_compact` hook emission**.

## Narrowed root-cause set
At this point the narrowed set is:
1. internal candidate-builder / preparation-builder zeroes both arrays before hook emission
2. internal preparation object is not loaded/populated from the non-empty handoff messages
3. less likely: another unresolved internal runtime path shares the same hook but swaps in an empty preparation object

## Minimal real repair point
The minimal real repair point is the **internal preparation-builder step inside `session.compact(...)`** that populates:
- `preparation.messagesToSummarize`
- `preparation.turnPrefixMessages`

not the safeguard predicate itself.

## Why this is closer than editing safeguard again
Because we now have direct evidence that:
- outer visible stages still carry 285 real messages
- the safeguard receives zero candidates
- therefore the loss occurs before the safeguard makes any semantic decision

Changing `isRealConversationMessage()` again would not repair an already-empty candidate set.

## Next step
Instrument or directly locate the internal preparation-builder function/line inside the `session.compact(...)` path and capture:
- source array name
- builder input count
- builder output count
- exact branch/condition that yields empty `messagesToSummarize` and `turnPrefixMessages`
