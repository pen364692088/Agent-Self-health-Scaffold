# Session: 2026-03-04 02:31:00 UTC

- **Session Key**: agent:main:main
- **Session ID**: 2bb0cfaf-82db-4b2a-b322-6eb17a876e8a
- **Source**: telegram

## Conversation Summary

assistant: 开始实现。更新 dashboard 添加场景分桶：
assistant: **✅ Memory Retrieval Hardening v1.2.5 完成**

| Task | 状态 | 交付物 |
|------|------|--------|
| 1. 场景分桶 | ✅ | A/B 桶分离，只对 A 桶用 10% WARN |
| 2. 豁免项 | ✅ | `linkability` 字段，只统计 expected |
| 3. 文档更新 | ✅ | MAINTENANCE.md |

---

**完整版本演进 (v1.2 → v1.2.5)**:

| 版本 | 功能 |
|------|------|
| v1.2 | Adoption 指标拆分 + Use 结构化输出 + 语义闸门 + 监控面板 |
| v1.2.1 | 强一致回归测试 + 口径细化 + 风险告警 |
| v1.2.2 | 样本量门槛 + 分阶段阈值 + orphan 指标 |
| v1.2.3 | 报告版本化 + 可消费摘要 + CI 集成 |
| v1.2.4 | config_hash 可复现 + orphan 拆分 + 快照回归 |
| v1.2.5 | 场景分桶 + 豁免项 |

---

**关键改进 (v1.2.5)**:

| 指标 | 改进前 | 改进后 |
|------|--------|--------|
| `unadopted_recall_rate` | 统一 10% WARN | A 桶 10% WARN，B 桶宽松 |
| `broken_link_recall_rate` | 统计所有 | 只统计 `linkability=expected` |

**新增指标**:
- `recall_bucket_a` / `recall_bucket_b`
- `unadopted_rate_bucket_a` / `unadopted_rate_bucket_b`
- `expected_link_count` / `broken_link_expected`

---

**告警规则 (v1.2.5 最终版)**:

| 指标 | 条件 | 级别 |
|------|------|------|
| `unadopted_rate_bucket_a` | > 10% | WARN |
| `broken_link_recall_rate` | > 5% (expected) | ERROR |

---

**运行命令**:
```bash
# 每日观测
~/.openclaw/workspace/tools/memory-daily-obs

# CI 检查
~/.openclaw/workspace/tools/ci-memory-hardening

# 回归测试
python3 ~/.openclaw/workspace/tests/test_memory_retrieval_hardening.py
```
user: Conversation info (untrusted metadata):
```json
{
  "timestamp": "Tue 2026-03-03 19:59 CST"
}
```

