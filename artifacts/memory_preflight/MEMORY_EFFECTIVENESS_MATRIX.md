# Memory Effectiveness Matrix

## Matrix Overview

评估记忆系统在四个维度的有效性：
- **Declared**: 系统声明具备此功能
- **Persisted**: 数据真正写入存储
- **Retrievable**: 数据可以被检索到
- **Behavior-Changing**: 检索结果改变 Agent 行为

---

## Component Effectiveness Matrix

| Component | Declared | Persisted | Retrievable | Behavior-Changing |
|-----------|:--------:|:---------:|:-----------:|:-----------------:|
| SESSION-STATE.md | ✅ | ✅ | ✅ | ❌ |
| working-buffer.md | ✅ | ✅ | ✅ | ❌ |
| handoff.md | ✅ | ✅ | ✅ | ❌ |
| memory.md | ✅ | ✅ | ✅ | ❌ |
| Session Index (DB) | ✅ | ✅ | 🟡 | ❌ |
| OpenViking Vector | ✅ | 🟡 | ❌ | ❌ |
| Capsules | ✅ | ✅ | 🟡 | ❌ |
| Context Compression | ✅ | ✅ | N/A | ❌ |
| Continuity Events | ✅ | ✅ | ✅ | ❌ |
| SOUL.md Rules | ✅ | ✅ | ✅ | ❌ |

**Legend**: ✅ Full | 🟡 Partial | ❌ None

---

## Dimension Analysis

### 1. Declared (声明)

**Score: 10/10** - 所有核心记忆组件都在 SOUL.md/AGENTS.md/memory.md 中声明。

| Component | Declaration Location |
|-----------|---------------------|
| SESSION-STATE.md | AGENTS.md: "当前总目标、阶段、分支、blocker" |
| working-buffer.md | AGENTS.md: "当前工作焦点、假设、待验证点" |
| handoff.md | AGENTS.md: "交接摘要（长会话或任务交接时）" |
| Session Index | memory.md: "session-indexer" |
| OpenViking | memory.md: "openviking find" |
| Capsules | memory.md: "Capsule Fallback" |
| Context Compression | memory.md: "Context Compression Pipeline v1.0" |

**Conclusion**: 架构设计完整，声明层无问题。

---

### 2. Persisted (持久化)

**Score: 8/10** - 大部分数据持久化成功，OpenViking 向量索引部分完成。

| Component | Persistence Status | Evidence |
|-----------|-------------------|----------|
| SESSION-STATE.md | ✅ Full | File exists, 61 lines |
| working-buffer.md | ✅ Full | File exists, 57 lines |
| handoff.md | ✅ Full | File exists, 49 lines |
| Session Index | ✅ Full | 113,352 events in DB |
| OpenViking | 🟡 Partial | Directories exist, abstracts NOT ready |
| Capsules | ✅ Full | 6 capsule files |
| Continuity Events | ✅ Full | 689 events logged |

**Gaps**:
- OpenViking abstracts not generated (vector index incomplete)

**Conclusion**: 持久化层基本可用，OpenViking 需要完成索引。

---

### 3. Retrievable (可检索)

**Score: 4/10** - 文件可读，但语义检索质量差。

| Component | Retrieval Status | Evidence |
|-----------|-----------------|----------|
| SESSION-STATE.md | ✅ Direct read works | File readable |
| working-buffer.md | ✅ Direct read works | File readable |
| handoff.md | ✅ Direct read works | File readable |
| Session Index | 🟡 Returns raw logs | session-query returns events, not semantics |
| OpenViking | ❌ No content | Returns directories, no abstracts |
| Capsules | 🟡 Generic summaries | "Turn 1 到 69 的对话内容" |
| context-retrieve | ❌ Returns 0 results | L1 extraction broken |

**Gaps**:
- session-query: Returns raw events, not semantic content
- context-retrieve: L1 extraction returns 0 results
- OpenViking: Vector search not functional
- Capsules: Content quality insufficient

**Conclusion**: 检索层严重退化，只能直接读文件，无法语义检索。

---

### 4. Behavior-Changing (行为改变)

**Score: 1/10** - 几乎没有行为改变证据。

| Component | Behavior Change Status | Evidence |
|-----------|----------------------|----------|
| SESSION-STATE.md | ❌ Not in main flow | session-start-recovery only checks existence |
| working-buffer.md | ❌ Not in main flow | No tool reads it |
| handoff.md | ❌ Not in main flow | Recovery doesn't use content |
| Session Index | ❌ Not called | No session-query calls in heartbeat |
| OpenViking | ❌ Not called | No openviking calls in main flow |
| Capsules | ❌ Not called | No capsule retrieval in main flow |
| SOUL.md Rules | ❌ Not enforced | No tool enforces declared rules |

**Gaps**:
- Main flow (HEARTBEAT, session startup) doesn't call retrieval tools
- Rules in SOUL.md are documentation only, no enforcement

**Conclusion**: 行为改变层几乎不存在。记忆系统"记住了但用不上"。

---

## Effectiveness Scorecard

| Dimension | Score | Status |
|-----------|:-----:|--------|
| Declared | 10/10 | ✅ Excellent |
| Persisted | 8/10 | ✅ Good |
| Retrievable | 4/10 | ⚠️ Degraded |
| Behavior-Changing | 1/10 | ❌ Failed |

**Overall Memory Effectiveness**: **5.75/10**

---

## Key Insight

```
Declared ────✅────> Persisted ────✅────> Retrievable ────❌────> Behavior-Changing
   10/10           8/10              4/10                 1/10

                                   ▲
                                   │
                          FAILURE POINT
```

**The chain breaks at Retrievable → Behavior-Changing transition.**

Memory is written but never used.

---

## Improvement Priority

| Priority | Dimension | Current | Target | Effort |
|----------|-----------|---------|--------|--------|
| P0 | Behavior-Changing | 1/10 | 7/10 | Medium - Add retrieval calls to main flow |
| P1 | Retrievable | 4/10 | 7/10 | Medium - Fix L1 extraction, index OpenViking |
| P2 | Persisted | 8/10 | 10/10 | Low - Complete OpenViking indexing |
| N/A | Declared | 10/10 | 10/10 | No action needed |
