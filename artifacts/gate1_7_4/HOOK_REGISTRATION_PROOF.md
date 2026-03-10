# HOOK_REGISTRATION_PROOF

Date: 2026-03-10

## Contract proof
From OpenClaw plugin SDK types:
- `agent_end` is a valid `PluginHookName`
- memory-lancedb registers `api.on("agent_end", ...)` when `autoCapture === true`

## Runtime proof
Earlier runtime log showed:

```text
memory-lancedb: capture failed: Error: 404 404 page not found
```

That message is only reachable if:
1. plugin initialized
2. `agent_end` hook fired
3. autoCapture handler executed

Therefore hook registration is not theoretical only; it executed in runtime.

## Conclusion
- hook name valid: YES
- registration path active at runtime: YES
- capture handler entered: YES
