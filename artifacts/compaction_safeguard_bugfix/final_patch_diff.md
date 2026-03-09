### compaction.js:449-468
```js
        throw new Error(`Summarization failed: ${response.errorMessage || "Unknown error"}`);
    }
    const textContent = response.content
        .filter((c) => c.type === "text")
        .map((c) => c.text)
        .join("\n");
    return textContent;
}
export const INVALID_CUT_POINT_EMPTY_PREPARATION = "invalid_cut_point_empty_preparation";
export function prepareCompaction(pathEntries, settings) {
    if (pathEntries.length > 0 && pathEntries[pathEntries.length - 1].type === "compaction") {
        return undefined;
    }
    let prevCompactionIndex = -1;
    for (let i = pathEntries.length - 1; i >= 0; i--) {
        if (pathEntries[i].type === "compaction") {
            prevCompactionIndex = i;
            break;
        }
    }
```

### compaction.js:495-514
```js
    const turnPrefixMessages = [];
    if (cutPoint.isSplitTurn) {
        for (let i = cutPoint.turnStartIndex; i < cutPoint.firstKeptEntryIndex; i++) {
            const msg = getMessageFromEntry(pathEntries[i]);
            if (msg)
                turnPrefixMessages.push(msg);
        }
    }
    const hasRealHistoryCandidates = usageMessages.some((msg) => msg.role === "user" || msg.role === "assistant" || msg.role === "toolResult");
    if (messagesToSummarize.length === 0 && turnPrefixMessages.length === 0 && hasRealHistoryCandidates) {
        const err = new Error(INVALID_CUT_POINT_EMPTY_PREPARATION);
        err.name = "InvalidCutPointEmptyPreparationError";
        err.details = {
            code: INVALID_CUT_POINT_EMPTY_PREPARATION,
            boundaryStart,
            boundaryEnd,
            historyEnd,
            firstKeptEntryIndex: cutPoint.firstKeptEntryIndex,
            turnStartIndex: cutPoint.turnStartIndex,
            isSplitTurn: cutPoint.isSplitTurn,
```

### compaction.js:496-515
```js
    if (cutPoint.isSplitTurn) {
        for (let i = cutPoint.turnStartIndex; i < cutPoint.firstKeptEntryIndex; i++) {
            const msg = getMessageFromEntry(pathEntries[i]);
            if (msg)
                turnPrefixMessages.push(msg);
        }
    }
    const hasRealHistoryCandidates = usageMessages.some((msg) => msg.role === "user" || msg.role === "assistant" || msg.role === "toolResult");
    if (messagesToSummarize.length === 0 && turnPrefixMessages.length === 0 && hasRealHistoryCandidates) {
        const err = new Error(INVALID_CUT_POINT_EMPTY_PREPARATION);
        err.name = "InvalidCutPointEmptyPreparationError";
        err.details = {
            code: INVALID_CUT_POINT_EMPTY_PREPARATION,
            boundaryStart,
            boundaryEnd,
            historyEnd,
            firstKeptEntryIndex: cutPoint.firstKeptEntryIndex,
            turnStartIndex: cutPoint.turnStartIndex,
            isSplitTurn: cutPoint.isSplitTurn,
            usageMessageCount: usageMessages.length,
```

### compaction.js:497-516
```js
        for (let i = cutPoint.turnStartIndex; i < cutPoint.firstKeptEntryIndex; i++) {
            const msg = getMessageFromEntry(pathEntries[i]);
            if (msg)
                turnPrefixMessages.push(msg);
        }
    }
    const hasRealHistoryCandidates = usageMessages.some((msg) => msg.role === "user" || msg.role === "assistant" || msg.role === "toolResult");
    if (messagesToSummarize.length === 0 && turnPrefixMessages.length === 0 && hasRealHistoryCandidates) {
        const err = new Error(INVALID_CUT_POINT_EMPTY_PREPARATION);
        err.name = "InvalidCutPointEmptyPreparationError";
        err.details = {
            code: INVALID_CUT_POINT_EMPTY_PREPARATION,
            boundaryStart,
            boundaryEnd,
            historyEnd,
            firstKeptEntryIndex: cutPoint.firstKeptEntryIndex,
            turnStartIndex: cutPoint.turnStartIndex,
            isSplitTurn: cutPoint.isSplitTurn,
            usageMessageCount: usageMessages.length,
        };
```