v1.2.5 交接摘要（复制即用） 版本能力 unadopted 指标：分 A/B 桶，只对 A 桶执行 >10% WARN broken_link 指标：引入 linkability，只统计 expected（避免不可链接数据源误报） 文档：已更新 memory/MAINTENANCE.md 新增/调整指标 recall_bucket_a, recall_bucket_b unadopted_rate_bucket_a, unadopted_rate_bucket_b expected_link_count, broken_link_expected broken_link_recall_rate = broken_link_expected / max(expected_link_count, 1) 告警规则（最终版） unadopted_rate_bucket_a > 10% → WARN broken_link_recall_rate > 5%（expected-only）→ ERROR 运行命令 # 每日观测 ~/.openclaw/workspace/tools/memory-daily-obs # CI 检查 ~/.openclaw/workspace/tools/ci-memory-hardening # 回归测试 python3 ~/.openclaw/workspace/tests/test_memory_retrieval_hardening.py 我建议你立刻补的 2 条“防走样”告警（强烈推荐） 分桶 + 豁免项会降低误报，但也可能出现两种“掩盖式健康”： 1) Bucket Mix Drift：A 桶占比异常下降（把 WARN 样本挪走） 指标： bucket_a_ratio = recall_bucket_a / max(recall_bucket_a + recall_bucket_b, 1) 告警建议： bucket_a_ratio 日环比相对下降 > 30% → WARN （或：低于 7 日中位数的 0.7 倍） 含义：A 桶突然变少，unadopted_rate_bucket_a 可能“看起来变好”，但实际上是桶边界/阈值/候选质量变化导致样本漂移。 2) Linkability Coverage：expected 占比下降（把 ERROR 样本豁免掉） 指标： expected_ratio = expected_link_count / max(total_recall_count, 1) 告警建议： expected_ratio < 70% → WARN（或 ERROR，取决于你数据源是否本应全可链接） 或：连续 2 天下降且累计下降 > 15% → WARN 含义：你只统计 expected 是对的，但如果上游开始把事件标成 unknown/not_applicable，broken_link_recall_rate 会假装健康。 如果你愿意把它纳入 v1.2.6，我可以把这两条直接写成 memory-risk-alerts 的规则块（按你现在的配置风格：阈值/分阶段/LOW_SAMPLE 降级/strict 模式）。 你更倾向用哪种阈值形式？ A) 固定阈值（70%、30%） B) 相对基线（对 7 日滚动中位数/均值的偏离）
assistant: 选择 **B) 相对基线**，与现有分阶段阈值哲学一致。开始实现 v1.2.6：
assistant: **✅ Memory Retrieval Hardening v1.2.6 完成**

| Task | 状态 | 交付物 |
|------|------|--------|
| 1. Bucket Mix Drift | ✅ | `bucket_a_ratio` < 70% 中位数 → WARN |
| 2. Linkability Coverage | ✅ | `expected_ratio` < 70% 或 < 85% 中位数 → WARN |
| 3. 历史基线 | ✅ | 7 日滚动中位数 |

---

**完整版本演进 (v1.2 → v1.2.6)**:

| 版本 | 功能 |
|------|------|
| v1.2 | Adoption 指标拆分 + Use 结构化输出 + 语义闸门 + 监控面板 |
| v1.2.1 | 强一致回归测试 + 口径细化 + 风险告警 |
| v1.2.2 | 样本量门槛 + 分阶段阈值 + orphan 指标 |
| v1.2.3 | 报告版本化 + 可消费摘要 + CI 集成 |
| v1.2.4 | config_hash 可复现 + orphan 拆分 + 快照回归 |
| v1.2.5 | 场景分桶 + 豁免项 |
| v1.2.6 | 漂移检测：Bucket Mix Drift + Linkability Coverage |

---

**告警规则 (v1.2.6 最终版)**:

| 指标 | 条件 | 级别 | 目的 |
|------|------|------|------|
| `unadopted_rate_bucket_a` | > 10% | WARN | 业务问题 |
| `broken_link_recall_rate` | > 5% (expected) | ERROR | 工程质量 |
| `bucket_a_ratio` | < 70% 中位数 | WARN | 防掩盖 |
| `expected_ratio` | < 70% 或 < 85% 中位数 | WARN | 防掩盖 |

---

**运行命令**:
```bash
# 每日观测
~/.openclaw/workspace/tools/memory-daily-obs

# CI 检查
~/.openclaw/workspace/tools/ci-memory-hardening

# 回归测试
python3 ~/.openclaw/workspace/tests/test_memory_retrieval_hardening.py
```
user: Conversation info (untrusted metadata):
```json
{
  "timestamp": "Tue 2026-03-03 20:09 CST"
}
```

会话归档
assistant: ## Session Wrap-Up Complete ✅

**Captured to daily log:**
- Memory Retrieval Hardening v1.2 → v1.2.6 完整实现
- 7 个版本迭代，从基础指标到漂移检测
- 完整工具链：dashboard, alerts, daily-obs, CI, tests

**Updated:**
- `memory/2026-03-03.md`: 会话详情
- `memory.md`: 核心语义 + 工具位置
- `SESSION-STATE.md`: 任务状态

