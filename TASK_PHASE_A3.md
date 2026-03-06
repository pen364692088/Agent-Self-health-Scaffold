# Phase A.3: FP/FN Metrics System

## Context
SELF_REPORT_ALIGNMENT协议需要误报/漏报统计能力。

## Goal
添加5个核心指标字段，集成到checker，支持shadow mode日志记录。

## Required Fields

| 字段 | 含义 |
|------|------|
| `total_self_reports` | 总自我陈述计数 |
| `flagged_count` | 被标记数量 |
| `confirmed_true_violation` | 确认的真实违规 |
| `confirmed_false_positive` | 确认的误报 |
| `suspected_false_negative` | 怀疑的漏报 |

## Implementation Requirements

### File Location
`emotiond/self_report_metrics.py`

### Core Class
```python
class SelfReportMetrics:
    """FP/FN metrics collector for self-report consistency checker"""
    
    def __init__(self, log_path: str = "reports/self_report_metrics.jsonl"):
        self.log_path = log_path
        
    def record_check(self, result: ConsistencyResult, confirmed: bool = None):
        """
        Record a consistency check result.
        If confirmed is None, it's an unreviewed shadow mode entry.
        """
        
    def get_stats(self, window_hours: int = 24) -> dict:
        """Get statistics for time window"""
        
    def calculate_rates(self) -> dict:
        """Calculate FP rate, FN rate, precision, recall"""
```

### Integration Points
1. `self_report_consistency_checker.py` - call metrics.record_check()
2. Shadow mode: log all checks without confirmation
3. Enforced mode: require human confirmation for violations

### Acceptance Criteria
- [ ] 5 core fields implemented
- [ ] JSONL logging format
- [ ] Windowed statistics calculation
- [ ] FP/FN rate calculation
- [ ] Test cases ≥ 20

## Project Root
`/home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion`

## Run Tests
```bash
cd /home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion
python3 -m pytest tests/test_self_report_metrics.py -v
```
