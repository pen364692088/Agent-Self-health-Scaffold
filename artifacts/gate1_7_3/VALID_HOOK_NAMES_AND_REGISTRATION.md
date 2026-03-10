# Valid Hook Names and Registration Guide

**Date**: 2026-03-09
**OpenClaw Version**: Latest (installed via npm)

---

## Complete Hook Names List

The following hook names are valid in OpenClaw's plugin system:

| Hook Name | Category | Description |
|-----------|----------|-------------|
| `before_model_resolve` | Agent | Before model selection |
| `before_prompt_build` | Agent | Before prompt assembly |
| `before_agent_start` | Agent | Before agent begins processing |
| `llm_input` | LLM | LLM input event |
| `llm_output` | LLM | LLM output event |
| `agent_end` | Agent | **After agent completes** |
| `before_compaction` | Context | Before context compaction |
| `after_compaction` | Context | After context compaction |
| `before_reset` | Session | Before session reset |
| `message_received` | Messaging | When message received |
| `message_sending` | Messaging | Before message sent |
| `message_sent` | Messaging | After message sent |
| `before_tool_call` | Tools | Before tool execution |
| `after_tool_call` | Tools | After tool execution |
| `tool_result_persist` | Tools | Tool result persistence |
| `before_message_write` | Session | Before message written |
| `session_start` | Session | Session started |
| `session_end` | Session | Session ended |
| `subagent_spawning` | Subagent | Before subagent spawn |
| `subagent_delivery_target` | Subagent | Subagent delivery target |
| `subagent_spawned` | Subagent | After subagent spawned |
| `subagent_ended` | Subagent | Subagent ended |
| `gateway_start` | Gateway | Gateway started |
| `gateway_stop` | Gateway | Gateway stopped |

---

## Agent Completion Hooks

For memory capture functionality, the following hooks can be used:

### 1. `agent_end` (Recommended)

```typescript
api.on("agent_end", async (event, ctx) => {
    // event: PluginHookAgentEndEvent
    // {
    //   messages: unknown[];
    //   success: boolean;
    //   error?: string;
    //   durationMs?: number;
    // }
    
    if (!event.success) return;
    // Process messages for capture
});
```

**When it fires**: After each agent turn completes (success or failure)

**Best for**: Memory capture, conversation logging, analytics

### 2. `llm_output` (Alternative)

```typescript
api.on("llm_output", async (event, ctx) => {
    // event: PluginHookLlmOutputEvent
    // {
    //   runId: string;
    //   sessionId: string;
    //   provider: string;
    //   model: string;
    //   assistantTexts: string[];
    //   lastAssistant?: unknown;
    //   usage?: { ... };
    // }
});
```

**When it fires**: After LLM response received

**Best for**: Token tracking, response logging

### 3. `session_end` (Alternative)

```typescript
api.on("session_end", async (event, ctx) => {
    // event: PluginHookSessionEndEvent
    // {
    //   sessionId: string;
    //   sessionKey?: string;
    //   messageCount: number;
    //   durationMs?: number;
    // }
});
```

**When it fires**: When session ends (user closes, timeout, etc.)

**Best for**: Session-level aggregation, cleanup

---

## Registration Methods

### Method 1: api.on() (Preferred)

```typescript
// In plugin register()
register(api: OpenClawPluginApi) {
    api.on("agent_end", async (event, ctx) => {
        // Handler logic
    });
}
```

### Method 2: registerHook()

```typescript
register(api: OpenClawPluginApi) {
    api.registerHook("agent_end", async (event, ctx) => {
        // Handler logic
    }, { priority: 10 });
}
```

### Method 3: Array of events

```typescript
api.registerHook(
    ["agent_end", "session_end"], 
    async (event, ctx) => {
        // Shared handler
    }
);
```

---

## Event Context Types

Each hook receives both `event` and `ctx`:

```typescript
// PluginHookAgentContext
interface PluginHookAgentContext {
    agentId?: string;
    sessionKey?: string;
    sessionId?: string;
    workspaceDir?: string;
    messageProvider?: string;
    trigger?: string;      // "user" | "heartbeat" | "cron" | "memory"
    channelId?: string;    // "telegram" | "discord" | etc.
}
```

---

## Handler Signature

```typescript
type PluginHookHandlerMap = {
    agent_end: (
        event: PluginHookAgentEndEvent, 
        ctx: PluginHookAgentContext
    ) => Promise<void> | void;
    
    before_agent_start: (
        event: PluginHookBeforeAgentStartEvent,
        ctx: PluginHookAgentContext
    ) => Promise<PluginHookBeforeAgentStartResult | void> 
      | PluginHookBeforeAgentStartResult | void;
    
    // ... other hooks
};
```

---

## Common Patterns

### Capture User Messages

```typescript
api.on("agent_end", async (event) => {
    if (!event.success || !event.messages) return;
    
    for (const msg of event.messages) {
        if (msg.role === "user") {
            const content = extractTextContent(msg.content);
            if (shouldCapture(content)) {
                await store(content);
            }
        }
    }
});
```

### Inject Context Before Agent

```typescript
api.on("before_agent_start", async (event) => {
    const memories = await recall(event.prompt);
    if (memories.length > 0) {
        return {
            prependContext: formatMemories(memories)
        };
    }
});
```

---

## Registration Verification

To verify hooks are registered:

```typescript
// Check hook count
const hookRunner = createHookRunner(registry);
const count = hookRunner.getHookCount("agent_end");
console.log(`agent_end hooks: ${count}`);

// Check if any hooks exist
const hasHooks = hookRunner.hasHooks("agent_end");
```

---

## Common Mistakes

### ❌ Wrong Hook Name

```typescript
api.on("after_agent_end", handler);  // Wrong!
api.on("agent_complete", handler);   // Wrong!
api.on("completion", handler);       // Wrong!
```

### ✅ Correct Hook Name

```typescript
api.on("agent_end", handler);  // Correct!
```

### ❌ Wrong Registration Method

```typescript
// Not using plugin API
someEventEmitter.on("agent_end", handler);  // Wrong!
```

### ✅ Correct Registration

```typescript
// Using plugin API
api.on("agent_end", handler);  // Correct!
```

---

## Summary

| Hook | Valid | Category | When |
|------|-------|----------|------|
| `agent_end` | ✅ | Agent | After agent turn |
| `llm_output` | ✅ | LLM | After LLM response |
| `session_end` | ✅ | Session | Session end |
| `after_agent_end` | ❌ | - | Invalid |
| `completion` | ❌ | - | Invalid |
