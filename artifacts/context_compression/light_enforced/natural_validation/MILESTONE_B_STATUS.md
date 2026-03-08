# Milestone B Status

**Updated**: 2026-03-07T23:58:00-06:00

---

## Current Status

| Item | Status |
|------|--------|
| Configuration Locked | ✅ Done |
| Natural Session Selected | ✅ Done |
| Budget Trace Started | ✅ In Progress |
| Natural Trigger Captured | ⏳ Pending |
| Evidence Package | ⏳ Pending |
| Timing Analysis | ⏳ Pending |

---

## Budget Progress

| Timestamp | Ratio | Phase | Zone |
|-----------|-------|-------|------|
| 23:52:00 | 0.810 | candidate | normal |
| 23:52:30 | 0.825 | candidate | normal |
| Next | ~0.840+ | candidate | **hot zone** |
| Trigger | >= 0.85 | threshold | enforced |

---

## Evidence Hot Zone

**Activated when**: budget_ratio >= 0.84

**Purpose**: 提高证据捕获粒度，确保不错过首个自然 trigger

**Auto-capture on each assemble**:
- [ ] Counter before/after
- [ ] Budget before/after
- [ ] Guardrail event
- [ ] Capsule metadata
- [ ] Session note

---

## Expected Behavior (Corrected)

若当前自然 low-risk 会话后续**真实跨过 0.85**，并**进入下一轮 assemble**，则应触发首次自然 enforced compression。

**重要限定**:
- 当前 ratio ~0.825，离阈值不远，但还没到
- "高概率即将发生" ≠ "应该马上发生"
- 不制造触发，只等待并记录

---

## What's Needed

To complete Milestone B:

1. **Natural growth** to budget_ratio >= 0.85
2. **Enter next assemble** (pre-reply phase)
3. **Trigger forced_standard_compression**
4. **Complete evidence package** (auto-captured in hot zone)

---

## Key Constraint

**Do NOT force trigger**:
- ✅ Wait for natural growth
- ✅ Use default 100k config
- ❌ Do not lower max_tokens
- ❌ Do not modify threshold

---

*Milestone B status: WAITING_FOR_NATURAL_TRIGGER*
*Hot zone: ACTIVATED_AT_0.84*
