# Scoring-Canary Runbook

**Created**: 2026-03-03 11:53 CST
**Commit**: `fd59d83`
**Mode**: Scoring-Canary (SI scoring ON, Shadow OFF)

---

## 当前配置

```json
{
  "shadow_sources": [],
  "enable_self_improving_scoring": true,
  "score_sources": ["self_improving"],
  "score_scope_allowlist": ["projects/openemotion", "domains/infra"],
  "max_corrections_per_entry_per_day": 3,
  "max_pending_proposals_per_scope_per_day": 10
}
```

---

## 运维节奏

### 每次 sweeper 跑完检查 6 项

| 指标 | 阈值 | 状态 |
|------|------|------|
| `rejected_rate` | 必须持续 0% | ⚠️ |
| `missing_session_rate` | 必须 ≤1% | ⚠️ |
| `prod_quarantined_rate_24h` | 持续 ≤5% | ⚠️ |
| `pending_review_growth_24h` | ≤20/天 | ⚠️ |
| `tier_changes_by_source[self_improving]` | 无异常尖峰 | ⚠️ |
| **allowlist 外影响** | 必须为 0 | ⚠️ |

### 建议频率

- **前 24h**: 每次 sweeper 后检查
- **3 天后**: 形成基线，可降低频率

---

## 回滚触发条件

命中任意一条立即秒回滚：

```bash
# 标准回滚
cat > ~/.openclaw/workspace/memory/sweeper_config.json << 'EOF'
{
  "shadow_sources": ["self_improving"],
  "enable_self_improving_scoring": false
}
EOF

# 紧急回滚 (完全忽略)
cat > ~/.openclaw/workspace/memory/sweeper_config.json << 'EOF'
{
  "ignore_sources": ["self_improving"]
}
EOF
```

### 回滚阈值

| 指标 | 触发值 |
|------|--------|
| `rejected_rate` | >0% |
| `missing_session_rate` | >1% |
| `prod_quarantined_rate_24h` | >5% 且持续上升 |
| `pending_review_growth_24h` | >20 |
| allowlist 外 tier/proposal 变更 | 任意出现 |
| tier_changes 异常尖峰 | 集中打某个 entry |

---

## 扩容条件

满足以下 **全部** 条件后再扩：

- [ ] 连续 ≥3 天 `rejected_rate = 0%`
- [ ] 连续 ≥3 天 `missing_session_rate ≤ 1%`
- [ ] 连续 ≥3 天 `prod_quarantined_rate_24h ≤ 5%`
- [ ] pending_review_growth 不超审核能力
- [ ] allowlist 外影响 = 0

### 扩容方式（渐进）

1. allowlist 增加 1 个 scope
2. 观察 24h
3. 再加下一个

---

## 基线建立（未来 3 天）

目标：获得两条经验阈值

1. **SI 事件日均量** (accepted / dedup / quarantined)
2. **人审负载** (pending 新增 / approve / reject 比例)

### 判断标准

| approve_rate | 含义 | 行动 |
|--------------|------|------|
| >70% | 信号质量不错 | 可考虑扩容 |
| >50% reject | 触发器太敏感 | 先调 adapter/规则 |

---

## 快速命令

```bash
# 检查状态
python3 ~/.openclaw/workspace/tools/memory-sweeper

# 查看统计
python3 ~/.openclaw/workspace/tools/memory-sweeper stats | jq '.window_24h'

# 查看 pending
cat ~/.openclaw/workspace/memory/review_queue.json | jq '.pending'

# 秒回滚
echo '{"shadow_sources": ["self_improving"], "enable_self_improving_scoring": false}' > ~/.openclaw/workspace/memory/sweeper_config.json
```

---

## 历史记录

| 时间 | 事件 | Commit |
|------|------|--------|
| 2026-03-03 14:40 | score 组件 + revisit 分离 + 趋势预警 | `c6fc0a2` |
| 2026-03-03 14:35 | 两类 boundary distance + hysteresis 推荐 | `323fe22` |
| 2026-03-03 14:25 | sweeper v2.0 - tier_change metrics + sim 自动检测 | `b71df28` |

---

## 当前 Canary 状态

