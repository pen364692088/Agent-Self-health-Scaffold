# UNPATCHED_PATH_DIFF

## What was expected
The patch should have transformed all safeguard predicates from top-level role checks to nested-or-flat role checks:

```js
const msg = message.message || message;
return msg.role === "user" || msg.role === "assistant" || msg.role === "toolResult";
```

and:

```js
const m = msg.message || msg;
return m.role === "user" || m.role === "assistant" || m.role === "toolResult";
```

## What the live runtime bundle actually contains
In the direct runtime bundle `reply-C5LKjXcC.js`:

### isRealConversationMessage
```js
function isRealConversationMessage(message) {
    // PATCHED: Support both nested (event) and flat message formats
    const msg = message.message || message;
    return message.role === "user" || message.role === "assistant" || message.role === "toolResult";
}
```

### hasRealConversationContent
```js
function hasRealConversationContent(msg) {
    // PATCHED: Support both nested (event) and flat message formats
    const m = msg.message || msg;
    return m.role === "user" || msg.role === "assistant" || msg.role === "toolResult";
}
```

## Why this still fails
The patch inserted the alias variables (`msg`, `m`) but did **not** fully rewrite all old references in several runtime bundles.

So the active live path still checks the wrong object:
- `message.role` instead of `msg.role`
- `msg.role` instead of `m.role`

For nested entries like:

```json
{
  "type": "message",
  "message": {
    "role": "user"
  }
}
```

the top-level `message.role` is `null/undefined`, so the predicate still returns false and the safeguard cancels compaction.

## Bundle status summary

| Bundle | Status |
|---|---|
| `compact-B247y5Qt.js` | fully patched |
| `reply-C5LKjXcC.js` | partially patched, still broken |
| `pi-embedded-C6ITuRXf.js` | partially patched, still broken |
| `pi-embedded-DoQsYfIY.js` | partially patched, still broken |
| `plugin-sdk/dispatch-*.js` | partially patched, still broken |
| `plugin-sdk/reply-DbZnH8-h.js` | partially patched, still broken |

## Minimal fix
Do a **full variable rewrite** in the real runtime bundle(s), not just marker insertion:

- `message.role` -> `msg.role` inside `isRealConversationMessage`
- `msg.role` -> `m.role` inside `hasRealConversationContent`

Start with `reply-C5LKjXcC.js` because it is directly imported by `index.js` and is the most likely live gateway execution path.
