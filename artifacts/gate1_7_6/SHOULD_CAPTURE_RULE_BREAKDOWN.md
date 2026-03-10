# SHOULD_CAPTURE_RULE_BREAKDOWN

Date: 2026-03-10

## shouldCapture() actual logic
From `extensions/memory-lancedb/index.ts`:

```ts
export function shouldCapture(text: string, options?: { maxChars?: number }): boolean {
  const maxChars = options?.maxChars ?? DEFAULT_CAPTURE_MAX_CHARS;
  if (text.length < 10 || text.length > maxChars) return false;
  if (text.includes("<relevant-memories>")) return false;
  if (text.startsWith("<") && text.includes("</")) return false;
  if (text.includes("**") && text.includes("\n-")) return false;
  const emojiCount = (text.match(/[\u{1F300}-\u{1F9FF}]/gu) || []).length;
  if (emojiCount > 3) return false;
  if (looksLikePromptInjection(text)) return false;
  return MEMORY_TRIGGERS.some((r) => r.test(text));
}
```

## Minimum blocking conditions
### accepted path
A text is capturable iff all of these hold:
- length between 10 and `captureMaxChars` (default 500)
- not injected memory wrapper
- not XML/system-like wrapper
- not markdown summary-like
- not emoji-heavy
- not prompt-injection-like
- matches at least one trigger regex

### rejected_by_length
- text length < 10
- text length > maxChars

### rejected_by_source
Any of these is enough:
- contains `<relevant-memories>`
- starts with `<` and contains closing tag
- looks like injected/system/tool/developer content
- markdown-summary-like
- emoji-heavy
- prompt-injection-like

### rejected_by_similarity
Not part of `shouldCapture()`.
Similarity/duplicate suppression happens later in handler via:
```ts
const existing = await db.search(vector, 1, 0.95);
if (existing.length > 0) continue;
```

### rejected_by_importance
Not part of `shouldCapture()`.
Importance is hardcoded at write time:
```ts
importance: 0.7
```

### rejected_by_category
Not part of `shouldCapture()`.
Category is assigned later by `detectCategory()` and does not block capture.

## matched_rules
Current trigger regexes:
- `/zapamatuj si|pamatuj|remember/i`
- `/preferuji|radši|nechci|prefer/i`
- `/rozhodli jsme|budeme používat/i`
- `/\+\d{10,}/`
- `/[\w.-]+@[\w.-]+\.\w+/`
- `/můj\s+\w+\s+je|je\s+můj/i`
- `/my\s+\w+\s+is|is\s+my/i`
- `/i (like|prefer|hate|love|want|need)/i`
- `/always|never|important/i`

## Runtime debug evidence
Observed in gateway logs after debug instrumentation:
- `capture_hook_entered`
- `shouldCapture=false`
- `skip_reason=filtered_all`

The logged text was the injected wrapper starting with:
- `<relevant-memories>...`

So the current minimal runtime blocker is:
- `rejected_by_source=true`
- not category
- not importance
- not similarity
- not LanceDB
- not embeddings
