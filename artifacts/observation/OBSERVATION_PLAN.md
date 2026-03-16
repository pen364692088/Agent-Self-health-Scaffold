# Observation Plan: Default Autonomy Validation

**Version**: 1.0.0
**Date**: 2026-03-16
**Duration**: 7 days (2026-03-16 ~ 2026-03-23)
**Mode**: Real workload validation

---

## Objective

验证默认自治闭环能力，收集真实负载证据，确定是否可以安全扩大自治范围。

---

## Scope

### In Scope

1. 自动入任务能力验证
2. 长任务规划与恢复验证
3. 执行/重试/回滚验证
4. 风险门控验证
5. 成功判定防假完成验证

### Out of Scope

1. 生产级自治宣称
2. 任意问题无人监管
3. 高并发场景（>10 并行）
4. 长时间运行（>24h）

---

## Daily Tasks

### Day 1 (2026-03-16): Baseline + Contract Setup

- [x] Gap matrix created
- [x] V2 baseline fixed
- [x] 5 contract documents created
- [ ] Initial test suite setup
- [ ] First observation report

### Day 2 (2026-03-17): Implementation Start

- [ ] Task admission pipeline
- [ ] Retry policy implementation
- [ ] Risk classifier implementation
- [ ] Daily observation report

### Day 3 (2026-03-18): Recovery & Rollback

- [ ] Recovery handler implementation
- [ ] Rollback manager implementation
- [ ] Test execution
- [ ] Daily observation report

### Day 4 (2026-03-19): Verification Enhancement

- [ ] Success verification enhancement
- [ ] False positive detector
- [ ] Test execution
- [ ] Daily observation report

### Day 5 (2026-03-20): Integration Testing

- [ ] E2E integration tests
- [ ] Edge case testing
- [ ] Daily observation report

### Day 6 (2026-03-21): Stress Testing

- [ ] Multiple concurrent tasks
- [ ] Failure injection
- [ ] Recovery testing
- [ ] Daily observation report

### Day 7 (2026-03-22): Final Validation

- [ ] Full validation suite
- [ ] Evidence collection
- [ ] Daily observation report

---

## Metrics to Track

### Primary Metrics

| Metric | Target | Collection |
|--------|--------|------------|
| Auto-admission rate | ≥ 80% | Daily |
| Retry success rate | ≥ 90% | Daily |
| Rollback success rate | 100% | Per rollback |
| False positive rate | ≤ 1% | Daily |
| Blocker escalation accuracy | 100% | Per blocker |

### Secondary Metrics

| Metric | Target | Collection |
|--------|--------|------------|
| Task completion rate | ≥ 95% | Daily |
| Recovery success rate | ≥ 95% | Per recovery |
| Evidence completeness | 100% | Per task |
| Audit trail integrity | 100% | Daily |

---

## Real Workload Tasks

### Task Categories

| Category | Count | Description |
|----------|-------|-------------|
| Code analysis | 3 | Analyze existing codebase |
| File creation | 3 | Create new files |
| Configuration | 2 | Modify configurations |
| Multi-step | 2 | Complex multi-step tasks |
| Edge case | 2 | Unusual scenarios |

**Total**: 12 tasks over 7 days

---

## Risk Controls

### Observation Mode Rules

1. **不新增高风险功能**
2. **不修改 Gate 标准**
3. **不破坏 v2 baseline**
4. **不宣称生产级自治**

### Emergency Stop

以下情况立即停止观察期：
- R3 操作未授权执行
- 数据丢失
- 系统崩溃
- 安全审计失败

---

## Daily Report Template

```markdown
# Daily Run Report - YYYY-MM-DD

## Summary
- Status: [healthy | warning | critical]
- Tasks executed: N
- Tasks completed: N
- Tasks failed: N

## Metrics
| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Auto-admission rate | X% | ≥80% | ✅/⚠️/❌ |
| Retry success rate | X% | ≥90% | ✅/⚠️/❌ |
| False positive rate | X% | ≤1% | ✅/⚠️/❌ |

## Anomalies
- [List any anomalies]

## Blockers
- [List any blockers]

## Evidence
- [Link to evidence files]

## Next Steps
- [Planned actions for next day]
```

---

## Final Deliverables

### After 7 Days

1. **DAILY_RUN_REPORT_*.md** (7 reports)
2. **STABILITY_VALIDATION_REPORT.md**
3. **DEFAULT_AUTONOMY_GAP_CLOSURE_REPORT.md**

### Required Answers

1. 哪些缺口已关闭
2. 哪些仍未关闭
3. 是否仍不能宣称生产级自治
4. 下一步应该进入什么验证阶段

---

## Success Criteria

### Observation Period Success

- [ ] ≥ 10 tasks executed
- [ ] Auto-admission rate ≥ 80%
- [ ] Retry success rate ≥ 90%
- [ ] False positive rate ≤ 1%
- [ ] No R3 unauthorized execution
- [ ] All evidence complete

### Gap Closure Success

- [ ] All P0 contracts completed
- [ ] All P0 implementations completed
- [ ] All P0 tests passing

---

## Appendix

### Related Documents

- GAP_MATRIX.md
- 5 Contract Documents
- GATE_RULES.md
- AUTONOMY_CAPABILITY_BOUNDARY.md
