# SESSION-STATE.md

## 当前目标
**观察层 - 规则已锁定**

---

## 当前真实状态（2026-03-17T22:20:00Z）

### A. 当前所在层
**观察层（规则已锁定）**

### B. 主链接入状态
**已接入**

调用链：`openclaw-gateway.service` → `auto-resume-orchestrator.service` → `run-state recover` → `subtask-orchestrate resume`

### C. 启用状态
**默认启用** - `PartOf=openclaw-gateway.service`

### D. 真实触发证据
**有**

| 项目 | 值 |
|------|-----|
| 最新 E2E | ✅ PASS (2026-03-16) |
| 历史 baseline 样本 | 11 次 |
| 本轮窗口样本 | 0 次 |

### E. 观察期规则锁定状态

| 规则 | 状态 |
|------|------|
| 历史样本排除出本轮毕业统计 | ✅ 已锁定 |
| 恢复机会定义收紧 | ✅ 已锁定 |
| 自然/主动演练样本分层 | ✅ 已锁定 |
| 版本冻结写入 | ✅ 已锁定 |

---

## 观察期状态

| 项目 | 值 |
|------|-----|
| 开始时间 | 2026-03-17T22:20:00Z |
| 预计结束 | 2026-03-24T22:20:00Z |
| 版本锁定 | self-health-v2-obs-day0 |
| 当前天数 | Day 0 |
| Baseline 样本 | 11 次（不计入毕业） |
| **窗口新增样本** | **0 次** |
| 红线违规 | 0 |

### 毕业条件

- [ ] 观察窗口新增有效样本 ≥ 10
- [ ] 成功率 ≥ 95%
- [ ] 人工补继续 = 0
- [ ] 误恢复 = 0
- [ ] 红线违规 = 0

---

## 分支
main

## Blocker
无

## 下一步
- 开始 Day 1 样本统计
- 等待自然发生的 gateway restart 或触发主动演练

---

## 更新时间
2026-03-17T22:20:00Z

## 审计证据
- 审计报告: `docs/AUDIT_REPORT_2026-03-17.md`
- 整改报告: `docs/AUDIT_REMEDIATION_REPORT_2026-03-17.md`
- E2E 报告: `docs/AUTO_RESUME_LATEST_E2E_REPORT_2026-03-17.md`
- 观察期方案: `docs/OBSERVATION_PERIOD_PLAN_2026-03-17.md`
- 观察期状态: `artifacts/self_health/observation/observation_state.json`
