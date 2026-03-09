# HALF_PATCH_TO_FULL_PATCH

## Final classification

The final root cause was **not** a missed runtime path and **not** loading the wrong file.

It was a **half-patch on the live runtime bundle**:
- compatibility alias was introduced
- but the actual predicate still read the old top-level field

## Broken half-patch shape

```js
const msg = message.message || message;
return message.role === "user" || ...
```

This still fails for nested session entries because the return expression continues to read the top-level object.

## Correct full patch shape

```js
const msg = message.message || message;
return msg.role === "user" || msg.role === "assistant" || msg.role === "toolResult";
```

and

```js
const m = msg.message || msg;
return m.role === "user" || m.role === "assistant" || m.role === "toolResult";
```

## Why this matters

This class of bug can recur when a patch introduces an alias variable but does not fully rewrite all downstream field accesses.

## Preventive rule

When patching schema-compatibility logic:
1. introduce compatibility alias
2. rewrite **all** predicate reads to the alias
3. diff-check final function body, not just marker insertion
4. verify live runtime bundle first, mirror bundles second

Timestamp: 2026-03-08T20:10:00-05:00
