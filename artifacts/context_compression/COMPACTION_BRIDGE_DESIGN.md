# Compaction Bridge Design

**Version**: 1.0.0
**Date**: 2026-03-10
**Status**: DESIGN

---

## Problem Statement

**当前状态**：
- Plugin (`context-guard`) 在 `before_prompt_build` hook 中检测高压，设置 `event.needsCompact = true`
- 核心的 `mergeBeforePromptBuild` 只提取 `systemPrompt` 等字段，**不传递 `needsCompact`**
- 主链路在 `resolvePromptBuildHookResult` 后直接构建 prompt，**不检查压缩标记**
- 压缩只在 `context overflow` 异常时被动触发

**结果**：检测和执行断开，高压检测无法触发主动压缩。

---

## Architecture Analysis

### Current Flow

```
before_prompt_build hook
    ↓
event.needsCompact = true (set by plugin)
    ↓
mergeBeforePromptBuild()
    → extracts: systemPrompt, prependContext, prependSystemContext, appendSystemContext
    → ignores: needsCompact, compactReason, estimatedContextRatio
    ↓
resolvePromptBuildHookResult()
    → uses merged result
    → never checks needsCompact
    ↓
prompt assembly → LLM call
    ↓
(if overflow) → reactive compaction
```

### Required Flow

```
before_prompt_build hook
    ↓
event.needsCompact = true (set by plugin)
    ↓
mergeBeforePromptBuild()
    → extracts: systemPrompt, prependContext, ...
    → passes: needsCompact, compactReason, estimatedContextRatio, contextPressureMode
    ↓
resolvePromptBuildHookResult()
    → returns: { systemPrompt, prependContext, ..., needsCompact, compactReason }
    ↓
Bridge Check (NEW)
    if (result.needsCompact) {
        triggerCompaction()
    }
    ↓
prompt assembly → LLM call
```

---

## Design Decisions

### D1: Bridge Location

**选择**: 在 `resolvePromptBuildHookResult` 之后，prompt 组装之前

**原因**：
1. 已经合并了所有 hook 结果
2. 可以访问完整的 `params` 上下文（session, provider, model）
3. 可以复用现有的 `session.compact()` 方法
4. 不改变现有的 hook 接口

### D2: Field Consumption

**Plugin 设置的字段**：
```typescript
event.needsCompact: boolean          // 是否需要压缩
event.compactReason: string          // 原因：'context_pressure_high'
event.estimatedContextRatio: number  // 估算的比例
event.contextPressureMode: string    // 模式：'estimated'
```

**Merge 函数需要传递**：
```typescript
interface BeforePromptBuildResult {
  // Existing fields
  systemPrompt?: string;
  prependContext?: string;
  prependSystemContext?: string;
  appendSystemContext?: string;
  
  // New fields for compaction bridge
  needsCompact?: boolean;
  compactReason?: string;
  estimatedContextRatio?: number;
  contextPressureMode?: string;
}
```

### D3: Compaction Trigger Strategy

**当 `needsCompact=true` 时**：

| 策略 | 触发条件 | 执行动作 |
|------|----------|----------|
| **compact** | session 支持 compact | 调用 `session.compact()` |
| **summarize** | 有 context engine | 调用 `contextEngine.compact()` |
| **trim** | 不支持 compact | 裁剪最早的消息 |
| **block** | 配置为安全模式 | 返回错误，阻断请求 |

**默认策略**: `compact` → `summarize` → `trim` → `block`

### D4: Safety Guard

**防止过度压缩**：
1. 检查 `session.messages.length >= 5`（最小消息数）
2. 检查 `compactCooldown`（压缩冷却时间）
3. 检查 `lastCompactionTime`（上次压缩时间）
4. 检查 `compactionAttempts < maxAttempts`（最大尝试次数）

**Cooldown 规则**：
- 同一 session 5 分钟内最多 1 次主动压缩
- 可通过配置调整

---

## Implementation Plan

### Phase 1: Extend Merge Function

**文件**: `src/plugins/hook-runner.ts`

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
  
  // New fields for compaction bridge
  needsCompact: acc?.needsCompact ?? next.needsCompact,
  compactReason: acc?.compactReason ?? next.compactReason,
  estimatedContextRatio: next.estimatedContextRatio ?? acc?.estimatedContextRatio,
  contextPressureMode: next.contextPressureMode ?? acc?.contextPressureMode
});
```

### Phase 2: Add Bridge Function

**文件**: `src/agents/pi-embedded-runner/prompt-helpers.ts`

```typescript
interface CompactionBridgeResult {
  compacted: boolean;
  reason?: string;
  tokensBefore?: number;
  tokensAfter?: number;
}

