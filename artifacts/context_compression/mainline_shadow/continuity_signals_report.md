# Continuity Signals Report

**Period**: 2026-03-07 (Initial)
**Status**: No Data Available

---

## Overview

Continuity signals measure whether context compression preserves conversation continuity:

1. **Old-topic continuity**: Can agent recall and continue old topics?
2. **Open-loop preservation**: Are open commitments maintained?
3. **User-correction stability**: Do user corrections persist?

---

## Signals Status

### Old-Topic Continuity

| Metric | Current | Target |
|--------|---------|--------|
| Sessions with old-topic recall | N/A | >= 1 |
| Successful recall rate | N/A | >= 0.8 |

**Status**: ❌ No data - need sessions with topic switches

### Open-Loop Preservation

| Metric | Current | Target |
|--------|---------|--------|
| Sessions with open loops | N/A | >= 1 |
| Loops preserved after compression | N/A | 100% |

**Status**: ❌ No data - need sessions with TODOs/TBDs

### User-Correction Stability

| Metric | Current | Target |
|--------|---------|--------|
| Sessions with user corrections | N/A | >= 1 |
| Corrections preserved | N/A | 100% |

**Status**: ❌ No data - need sessions with constraint corrections

---

## Required Data

To evaluate continuity signals, we need:

| Signal | Session Type | Min Sessions |
|--------|--------------|--------------|
| Old-topic | Multi-topic chat | 10 |
| Open-loop | Task with TODOs | 5 |
| User-correction | Constraint clarification | 5 |

---

## Evaluation Method

When data available:

1. **Old-topic**: Compare agent response to previous topic reference
2. **Open-loop**: Check TODO/TBD items preserved in compressed context
3. **User-correction**: Verify constraint modifications maintained

---

## Expected Thresholds

| Signal | Threshold | Action if Failed |
|--------|-----------|------------------|
| Old-topic recall | >= 0.8 | Investigate capsule |
| Open-loop preservation | 100% | Block Light Enforced |
| User-correction stability | 100% | Block Light Enforced |

---

## Next Steps

1. Wait for mainline shadow sessions
2. Identify sessions with continuity opportunities
3. Analyze signals
4. Update this report

---

**Status**: Awaiting observation data
