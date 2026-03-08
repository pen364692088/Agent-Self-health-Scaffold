# Runtime Policy Source of Truth

**Created**: 2026-03-08T00:35:00-06:00
**Status**: DEFINING

---

## Current State Analysis

### Hook Location
- File: `~/.openclaw/hooks/context-compression-shadow/handler.ts`
- Trigger: `message.preprocessed` event
- NOT in prompt assemble phase

### Hardcoded Values (Problem)
```typescript
// Line 258 in handler.ts
'--max-tokens', '100000'
```

### Runtime Reality
- Model contextWindow: 200000 (from model config)
- Compression threshold: 0.92 (inferred from behavior)
- Pre-assemble: NOT IMPLEMENTED

---

## Target Policy

### Thresholds
```
< 0.75    → observe
0.75-0.85 → candidate (mark for potential compression)
0.85-0.92 → pre-assemble standard compression (MUST EXECUTE)
>= 0.92   → strong compression
```

### Critical Rule
**不允许跨过 0.85 后继续拖延**

压缩判定必须在 prompt assemble 前执行。

---

## Implementation Requirements

### 1. Hook Timing
Current: `message.preprocessed` (too early)
Target: `prompt.assemble` (before prompt is built)

### 2. max_tokens Source
Current: Hardcoded 100000
Target: Model's contextWindow from config

### 3. Threshold Enforcement
Current: Triggers at 0.92 (strong)
Target: Triggers at 0.85 (standard)

---

## Open Questions

1. How to hook into prompt assemble phase?
2. Does OpenClaw provide `pre-assemble` hook point?
3. How to access model's contextWindow dynamically?

---

## Next Steps

1. Check OpenClaw documentation for hook points
2. Check if `prompt.assemble` hook exists
3. Implement dynamic max_tokens reading
4. Add threshold_enforced = 0.85 parameter

---

*Document created: 2026-03-08T00:35:00-06:00*
