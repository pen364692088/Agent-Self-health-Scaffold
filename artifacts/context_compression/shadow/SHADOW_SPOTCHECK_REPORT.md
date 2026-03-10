# Shadow Spot-check Report

**Date**: 2026-03-09T11:25:49.685332
**Phase**: 5B · Spot-check 人工复核

---

## Summary

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Total Traces | 15 | >= 10 | ✅ |
| Agreement Rate | 93% | >= 80% | ✅ |
| False Positive Rate | 7% | < 20% | ✅ |
| False Negative Rate | 0% | < 15% | ✅ |

---

## Gate Analysis

| Result | Count |
|--------|-------|
| Gates Passed | 4 |
| Gates Failed | 11 |

---

## Known Issues

| Issue | Count | Impact |
|-------|-------|--------|
| Create Action Ambiguity | 1 | Non-blocking |

---

## Sample Details


### shadow_20260309_1124...

- **Auto Score**: 0.00
- **Human Score**: 0.00
- **Agreement**: ✅
- **Human Reason**: 信息不足
- **Gates**: {'topic_present': False, 'passed': False, 'failed_at': 'topic'}

### shadow_20260309_1124...

- **Auto Score**: 0.00
- **Human Score**: 0.00
- **Agreement**: ✅
- **Human Reason**: 信息不足
- **Gates**: {'topic_present': False, 'passed': False, 'failed_at': 'topic'}

### shadow_20260309_1124...

- **Auto Score**: 0.00
- **Human Score**: 0.00
- **Agreement**: ✅
- **Human Reason**: 信息不足
- **Gates**: {'topic_present': False, 'passed': False, 'failed_at': 'topic'}

### shadow_20260309_1124...

- **Auto Score**: 0.00
- **Human Score**: 0.00
- **Agreement**: ✅
- **Human Reason**: 信息不足
- **Gates**: {'topic_present': False, 'passed': False, 'failed_at': 'topic'}

### shadow_20260309_1124...

- **Auto Score**: 0.00
- **Human Score**: 0.00
- **Agreement**: ✅
- **Human Reason**: 信息不足
- **Gates**: {'topic_present': True, 'task_active': False, 'passed': False, 'failed_at': 'task_completed'}

### shadow_20260309_1124...

- **Auto Score**: 0.20
- **Human Score**: 0.00
- **Agreement**: ✅
- **Human Reason**: 信息不足
- **Gates**: {'topic_present': True, 'task_active': True, 'passed': True}

### shadow_20260309_1124...

- **Auto Score**: 0.80
- **Human Score**: 0.25
- **Agreement**: ❌
- **Human Reason**: topic清晰
- **Gates**: {'topic_present': True, 'task_active': True, 'passed': True}

### shadow_20260309_1124...

- **Auto Score**: 0.00
- **Human Score**: 0.00
- **Agreement**: ✅
- **Human Reason**: 信息不足
- **Gates**: {'topic_present': False, 'passed': False, 'failed_at': 'topic'}

### shadow_20260309_1124...

- **Auto Score**: 0.20
- **Human Score**: 0.00
- **Agreement**: ✅
- **Human Reason**: 信息不足
- **Gates**: {'topic_present': True, 'task_active': True, 'passed': True}

### shadow_20260309_1124...

- **Auto Score**: 0.00
- **Human Score**: 0.00
- **Agreement**: ✅
- **Human Reason**: 信息不足
- **Gates**: {'topic_present': False, 'passed': False, 'failed_at': 'topic'}


---

## Verdict

✅ **PASS** - Shadow validation successful, ready for Gate 1 closure