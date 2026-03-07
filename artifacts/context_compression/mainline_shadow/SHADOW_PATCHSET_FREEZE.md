# Mainline Shadow Patch Set Freeze

**Version**: 1.0
**Frozen At**: 2026-03-07T04:36:00CST
**Status**: FROZEN
**Mode**: SHADOW ONLY

---

## Purpose

Declare the fixed patch set for mainline shadow integration. This patch set will NOT be modified during the shadow observation period.

---

## Critical Declaration

```
⚠️  THIS IS SHADOW ONLY
⚠️  DO NOT ENABLE ENFORCED
⚠️  DO NOT MODIFY REAL REPLIES
```

---

## Included Patches

### 1. Anchor-Enhanced Capsule Builder

**Version**: 1.0
**Location**: `tools/capsule-builder` (shadow wrapper)

**Behavior**:
- Runs in shadow mode
- Extracts anchors from session events
- Writes to shadow artifacts only
- Does NOT modify active session

### 2. Anchor-Aware Retrieve

**Version**: 1.0
**Location**: `tools/context-retrieve` (shadow wrapper)

**Behavior**:
- Runs in shadow mode
- Uses anchor-based ranking
- Returns shadow recall results
- Does NOT affect real prompt assembly

### 3. Admissibility Policy

**Version**: 1.0
**Location**: `artifacts/context_compression/anchor-binding/ADMISSIBILITY_POLICY.md`

**Purpose**:
- Sample quality gate for evaluation
- Does NOT filter real conversations
- Used only for shadow observation metrics

---

## Explicitly Excluded

The following are **NOT** included in this patch set:

| Component | Reason |
|-----------|--------|
| Prompt Assemble Anchor Injection | Not in scope |
| Enforced Compression Mode | Shadow only |
| Real Session Modification | Forbidden |
| High-Risk Session Coverage | Out of scope |
| Scoring Changes | Keep compatibility |
| Metrics Changes | Keep compatibility |
| Schema Changes | No modifications |

---

## Feature Flags

```bash
CONTEXT_COMPRESSION_ENABLED=1
CONTEXT_COMPRESSION_MODE=shadow
CONTEXT_COMPRESSION_BASELINE=new_baseline_anchor_patch
```

**Allowed modes**: `shadow` only (for now)

---

## Kill Switch

**Location**: `artifacts/context_compression/mainline_shadow/KILL_SWITCH.md`

**Trigger conditions**:
- Manual trigger
- Error rate > 5%
- Replay regression detected
- User complaint

**Effect**: Immediately disable shadow integration

---

## Integration Points

```
┌─────────────────────────────────────────────────────────────┐
│                    MAIN SESSION FLOW                        │
│                                                             │
│  User Message ──► Process ──► [budget check] ──► Reply     │
│                          │                                  │
│                          ▼                                  │
│                    ┌──────────┐                             │
│                    │  SHADOW  │ ◄── Does NOT affect reply   │
│                    │  PATH    │                             │
│                    └──────────┘                             │
│                          │                                  │
│                          ▼                                  │
│              Shadow Artifacts (separate)                    │
└─────────────────────────────────────────────────────────────┘
```

**Shadow path actions**:
1. `context-budget-check` (shadow)
2. `context-compress --mode shadow` (if threshold)
3. `anchor-aware-retrieve` (shadow recall)
4. Write shadow artifacts

**Real path actions**:
1. Normal prompt assembly
2. Normal response generation
3. User sees unchanged behavior

---

## Session Scoping

### Allowed (Low Risk)

- Single topic daily chat
- Non-critical task
- Simple tool context

### Excluded (High Risk)

- Multi-file debug sessions
- High-commitment tasks
- Critical execution paths
- Multi-agent collaboration
- High-risk scenarios

---

## Modification Policy

**This patch set is FROZEN.**

Any modification requires:
1. Explicit approval
2. Version bump to 1.1
3. Re-integration test
4. Update to SHADOW_MANIFEST.json

---

## Relationship to Previous Work

| Stage | Status | File |
|-------|--------|------|
| Old S1 Baseline | FROZEN (conclusion intact) | S1_BASELINE_MANIFEST.json |
| New Baseline | ESTABLISHED | BASELINE_MANIFEST.json |
| **Mainline Shadow** | **THIS DOCUMENT** | SHADOW_MANIFEST.json |

**Inheritance**: New baseline → Mainline shadow (patch set carried over)

---

**Keywords**: `mainline-shadow` `frozen-patchset` `shadow-only` `no-enforced`
