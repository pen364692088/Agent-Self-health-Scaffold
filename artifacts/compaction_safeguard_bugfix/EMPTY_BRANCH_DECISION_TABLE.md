# EMPTY_BRANCH_DECISION_TABLE

| Branch / condition | File | Function | Approx line | Effect on messagesToSummarize | Effect on turnPrefixMessages | Hit confidence | Notes |
|---|---|---:|---:|---|---|---|---|
| `pathEntries[last].type === "compaction"` -> `return undefined` | `.../pi-coding-agent/dist/core/compaction/compaction.js` | `prepareCompaction` | ~464 | no preparation | no preparation | low | Would likely skip compaction entirely, not match observed empty preparation hook |
| `!firstKeptEntry?.id` -> `return undefined` | same | `prepareCompaction` | ~482 | no preparation | no preparation | low | Session migration path; unlikely for live repeated repro |
| default empty init `const messagesToSummarize = []` | same | `prepareCompaction` | ~487 | starts empty | n/a | certain | first source |
| population loop `for (i=boundaryStart; i<historyEnd; i++)` | same | `prepareCompaction` | ~488-492 | loads only if history range exists and entries yield messages | n/a | high | if `historyEnd == boundaryStart`, remains empty |
| default empty init `const turnPrefixMessages = []` | same | `prepareCompaction` | ~494 | n/a | starts empty | certain | first source |
| `if (cutPoint.isSplitTurn)` false | same | `prepareCompaction` | ~495 | n/a | stays empty | high | strongest reason for empty turnPrefixMessages |
| prefix population loop | same | `prepareCompaction` | ~496-500 | n/a | loads only on split-turn path and message-producing entries | high | skipped entirely when not split-turn |
| object literal return with both arrays as-is | same | `prepareCompaction` | ~517-525 | returns current array value | returns current array value | certain | no overwrite observed in source |

## Current winner

**conditional_skip_not_loaded**

### Exact likely condition set
- `cutPoint.firstKeptEntryIndex === boundaryStart`
- `cutPoint.isSplitTurn === false`

### Result
- `messagesToSummarize` remains default `[]`
- `turnPrefixMessages` remains default `[]`
- empty preparation is returned directly

## Current confidence
- `conditional_skip_not_loaded`: **high**
- `default_empty_never_loaded`: **high** (mechanically true)
- `fallback_empty_preparation`: **medium-low**
- `loaded_then_overwritten_empty`: **low** (no source evidence in `prepareCompaction`)
