# Memory Capture Registration Fix

**Date**: 2026-03-09
**Status**: FIX REQUIRED - Configuration Gap
**Plugin**: memory-lancedb

---

## Problem Statement

The memory-lancedb plugin's auto-capture feature is not firing because:

1. **Configuration missing**: `embedding.apiKey` is required but not configured
2. **autoCapture defaults to false**: Must be explicitly enabled
3. **Plugin may not initialize**: Without valid config, parse() throws error

---

## Root Cause Analysis

### Configuration Schema

```typescript
// Required fields
{
  "embedding": {
    "apiKey": string,  // REQUIRED - throws if missing
    "model": string,   // optional, default: "text-embedding-3-small"
    "baseUrl": string, // optional
    "dimensions": number // optional
  },
  "autoCapture": boolean,  // optional, DEFAULT: false
  "autoRecall": boolean,   // optional, DEFAULT: true
}
```

### Parse Behavior

```typescript
// From config.ts
parse(value: unknown): MemoryConfig {
    // ...
    if (!embedding || typeof embedding.apiKey !== "string") {
        throw new Error("embedding.apiKey is required");
    }
    // ...
    return {
        autoCapture: cfg.autoCapture === true,  // DEFAULT: false
        // ...
    };
}
```

### Current State

- `~/.openclaw/config.json` does not exist
- No plugin configuration for `memory-lancedb`
- Plugin cannot initialize without required config

---

## Fix: Add Configuration

### Step 1: Create Config File

```bash
mkdir -p ~/.openclaw
```

### Step 2: Add memory-lancedb Configuration

Create or update `~/.openclaw/config.json`:

```json
{
  "plugins": {
    "memory-lancedb": {
      "embedding": {
        "apiKey": "${OPENAI_API_KEY}",
        "baseUrl": "http://192.168.79.1:11434/v1",
        "model": "mxbai-embed-large",
        "dimensions": 1024
      },
      "autoCapture": true,
      "autoRecall": true,
      "captureMaxChars": 500
    }
  }
}
```

### Alternative: OpenAI Configuration

```json
{
  "plugins": {
    "memory-lancedb": {
      "embedding": {
        "apiKey": "${OPENAI_API_KEY}",
        "model": "text-embedding-3-small"
      },
      "autoCapture": true,
      "autoRecall": true
    }
  }
}
```

---

## Implementation Details

### Hook Registration (Already Correct)

```typescript
// From memory-lancedb/index.ts
if (cfg.autoCapture) {
    api.on("agent_end", async (event) => {
        if (!event.success || !event.messages || event.messages.length === 0) {
            return;
        }
        
        // Extract text from user messages
        const texts: string[] = [];
        for (const msg of event.messages) {
            if (msg.role !== "user") continue;
            // ... extract content
        }
        
        // Filter for capturable content
        const toCapture = texts.filter(text => 
            text && shouldCapture(text, { maxChars: cfg.captureMaxChars })
        );
        
        // Store each capturable piece (limit to 3 per conversation)
        for (const text of toCapture.slice(0, 3)) {
            const category = detectCategory(text);
            const vector = await embeddings.embed(text);
            
            // Check for duplicates
            const existing = await db.search(vector, 1, 0.95);
            if (existing.length > 0) continue;
            
            await db.store({ text, vector, importance: 0.7, category });
            stored++;
        }
        
        if (stored > 0) {
            api.logger.info(`memory-lancedb: auto-captured ${stored} memories`);
        }
    });
}
```

### Capture Trigger Patterns

```typescript
const MEMORY_TRIGGERS = [
  /zapamatuj si|pamatuj|remember/i,
  /preferuji|radši|nechci|prefer/i,
  /rozhodli jsme|budeme používat/i,
  /\+\d{10,}/,
  /[\w.-]+@[\w.-]+\.\w+/,
  /můj\s+\w+\s+je|je\s+můj/i,
  /my\s+\w+\s+is|is\s+my/i,
  /i (like|prefer|hate|love|want|need)/i,
  /always|never|important/i,
];
```

---

## Verification Steps

### 1. Verify Config

```bash
cat ~/.openclaw/config.json | jq '.plugins["memory-lancedb"]'
```

Expected output:
```json
{
  "embedding": {
    "apiKey": "${OPENAI_API_KEY}",
    "baseUrl": "http://192.168.79.1:11434/v1",
    "model": "mxbai-embed-large",
    "dimensions": 1024
  },
  "autoCapture": true
}
```

### 2. Restart Gateway

```bash
openclaw gateway restart
```

### 3. Verify Plugin Loaded

```bash
openclaw plugins list | grep memory
```

Expected output:
```
memory-lancedb  (enabled)
```

### 4. Test Capture

Send a message with trigger phrase:
```
"Remember this: I prefer dark mode"
```

Check logs:
```bash
journalctl --user -u openclaw-gateway -f | grep memory-lancedb
```

Expected output:
```
memory-lancedb: auto-captured 1 memories
```

### 5. Verify LanceDB

```bash
ls -la ~/.openclaw/memory/lancedb/
```

Should show `.lance` files with data.

### 6. Test Recall

```bash
openclaw ltm search "dark mode"
```

Expected output:
```json
[
  {
    "id": "...",
    "text": "I prefer dark mode",
    "category": "preference",
    "score": 0.95
  }
]
```

---

## Common Issues

### Issue: Plugin Not Loading

**Cause**: Missing `embedding.apiKey`

**Fix**: Add required config field

### Issue: Capture Not Triggering

**Cause**: `autoCapture` defaults to `false`

**Fix**: Set `autoCapture: true` in config

### Issue: Embedding API Errors

**Cause**: Invalid API key or unreachable base URL

**Fix**: 
1. Verify API key is set: `echo $OPENAI_API_KEY`
2. Test API: `curl http://192.168.79.1:11434/v1/models`

### Issue: LanceDB Not Initialized

**Cause**: No memories captured yet

**Fix**: Trigger capture with test message

---

## Summary

| Issue | Cause | Fix |
|-------|-------|-----|
| Plugin not loading | Missing config | Add `embedding.apiKey` |
| Capture not firing | `autoCapture: false` | Set `autoCapture: true` |
| No memories stored | Never triggered | Send trigger message |
| Recall returns empty | DB empty | Verify capture worked |

**Fix Type**: Configuration gap (not code bug)
