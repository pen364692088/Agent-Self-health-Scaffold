# Memory Failure Root Cause Analysis

## Document Info
- **Version**: v1.0
- **Date**: 2026-03-16
- **Status**: ROOT_CAUSE_IDENTIFIED
- **Severity**: BLOCKING_CRITICAL

---

## 0. Executive Summary

### Core Finding
The root cause is NOT "missing memory" or "missing handoff documents", but:

**Memory Kernel is currently Limited Mainline Assist / Bridge Integration, NOT a mandatory pre-decision checkpoint.**

The system has memory, recall, and bridge capabilities, but **memory constraints are NOT bound to the minimal decision point before write operations**, allowing the system to bypass existing memory and make incorrect actions in new sessions, different entry points, or different agents.

### Failure Chain
```
Archived → Not necessarily read → Read but not used for target resolution
        → Used but cannot block wrong writes
```

---

## 1. Incident Description

### Observed Behavior
1. System determined "unified progress ledger doesn't exist, creating new one"
2. User corrected: "There is already a unified progress ledger v1, must use unified entry point"
3. System then realized it should update the existing canonical file, not create new

### What This Reveals
When executing "update unified progress ledger", the system:
- Did NOT complete **canonical source resolution** before writing
- Was NOT blocked by the constraint "unified entry point already exists"

---

## 2. Root Cause Analysis

### Root Cause A: Memory Layer is Bridge Assist, NOT Mandatory Mainline Entry

The handoff document shows current baseline is **Memory Kernel v1 + Bridge Integration**, and **Bridge Mainline Limited** is still "limited mainline suggestion mode, not full-on".

This means the system currently has:
- ✅ Unified query
- ✅ Controlled recall
- ✅ Bridge suggestion
- ✅ Limited assist

But NOT:
- ❌ All critical actions must first check canonical source
- ❌ All mutations must pass through memory gate
- ❌ All agents/entries controlled by same constraint layer

---

### Root Cause B: Handoff Documents are Human-Readable, NOT Machine-Executable Contracts

Documents state:
- "Files to check first in new session"
- "First step after session takeover"

These are valuable but are essentially:
- Handoff instructions
- Operational suggestions
- Session recovery guides

NOT:
- Preflight contracts automatically executed before writes
- Canonical object registry
- Mutation blockers

Therefore, even if the system "theoretically should check first", it can still skip in action chain.

---

### Root Cause C: Missing Canonical Target Resolution

The minimal decision point should have been:
> When task involves "update unified progress ledger", system must first resolve "where is the single source of truth file".

But currently missing mandatory steps for:
- object name → canonical path
- canonical path → write policy
- write policy → allowed action

This led to:
- Existing truth source present
- Still created duplicate file
- Only reverted after user correction

---

### Root Cause D: Missing Fail-Closed Blocking Mechanism

Current recall system emphasizes fail-open stability (must maintain 100%).

But for "write operation target resolution" high-risk actions, **cannot continue with loose fail-open mentality**.

Correct strategy should be:
**When target unclear, FAIL-CLOSED, NOT continue guessing.**

Otherwise system will create new files when "uncertain where to write", creating new truth source fragmentation.

---

## 3. Why "Already Archived" Was Insufficient

Archiving only solved "information exists", not these three issues:

1. **Whether hit by current entry point**
2. **Whether retrieved at current task timing**
3. **Whether can block write operations**

Therefore:
- Archiving solves "recoverability"
- This incident lacked "enforceability"
- What's truly needed is "pre-execution regime"

---

## 4. Why This is BUG FIX, NOT Feature Addition

### G3.5 Boundary Compliance
Current G3.5 frozen observation period boundary:
- ❌ No new features
- ❌ No expansion to multi-entry/multi-agent
- ❌ No full-on
- ✅ Allow fixing bugs blocking mainline or breaking observation validity

### This Fix Qualifies as BUG FIX Because:
1. **System violated existing invariant** - Should not create duplicate canonical files
2. **Broke mainline trustworthiness** - Truth source fragmentation
3. **Reliable execution broken** - Depended on user manual correction
4. **No new capability** - Only enforcing existing constraints
5. **Not expanding scope** - Single entry point, single agent, limited mainline

---

## 5. Impact Assessment

### Severity: BLOCKING_CRITICAL

| Impact | Level | Reason |
|--------|-------|--------|
| Truth Source Fragmentation | HIGH | Multiple "unified" files |
| User Trust | HIGH | Required manual correction |
| System Reliability | HIGH | Cannot self-correct |
| Observation Validity | MEDIUM | Drift from canonical state |
| Mainline Continuity | MEDIUM | Session handoff failure |

---

## 6. Resolution Strategy

### Core Objective
**Upgrade key memory from "referenceable information" to "mandatory gate before write operations".**

### Specific Goals
1. **Goal 1**: Mandatory **Memory Preflight** for all state/file mutation actions
2. **Goal 2**: Mandatory **Canonical Target Resolution** for all canonical objects
3. **Goal 3**: **Block create/new file** when canonical target not resolved
4. **Goal 4**: Solidify as **regression test** to prevent recurrence

---

## 7. Key Insights

### Insight 1: Memory is Information, Not Constraint
Current memory tells "what exists" but cannot prevent "wrong action".

### Insight 2: Documents are Suggestions, Not Contracts
Handoff documents are guides, not executable gates.

### Insight 3: Fail-Open is Wrong for Mutations
For write operations, fail-closed is correct, not fail-open.

### Insight 4: Resolution Must Precede Action
Target resolution must happen BEFORE write, not after user correction.

---

## 8. Lessons Learned

1. **Single source of truth requires enforcement, not documentation**
2. **Memory must gate mutations, not just inform**
3. **Ambiguity must block, not trigger creation**
4. **Every mutation must leave evidence chain**
5. **New session must inherit same constraints**

---

## 9. Document Status

- ✅ Root cause identified
- ✅ Impact assessed
- ✅ Resolution strategy defined
- ✅ G3.5 boundary compliance verified
- 🔜 Implementing fix

---

## 10. References

- Task Document: `OpenClaw_记忆失效根因分析_强制修复任务单`
- G3.5 Freeze Boundary: Phase G3.5 frozen observation period
- Recovery Contract: `docs/RESTART_RECOVERY_CONTRACT.md`
