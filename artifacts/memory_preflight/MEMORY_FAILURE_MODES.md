# Memory Failure Modes

## Identified Failure Modes

### F1: Main Flow Integration Failure ⚠️ HIGH SEVERITY

**Symptom**: Memory tools (session-query, context-retrieve, openviking) are never called in the main session flow.

**Root Cause**: 
- HEARTBEAT.md only calls `session-start-recovery` for file checks
- AGENTS.md session startup only reads files directly
- No hook calls retrieval tools before decisions

**Evidence**:
```
$ grep -r "session-query\|context-retrieve\|openviking" HEARTBEAT.md AGENTS.md SOUL.md
# Returns empty - no references
```

**Impact**: 
- Indexed memory (113K events) never used
- Capsules (6 generated) never retrieved
- Agent operates without semantic memory

**Fix Priority**: P0 - Blocking behavior change

---

### F2: L1 Extraction Failure ⚠️ HIGH SEVERITY

**Symptom**: context-retrieve returns 0 results for all queries.

**Root Cause**:
- L1 extraction from session index not working
- Possibly capsule content not properly structured

**Evidence**:
```json
{
  "query": "SOUL.md",
  "snippets": [],
  "total_found": 0,
  "metrics": { "capsule_count": 0, "vector_count": 0 }
}
```

**Impact**:
- Capsule-based retrieval broken
- Cannot recover semantic context from compressed sessions

**Fix Priority**: P0 - Blocking retrieval

---

### F3: OpenViking Vector Index Not Ready ⚠️ MEDIUM SEVERITY

**Symptom**: OpenViking returns "[.abstract.md is not ready]" for all resources.

**Root Cause**:
- Vector indexing not completed
- Abstracts not generated
- Possibly embedding process not run

**Evidence**:
```json
{"abstract": "[.abstract.md is not ready]"}
```

**Impact**:
- L2 vector search unavailable
- Semantic search degrades to keyword matching

**Fix Priority**: P1 - Degrades retrieval quality

---

### F4: Session Query Returns Raw Logs ⚠️ MEDIUM SEVERITY

**Symptom**: session-query returns raw event logs, not semantic content.

**Root Cause**:
- Indexer stores events, not extracted semantics
- No semantic extraction layer between indexer and query

**Evidence**:
```
[1] 2026-03-09T03:54:15.927Z | None | model_change
    source: 59a65b21-81ad-4d9e-ad19-57d162fd3131.jsonl:2
```

**Impact**:
- Search returns noise instead of signal
- User gets log fragments, not meaningful content

**Fix Priority**: P1 - Degrades retrieval quality

---

### F5: SESSION-STATE Content Quality ⚠️ MEDIUM SEVERITY

**Symptom**: SESSION-STATE.md exists but grep for key fields returns nothing.

**Root Cause**:
- Content not properly structured
- Possibly overwritten or corrupted

**Evidence**:
```
$ grep -E "objective|phase|branch|blocker" SESSION-STATE.md
# Returns empty
```

**Impact**:
- Recovery gets file but no useful content
- Session continuity degraded

**Fix Priority**: P1 - Degrades recovery quality

---

### F6: SOUL.md Rules Not Enforced ⚠️ MEDIUM SEVERITY

**Symptom**: Rules declared in SOUL.md (e.g., "禁止使用 edit") are not enforced by any tool.

**Root Cause**:
- Rules are documentation only
- No tool reads and enforces them
- Relies on model to remember

**Evidence**:
```
$ grep -l "SOUL.md" tools/*
tools/probe-proposal-boundary
tools/probe-task-completion-protocol
# Only probe tools, not enforcement tools
```

**Impact**:
- Rules can be forgotten during long sessions
- No systematic enforcement

**Fix Priority**: P2 - Risk of forgetting

---

### F7: Capsule Content Quality ⚠️ LOW SEVERITY

**Symptom**: Capsule summary is generic ("Turn 1 到 69 的对话内容"), not semantic.

**Root Cause**:
- Capsule builder may not extract key semantics
- Content summarization quality issue

**Evidence**:
```json
{"summary": "Turn 1 到 69 的对话内容，共 69 条消息。"}
```

**Impact**:
- Capsule retrieval returns generic summaries
- Less useful for context recovery

**Fix Priority**: P2 - Degrades capsule utility

---

### F8: Duplicate Rule Declarations ⚠️ LOW SEVERITY

**Symptom**: Same rule declared in multiple files.

**Root Cause**:
- Organic growth of documentation
- No deduplication process

**Evidence**:
```
$ grep -l "禁止使用 edit" *.md
TOOLS.md
working-buffer.md
```

**Impact**:
- Confusion about authoritative source
- Potential conflicts if rules diverge

**Fix Priority**: P3 - Maintenance issue

---

## Failure Mode Summary

| ID | Failure Mode | Severity | Priority | Blocking |
|----|--------------|----------|----------|----------|
| F1 | Main Flow Integration | HIGH | P0 | ✅ Yes |
| F2 | L1 Extraction | HIGH | P0 | ✅ Yes |
| F3 | OpenViking Vector Index | MEDIUM | P1 | ❌ No |
| F4 | Session Query Raw Logs | MEDIUM | P1 | ❌ No |
| F5 | SESSION-STATE Content | MEDIUM | P1 | ❌ No |
| F6 | SOUL.md Enforcement | MEDIUM | P2 | ❌ No |
| F7 | Capsule Quality | LOW | P2 | ❌ No |
| F8 | Duplicate Rules | LOW | P3 | ❌ No |

---

## Recommended Fix Order

1. **P0**: Fix F1 (Main Flow) and F2 (L1 Extraction) - These are blocking behavior change
2. **P1**: Fix F3, F4, F5 - These degrade quality but don't block
3. **P2**: Fix F6, F7 - These are improvement opportunities
4. **P3**: Fix F8 - This is a maintenance task
