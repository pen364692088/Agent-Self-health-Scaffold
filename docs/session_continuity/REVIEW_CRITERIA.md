# Session Continuity Review Criteria

**Version**: v1.1.1a
**Purpose**: 定义观察期评审门槛

---

## 可以进入 Layer 2 / MVP11.5 的条件

### 硬性门槛

| 条件 | 要求 | 检查方式 |
|------|------|----------|
| Recovery Success Rate | > 95% | daily_metrics.json |
| Uncertainty Rate | < 10% | daily_metrics.json |
| 无结构性漏记 | 0 major issues | deep-audit |
| 无明显去重错误 | 0 duplicate keys | deep-audit |

### 软性门槛

| 条件 | 要求 | 检查方式 |
|------|------|----------|
| Main agent 样本 | ≥ 3 real recoveries | event log |
| cc-godmode 样本 | ≥ 1 real task | event log |
| Gate 样本 | ≥ 1 real gate run | event log |
| 异常案例可解释 | 100% explained | anomaly ledger |

---

## 不建议推进的情况

### 阻断性

| 问题 | 原因 |
|------|------|
| 样本量过小 | < 5 recoveries total |
| 假成功事件 | success rate 高但不可用 |
| 数据不一致 | summary 与 event log 对不上 |
| 去重失效 | duplicate keys 存在 |

### 需调查性

| 问题 | 原因 |
|------|------|
| 链路空洞 | Gate/handoff 无真实样本 |
| cc-godmode 仅文档 | 无实际长任务运行 |
| uncertainty 过高 | > 10% 但未解释 |
| 跨入口不一致 | 不同入口表现不同 |

---

## 评审清单

### 数据完整性

- [ ] Event log 可追溯
- [ ] Daily snapshots 完整
- [ ] Anomaly ledger 已填写
- [ ] Coverage targets 达成

### 质量指标

- [ ] Recovery Success Rate > 95%
- [ ] Uncertainty Rate < 10%
- [ ] Dedup correctness 100%
- [ ] Event/File consistency 100%

### 样本分布

- [ ] Main agent 有样本
- [ ] cc-godmode 有样本
- [ ] Gate A/B/C 有样本
- [ ] 跨入口一致

### 异常处理

- [ ] 所有异常已记录
- [ ] 根因已分析
- [ ] 无未解释的异常

---

## 评审输出

### PASS - 进入 Layer 2

条件：
- 所有硬性门槛满足
- 所有软性门槛满足
- 无阻断性问题

### CONDITIONAL - 有条件进入

条件：
- 硬性门槛满足
- 部分软性门槛未满足
- 需补充说明或承诺

### FAIL - 继续观察

条件：
- 硬性门槛未满足
- 或存在阻断性问题

---

## 评审日期

**Scheduled**: 2026-03-14
**Location**: artifacts/session_continuity/v1_1_1/REVIEW_REPORT.md

---

*End of Review Criteria*
