# GATE1_7_7_VERDICT

Date: 2026-03-10
Gate: 1.7.7 - Source Isolation Fix

---

## Allowed Verdict

**fixed for positive path, guard preserved**

---

## Evidence Summary

### A. Positive Closed Loop ✅

| Check | Result | Evidence |
|-------|--------|----------|
| `embedding_ok` | ✅ | memory_store succeeded |
| `write_ok` | ✅ | LanceDB row count +1 |
| `row_count +1` | ✅ | 1 → 2 |
| `recall_hit` | ✅ | 89% match for AUTOCAPTURE-PROOF-001 |
| `context_injection` | ✅ | 2 memories injected |

### B. Negative Guard Proof ✅

| Guard | Status | Behavior |
|-------|--------|----------|
| `<relevant-memories>` rejection | ✅ Active | Wrapper content rejected |
| XML/system rejection | ✅ Active | System tags rejected |
| Prompt injection detection | ✅ Active | Attack patterns rejected |
| Markdown summary rejection | ✅ Active | Agent output rejected |
| Emoji count limit | ✅ Active | Emoji-heavy content rejected |
| Length limits | ✅ Active | Short/long content rejected |

### C. Source Isolation Fix ✅

**Before Fix:**
```
shouldCapture=false text="<relevant-memories>...user message..."
rejected_by_source = true (false negative)
```

**After Fix:**
```
extractRawUserText() strips wrapper
shouldCapture=true text="Remember this exactly: AUTOCAPTURE-PROOF-001"
shouldCapture = true (correct)
```

---

## Integration Test Results

| Case | Input | Expected | Actual | Status |
|------|-------|----------|--------|--------|
| Wrapper + remember | `<relevant-memories>...Remember this` | shouldCapture=true | shouldCapture=true | ✅ PASS |
| Wrapper + no trigger | `<relevant-memories>...regular msg` | shouldCapture=false | shouldCapture=false | ✅ PASS |
| No wrapper + remember | `Remember this fact` | shouldCapture=true | shouldCapture=true | ✅ PASS |
| Pure wrapper | `<relevant-memories>...` | shouldCapture=false | shouldCapture=false | ✅ PASS |

---

## Code Changes Applied

### File: `~/.npm-global/lib/node_modules/openclaw/extensions/memory-lancedb/index.ts`

**Added:**
```typescript
function extractRawUserText(content: string): string {
  if (!content || typeof content !== 'string') {
    return content;
  }
  const stripped = content.replace(
    /^<relevant-memories>[\s\S]*?<\/relevant-memories>\s*/i,
    ''
  ).trim();
  return stripped || content;
}
```

**Modified:**
```typescript
// In agent_end hook
if (typeof content === "string") {
  const rawText = extractRawUserText(content);
  texts.push(rawText);
}
```

---

## Why This Verdict

1. **Positive path fixed**: `extractRawUserText()` correctly strips `<relevant-memories>` wrapper, allowing valid user text to reach `shouldCapture()`

2. **Guards preserved**: All source guards remain active in `shouldCapture()`, providing defense in depth

3. **No global relaxation**: Did not weaken any security filters; only separated input sources

4. **Logs confirm fix**: After restart, shouldCapture logs show clean text without wrapper prefix

---

## Remaining Observations

1. **AutoCapture trigger scope**: Not all user messages contain MEMORY_TRIGGERS keywords. This is expected behavior.

2. **Direct tool path**: `memory_store` bypasses `agent_end` hook. This is intentional for explicit memory operations.

3. **Edge case: pure wrapper**: When input is only wrapper content, `extractRawUserText()` returns original content (fallback), and `shouldCapture()` correctly rejects it.

---

## Deliverables

| Document | Path |
|----------|------|
| Source Isolation Fix | `artifacts/gate1_7_7/SOURCE_ISOLATION_FIX.md` |
| Before/After Analysis | `artifacts/gate1_7_7/AUTOCAPTURE_INPUT_PATH_BEFORE_AFTER.md` |
| Positive Closed Loop | `artifacts/gate1_7_7/AUTOCAPTURE_POSITIVE_CLOSED_LOOP.md` |
| Negative Guard Proof | `artifacts/gate1_7_7/AUTOCAPTURE_NEGATIVE_GUARD_PROOF.md` |
| Verdict | `artifacts/gate1_7_7/GATE1_7_7_VERDICT.md` |

---

## Conclusion

**Gate 1.7.7: PASSED**

The source isolation fix correctly separates:
- `capture_candidate_text` = raw user-authored message text
- `recall/injected content` = used for reasoning only, not capture evaluation

All negative guards preserved. Positive capture path now works for user messages that:
1. Pass through `agent_end` hook
2. Contain MEMORY_TRIGGERS keywords
3. Are within length limits
4. Don't trigger other guards
