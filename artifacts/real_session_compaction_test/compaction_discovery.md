# Compaction Entry Point Discovery (2026-03-08)

## Critical Finding

`sessions.compact` RPC ≠ Native Compaction

### sessions.compact RPC Behavior
- **Purpose**: Simple line-based truncation (threshold: 400 lines)
- **Logic**: If lines <= 400, return `compacted: false, kept: <lines>`
- **Never calls**: `compactEmbeddedPiSession`, `contextEngine.compact`

### True Native Compaction Entry
- **Command**: `/compact` (slash command via Telegram)
- **Path**: `handleCompactCommand` → `compactEmbeddedPiSession` → `contextEngine.compact` → `compactEmbeddedPiSessionDirect`

## Previous Validation Error

| Aspect | Previous Claim | Actual Reality |
|--------|---------------|----------------|
| Entry point | `sessions.compact` RPC | `/compact` command |
| Code path | ❌ Not executed | N/A (wrong entry) |
| Result meaning | `compacted: false` = semantic skip | `compacted: false` = lines < 400 |

## Next Steps

1. Use `/compact` command on real conversation session
2. Verify post-adoption behavior:
   - Does `invalid_cut_point_empty_preparation` occur?
   - Or does native compaction work correctly?

## Session Candidates

| Session | Messages | Context Usage | Suitable For |
|---------|----------|---------------|--------------|
| testbot:telegram:direct | 62 (7u/32a/23t) | 93% | ✅ High context |
| yuno:telegram:direct | 27 (6u/19a/2t) | ~10% | ❌ Low context |
| main:telegram:direct | 5 | ~0% | ❌ Event log |

