# Compaction Bridge Patch

**Version**: 1.0.0
**Date**: 2026-03-10
**Status**: PATCH_PLAN

---

## Overview

本文档描述实现 Compaction Bridge 所需的具体代码修改。

---

## Patch 1: Extend mergeBeforePromptBuild

**文件**: `src/plugins/hook-runner.ts`

**当前代码**:
```typescript
const mergeBeforePromptBuild = (acc, next) => ({
  systemPrompt: next.systemPrompt ?? acc?.systemPrompt,
  prependContext: concatOptionalTextSegments({
    left: acc?.prependContext,
    right: next.prependContext
  }),
  prependSystemContext: concatOptionalTextSegments({
    left: acc?.prependSystemContext,
    right: next.prependSystemContext
  }),
  appendSystemContext: concatOptionalTextSegments({
    left: acc?.appendSystemContext,
    right: next.appendSystemContext
  })
});
```

**修改后**:
```typescript
const mergeBeforePromptBuild = (acc, next) => ({
  // Existing fields
  systemPrompt: next.systemPrompt ?? acc?.systemPrompt,
  prependContext: concatOptionalTextSegments({
    left: acc?.prependContext,
    right: next.prependContext
  }),
  prependSystemContext: concatOptionalTextSegments({
    left: acc?.prependSystemContext,
    right: next.prependSystemContext
  }),
  appendSystemContext: concatOptionalTextSegments({
    left: acc?.appendSystemContext,
    right: next.appendSystemContext
  }),
  
  // Compaction bridge fields
  needsCompact: acc?.needsCompact ?? next.needsCompact,
  compactReason: acc?.compactReason ?? next.compactReason,
  estimatedContextRatio: next.estimatedContextRatio ?? acc?.estimatedContextRatio,
  contextPressureMode: next.contextPressureMode ?? acc?.contextPressureMode
});
```

**影响**: 低 - 只是传递额外字段，不改变现有行为

---

## Patch 2: Add Compaction Bridge Function

**文件**: 新建 `src/agents/pi-embedded-runner/compaction-bridge.ts`

