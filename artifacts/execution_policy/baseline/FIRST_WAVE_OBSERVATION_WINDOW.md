# First Wave Observation Window Tracker

## Status
🟡 CONTROLLED OBSERVATION - A-Candidate

## 核心目标 (明确)

**当前阶段目标不是减少 violation 数，而是拿到足够有效样本，验证策略链路是否真实成立。**

当前 0 deny / 0 warn / 0 fallback 不等于系统很好，更多说明：
- 规则还没被真实任务充分触发
- 或真实任务流量还没覆盖关键场景

**追求的不是"零"，而是"有代表性的触发"。**

---

## Time Window
- **Start**: 2026-03-09 18:30 UTC
- **Duration**: 3-7 天
- **Current**: Day 0

## Sample Maturity Thresholds (FROZEN - 观察窗期间不改)

| 样本类型 | 最小要求 | 当前 | 状态 |
|---------|---------|------|------|
| Deny 样本 | ≥5 | 0 | ❌ |
| Warn 样本 | ≥10 | 0 | ❌ |
| Fallback 样本 | ≥3 | 0 | ❌ |
| Gate deny/recover | ≥3 | 0 | ❌ |
| 敏感路径操作 | ≥20 | 0 | ❌ |

**重要**: 阈值在首轮观察窗期间冻结，不再调整，确保可比性。

---

## Daily Checklist (5 件事)

每天只看这五项，足够判断观察窗是否有价值：

| # | 检查项 | 当前 | 目标 |
|---|--------|------|------|
| 1 | 第一批 deny 样本 | 0 | ≥5 |
| 2 | 第一批 warn 样本 | 0 | ≥10 |
| 3 | fallback 实际成功样本 | 0 | ≥3 |
| 4 | top repeated rule/path 开始集中 | 无数据 | 有明确 top |
| 5 | shadow rules 首次命中 | 0 | 开始出现 |

**只要这五项开始动起来，观察窗就真正开始有价值。**

---

## 0 Hits 诊断 (重点)

Shadow tracking 全是 0 hits，需要区分两种情况：

### 情况 A: 真的没有对应行为发生
- 说明这批规则可能不是当前最值得工程化的
- 结论：观察后再决定是否调整优先级

### 情况 B: 行为发生了，但 tracker 没捕捉到
- 说明 matcher / event source / instrumentation 有漏
- 结论：需要修复检测链路

**诊断方法**: 抽几次真实任务人工复核
- 理论上该命中的，shadow 有没有命中
- 理论上不该命中的，有没有误命中

---

## Conclusion Interpretation

| Grade | 含义 | 当前 |
|-------|------|------|
| A-candidate | 结构正常，样本不足 | ✅ 当前状态 |
| A-confirmed | 样本成熟 + 指标达标 | ⏳ 待验证 |
| B | 有小问题，需小修 | - |
| C | 部分指标异常，需收缩 | - |
| D | 主链路有问题 | - |

---

## v1.1 Priority (冻结)

等样本成熟后，按此顺序推进 runtime：

1. **FRAGILE_REPLACE_BLOCK** - 最接近已上线规则，收益明确
2. **CHECKPOINT_REQUIRED_BEFORE_CLOSE** - 边界清楚，易验证
3. **PERSIST_BEFORE_REPLY** - 价值高，但上下文依赖强，适合慢一点

**当前策略**: Shadow tracking only，不急着上 runtime

---

## Daily Check Commands

```bash
# 日常巡检 (5 件事)
~/.openclaw/workspace/tools/policy-daily-check

# 分布分析
~/.openclaw/workspace/tools/policy-violation-summary --hours 24

# Shadow tracking
~/.openclaw/workspace/tools/policy-shadow-tracker --summarize
```

---

Last Updated: 2026-03-09 19:15 UTC
