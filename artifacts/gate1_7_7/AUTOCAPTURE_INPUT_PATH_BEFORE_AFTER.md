# AUTOCAPTURE_INPUT_PATH Before/After

Date: 2026-03-10

---

## Before Fix

### Input Flow

```
agent_end event
  └── event.messages[]
        └── { role: "user", content: "..." }
              │
              ▼
              content = "<relevant-memories>
                          Treat every memory below...
                          1. [preference] I prefer dark mode
                        </relevant-memories>
                        
                        Remember this exactly: AUTOCAPTURE-PROOF-001"
              │
              ▼
              texts.push(content)  <-- POLLUTED TEXT
              │
              ▼
              shouldCapture(content)
                    │
                    ├── content.includes("<relevant-memories>") → TRUE
                    │
                    └── return false  (rejected_by_source)
```

### Log Output

```
memory-lancedb: shouldCapture=false text="<relevant-memories>\\nTreat every memory below...\\n1. [preference] I prefer dark mode\\n</relevant-memories>\\n\\nRemember this exactly: AUTOCAPTURE-PROOF-001"
memory-lancedb: skip_reason=filtered_all
```

### Problem

- User's actual message is buried in wrapper content
- `shouldCapture` sees merged text, not raw user text
- Source guard correctly rejects, but this is a false negative

---

## After Fix

### Input Flow

```
agent_end event
  └── event.messages[]
        └── { role: "user", content: "..." }
              │
              ▼
              content = "<relevant-memories>...
                        </relevant-memories>
                        
                        Remember this exactly: AUTOCAPTURE-PROOF-001"
              │
              ▼
              rawText = extractRawUserText(content)
              │
              ├── Strip leading <relevant-memories>...</relevant-memories>
              │
              └── rawText = "Remember this exactly: AUTOCAPTURE-PROOF-001"
              │
              ▼
              texts.push(rawText)  <-- CLEAN TEXT
              │
              ▼
              shouldCapture(rawText)
                    │
                    ├── /remember/i.test("Remember this exactly: AUTOCAPTURE-PROOF-001") → TRUE
                    │
                    └── return true  (should capture)
```

### Log Output (Expected)

```
memory-lancedb: shouldCapture=true text="Remember this exactly: AUTOCAPTURE-PROOF-001"
memory-lancedb: row_count_before=N
memory-lancedb: embedding_ok text="Remember this exactly: AUTOCAPTURE-PROOF-001"
memory-lancedb: write_ok text="Remember this exactly: AUTOCAPTURE-PROOF-001"
memory-lancedb: row_count_after=N+1
memory-lancedb: auto-captured 1 memories
```

---

## Code Diff

### Added: extractRawUserText helper

```typescript
/**
 * Extract raw user text from potentially wrapper-contaminated content.
 * Strips <relevant-memories> blocks injected by autoRecall.
 */
function extractRawUserText(content: string): string {
  if (!content || typeof content !== 'string') {
    return content;
  }
  // Remove leading <relevant-memories>...</relevant-memories> wrapper
  const stripped = content.replace(
    /^<relevant-memories>[\s\S]*?<\/relevant-memories>\s*/i,
    ''
  ).trim();
  return stripped || content;
}
```

### Modified: agent_end hook

```diff
- if (typeof content === "string") {
-   texts.push(content);
+ if (typeof content === "string") {
+   const rawText = extractRawUserText(content);
+   texts.push(rawText);
```

```diff
- texts.push((block as Record<string, unknown>).text as string);
+ const rawText = extractRawUserText((block as Record<string, unknown>).text as string);
+ texts.push(rawText);
```

---

## Key Design Decision

### Why strip at capture time instead of removing source guard?

1. **Defense in depth**: Source guard remains active for other injection vectors
2. **Explicit separation**: Clear intent that capture evaluates raw user text only
3. **Auditability**: Logs show exactly what text is being evaluated
4. **No false positives**: Wrapper content still rejected if somehow reaches shouldCapture

### Why regex-based strip?

1. **Deterministic**: No complex parsing logic
2. **Specific**: Only targets `<relevant-memories>` wrapper
3. **Safe**: Only removes content at start of message
4. **Fallback**: Returns original content if no wrapper found

---

## Verification

### Unit Test (manual)

```typescript
extractRawUserText("<relevant-memories>foo</relevant-memories>\nbar")
// → "bar"

extractRawUserText("no wrapper here")
// → "no wrapper here"

extractRawUserText("<relevant-memories>\n  1. [preference] dark mode\n</relevant-memories>\n\nRemember this: X")
// → "Remember this: X"
```

### Integration Test

Run positive closed loop test with "Remember this exactly: AUTOCAPTURE-PROOF-001"