```typescript
/**
 * Compaction Bridge - Connects plugin detection to core compaction
 * 
 * When a plugin sets event.needsCompact=true in before_prompt_build hook,
 * this bridge triggers the appropriate compaction strategy.
 */

import type { Session } from '../session-types';
import type { ContextEngine } from '../../context-engine/types';

export interface CompactionBridgeParams {
  needsCompact?: boolean;
  compactReason?: string;
  estimatedContextRatio?: number;
  contextPressureMode?: string;
  session: Session;
  sessionKey: string;
  provider: string;
  modelId: string;
  contextEngine?: ContextEngine;
  maxAttempts?: number;
  cooldownMs?: number;
  minMessages?: number;
  strategies?: ('compact' | 'summarize' | 'trim')[];
}

export interface CompactionBridgeResult {
  compacted: boolean;
  reason?: string;
  tokensBefore?: number;
  tokensAfter?: number;
  strategy?: string;
  durationMs?: number;
}

const DEFAULT_COOLDOWN_MS = 5 * 60 * 1000; // 5 minutes
const DEFAULT_MIN_MESSAGES = 5;
const DEFAULT_STRATEGIES: ('compact' | 'summarize' | 'trim')[] = ['compact', 'summarize', 'trim'];

/**
 * Check if compaction is on cooldown
 */
function isOnCooldown(session: Session, cooldownMs: number): boolean {
  const lastCompact = (session as any).lastCompactionTime;
  if (!lastCompact) return false;
  return Date.now() - lastCompact < cooldownMs;
}

/**
 * Check if session has enough messages to compact
 */
function hasEnoughMessages(session: Session, minMessages: number): boolean {
  return session.messages.length >= minMessages;
}

/**
 * Execute session.compact() strategy
 */
async function executeCompactStrategy(
  session: Session,
  params: CompactionBridgeParams
): Promise<CompactionBridgeResult> {
  if (typeof session.compact !== 'function') {
    return { compacted: false, reason: 'compact_not_available' };
  }
  
  const start = Date.now();
  try {
    const result = await session.compact();
    return {
      compacted: true,
      strategy: 'compact',
      tokensBefore: result.tokensBefore,
      tokensAfter: result.tokensAfter,
      durationMs: Date.now() - start
    };
  } catch (err) {
    return {
      compacted: false,
      reason: `compact_error: ${err instanceof Error ? err.message : String(err)}`,
      durationMs: Date.now() - start
    };
  }
}

/**
 * Execute contextEngine.compact() strategy
 */
async function executeSummarizeStrategy(
  params: CompactionBridgeParams
): Promise<CompactionBridgeResult> {
  if (!params.contextEngine) {
    return { compacted: false, reason: 'context_engine_not_available' };
  }
  
  const start = Date.now();
  try {
    const result = await params.contextEngine.compact({
      sessionId: params.sessionKey,
      force: true
    });
    return {
      compacted: result.compacted,
      strategy: 'summarize',
      tokensBefore: result.result?.tokensBefore,
      tokensAfter: result.result?.tokensAfter,
      durationMs: Date.now() - start
    };
  } catch (err) {
    return {
      compacted: false,
      reason: `summarize_error: ${err instanceof Error ? err.message : String(err)}`,
      durationMs: Date.now() - start
    };
  }
}

/**
 * Execute trim strategy (remove oldest 20% of messages)
 */
async function executeTrimStrategy(
  session: Session
): Promise<CompactionBridgeResult> {
  const start = Date.now();
  const messageCount = session.messages.length;
  
  if (messageCount < 10) {
    return { compacted: false, reason: 'insufficient_messages_for_trim' };
  }
  
  const trimCount = Math.floor(messageCount * 0.2);
  const messagesBefore = session.messages.length;
  
  // Keep the last 80% of messages
  session.messages = session.messages.slice(trimCount);
  
  const tokensBefore = messagesBefore; // Approximate
  const tokensAfter = session.messages.length;
  
  return {
    compacted: true,
    strategy: 'trim',
    tokensBefore,
    tokensAfter,
    reason: `trimmed_${trimCount}_messages`,
    durationMs: Date.now() - start
  };
}

/**
 * Main bridge function - check and trigger compaction
 */
export async function checkAndTriggerCompaction(
  params: CompactionBridgeParams
): Promise<CompactionBridgeResult> {
  const {
    needsCompact,
    compactReason,
    estimatedContextRatio,
    session,
    sessionKey,
    provider,
    modelId,
    cooldownMs = DEFAULT_COOLDOWN_MS,
    minMessages = DEFAULT_MIN_MESSAGES,
    strategies = DEFAULT_STRATEGIES
  } = params;
  
  // Guard 1: Not needed
  if (!needsCompact) {
    return { compacted: false, reason: 'not_needed' };
  }
  
  // Guard 2: Insufficient messages
  if (!hasEnoughMessages(session, minMessages)) {
    return { compacted: false, reason: `insufficient_messages_${session.messages.length}_${minMessages}` };
  }
  
  // Guard 3: On cooldown
  if (isOnCooldown(session, cooldownMs)) {
    return { compacted: false, reason: 'cooldown' };
  }
  
  // Try strategies in order
  for (const strategy of strategies) {
    let result: CompactionBridgeResult;
    
    switch (strategy) {
      case 'compact':
        result = await executeCompactStrategy(session, params);
        break;
      case 'summarize':
        result = await executeSummarizeStrategy(params);
        break;
      case 'trim':
        result = await executeTrimStrategy(session);
        break;
      default:
        continue;
    }
    
    if (result.compacted) {
      // Update last compaction time
      (session as any).lastCompactionTime = Date.now();
      return result;
    }
  }
  
  return { compacted: false, reason: 'all_strategies_failed' };
}
```