**Indexed to SQLite:**
- 4622 events, 889 high-signal extractions ✅

**OpenViking semantic:** 有部分错误（context length），但语义层 33 条已处理

**Raw logs preserved:** `~/.openclaw/agents/main/sessions/` (audit-ready)

**Committed:** `wrap-up: 2026-03-03 session summary` ✅

**Push failed:** 无远程仓库配置（本地提交已保留）

---

### Follow-up Next Session

- 运行每日观测：`~/.openclaw/workspace/tools/memory-daily-obs`
- 观测期 (2026-03-03 → 2026-03-06) 检查指标趋势
- `use_term_p50` 是否从 0 抬升

---

### 版本交付物

| 版本 | 核心功能 |
|------|----------|
| v1.2.6 | 漂移检测 |
| v1.2.5 | 场景分桶 + 豁免项 |
| v1.2.4 | 快照回归 |
| v1.2.3 | CI 集成 |
| v1.2.2 | 样本量门槛 |
| v1.2.1 | 回归测试 |
| v1.2 | 基础指标 |

**Ready for new session! ⚡**
user: Conversation info (untrusted metadata):
```json
{
  "timestamp": "Tue 2026-03-03 20:11 CST"
}
```

执行长任务,任务目标在:/home/moonlight/Desktop/BetterWork/handover_memory_retrieval_hardening_v1_2_6.md
assistant: 理解。启动 **v1.2.7 基线热启动 + 绝对下限 + 解释字段 + 快照回归**：
assistant: **✅ Memory Retrieval Hardening v1.2.7 完成**

| Task | 状态 | 交付物 |
|------|------|--------|
| 1. 基线热启动期 | ✅ | `WARN_SOFT` + `baseline_warmup` 字段 |
| 2. 绝对下限保护 | ✅ | 10% / 50% 最小阈值 |
| 3. 解释字段 | ✅ | value, baseline, threshold_applied, delta_pct |
| 4. 快照回归 | ✅ | sample_9 + sample_10 (10 tests) |

---

**完整版本演进 (v1.2 → v1.2.7)**:

| 版本 | 功能 |
|------|------|
| v1.2.7 | 热启动期 + 绝对下限 + 解释字段 |
| v1.2.6 | 漂移检测 |
| v1.2.5 | 场景分桶 + 豁免项 |
| v1.2.4 | 快照回归 |
| v1.2.3 | CI 集成 |
| v1.2.2 | 样本量门槛 |
| v1.2.1 | 回归测试 |
| v1.2 | 基础指标 |

---

**漂移检测规则 (v1.2.7 最终版)**:

| 指标 | 告警规则 | 下限 |
|------|----------|------|
| `bucket_a_ratio` | < max(0.70 × median, 0.10) | 10% |
| `expected_ratio` | < max(0.85 × median, 0.50) | 50% |

**热启动期**:
- 基线天数 < 7 → `WARN_SOFT`（不触发 strict fail）

**解释字段**:
```
{
  "value": 0.45,
  "baseline": 0.65,
  "threshold_applied": 0.455,
  "delta_pct": -0.3077,
  "baseline_days": 3,
  "warmup": true
}
```

---

**运行命令**:
```bash
# 每日观测
~/.openclaw/workspace/tools/memory-daily-obs

# CI 检查
~/.openclaw/workspace/tools/ci-memory-hardening

# 回归测试
python3 ~/.openclaw/workspace/tests/test_memory_retrieval_hardening.py
```
user: Conversation info (untrusted metadata):
```json
{
  "timestamp": "Tue 2026-03-03 20:23 CST"
}
```

执行长任务,任务目标在:/home/moonlight/Desktop/BetterWork/handover_memory_retrieval_hardening_v1_2_7.md
assistant: 这是 v1.2.7 stable handover 文档。启动 **v1.2.8 操作章程加固**：
assistant: **✅ Memory Retrieval Hardening v1.2.8 完成**

