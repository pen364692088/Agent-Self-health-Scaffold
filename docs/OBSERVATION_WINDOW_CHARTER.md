# 观察窗口启动声明

## 正式状态标记

**生效时间**: 2026-03-15 05:17 CDT
**项目**: Agent-Self-health-Scaffold
**阶段**: 首期自愈闭环验收通过

---

## 当前授权状态

| 项目 | 状态 | 说明 |
|------|------|------|
| 首期自愈闭环验收 | ✅ 已通过 | Gate A/B/C 全部通过 |
| 进入观察期 | ✅ 已批准 | 7-14 天观察窗口 |
| 自动进化主链 | ❌ 未授权 | 禁止自动修改主链代码 |
| 高风险目录自动修改 | ❌ 未授权 | 仅限沙箱内操作 |
| 自动合主链 | ❌ 未授权 | 所有人工审核 |

---

## 观察窗口参数

| 参数 | 值 |
|------|------|
| 启动时间 | 2026-03-15 05:17 CDT |
| 结束时间 | 2026-03-29 05:17 CDT (14天) |
| 基线 tag | self-health-v1-obs-day0 |
| 观察范围 | self-healing 模块 |

---

## 观察期禁止事项

1. **禁止扩大 scope** - 只修 bug，不增加新功能
2. **禁止修改 Gate 定义** - Gate A/B/C 契约冻结
3. **禁止自动合主链** - 所有修复需人工审核
4. **禁止外部学习入主链** - shadow 层隔离

---

## 观察期监控指标

每日记录以下指标：

| 指标 | 说明 | 目标 |
|------|------|------|
| recurrence_rate_by_signature | 按签名的复发率 | < 10% |
| auto_remediation_success_rate | 自动修复成功率 | > 80% |
| false_fix_rate | 误修率 | < 5% |
| rollback_count | 回滚次数 | < 3/周 |
| prevention_hit_rate | 预防规则命中率 | 记录趋势 |

---

## 观察期结束后评估

观察期结束后需回答五个核心问题：

1. **人工继续**: 是否仍需频繁人工介入？
2. **重复泄漏**: 是否有签名反复泄漏？
3. **ledger 分叉**: 记忆是否出现不一致？
4. **恢复后停滞**: 修复后系统是否正常工作？
5. **恢复风暴**: 是否出现级联修复？

---

## 归档证据路径

| 证据 | 路径 |
|------|------|
| Final Audit Pack V2 | `docs/archive/FINAL_AUDIT_PACK_V2.md` |
| Gate B 原始输出 | `artifacts/observation_window/gate_b_stdout.txt` |
| Gate C 原始输出 | `artifacts/observation_window/gate_c_stdout.txt` |
| Evidence 2 JSON 样本 | `artifacts/observation_window/evidence_2_sample.json` |
| Commit Diff | `artifacts/observation_window/commit_diffs.patch` |

---

## 签署

- **验收通过**: 2026-03-15 05:10 CDT
- **观察窗口启动**: 2026-03-15 05:17 CDT
- **系统成熟度声明**: ❌ 未成熟，需观察期验证

---

*此文件为观察窗口启动的正式声明，任何超出授权范围的修改需重新审批。*
