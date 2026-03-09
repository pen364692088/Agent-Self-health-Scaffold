# ROOT_CAUSE_SINGLE_POINT

## Fixed status language
- Config Alignment Gate: PASS
- Phase C / Controlled Validation: PASS
- Phase D / Natural Validation: BLOCKED
- Safeguard bugfix revalidation: FAILED
- Native compaction safeguard bug: OPEN

## Single-point root cause

### File
`/home/moonlight/.npm-global/lib/node_modules/openclaw/node_modules/@mariozechner/pi-coding-agent/dist/core/compaction/compaction.js`

### Function
`prepareCompaction(pathEntries, settings)`

### Approx code region
- `~487`: `const messagesToSummarize = [];`
- `~488-492`: populate from `pathEntries[boundaryStart .. historyEnd)`
- `~494`: `const turnPrefixMessages = [];`
- `~495-500`: populate from split-turn prefix only when `cutPoint.isSplitTurn`
- `~517-525`: return preparation object with both arrays

## Exact empty-path condition
Best current pin:

```js
const historyEnd = cutPoint.isSplitTurn ? cutPoint.turnStartIndex : cutPoint.firstKeptEntryIndex;
const messagesToSummarize = [];
for (let i = boundaryStart; i < historyEnd; i++) { ... }

const turnPrefixMessages = [];
if (cutPoint.isSplitTurn) {
  for (let i = cutPoint.turnStartIndex; i < cutPoint.firstKeptEntryIndex; i++) { ... }
}
```

If the cut point lands exactly at the boundary start and the cut is not a split turn, then both loops are skipped / empty:
- `messagesToSummarize = []`
- `turnPrefixMessages = []`

and the preparation object is returned with both arrays empty.

## Root-cause class
**conditional_skip_not_loaded**

More precise phrasing:
- fields are default-empty initialized
- then never populated because the builder’s cut-point conditions leave no summarizeable history region and no split-turn prefix region

## Why this is closer than the safeguard predicate
Because the safeguard only consumes `preparation`.
The empty arrays are already produced earlier by `prepareCompaction(...)`.
So changing `isRealConversationMessage()` cannot fix an empty builder output.

## Why live Telegram can hit it
The live Telegram session appears to hit a cut-point configuration where:
- kept region starts immediately at `boundaryStart`
- no history exists strictly before the kept region
- cut is not classified as split-turn

That makes both source loops yield nothing even though outer session history is non-empty.

## Why controlled path may differ
Controlled scenarios likely had one of these properties:
- earlier cut point with summarizeable history before it
- split-turn path enabled
- different segment layout in `pathEntries`

So the same builder function would populate arrays there instead of returning both empty.