**影响**: 低 - 新文件，不影响现有代码

---

## Patch 3: Integrate Bridge into Reply Path

**文件**: `src/agents/pi-embedded-runner/reply.ts`

**位置**: `resolvePromptBuildHookResult()` 之后

**找到**:
```typescript
async function resolvePromptBuildHookResult(params) {
  const promptBuildResult = params.hookRunner?.hasHooks("before_prompt_build") 
    ? await params.hookRunner.runBeforePromptBuild({...}, params.hookCtx).catch(...) 
    : void 0;
  // ...
  return {
    systemPrompt: promptBuildResult?.systemPrompt ?? legacyResult?.systemPrompt,
    prependContext: ...,
    prependSystemContext: ...,
    appendSystemContext: ...
  };
}
```

**修改**:
```typescript
async function resolvePromptBuildHookResult(params) {
  const promptBuildResult = params.hookRunner?.hasHooks("before_prompt_build") 
    ? await params.hookRunner.runBeforePromptBuild({...}, params.hookCtx).catch(...) 
    : void 0;
  // ...
  return {
    systemPrompt: promptBuildResult?.systemPrompt ?? legacyResult?.systemPrompt,
    prependContext: ...,
    prependSystemContext: ...,
    appendSystemContext: ...,
    
    // NEW: Pass compaction bridge fields
    needsCompact: promptBuildResult?.needsCompact ?? legacyResult?.needsCompact,
    compactReason: promptBuildResult?.compactReason ?? legacyResult?.compactReason,
    estimatedContextRatio: promptBuildResult?.estimatedContextRatio,
    contextPressureMode: promptBuildResult?.contextPressureMode
  };
}
```

**找到调用位置**:
```typescript
const promptBuildResult = await resolvePromptBuildHookResult(params);
// ... then uses promptBuildResult.systemPrompt etc.
```

**添加** (在 `promptBuildResult` 使用之前):
```typescript
const promptBuildResult = await resolvePromptBuildHookResult(params);

// NEW: Compaction Bridge
if (promptBuildResult?.needsCompact) {
  const { checkAndTriggerCompaction } = await import('./compaction-bridge.js');
  
  const compactResult = await checkAndTriggerCompaction({
    needsCompact: promptBuildResult.needsCompact,
    compactReason: promptBuildResult.compactReason,
    estimatedContextRatio: promptBuildResult.estimatedContextRatio,
    contextPressureMode: promptBuildResult.contextPressureMode,
    session: params.session,
    sessionKey: params.sessionKey ?? params.sessionId,
    provider: params.provider,
    modelId: params.modelId,
    contextEngine: params.contextEngine,
    cooldownMs: params.config?.compaction?.cooldownMs
  });
  
  if (compactResult.compacted) {
    log$10.info('[compaction-bridge] compacted', {
      sessionKey: params.sessionKey,
      reason: promptBuildResult.compactReason,
      ratio: promptBuildResult.estimatedContextRatio,
      strategy: compactResult.strategy,
      tokensBefore: compactResult.tokensBefore,
      tokensAfter: compactResult.tokensAfter,
      durationMs: compactResult.durationMs
    });
  } else {
    log$10.debug('[compaction-bridge] skipped', {
      sessionKey: params.sessionKey,
      reason: compactResult.reason
    });
  }
}
```

**影响**: 中 - 改变主链路，需要仔细测试

---

## Patch 4: Add Compaction Metadata to Session

**文件**: `src/agents/pi-embedded-runner/session.ts`

**添加属性**:
```typescript
// Add to Session interface/class
interface Session {
  // ... existing properties
  
  // Compaction metadata
  lastCompactionTime?: number;
  compactionCount?: number;
}
```

