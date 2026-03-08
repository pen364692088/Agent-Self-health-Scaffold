# Runtime Policy Patch Report

**Created**: 2026-03-08T00:40:00-06:00
**Status**: ANALYSIS COMPLETE

---

## Current State

### Hook Location
- File: `~/.openclaw/hooks/context-compression-shadow/handler.ts`
- Trigger Event: `message.preprocessed`
- Problem: NOT in prompt assemble phase

### Existing Tools (GOOD)
- `tools/context-budget-check` ✅
- `tools/context-compress` ✅
- `tools/prompt-assemble` ✅ (already has LIGHT_ENFORCED_THRESHOLD = 0.85)
- `tools/context-retrieve` ✅

### Hardcoded Issues
```typescript
// Line 258 in handler.ts
'--max-tokens', '100000'  // Should be dynamic from model config
```

---

## Patch Required

### 1. Hook Handler Modification

**File**: `~/.openclaw/hooks/context-compression-shadow/handler.ts`

**Changes**:
1. Read max_tokens from model config instead of hardcoding
2. Call `prompt-assemble` instead of separate budget-check + compress
3. Use threshold_enforced = 0.85

### 2. Hook Timing Issue

**Current**: `message.preprocessed` (too early)
**Ideal**: `prompt.assemble` (before prompt is built)

**Options**:
- A. Modify OpenClaw core to add `prompt.assemble` hook point (requires OpenClaw update)
- B. Use existing `preprocessed` hook but call `prompt-assemble` tool

**Decision**: Option B (minimal change, works now)

### 3. Dynamic max_tokens

**Current**: Hardcoded 100000
**Target**: Model's contextWindow from config

**Implementation**:
```typescript
// Get from agent config
const agentConfig = getAgentConfig();  // Need to implement
const maxTokens = agentConfig.model.contextWindow || 200000;
```

---

## Implementation Plan

### Phase A: Minimal Patch (Immediate)
1. Modify handler.ts to use 200000 as max_tokens (matches current runtime)
2. Add threshold_enforced = 0.85 check
3. Call prompt-assemble when ratio >= 0.85

### Phase B: Dynamic Config (Follow-up)
1. Read contextWindow from model config
2. Support per-model thresholds

---

## Files to Modify

| File | Change |
|------|--------|
| `hooks/context-compression-shadow/handler.ts` | Main patch |
| `tools/context-budget-check` | Update threshold to 0.85 |
| `tools/prompt-assemble` | Already correct (0.85 threshold) |

---

## Validation Checklist

- [ ] max_tokens matches runtime (200000)
- [ ] threshold_enforced = 0.85
- [ ] prompt-assemble called before LLM request
- [ ] Safety counters remain zero
- [ ] Kill switch still works

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Hook timing wrong | Low | Medium | Test with natural traffic |
| Compression corrupts context | Low | High | Kill switch + rollback |
| Threshold too aggressive | Medium | Medium | Monitor enforced_trigger_count |

---

## Next Steps

1. Apply minimal patch to handler.ts
2. Test with controlled validation
3. Monitor natural traffic
4. Iterate if needed

---

*Report created: 2026-03-08T00:40:00-06:00*