```
🔍 Canary 6-Point Check
  1. rejected_rate = 0%: ✅ (0)
  2. missing_session_rate ≤ 1%: ✅ (0.0%)
  3. prod_quarantined_rate ≤ 5%: ✅ (4.9%)
  4. pending_review_growth ≤ 20/day: ✅ (2)
  5. tier_changes_spike ≤ 30: ⚠️ WARN (51 prod)
  6. allowlist外影响 = 0: ✅ (0)

🚦 CANARY_STATUS=WARN
```

### 状态机规则

| 状态 | 条件 | rollback_recommended |
|------|------|---------------------|
| PASS | 全部 ✅ | false |
| WARN | 至少一个 ⚠️, 无 ❌ | false |
| FAIL | 出现任意 ❌ | true |

### 第5项阈值

| tier_changes_24h_prod | 状态 | 含义 |
|-----------------------|------|------|
| ≤30 | ✅ | 正常 |
| 31-60 | ⚠️ WARN | 观察 |
| >60 | ❌ | 需要回滚 |

### dry-run 模式

```bash
# 测试/演练时不触发自动回滚
CANARY_DRYRUN=1 python3 ~/.openclaw/workspace/tools/memory-sweeper
```

### 机器可读输出

```json
{
  "canary_status": "WARN",
  "rollback_recommended": false,
  "tier_changes_24h_prod": 51,
  "diagnostics": {
    "revisit_rate": 7.4,
    "max_changes_per_entry": 4
  }
}
```

---

## 诊断指标

### 输出格式

```
📈 Diagnostics (prod+allowlist, last 24h)
  Unique entries: 54
  Revisit count (≥2 changes): 4
  Revisit rate: 7.4%
  Max changes per entry: 4
  Top churn entries:
    - mem_openemotion_001: 4 changes (projects/openemotion)
```

### 指标含义

| 指标 | 含义 | 判断标准 |
|------|------|----------|
| revisit_rate | 被修正 ≥2 次的 entry 占比 | >20% 需要关注 |
| max_changes | 单 entry 最高修正次数 | >5 需要 hysteresis |

### 诊断结论

| revisit_rate | max_changes | 结论 |
|--------------|-------------|------|
| ≤10% | ≤2 | 低抖动，系统在吸收新知识 |
| 10-20% | 3-5 | 中等波动，观察 |
| >20% | >5 | 高抖动，需要 hysteresis |

---

## 模拟流量隔离

### 自动检测 (memory-emit v1.4)

以下情况自动标记为 `source=sim`：

| 条件 | 示例 |
|------|------|
| memory_id 包含 batch_ | `mem_openemotion_batch_1` |
| memory_id 包含 final_ | `mem_openemotion_final_1` |
| memory_id 包含 sim_ | `mem_sim_test` |
| task_id 包含 dryrun | `task_dryrun_1` |
| CANARY_DRYRUN=1 环境 | 自动标记 user 为 sim |

### 手动标记

```bash
python3 ~/.openclaw/workspace/tools/memory-emit '{"event":"correction",...}' --source sim
```

`sim` source 会被排除在 prod 指标之外（与 `test` 同级）。

---

## Tier Change Metrics

### 输出位置

`memory/metrics/tier_changes.jsonl`

### Schema

```json
{
  "event": "tier_change",
  "timestamp": "2026-03-03T14:25:00Z",
  "memory_id": "mem_openemotion_001",
  "scope": "projects/openemotion",
  "from_tier": "WARM",
  "to_tier": "HOT",
  "score": 7.2,
  "threshold": 7.0,
  "boundary_distance": 0.2,
  "source_breakdown_24h": {"self_improving": 3, "user": 1}
}
```

### Tier 阈值

| Tier | Score 阈值 |
|------|-----------|
| HOT | ≥ 7.0 |
| WARM | ≥ 3.0 |
| COLD | < 3.0 |

### Boundary Distance

**两类指标**：

| 指标 | 含义 | 计算 |
|------|------|------|
| crossing_distance | tier_change 时的阈值距离 | 只在跨越时计算 |
| near_boundary_distance | 所有 entry 到最近阈值距离 | 始终计算 |

**输出示例**：

```
📊 Boundary Distance (crossings, tier_change 时)
  P50: 0.15
  P90: 0.45

📊 Distance to Nearest Threshold (all entries)
  P50: 1.65
  P90: 1.7
```

**判断标准**：