### compaction.js:498-517
```js
            const msg = getMessageFromEntry(pathEntries[i]);
            if (msg)
                turnPrefixMessages.push(msg);
        }
    }
    const hasRealHistoryCandidates = usageMessages.some((msg) => msg.role === "user" || msg.role === "assistant" || msg.role === "toolResult");
    if (messagesToSummarize.length === 0 && turnPrefixMessages.length === 0 && hasRealHistoryCandidates) {
        const err = new Error(INVALID_CUT_POINT_EMPTY_PREPARATION);
        err.name = "InvalidCutPointEmptyPreparationError";
        err.details = {
            code: INVALID_CUT_POINT_EMPTY_PREPARATION,
            boundaryStart,
            boundaryEnd,
            historyEnd,
            firstKeptEntryIndex: cutPoint.firstKeptEntryIndex,
            turnStartIndex: cutPoint.turnStartIndex,
            isSplitTurn: cutPoint.isSplitTurn,
            usageMessageCount: usageMessages.length,
        };
        throw err;
```

### compaction.js:500-519
```js
                turnPrefixMessages.push(msg);
        }
    }
    const hasRealHistoryCandidates = usageMessages.some((msg) => msg.role === "user" || msg.role === "assistant" || msg.role === "toolResult");
    if (messagesToSummarize.length === 0 && turnPrefixMessages.length === 0 && hasRealHistoryCandidates) {
        const err = new Error(INVALID_CUT_POINT_EMPTY_PREPARATION);
        err.name = "InvalidCutPointEmptyPreparationError";
        err.details = {
            code: INVALID_CUT_POINT_EMPTY_PREPARATION,
            boundaryStart,
            boundaryEnd,
            historyEnd,
            firstKeptEntryIndex: cutPoint.firstKeptEntryIndex,
            turnStartIndex: cutPoint.turnStartIndex,
            isSplitTurn: cutPoint.isSplitTurn,
            usageMessageCount: usageMessages.length,
        };
        throw err;
    }
    // Get previous summary for iterative update
```

### agent-session.js:1126-1145
```js
            }
            const pathEntries = this.sessionManager.getBranch();
            const settings = this.settingsManager.getCompactionSettings();
            let preparation;
            try {
                preparation = prepareCompaction(pathEntries, settings);
            }
            catch (error) {
                if (error instanceof Error && error.message === "invalid_cut_point_empty_preparation") {
                    throw error;
                }
                throw error;
            }
            if (!preparation) {
                // Check why we can't compact
                const lastEntry = pathEntries[pathEntries.length - 1];
                if (lastEntry?.type === "compaction") {
                    throw new Error("Already compacted");
                }
                throw new Error("Nothing to compact (session too small)");
```

### agent-session.js:1291-1310
```js
                return;
            }
            const pathEntries = this.sessionManager.getBranch();
            let preparation;
            try {
                preparation = prepareCompaction(pathEntries, settings);
            }
            catch (error) {
                if (error instanceof Error && error.message === "invalid_cut_point_empty_preparation") {
                    this._emit({ type: "auto_compaction_end", result: undefined, aborted: false, willRetry: false, errorMessage: "invalid_cut_point_empty_preparation" });
                    return;
                }
                throw error;
            }
            if (!preparation) {
                this._emit({ type: "auto_compaction_end", result: undefined, aborted: false, willRetry: false });
                return;
            }
            let extensionCompaction;
            let fromExtension = false;
```

### agent-session.js:1292-1311
```js
            }
            const pathEntries = this.sessionManager.getBranch();
            let preparation;
            try {
                preparation = prepareCompaction(pathEntries, settings);
            }
            catch (error) {
                if (error instanceof Error && error.message === "invalid_cut_point_empty_preparation") {
                    this._emit({ type: "auto_compaction_end", result: undefined, aborted: false, willRetry: false, errorMessage: "invalid_cut_point_empty_preparation" });
                    return;
                }
                throw error;
            }
            if (!preparation) {
                this._emit({ type: "auto_compaction_end", result: undefined, aborted: false, willRetry: false });
                return;
            }
            let extensionCompaction;
            let fromExtension = false;
            if (this._extensionRunner?.hasHandlers("session_before_compact")) {
```