| Task | 状态 | 交付物 |
|------|------|--------|
| 1. strict 定义 | ✅ | ERROR/WARN/WARN_SOFT 行为规范 |
| 2. baseline 审计 | ✅ | config_hash 变化检测 + BASELINE_RESET |
| 3. 工具更新 | ✅ | dashboard + alerts 显示 config_hash |

---

**完整版本演进 (v1.2 → v1.2.8)**:

| 版本 | 功能 |
|------|------|
| v1.2.8 | 操作章程：strict 定义 + baseline 审计 |
| v1.2.7 | 热启动期 + 绝对下限 + 解释字段 |
| v1.2.6 | 漂移检测 |
| v1.2.5 | 场景分桶 + 豁免项 |
| v1.2.4 | 快照回归 |
| v1.2.3 | CI 集成 |
| v1.2.2 | 样本量门槛 |
| v1.2.1 | 回归测试 |
| v1.2 | 基础指标 |

---

**操作章程（v1.2.8 最终版）**:

| 级别 | strict=true | strict=false | 行为 |
|------|-------------|--------------|------|
| ERROR | fail | fail | 工程质量，永远 fail |
| WARN | fail | 不 fail | 业务问题，由 strict 决定 |
| WARN_SOFT | 不 fail | 不 fail | 热启动期，永远不 fail |
| INFO | 不 fail | 不 fail | 提示信息 |

**baseline 审计规则**:
- baseline 只能来自同一 `config_hash`
- 跨 `config_hash` → `BASELINE_RESET` → 重新进入 warmup

**新增字段**:
```json
{
  "config_hash": "ac075ff6",
  "baseline_config_hash": "ac075ff6",
  "config_hash_match": true,
  "baseline_reset": false
}
```

---

**运行命令**:
```bash
# 每日观测
~/.openclaw/workspace/tools/memory-daily-obs

# CI 检查
~/.openclaw/workspace/tools/ci-memory-hardening

# 回归测试
python3 ~/.openclaw/workspace/tests/test_memory_retrieval_hardening.py
```
user: Conversation info (untrusted metadata):
```json
{
  "timestamp": "Tue 2026-03-03 20:29 CST"
}
```

会话归档
assistant: ## Session Wrap-Up Complete ✅

**Captured to daily log:**
- Memory Retrieval Hardening v1.2 → v1.2.8 完整实现
- 8 个版本迭代，从基础指标到操作章程
- 完整工具链 + 告警规则 + 维护文档

**Updated:**
- `memory/2026-03-03.md`: 完整会话记录
- `memory.md`: 操作章程 + 版本演进
- `SESSION-STATE.md`: 任务状态

**Indexed to SQLite:**
- 4468 events, 831 high-signal extractions ✅

**Raw logs preserved:** `~/.openclaw/agents/main/sessions/` (audit-ready)

**Committed:** `wrap-up: 2026-03-03 session summary` ✅

**Push failed:** 无远程仓库配置（本地提交已保留）

---

### 版本交付物

| 版本 | 核心功能 |
|------|----------|
| v1.2.8 | 操作章程：strict + baseline 审计 |
| v1.2.7 | 热启动期 + 绝对下限 + 解释字段 |
| v1.2.6 | 漂移检测 |
| v1.2.5 | 场景分桶 |
| v1.2.4 | 快照回归 |
| v1.2.3 | CI 集成 |
| v1.2.2 | 样本量门槛 |
| v1.2.1 | 回归测试 |
| v1.2 | 基础指标 |

---

### Follow-up Next Session

- 运行每日观测：`~/.openclaw/workspace/tools/memory-daily-obs`
- 观测期 (2026-03-03 → 2026-03-06) 检查指标趋势
- `use_term_p50` 是否从 0 抬升
- `config_hash` 是否触发 BASELINE_RESET

---

**Ready for new session! ⚡**