| crossing_distance_p50 | 含义 |
|----------------------|------|
| < 0.3 | 阈值边缘抖动，需要 hysteresis |
| ≥ 0.3 | 真实学习信号 |

---

## Hysteresis 自动推荐

### 触发条件

满足任意条件即推荐：

| 条件 | 含义 |
|------|------|
| `crossing_distance_p50 < 0.3` 且 `tier_changes >= 10` | 频繁边缘跨越 |
| `revisit_rate > 20%` | 同一 entry 被反复修正 |

### 推荐配置

```json
{
  "HOT_UP": 7.2,
  "HOT_DOWN": 6.8,
  "WARM_UP": 3.2,
  "WARM_DOWN": 2.8
}
```

### 冷却期

```
min_tier_change_interval_hours = 12
```

同一 entry 12 小时内最多变一次 tier。

### 输出示例

```
⚠️  Hysteresis Recommended: crossing_distance_low
  Recommended config: {"HOT_UP": 7.2, "HOT_DOWN": 6.8, ...}
```

---

## Score 分布

### 输出示例

```
📊 Score Distribution
  Score P50: 1.35
  Score P90: 1.6
  Components P50: use=0.0, recency=1.05, importance=0.3, conflict=0.0
```

### Score 组件

| 组件 | 计算方式 | 含义 |
|------|----------|------|
| use_term | `log(1 + use_count) * 1.5` | 使用频率 |
| recency_term | `1.0 - days_ago * 0.05` | 最近活跃度 |
| importance_term | `min(1.5, correction_count * 0.3)` | 重要程度 |
| conflict_term | `conflict_count * 0.5` | 冲突惩罚 |

### 诊断用途

- `use_term_p50 = 0` → 需要更多 use 事件
- `recency_term_p50 < 0.5` → 事件过期太快
- `importance_term_p50 = 0` → 需要 correction 事件

---

## Revisit 分离

| 指标 | 含义 | 触发 hysteresis |
|------|------|-----------------|
| revisit_rate (events) | 同一 entry 多次收到事件 | ❌ 不触发 |
| revisit_rate_tier_changes | 同一 entry 多次 tier 变化 | ✅ 触发 |

---

## 趋势预警

### Delta 输出

```
📊 Distance to Nearest Threshold (all entries)
  P50: 1.65
  Delta 24h: -0.3
  ⚠️  快速接近阈值 → 提高观察频率
```

### 预警规则

| delta_24h | 含义 |
|-----------|------|
| < -0.5 | 快速接近阈值，提高观察频率 |
| > 0 | 远离阈值，系统稳定 |

---

## 扩容硬门槛

准备扩大 allowlist 或全量启用时，必须满足：

- [ ] 连续 3 天 `CANARY_STATUS=PASS`
- [ ] `tier_changes_24h_prod` 在可控范围 (≤30)
- [ ] `crossing_distance_p50` ≥ 0.3 (或 tier_changes 很少)
- [ ] `allowlist外影响 = 0`

---

## 48 小时稳态验证清单

### 检索覆盖率

| 指标 | 目标 | 检查方式 |
|------|------|----------|
| retrieval_trigger_rate | ≥90% | `grep -c '"event": "retrieval"' events.log` |
| pinned_hit_rate | ≥50% | Stage 1 命中率 |

### 召回精度

| 指标 | 目标 | 检查方式 |
|------|------|----------|
| tombstone_hit_rate | 0% | `jq 'select(.tombstone_hits > 0)' events.log` |
| citation_complete_rate | 100% | 手动检查引用是否带 doc_id |

### 验证步骤

```bash
# 1. 检查检索事件
grep '"event": "retrieval"' ~/.openclaw/workspace/memory/events.log | wc -l

# 2. 检查 tombstone 命中
grep '"tombstone_hits": [1-9]' ~/.openclaw/workspace/memory/events.log

# 3. 检查 Stage 1 vs Stage 2 比例
grep '"stage": "pinned"' ~/.openclaw/workspace/memory/events.log | wc -l
grep '"stage": "semantic"' ~/.openclaw/workspace/memory/events.log | wc -l
```

### 失败处理

| 问题 | 行动 |
|------|------|
| retrieval_trigger_rate < 90% | 检查触发规则是否完整 |
| tombstone_hit_rate > 0 | 更新 TOMBSTONES.jsonl |
| Stage 1 命中率低 | 更新 pinned_pointers |
