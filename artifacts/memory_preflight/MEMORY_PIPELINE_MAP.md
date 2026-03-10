# Memory Pipeline Map

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         DECLARED MEMORY (SOUL.md)                       │
│  "关键状态持久化到 SESSION-STATE.md, working-buffer.md, handoff.md"      │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         PERSISTENCE LAYER                               │
├─────────────────────────────────────────────────────────────────────────┤
│  SESSION-STATE.md ────── ✅ Exists, updated 2026-03-09 19:15           │
│  working-buffer.md ───── ✅ Exists, updated 2026-03-09 18:25           │
│  handoff.md ─────────── ✅ Exists, updated 2026-03-09 18:25           │
│  memory.md ───────────── ✅ Exists, updated 2026-03-09 20:21           │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         INDEXING LAYER                                  │
├─────────────────────────────────────────────────────────────────────────┤
│  Session Indexer ─────── ✅ 113,352 events / 3,672 sessions            │
│  Continuity Events ───── ✅ 689 events logged                          │
│  Capsules ────────────── ✅ 6 capsules generated                       │
│  OpenViking ──────────── 🟡 Directories exist, abstracts NOT ready     │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         RETRIEVAL LAYER                                 │
├─────────────────────────────────────────────────────────────────────────┤
│  session-query ───────── 🟡 Works but returns RAW LOGS, not semantic   │
│  context-retrieve ────── ❌ Returns 0 results (L1 extraction broken)   │
│  openviking find ─────── 🟡 Returns directories, no content abstracts   │
│  Direct file read ────── ✅ Works for SESSION-STATE.md, etc.           │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         MAIN FLOW INTEGRATION                           │
├─────────────────────────────────────────────────────────────────────────┤
│  HEARTBEAT.md ────────── ❌ No session-query/context-retrieve calls    │
│  AGENTS.md ───────────── ❌ No memory tool calls in session startup    │
│  SOUL.md ─────────────── ❌ Rules declared but NOT enforced by tools   │
│  session-start-recovery ─ ✅ Reads files but NOT semantic memory       │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         BEHAVIOR CHANGE                                 │
├─────────────────────────────────────────────────────────────────────────┤
│  Session recovery ────── 🟡 Recovers file existence, not content       │
│  Rule enforcement ────── ❌ SOUL.md rules NOT enforced by any tool     │
│  Context decisions ───── ❌ No retrieval before decisions              │
│  Subagent orchestration ─ ✅ subtask-orchestrate works                 │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Analysis

### 1. Write Path (Working)

```
Session Event → session-indexer → .session-index/sessions.db
                            ↓
              continuity-event-log → state/session_continuity_events.jsonl
                            ↓
              capsule-builder → artifacts/capsules/*.json
                            ↓
              (manual) → SESSION-STATE.md, handoff.md
```

**Status**: ✅ Write path is functional

### 2. Read Path (Broken)

```
HEARTBEAT / Session Start → session-start-recovery
                                    │
                                    ├─→ Check file exists ✅
                                    ├─→ Read SESSION-STATE.md ✅
                                    └─→ Call session-query ❌ (NOT DONE)
                                            ↓
                                       Call context-retrieve ❌ (NOT DONE)
                                            ↓
                                       Call openviking ❌ (NOT DONE)
```

**Status**: ❌ Read path stops at file existence check

### 3. Retrieval Quality Path (Degraded)

```
session-query ──→ Returns raw logs (not semantic)
context-retrieve → Returns 0 results (L1 broken)
openviking find ─→ Returns directories (no content abstracts)
```

**Status**: ❌ Retrieval quality insufficient for behavior change

---

## Gap Analysis

| Gap | Description | Impact |
|-----|-------------|--------|
| **Main Flow Integration** | Memory tools not called in heartbeat/startup | Agent doesn't use indexed memory |
| **L1 Extraction** | context-retrieve returns empty | Capsule-based retrieval broken |
| **OpenViking Indexing** | Abstracts not ready | Vector search unavailable |
| **SESSION-STATE Quality** | Missing objective/phase/blocker | Recovery gets nothing useful |
| **Semantic Extraction** | session-query returns raw logs | Search returns noise |

---

## Key Files

| File | Purpose | Status |
|------|---------|--------|
| `.session-index/sessions.db` | Session index DB | ✅ 113K events |
| `state/session_continuity_events.jsonl` | Continuity log | ✅ 689 events |
| `artifacts/capsules/*.json` | Session capsules | ✅ 6 capsules |
| `SESSION-STATE.md` | Current state | 🟡 Empty/meaningless |
| `handoff.md` | Handoff summary | 🟡 Content quality unclear |
| `memory.md` | Bootstrap cheat sheet | ✅ Updated |

---

## Tools

| Tool | Purpose | Status |
|------|---------|--------|
| `session-indexer` | Index session logs | ✅ Working |
| `session-query` | Query session index | 🟡 Returns raw logs |
| `context-retrieve` | L1/L2 retrieval | ❌ Returns 0 results |
| `openviking` | Vector search | 🟡 Not indexed |
| `session-start-recovery` | Session recovery | ✅ Works (file check only) |