**在 compact() 成功后更新**:
```typescript
async compact(customInstructions?: string): Promise<CompactResult> {
  // ... existing code
  
  // Update metadata
  this.lastCompactionTime = Date.now();
  this.compactionCount = (this.compactionCount ?? 0) + 1;
  
  return result;
}
```

**影响**: 低 - 只添加元数据属性

---

## Patch 5: Update Plugin to Set Proper Fields

**文件**: `extensions/context-guard/index.js`

**当前**:
```javascript
event.needsCompact = true;
event.contextGuard = { pressure: { estimated, ratio }, needsCompact: true };
```

**修改为**:
```javascript
// Set standard bridge fields
event.needsCompact = true;
event.compactReason = 'context_pressure_high';
event.estimatedContextRatio = ratio;
event.contextPressureMode = 'estimated';

// Also set contextGuard for debugging
event.contextGuard = { 
  pressure: { estimated, ratio }, 
  needsCompact: true,
  threshold 
};
```

**影响**: 低 - 只是设置额外字段

---

## Patch Summary

| Patch | File | Change Type | Impact | Lines |
|-------|------|-------------|--------|-------|
| 1 | `hook-runner.ts` | Extend function | Low | +4 |
| 2 | `compaction-bridge.ts` | New file | Low | ~150 |
| 3 | `reply.ts` | Add bridge call | Medium | +30 |
| 4 | `session.ts` | Add metadata | Low | +5 |
| 5 | `context-guard/index.js` | Set fields | Low | +3 |

**Total Estimated Changes**: ~200 lines

---

## Testing Patches

### Unit Test for Patch 1

```typescript
describe('mergeBeforePromptBuild', () => {
  it('should pass needsCompact from next', () => {
    const result = mergeBeforePromptBuild(null, { needsCompact: true });
    expect(result.needsCompact).toBe(true);
  });
  
  it('should pass needsCompact from acc', () => {
    const result = mergeBeforePromptBuild({ needsCompact: true }, {});
    expect(result.needsCompact).toBe(true);
  });
  
  it('should prefer acc over next', () => {
    const result = mergeBeforePromptBuild({ needsCompact: true }, { needsCompact: false });
    expect(result.needsCompact).toBe(true);
  });
});
```

### Integration Test for Patch 3

```typescript
describe('Compaction Bridge Integration', () => {
  it('should trigger compaction when needsCompact=true', async () => {
    const mockSession = {
      messages: Array(20).fill({ role: 'user', content: 'test' }),
      compact: jest.fn().mockResolvedValue({ tokensBefore: 1000, tokensAfter: 500 })
    };
    
    const params = {
      hookRunner: {
        hasHooks: () => true,
        runBeforePromptBuild: jest.fn().mockResolvedValue({
          needsCompact: true,
          compactReason: 'test'
        })
      },
      session: mockSession
    };
    
    await resolvePromptBuildHookResult(params);
    
    expect(mockSession.compact).toHaveBeenCalled();
  });
});
```

---

## Rollback Plan

如果 bridge 导致问题：

1. **立即禁用**: 在配置中设置 `compaction.bridgeEnabled = false`
2. **代码回滚**: 移除 Patch 3 中的 bridge 调用代码
3. **Plugin 回退**: Plugin 只记录日志，不设置 `needsCompact`

---

## Migration Guide

### For Plugin Developers

如果你的 plugin 检测 context 压力，请设置以下字段：

```javascript
api.on('before_prompt_build', async (event) => {
  if (shouldCompact) {
    event.needsCompact = true;
    event.compactReason = 'your_reason_here';
    event.estimatedContextRatio = ratio;
    event.contextPressureMode = 'estimated' | 'exact';
  }
});
```

### For Configuration

添加以下配置控制 bridge 行为：

```json
{
  "compaction": {
    "bridgeEnabled": true,
    "cooldownMs": 300000,
    "minMessages": 5,
    "strategies": ["compact", "summarize", "trim"]
  }
}
```
