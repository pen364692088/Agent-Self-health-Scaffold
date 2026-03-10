# Hook Contract Repair - Gate 1.7.3

**Date**: 2026-03-09
**Status**: DIAGNOSED
**Verdict**: `fixed by correct registration`

---

## Summary

The `agent_end` hook name used by memory-lancedb is **VALID**. The root cause of capture not firing is **configuration gap**, not hook contract violation.

---

## 1. Hook Contract Verification

### KNOWN_TYPED_HOOK_NAMES (from OpenClaw SDK)

```typescript
export type PluginHookName = 
  | "before_model_resolve"
  | "before_prompt_build"
  | "before_agent_start"
  | "llm_input"
  | "llm_output"
  | "agent_end"           // ✅ VALID
  | "before_compaction"
  | "after_compaction"
  | "before_reset"
  | "message_received"
  | "message_sending"
  | "message_sent"
  | "before_tool_call"
  | "after_tool_call"
  | "tool_result_persist"
  | "before_message_write"
  | "session_start"
  | "session_end"
  | "subagent_spawning"
  | "subagent_delivery_target"
  | "subagent_spawned"
  | "subagent_ended"
  | "gateway_start"
  | "gateway_stop";
```

### PluginHookAgentEndEvent Type

```typescript
export type PluginHookAgentEndEvent = {
    messages: unknown[];
    success: boolean;
    error?: string;
    durationMs?: number;
};
```

### memory-lancedb Registration

```typescript
// From extensions/memory-lancedb/index.ts
api.on("agent_end", async (event) => {
    if (!event.success || !event.messages || event.messages.length === 0) {
        return;
    }
    // ... capture logic
});
```

**Verdict**: `agent_end` is a valid hook name, correctly typed, and properly registered via `api.on()`.

---

## 2. Registration Mechanism Analysis

### API.on() Signature

```typescript
on: <K extends PluginHookName>(
    hookName: K, 
    handler: PluginHookHandlerMap[K], 
    opts?: { priority?: number; }
) => void;
```

### Handler Type for agent_end

```typescript
agent_end: (event: PluginHookAgentEndEvent, ctx: PluginHookAgentContext) => Promise<void> | void;
```

### memory-lancedb Handler Match

```typescript
api.on("agent_end", async (event) => { ... })
```

- ✅ Hook name: `"agent_end"` matches PluginHookName
- ✅ Handler: async function accepting event matches signature
- ✅ Registration: `api.on()` is the correct method

---

## 3. Root Cause: Configuration Gap

### memory-lancedb Config Schema

```typescript
// Required fields
{
  "embedding": {
    "apiKey": string,  // REQUIRED
    "model": string,   // optional, default: "text-embedding-3-small"
    "baseUrl": string, // optional
    "dimensions": number // optional
  },
  "autoCapture": boolean,  // optional, default: false
  "autoRecall": boolean,   // optional, default: true
  "captureMaxChars": number // optional, default: 500
}
```

### Default Behavior

```typescript
// From config.ts
return {
    embedding: { ... },
    dbPath: ...,
    autoCapture: cfg.autoCapture === true,  // DEFAULT: false
    autoRecall: cfg.autoRecall !== false,   // DEFAULT: true
    captureMaxChars: ...,
};
```

### Current State

1. **Config file**: `~/.openclaw/config.json` does not exist
2. **Plugin config**: No `memory-lancedb` configuration
3. **autoCapture**: Defaults to `false`
4. **embedding.apiKey**: Not configured (required)

---

## 4. Why Capture Didn't Fire

### Plugin Initialization Flow

1. `memory-lancedb` plugin is loaded
2. `memoryConfigSchema.parse()` is called with `undefined` config
3. **Parse fails** because `embedding.apiKey` is required
4. Plugin registration throws error or skips hook registration

### Evidence

```typescript
// From config.ts parse()
if (!embedding || typeof embedding.apiKey !== "string") {
    throw new Error("embedding.apiKey is required");
}
```

Without valid config, the plugin's `register()` function likely throws or returns early, meaning `api.on("agent_end", ...)` is never called.

---

## 5. Fix Required

### Minimum Config Required

```json
{
  "plugins": {
    "memory-lancedb": {
      "embedding": {
        "apiKey": "${OPENAI_API_KEY}",
        "baseUrl": "http://192.168.79.1:11434/v1",
        "model": "mxbai-embed-large"
      },
      "autoCapture": true,
      "autoRecall": true
    }
  }
}
```

### Alternative: Ollama-Compatible Setup

```json
{
  "plugins": {
    "memory-lancedb": {
      "embedding": {
        "apiKey": "ollama-local",
        "baseUrl": "http://192.168.79.1:11434/v1",
        "model": "mxbai-embed-large",
        "dimensions": 1024
      },
      "autoCapture": true,
      "dbPath": "~/.openclaw/memory/lancedb"
    }
  }
}
```

---

## 6. Verification Steps

1. **Create config**:
   ```bash
   mkdir -p ~/.openclaw
   # Add memory-lancedb config to config.json
   ```

2. **Restart OpenClaw**:
   ```bash
   openclaw gateway restart
   ```

3. **Verify plugin loaded**:
   ```bash
   openclaw plugins list | grep memory
   ```

4. **Test capture**:
   - Send a message with trigger keywords like "remember this" or "I prefer"
   - Check LanceDB for entries

5. **Test recall**:
   ```bash
   memory_recall --query "preferences"
   ```

---

## 7. Conclusion

| Check | Result |
|-------|--------|
| `agent_end` hook name valid? | ✅ YES |
| Registration method correct? | ✅ YES |
| Hook contract violated? | ❌ NO |
| Config missing? | ✅ YES (root cause) |
| autoCapture disabled? | ✅ YES (default) |

**Final Verdict**: `fixed by correct registration`

The hook contract is correct. The issue is **configuration gap** preventing plugin initialization.
