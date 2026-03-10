# Memory System Health Summary

**Gate 0: Memory System Preflight**
**Date**: 2026-03-09 20:30 CST
**Status**: 🟡 GO WITH RISKS

---

## Executive Summary

记忆系统存在**架构完整但链路断裂**的问题。核心功能（持久化、索引、检索）都已实现，但**主链路不使用检索工具**，导致"记住了但用不上"。

---

## Critical Findings

### ✅ What Works

| Component | Status | Evidence |
|-----------|--------|----------|
| Session State Persistence | ✅ | SESSION-STATE.md, handoff.md, working-buffer.md 存在且更新 |
| Session Indexer | ✅ | 113,352 events / 3,672 sessions indexed |
| Continuity Events | ✅ | 689 events logged |
| Recovery Mechanism | ✅ | session-start-recovery works |
| Context Compression | ✅ | Shadow mode running |
| Capsules | ✅ | 6 capsules generated |

### ❌ What Doesn't Work

| Component | Status | Evidence |
|-----------|--------|----------|
| L1 Retrieval Quality | ❌ | context-retrieve returns 0 results for "SOUL.md" |
| L2 Vector Index | ❌ | OpenViking abstracts "[not ready]" |
| Memory in Main Flow | ❌ | No session-query/context-retrieve calls in heartbeat |
| Structured Memory Extraction | ❌ | session-query returns raw logs, not semantic content |
| SESSION-STATE Content Quality | ❌ | Missing key fields (objective, phase, blocker) |

---

## Declared vs Persisted vs Retrievable vs Behavior-Changing

| Aspect | Declared | Persisted | Retrievable | Behavior-Changing |
|--------|----------|-----------|-------------|-------------------|
| SESSION-STATE.md | ✅ AGENTS.md | ✅ Exists | ✅ File read | ❌ Not in main flow |
| handoff.md | ✅ AGENTS.md | ✅ Exists | ✅ File read | ❌ Not used in recovery |
| Session Index | ✅ memory.md | ✅ 113K events | ❌ Returns raw logs | ❌ Not called |
| OpenViking | ✅ memory.md | ✅ Directory structure | ❌ No abstracts | ❌ Not called |
| Capsules | ✅ memory.md | ✅ 6 capsules | ✅ Can retrieve | ❌ Not in main flow |
| SOUL.md rules | ✅ SOUL.md | ✅ File exists | ✅ File read | ❌ No tool enforcement |

---

## Risk Assessment

### High Risk
1. **Memory tools not called in main flow** - Agent never retrieves semantic memory during session
2. **SESSION-STATE.md empty/meaningless** - Recovery gets nothing useful
3. **OpenViking L2 not indexed** - Vector retrieval unavailable

### Medium Risk
4. **Session-query returns raw logs** - Not semantic search
5. **Context-retrieve returns 0 results** - L1 extraction broken
6. **Rules in SOUL.md not enforced by tools** - Rely on model to remember

### Low Risk
7. **Duplicate rule declarations** - 182 unique rules across files
8. **Capsule quality unclear** - "Turn 1 到 69 的对话内容" not semantic

---

## Conclusion

**GO WITH RISKS**: 记忆系统架构完整，但**主链路断裂**。

- 持久化层工作正常
- 索引层有数据但检索质量差
- 检索层存在但不在主链路
- 行为改变层几乎不存在

**Recommendation**: 进入全系统健康审计，但优先修复记忆检索链路。
