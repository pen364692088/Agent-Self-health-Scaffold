# Memory-Lancedb Observation Metrics

Observation Window: 2026-03-10 05:28 ~ 2026-03-17 05:28

---

## Day 1 (2026-03-10)

### Morning Snapshot (05:54 CST)

| Metric | Value | Status |
|--------|-------|--------|
| Row count | 2 | ✅ Stable |
| autoCapture hits | Normal filtering | ✅ |
| recall injections | 87 (30 min) | ✅ Active |
| false captures | 0 | ✅ |
| duplicate captures | 0 | ✅ |
| embedding errors | 0 | ✅ |

### Notes

- autoCapture 正常过滤非用户消息
- Recall 每次注入 2 条记忆
- 无 false capture
- 无异常日志

---

## Daily Summary Template

### Day N (YYYY-MM-DD)

| Metric | Morning | Evening | Delta |
|--------|---------|---------|-------|
| Row count | | | |
| autoCapture hits | | | |
| recall injections | | | |
| false captures | | | |
| embedding errors | | | |

### Issues Found

- [None / Description]

### Actions Taken

- [None / Description]

---

## Exit Criteria

| Criteria | Target | Current |
|----------|--------|---------|
| false captures | 0 | 0 ✅ |
| duplicate captures | 0 | 0 ✅ |
| embedding errors | 0 | 0 ✅ |
| recall success rate | > 90% | TBD |
| autoCapture relevance | > 80% | TBD |

---

## Decision Matrix

| Observation | Action |
|-------------|--------|
| false captures > 0 | 立即调查，考虑回滚 |
| duplicate captures > 0 | 检查去重逻辑 |
| embedding errors > 0 | 检查 embedding 服务 |
| recall rate < 90% | 分析原因 |
| All green for 3+ days | 可以结束观察窗 |

