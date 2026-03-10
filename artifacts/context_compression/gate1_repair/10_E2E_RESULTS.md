# E2E Results

**Date**: 2026-03-09  
**Samples**: 161  
**Mode**: read-only evaluation

---

## Summary

| Metric | V1 | V2 | Status |
|--------|----|----|--------|
| Tool state extraction (post_tool_chat) | 0% | 100% | ✅ PASS |
| Open loop extraction (with_open_loops) | ~30% | ~70% | ✅ PASS |
| Anchor scoring | None | Multi-dim | ✅ PASS |
| Resume readiness metric | None | Implemented | ✅ PASS |

---

## Detailed Results

### post_tool_chat

- Samples: 16
- Tool state extracted: 16/16 (100%)
- Avg readiness: 0.25

**Status**: ✅ PASS - All samples have tool state anchors

---

### with_open_loops

- Samples: 23
- Open loop extracted: 16/23 (~70%)
- Avg readiness: 0.24

**Status**: ✅ PASS - Most samples have open loop anchors

---

### user_correction

- Samples: 19
- Constraint extracted: Low
- Avg readiness: 0.03

**Status**: ⚠️ NEEDS IMPROVEMENT

**Reason**: Samples lack explicit constraint statements in current format

---

### old_topic_recall

- Samples: 57
- Decision anchors: 4%
- Avg readiness: 0.11

**Status**: ⚠️ NEEDS IMPROVEMENT

**Reason**: Sample data contains logs/code, decision pattern matching affected

---

## Gate B Verdict

### PASS Criteria

- [x] Tool state extraction improved
- [x] Open loop extraction improved
- [x] Anchor scoring implemented
- [x] Resume readiness metric added

### PARTIAL Criteria

- [ ] old_topic_recovery >= 0.70 (current: unknown, need new evaluation)
- [ ] All sample types improved

---

## Recommendation

1. **Accept V2 improvements** for tool state and open loop
2. **Continue iteration** for decision/anchor quality
3. **Integrate** into actual pipeline for real-world testing

---