async function checkAndTriggerCompaction(
  params: {
    needsCompact?: boolean;
    compactReason?: string;
    estimatedContextRatio?: number;
    session: Session;
    sessionKey: string;
    provider: string;
    modelId: string;
    contextEngine?: ContextEngine;
    maxAttempts?: number;
    cooldownMs?: number;
  }
): Promise<CompactionBridgeResult> {
  // Safety guards
  if (!params.needsCompact) {
    return { compacted: false };
  }
  
  if (params.session.messages.length < 5) {
    return { compacted: false, reason: 'insufficient_messages' };
  }
  
  // Check cooldown
  const lastCompact = params.session.lastCompactionTime;
  const cooldown = params.cooldownMs ?? 5 * 60 * 1000; // 5 min default
  if (lastCompact && Date.now() - lastCompact < cooldown) {
    return { compacted: false, reason: 'cooldown' };
  }
  
  // Try compact strategies
  try {
    // Strategy 1: session.compact()
    if (typeof params.session.compact === 'function') {
      const result = await params.session.compact();
      return {
        compacted: true,
        tokensBefore: result.tokensBefore,
        tokensAfter: result.tokensAfter
      };
    }
    
    // Strategy 2: contextEngine.compact()
    if (params.contextEngine) {
      const result = await params.contextEngine.compact({
        sessionId: params.sessionKey,
        force: true
      });
      return {
        compacted: result.compacted,
        tokensBefore: result.result?.tokensBefore,
        tokensAfter: result.result?.tokensAfter
      };
    }
    
    // Strategy 3: trim oldest messages
    const trimCount = Math.floor(params.session.messages.length * 0.2);
    if (trimCount > 0) {
      params.session.messages = params.session.messages.slice(trimCount);
      return { compacted: true, reason: 'trimmed' };
    }
    
    return { compacted: false, reason: 'no_method_available' };
    
  } catch (err) {
    return { compacted: false, reason: `error: ${err.message}` };
  }
}
```

### Phase 3: Integrate Bridge into Main Path

**文件**: `src/agents/pi-embedded-runner/reply.ts`

**位置**: `resolvePromptBuildHookResult()` 之后

```typescript
// After resolvePromptBuildHookResult
const promptBuildResult = await resolvePromptBuildHookResult(params);

// NEW: Compaction Bridge
if (promptBuildResult?.needsCompact) {
  const compactResult = await checkAndTriggerCompaction({
    needsCompact: promptBuildResult.needsCompact,
    compactReason: promptBuildResult.compactReason,
    estimatedContextRatio: promptBuildResult.estimatedContextRatio,
    session: params.session,
    sessionKey: params.sessionKey,
    provider: params.provider,
    modelId: params.modelId,
    contextEngine: params.contextEngine,
    cooldownMs: params.config?.compaction?.cooldownMs
  });
  
  if (compactResult.compacted) {
    log$10.info(`[compaction-bridge] compacted session=${params.sessionKey} reason=${promptBuildResult.compactReason} tokensBefore=${compactResult.tokensBefore} tokensAfter=${compactResult.tokensAfter}`);
  }
}
```

---

## Metrics & Observability

### Metrics to Emit

```typescript
{
  event: 'compaction_bridge_triggered',
  sessionKey: string,
  reason: string,
  provider: string,
  modelId: string,
  estimatedRatio: number,
  compacted: boolean,
  tokensBefore: number,
  tokensAfter: number,
  durationMs: number
}
```

### Logs

```
[compaction-bridge] trigger session=xxx reason=context_pressure_high ratio=0.75
[compaction-bridge] compacted session=xxx tokensBefore=150000 tokensAfter=80000
```

---

## Testing Strategy

### Unit Tests

1. `mergeBeforePromptBuild` 传递 `needsCompact` 字段
2. `checkAndTriggerCompaction` 正确处理 cooldown
3. `checkAndTriggerCompaction` 正确处理最小消息数
4. `checkAndTriggerCompaction` 选择正确的压缩策略

### Integration Tests

1. Plugin 设置 `needsCompact=true` → 主链路触发压缩
2. 高压检测 → 压缩执行 → 压力回落
3. Cooldown 生效 → 5 分钟内不重复压缩
4. Provider unknown → 仍然可以触发压缩

### E2E Test

**场景**：
1. 发送大量消息使 context ratio > threshold
2. Plugin 检测高压，设置 `needsCompact=true`
3. 主链路消费标记，调用 `session.compact()`
4. 验证压缩后 context ratio < threshold

---

## Configuration

### New Config Options

```json
{
  "compaction": {
    "bridgeEnabled": true,
    "cooldownMs": 300000,
    "minMessages": 5,
    "maxAttempts": 3,
    "strategyPriority": ["compact", "summarize", "trim"]
  }
}
```

### Plugin Config (context-guard)

```json
{
  "plugins": {
    "entries": {
      "context-guard": {
        "config": {
          "contextThreshold": 0.7,
          "enableBridge": true
        }
      }
    }
  }
}
```

---

## Rollout Plan

### Phase 1: Shadow Mode
- 添加 bridge 代码
- 只记录日志，不实际压缩
- 验证标记传递正确

### Phase 2: Limited Rollout
- 启用实际压缩
- 限制为特定 session/provider
- 监控压缩效果

### Phase 3: Full Rollout
- 全量启用
- 移除 shadow mode 代码

---

## Open Questions

1. **Provider Unknown 处理**：当 provider 为 unknown 时，如何获取 context window？
   - 建议：使用默认值 200000

2. **压缩策略选择**：如何决定使用 compact/summarize/trim？
   - 建议：按可用性优先级选择

3. **压缩失败处理**：压缩失败后是否继续发送请求？
   - 建议：记录警告，继续发送（可能触发被动压缩）

---

## References

- `src/plugins/hook-runner.ts` - Hook runner implementation
- `src/agents/pi-embedded-runner/reply.ts` - Main reply path
- `src/agents/pi-embedded-runner/prompt-helpers.ts` - Prompt helpers
- `extensions/context-guard/index.js` - Plugin implementation
