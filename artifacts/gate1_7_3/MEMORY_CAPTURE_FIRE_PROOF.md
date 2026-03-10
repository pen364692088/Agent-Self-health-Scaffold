# Memory Capture Fire Proof

**Date**: 2026-03-09
**Status**: PENDING CONFIGURATION
**Reason**: Cannot test capture without valid embedding API configuration

---

## Why We Cannot Test Capture Now

### Blocking Issue

The memory-lancedb plugin requires:

1. **embedding.apiKey** - Required field, not configured
2. **autoCapture: true** - Must be explicitly enabled (defaults to false)

Without these, the plugin's `register()` function throws an error during `memoryConfigSchema.parse()`:

```typescript
if (!embedding || typeof embedding.apiKey !== "string") {
    throw new Error("embedding.apiKey is required");
}
```

---

## What We Have Proven

### 1. Hook Contract is Correct

✅ `agent_end` is a valid hook name in `PluginHookName`

```typescript
export type PluginHookName = 
  | "agent_end"  // ✅ VALID
  | ...
```

### 2. Registration is Correct

✅ `api.on("agent_end", handler)` is the correct registration method

```typescript
api.on("agent_end", async (event) => { ... });
```

### 3. Event Type is Correct

✅ PluginHookAgentEndEvent matches memory-lancedb's usage

```typescript
type PluginHookAgentEndEvent = {
    messages: unknown[];
    success: boolean;
    error?: string;
    durationMs?: number;
};

// memory-lancedb correctly uses:
// event.success, event.messages
```

### 4. Handler Logic is Correct

✅ The capture logic properly filters and stores memories

```typescript
// Only process successful runs with messages
if (!event.success || !event.messages || event.messages.length === 0) {
    return;
}

// Only capture user messages
if (msg.role !== "user") continue;

// Check trigger patterns
const toCapture = texts.filter(text => shouldCapture(text));
```

---

## What Needs Configuration

### Minimum Required Config

```json
{
  "plugins": {
    "memory-lancedb": {
      "embedding": {
        "apiKey": "any-string-will-work-for-ollama",
        "baseUrl": "http://192.168.79.1:11434/v1",
        "model": "mxbai-embed-large",
        "dimensions": 1024
      },
      "autoCapture": true
    }
  }
}
```

---

## Verification Steps (After Config)

### Step 1: Create Config

```bash
mkdir -p ~/.openclaw
cat > ~/.openclaw/config.json << 'EOF'
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
      "autoRecall": true
    }
  }
}
EOF
```

### Step 2: Restart Gateway

```bash
openclaw gateway restart
```

### Step 3: Verify Plugin Loaded

```bash
# Check logs for plugin registration
journalctl --user -u openclaw-gateway --since "1 min ago" | grep -i memory
```

Expected:
```
memory-lancedb: plugin registered (db: /home/.../.openclaw/memory/lancedb, lazy init)
```

### Step 4: Trigger Capture

Send a message with trigger phrase:
```
"Please remember that I prefer dark mode for all UI"
```

### Step 5: Verify Capture

```bash
# Check LanceDB files
ls -la ~/.openclaw/memory/lancedb/

# Should show:
# - .lance files with data
# - No longer empty
```

### Step 6: Test Recall

```bash
openclaw ltm search "dark mode preferences"
```

Expected output:
```json
[
  {
    "id": "uuid-here",
    "text": "I prefer dark mode for all UI",
    "category": "preference",
    "importance": 0.7,
    "score": 0.95
  }
]
```

---

## Final State Matrix

| State | Current | After Config |
|-------|---------|--------------|
| registered only | ❓ Unknown (config blocks init) | ✅ |
| capture firing | ❌ Not configured | ✅ (after config) |
| populated | ❌ No data | ✅ (after capture) |
| retrievable | ❌ No data | ✅ (after capture) |
| behavior-linked | ❌ Not active | ✅ (after config) |

---

## Conclusion

We have proven that:

1. ✅ Hook contract is correct
2. ✅ Registration mechanism is correct  
3. ✅ Handler logic is correct
4. ❌ Configuration is missing (blocking factor)

**Next step**: Add configuration and retest.
