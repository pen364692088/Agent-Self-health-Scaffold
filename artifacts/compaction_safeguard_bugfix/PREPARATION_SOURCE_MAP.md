# PREPARATION_SOURCE_MAP

## Single-point source location

The first real source for both fields is the unminified SDK implementation:

- File: `/home/moonlight/.npm-global/lib/node_modules/openclaw/node_modules/@mariozechner/pi-coding-agent/dist/core/compaction/compaction.js`
- Function: `prepareCompaction(pathEntries, settings)`

This is the internal preparation builder that the minified OpenClaw runtime ultimately relies on.

## Where preparation is created

Inside `prepareCompaction(...)`, the final preparation object is returned as an object literal around lines `517-525`.

## messagesToSummarize source

### First source variable
- `const messagesToSummarize = [];` at approx line `487`

### Population path
- Loop at approx lines `488-492`
- Source array: `pathEntries`
- Source extraction: `getMessageFromEntry(pathEntries[i])`
- Population condition:
  - iterate `i = boundaryStart .. historyEnd-1`
  - only `push(msg)` if `getMessageFromEntry(...)` returns a message

### Key derived bound
- `historyEnd = cutPoint.isSplitTurn ? cutPoint.turnStartIndex : cutPoint.firstKeptEntryIndex`

So `messagesToSummarize` is empty when:
- `historyEnd <= boundaryStart`, meaning there is no history region before the kept region
- or the scanned entries do not yield messages via `getMessageFromEntry`

## turnPrefixMessages source

### First source variable
- `const turnPrefixMessages = [];` at approx line `494`

### Population path
- Conditional block at approx lines `495-500`
- Source array: `pathEntries`
- Source extraction: `getMessageFromEntry(pathEntries[i])`
- Population condition:
  - only if `cutPoint.isSplitTurn`
  - iterate `i = cutPoint.turnStartIndex .. cutPoint.firstKeptEntryIndex-1`
  - only `push(msg)` if `getMessageFromEntry(...)` returns a message

So `turnPrefixMessages` is empty when:
- `cutPoint.isSplitTurn === false`
- or the scanned prefix region yields no message-producing entries

## Do both fields come from the same builder/factory?
Yes.
Both come from the same function: `prepareCompaction(...)`.

## Root-cause class
Current best fit:
- **conditional_skip_not_loaded**

Why this wins over other classes:
- both arrays are initialized empty by default
- both arrays are only populated by conditional loops
- if `historyEnd == boundaryStart` and `cutPoint.isSplitTurn == false`, both remain empty without any later overwrite
- this matches observed runtime better than `loaded_then_overwritten_empty`

## Most likely empty-path condition
The minimal internal empty-path condition is:

```js
const historyEnd = cutPoint.isSplitTurn ? cutPoint.turnStartIndex : cutPoint.firstKeptEntryIndex;
const messagesToSummarize = [];
for (let i = boundaryStart; i < historyEnd; i++) { ... }

const turnPrefixMessages = [];
if (cutPoint.isSplitTurn) {
  for (let i = cutPoint.turnStartIndex; i < cutPoint.firstKeptEntryIndex; i++) { ... }
}
```

If:
- `cutPoint.firstKeptEntryIndex === boundaryStart`
- and `cutPoint.isSplitTurn === false`

then:
- `messagesToSummarize` never loads
- `turnPrefixMessages` never loads
- preparation is returned with both arrays empty

## Why live Telegram likely hits it
The live Telegram session is extremely over-budget but still may produce a cut point at the boundary start of the compaction path segment. In that case the builder interprets the entire available region as “kept” rather than “summarizeable history before kept region”, leaving no pre-cut history and no split-turn prefix.

This is consistent with:
- outer handoff carrying hundreds of valid role-bearing messages
- safeguard still receiving empty preparation arrays

## Why controlled path may not hit it
Controlled validation likely used a different session shape / compaction segment layout where:
- `firstKeptEntryIndex > boundaryStart`, or
- `isSplitTurn === true`, or
- there were ordinary message-producing entries before the cut point

So the builder loops actually populated one or both arrays there.
