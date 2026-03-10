# Memory Minimal Fix Plan

## Objective

修复记忆系统的核心断裂点，使其真正影响 Agent 行为。

**目标状态**: GO (可以进入全系统健康审计)

---

## Fix Strategy: Minimal, High-Impact

### Phase 1: Restore Main Flow (P0) - 优先级最高

**Problem**: 记忆工具不在主链路中调用

**Fix 1.1: Add session-query to session-start-recovery**

```bash
# File: tools/session-start-recovery
# Add after file existence check:

# Query semantic memory
SEMANTIC_CONTEXT=$(session-query "$OBJECTIVE_KEYWORDS" 2>/dev/null | head -20)
if [ -n "$SEMANTIC_CONTEXT" ]; then
    echo "📌 Retrieved semantic context:"
    echo "$SEMANTIC_CONTEXT"
fi
```

**Fix 1.2: Add context-retrieve to heartbeat**

```bash
# File: HEARTBEAT.md
# Add after recovery check:

# Retrieve context before decisions
CONTEXT=$(context-retrieve --query "$CURRENT_OBJECTIVE" --json 2>/dev/null)
if [ "$(echo "$CONTEXT" | jq -r '.total_found')" -gt 0 ]; then
    echo "Context retrieved: $(echo "$CONTEXT" | jq -r '.total_found') snippets"
fi
```

**Fix 1.3: Add memory check to subagent spawn**

```bash
# File: tools/subtask-orchestrate
# Before spawning, check relevant memory:

MEMORY_HINT=$(session-query "$TASK_KEYWORDS" 2>/dev/null | head -10)
if [ -n "$MEMORY_HINT" ]; then
    TASK_PROMPT="$TASK_PROMPT\n\nRelevant context from memory:\n$MEMORY_HINT"
fi
```

**Estimated Effort**: 2-3 hours
**Impact**: HIGH - Enables behavior change

---

### Phase 2: Fix Retrieval Quality (P1)

**Problem**: L1 extraction 和 OpenViking 向量索引不可用

**Fix 2.1: Debug context-retrieve L1 extraction**

```bash
# Investigate why context-retrieve returns 0 results
tools/context-retrieve --query "test" --json --test

# Check if session index has semantic extractions
sqlite3 .session-index/sessions.db "SELECT * FROM signals LIMIT 10"
```

**Fix 2.2: Complete OpenViking indexing**

```bash
# Generate abstracts for existing resources
openviking add-resource viking://resources/user/memory --reindex

# Or run embedding process
# (Need to check OpenViking docs for proper indexing command)
```

**Fix 2.3: Improve session-query output**

```bash
# Modify session-query to extract semantic content, not raw logs
# Option 1: Add --semantic flag
# Option 2: Post-process results with jq
```

**Estimated Effort**: 4-6 hours
**Impact**: MEDIUM - Improves retrieval quality

---

### Phase 3: Fix Content Quality (P2)

**Problem**: SESSION-STATE.md 内容空洞，Capsule 摘要质量差

**Fix 3.1: Enforce SESSION-STATE.md structure**

```bash
# Create template and validator
cat > templates/SESSION-STATE.template.md << 'TEMPLATE'
# Session State

## Current Objective
<objective>

## Phase
<phase>

## Branch
<branch>

## Blocker
<blocker or "None">

## Next Actions
1. <action 1>
2. <action 2>

## Last Updated
<timestamp>
TEMPLATE

# Add validator to session-start-recovery
tools/session-state-doctor --fix
```

**Fix 3.2: Improve capsule extraction**

```bash
# Modify capsule-builder to extract key facts, not just summarize
# Add structured fields: objective, decisions, preferences, blockers
```

**Estimated Effort**: 3-4 hours
**Impact**: LOW - Improves content quality

---

## Implementation Order

```
┌─────────────────────────────────────────────────────────────┐
│ Phase 1: Restore Main Flow (P0)                             │
│                                                             │
│ Fix 1.1: session-query in session-start-recovery    [2h]    │
│ Fix 1.2: context-retrieve in heartbeat              [1h]    │
│ Fix 1.3: memory check in subtask-orchestrate        [1h]    │
│                                                             │
│ TOTAL: 4 hours                                              │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ Phase 2: Fix Retrieval Quality (P1)                         │
│                                                             │
│ Fix 2.1: Debug context-retrieve L1                 [2h]    │
│ Fix 2.2: Complete OpenViking indexing               [2h]    │
│ Fix 2.3: Improve session-query output               [2h]    │
│                                                             │
│ TOTAL: 6 hours                                              │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ Phase 3: Fix Content Quality (P2)                           │
│                                                             │
│ Fix 3.1: Enforce SESSION-STATE structure           [2h]    │
│ Fix 3.2: Improve capsule extraction                [2h]    │
│                                                             │
│ TOTAL: 4 hours                                              │
└─────────────────────────────────────────────────────────────┘
```

**Total Estimated Effort**: 14 hours (can be spread over 2-3 days)

---

## Verification Checklist

After Phase 1:

```bash
# 1. Check session-query is called in recovery
grep -n "session-query" tools/session-start-recovery

# 2. Check context-retrieve is called in heartbeat
grep -n "context-retrieve" HEARTBEAT.md

# 3. Test recovery with memory
tools/session-start-recovery --recover --summary
# Should show "Retrieved semantic context: ..."

# 4. Test heartbeat with retrieval
# Trigger heartbeat and verify context retrieval log
```

After Phase 2:

```bash
# 1. Test context-retrieve
tools/context-retrieve --query "execution policy" --json
# Should return snippets, not empty

# 2. Test OpenViking
openviking find "memory"
# Should return content abstracts, not "[not ready]"

# 3. Test session-query
tools/session-query "SOUL.md"
# Should return semantic content, not raw logs
```

After Phase 3:

```bash
# 1. Check SESSION-STATE.md structure
grep -E "objective|phase|blocker" SESSION-STATE.md
# Should return meaningful content

# 2. Check capsule quality
cat artifacts/capsules/cap_*.json | jq -r '.summary'
# Should return semantic summary, not "Turn X 到 Y"
```

---

## Success Criteria

| Criterion | Current | Target |
|-----------|---------|--------|
| Behavior-Changing Score | 1/10 | 7/10 |
| Retrievable Score | 4/10 | 7/10 |
| Main Flow Integration | ❌ | ✅ |
| L1 Extraction Working | ❌ | ✅ |
| OpenViking Vector Ready | ❌ | ✅ |

**Gate Decision**: When Behavior-Changing Score ≥ 7/10, GO for full system health audit.

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Fix breaks existing behavior | Test in shadow mode first |
| OpenViking indexing takes too long | Start with L1 only |
| Session-query changes break compatibility | Add --semantic flag, keep old behavior |

---

## Conclusion

**Current Status**: GO WITH RISKS
**After Phase 1**: GO WITH MINOR RISKS
**After Phase 2**: GO
**After Phase 3**: GO with improved quality

**Recommendation**: Start with Phase 1 (4 hours), verify behavior change, then proceed to Phase 2.
