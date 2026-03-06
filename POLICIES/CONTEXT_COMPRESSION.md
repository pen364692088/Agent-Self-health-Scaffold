# Context Compression Policy

## Three-Layer Context Model

| Layer | Location | Access Speed | Content |
|-------|----------|--------------|---------|
| Resident | Active prompt | Immediate | Current turn + active_state + recent tools |
| Active | Memory files | Fast | Recent turns (last N), open loops, decisions |
| Recall | Vector DB / Archives | Slower | Historical capsules, full session transcripts |

## Compression Classification

| Category | Action | Reason |
|----------|--------|--------|
| **Must Keep** | Never compress | Current turn, active_state, hard constraints |
| **Should Keep Original** | Delay compression | Open loops, recent decisions, response_contract |
| **Should Compress** | Create capsule | Completed subtasks, resolved loops, tool outputs |
| **Vector Index** | Index + compress | Historical context, reference material |
| **Evictable** | Archive + remove | Old turns, resolved content, low relevance |

## Thresholds

| Ratio | Pressure | Action |
|-------|----------|--------|
| < 70% | None | No action |
| 70-85% | Low | Gradual compression (compress oldest) |
| 85-92% | Medium | Aggressive compression (compress non-essential) |
| > 92% | Critical | Emergency compression (keep only resident) |

## Core Principles (P1-P6)

**P1: Preserve Intent**
- Never lose task_goal, response_contract, or hard_constraints
- Compression must not change agent behavior

**P2: Lossless for Active Work**
- Open loops and recent decisions stay in full detail
- Only compress content not needed for current response

**P3: Reconstructability**
- All compressed content must be retrievable
- Capsules link to full archives

**P4: Graceful Degradation**
- Start with gradual compression at 70%
- Never jump to emergency unless critical

**P5: Semantic Indexing**
- Vector-index compressed content for retrieval
- Enable semantic search over history

**P6: Audit Trail**
- Log all compression events
- Track what was compressed when

## Workflow

```
1. Turn completed → Estimate context tokens
2. If ratio < 70%: No action
3. If ratio >= 70%:
   a. Classify content by category
   b. Select content to compress
   c. Create capsule(s)
   d. Update active_state
   e. Log compression_event
   f. Update budget_snapshot
4. If ratio > 92%:
   - Emergency: Keep only current turn + active_state
   - Force vector indexing
```

## File Structure

```
.openclaw/
├── context/
│   ├── active_state.json      # Current resident state
│   ├── capsules/              # Compressed capsules
│   └── events/                # Compression event logs
├── schemas/                   # JSON schemas
│   ├── active_state.v1.schema.json
│   ├── session_capsule.v1.schema.json
│   ├── compression_event.v1.schema.json
│   └── budget_snapshot.v1.schema.json
└── POLICIES/
    └── CONTEXT_COMPRESSION.md
```

---
Version: 1.0
Created: 2026-03-06
