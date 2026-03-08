# Session Continuity Anomaly Ledger

**Purpose**: 记录异常案例，用于评审决策
**Started**: 2026-03-07T22:42:00-06:00

---

## Anomaly Categories

### 1. Recovery Failures
恢复失败案例 - recovery_failure 事件或实际恢复失败

### 2. Uncertainty Cases
uncertainty=true 案例 - 恢复存在不确定性

### 3. Event/File Inconsistencies
事件与文件不一致：
- 有恢复事件，无 recovery summary
- 有 handoff 事件，无 handoff 文件
- 有 gate_completed，无 gate 结果

### 4. Deduplication Anomalies
去重异常：
- 同一事件被重复记录
- 应该去重但未去重
- 去重键冲突导致丢失

### 5. False Positives/Negatives
假成功/假失败：
- recovery_success 但实际无法继续
- 事件记录但实际未执行
- 实际执行但无事件

---

## Anomaly Log

| Date | Category | Session | Description | Impact | Root Cause | Resolution |
|------|----------|---------|-------------|--------|------------|------------|
| - | - | - | - | - | - | - |

---

## Statistics

| Metric | Count |
|--------|-------|
| Total Anomalies | 0 |
| Recovery Failures | 0 |
| Uncertainty Cases | 0 |
| Event/File Inconsistencies | 0 |
| Deduplication Issues | 0 |
| False Positives/Negatives | 0 |

---

## Impact Assessment

### P0 Anomalies (Block Layer 2)
- Recovery failure rate > 5%
- Systematic event loss
- Data corruption

### P1 Anomalies (Needs Investigation)
- Single recovery failure
- Uncertainty rate > 10%
- Occasional dedup issues

### P2 Anomalies (Acceptable)
- Edge case failures
- Explained anomalies
- Non-blocking issues

---

*Updated: 2026-03-07T22:42:00-06:00*
