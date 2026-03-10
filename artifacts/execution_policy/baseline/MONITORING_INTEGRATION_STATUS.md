# Monitoring Integration Status

## Agent-Self-Health-Scaffold 运行状态

### Scheduler 统计
- **Total Runs**: 385+
- **Quick Mode**: 45+ runs (每 5 分钟)
- **Full Mode**: 21+ runs (每 1 小时)
- **Gate Mode**: 318+ runs (按需)
- **Last Heartbeat**: 2026-03-10 00:18 UTC

### Probe 状态
- **Total Probes**: 30
- **Passed**: 30/30 ✅
- **Failed**: 0

---

## Execution Policy 监控集成

### Probe: `probe-execution-policy-v2`

**状态**: ✅ 已集成到 P1_PROBES

**运行情况**:
```json
{
  "probe": "probe-execution-policy-v2",
  "status": "pass",
  "conclusion_type": "A-candidate",
  "policy_doctor_healthy": true,
  "sample_maturity": {
    "deny_samples": 0,
    "warn_samples": 0,
    "has_minimum_samples": false
  },
  "shadow_tracking": {
    "total_hits": 0
  }
}
```

**触发条件**:
- 每次 heartbeat 自动运行 (quick mode)
- 每 5 分钟检查一次
- Cooldown: 5 分钟

**输出位置**:
- `artifacts/self_health/probes/probe-execution-policy-v2.json`
- `artifacts/self_health/probes/probe_summary.json`

---

## 自动化功能

### 1. 自动 Probe 运行
✅ **已启用**
- Heartbeat 触发 quick mode
- 自动运行所有 P1_PROBES
- 包含 execution policy probe

### 2. 自动 Daily Report
✅ **已启用**
- Probe 运行时检查是否需要生成
- 每天只生成一次
- 保存到 `artifacts/execution_policy/daily_reports/`

### 3. 自动 Incident 生成
✅ **已启用**
- Probe 失败时自动创建 incident
- Dedup 机制防止重复告警

### 4. 自动 Proposal 生成
✅ **已启用**
- 严重问题时自动生成 proposal
- 建议修复动作

---

## Metrics 集成

### Always-On Metrics
```json
{
  "scheduler_runs_total": 385,
  "probe_runs_total": 50,
  "incident_total": 13,
  "proposal_total": 10,
  "deduped_incident_count": 16,
  "deduped_proposal_count": 19
}
```

### Execution Policy Metrics
- Policy Doctor: 7/7 checks passed
- Violations (24h): 0
- Effectiveness: N/A (样本不足)

---

## 监控覆盖范围

### Execution Policy Framework
| 组件 | Probe | 状态 |
|------|-------|------|
| Policy Doctor | ✅ | pass (7/7) |
| Rules Registry | ✅ | 9 active rules |
| Violations Dir | ✅ | monitored |
| Sample Maturity | ✅ | tracked |
| Shadow Tracking | ✅ | 3 rules monitored |
| Gate Integration | ✅ | connected |

### v1.1 Shadow Rules
| Rule | Status | Hits |
|------|--------|------|
| PERSIST_BEFORE_REPLY | shadow | 0 |
| FRAGILE_REPLACE_BLOCK | shadow | 0 |
| CHECKPOINT_REQUIRED_BEFORE_CLOSE | shadow | 0 |

---

## 下一步

1. **等待样本积累**: 真实任务触发 policy
2. **每日检查**: `policy-daily-report --save`
3. **监控告警**: Probe 失败会自动生成 incident
4. **样本成熟**: deny≥5, warn≥10 后进入 A-confirmed 评估

---

Last Updated: 2026-03-10 00:20 UTC
