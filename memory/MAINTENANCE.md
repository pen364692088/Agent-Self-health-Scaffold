# Memory Retrieval Hardening - Maintenance Guide

## Golden Fixture 更新流程（强制执行）

### 原则
Golden fixture 是回归测试的稳定基准，**严禁随意修改**。

### 允许更新的情况（语义级变更）
只有在以下情况下才允许更新 fixture：

1. **事件 schema 变更**：event_version 升级、字段重命名、新增必填字段
2. **指标口径变更**：adoption_rate_any 定义变化、orphan 判定逻辑变化
3. **阈值语义变更**：MIN_EVENTS、MIN_SESSIONS、分阶段阈值逻辑变化
4. **工具链变更**：新增核心工具、移除核心工具

### 更新流程
```bash
# 1. 创建变更 PR，在描述中写明：
#    - 为什么语义变了
#    - 哪些断言需要更新
#    - 预期的 dashboard/alerts 输出变化

# 2. 更新 fixture
vim memory/golden_fixtures/events_golden.jsonl

# 3. 更新测试断言
vim tests/test_memory_retrieval_hardening.py

# 4. 更新期望输出快照（如果有）
vim memory/golden_fixtures/expected_dashboard.json
vim memory/golden_fixtures/expected_alerts.json

# 5. 运行 CI 验证
./tools/ci-memory-hardening

# 6. 在 PR 中附上新旧快照 diff
```

### 禁止行为
- ❌ 为了让 CI 变绿而修改 fixture
- ❌ 修改 fixture 但不更新测试断言
- ❌ 修改 fixture 但不更新文档
- ❌ 跳过语义变更审查直接合并

---

## config_hash 计算规则（v1.2.4）

### 目的
确保报告可追溯到具体的配置版本。

### 规则
config_hash **只包含有效配置**：
- ✅ 工具版本号
- ✅ 阈值常量
- ✅ 部署日期

**不包含**：
- ❌ 时间戳
- ❌ 文件路径
- ❌ 随机种子
- ❌ 主机名/IP

### 示例
```json
{
  "tool_versions": "dashboard=1.2.3 alerts=1.2.3 audit=1.2.1",
  "thresholds": {
    "min_events": 200,
    "min_sessions": 20,
    "use_attribution": 0.99,
    "unique_to_raw_grace": 0.25,
    "unique_to_raw_strict": 0.50
  },
  "deploy_date": "2026-03-03"
}
```

hash = md5(json.dumps(payload, sort_keys=True))

---

## orphan_recall_rate 拆分定义（v1.2.4）

### 问题
`orphan_recall_rate` 混合了两种不同含义：
1. 正常业务：窗口内 recall 未被采用
2. 工程问题：recall 事件缺少可关联字段

### 拆分方案

| 指标 | 含义 | 类型 |
|------|------|------|
| `unadopted_recall_rate` | 窗口内未采用的 recall 占比 | 业务指标 |
| `broken_link_recall_rate` | 缺少可关联字段（如 recall_id）的 recall 占比 | 工程质量指标 |

### 告警级别
- `unadopted_recall_rate` 高 → WARN（业务问题）
- `broken_link_recall_rate` 高 → ERROR（工程质量问题）

---

## 场景分桶（v1.2.5）

### 问题
`unadopted_recall_rate` 混合了两种场景：
1. 应该被采用但未采用（问题）
2. 候选质量低导致未采用正常（正常）

### 拆分方案

| 桶 | 定义 | 告警阈值 |
|---|------|----------|
| A 桶 | 有候选且命中阈值（应该被采用） | 10% WARN |
| B 桶 | 候选质量低/被闸门过滤（未采用正常） | 宽松观测 |

### 判断逻辑
```python
if candidates_count > 0 and not filtered:
    bucket = "A"  # 应该被采用
else:
    bucket = "B"  # 未采用正常
```

---

## broken_link 豁免项（v1.2.5）

### 问题
某些数据源本身不带可关联字段，不应触发 ERROR。

### 方案
添加 `linkability` 字段：
- `expected`：应该有可关联字段（默认）
- `unknown`：未知数据源
- `not_applicable`：明确不需要关联

### 统计范围
只统计 `linkability=expected` 的部分。

### 示例
```json
{"event": "recall", "recall_id": "r1", "linkability": "expected", ...}
{"event": "recall", "linkability": "not_applicable", ...}  // 不计入 broken_link
```

---

## 快照回归

### 目的
防止 dashboard/alerts 输出格式意外变化。

### 位置
- `memory/golden_fixtures/expected_dashboard.json`
- `memory/golden_fixtures/expected_alerts.json`

### 更新时机
与 golden fixture 同步更新。

---

## 版本历史

| 版本 | 变更 |
|------|------|
| v1.2.8 | 操作章程：strict 定义 + baseline 审计 + config_hash RESET |
| v1.2.7 | 热启动期 + 绝对下限 + 解释字段 |
| v1.2.6 | 漂移检测：Bucket Mix Drift + Linkability Coverage |
| v1.2.5 | 场景分桶 + broken_link 豁免项 |
| v1.2.4 | config_hash 可复现 + orphan_recall_rate 拆分 + 快照回归 |
| v1.2.3 | 报告版本化 + 可消费摘要 + CI 集成 |
| v1.2.2 | 样本量门槛 + 分阶段阈值 + orphan 指标 |
| v1.2.1 | 强一致回归测试 + 口径细化 + 风险告警 |
| v1.2 | Adoption 指标拆分 + Use 结构化输出 + 语义闸门 |

---

## 漂移检测（v1.2.6）

### 问题
分桶 + 豁免项会降低误报，但也可能出现"掩盖式健康"。

### 解决方案

#### 1. Bucket Mix Drift
检测 A 桶占比异常下降（把 WARN 样本挪到 B 桶）。

| 指标 | 定义 | 告警规则 |
|------|------|----------|
| `bucket_a_ratio` | A 桶 / (A + B) | < 7日中位数的 70% → WARN |

#### 2. Linkability Coverage
检测 expected 占比下降（把 ERROR 样本标为 not_applicable）。

| 指标 | 定义 | 告警规则 |
|------|------|----------|
| `expected_ratio` | expected / total | < 70% → WARN |
| `expected_ratio` | expected / total | < 7日中位数的 85% → WARN |

### 历史基线
- 加载 7 日历史数据
- 使用滚动中位数作为基线
- 支持相对基线告警

### 热启动期处理（v1.2.7）

**问题**：基线天数 < 7 时，漂移规则会很敏感或没意义。

**解决方案**：
1. `baseline_days < 7` → 漂移告警降级为 `WARN_SOFT`，不进 strict fail
2. 报告添加 `baseline_warmup` 字段
3. md 摘要显示热启动状态

### 绝对下限保护（v1.2.7）

**问题**：分母接近 0 时，阈值会过低导致检测失效。

**解决方案**：
```python
# Bucket A 占比漂移阈值
threshold = max(0.70 * median, 0.10)  # 绝对下限 10%

# Expected 占比漂移阈值  
threshold = max(0.85 * median, 0.50)  # 绝对下限 50%
```

### 漂移告警解释字段（v1.2.7）

每个漂移告警包含：
- `value`: 当前值
- `baseline`: 7 日中位数
- `threshold_applied`: 实际应用的阈值
- `delta_pct`: 变化百分比
- `baseline_days`: 基线天数
- `warmup`: 是否在热启动期

---

## 操作章程（v1.2.8）

### strict 模式定义（强制执行）

**告警级别与 fail 行为**：

| 级别 | strict=true | strict=false | 说明 |
|------|-------------|--------------|------|
| ERROR | **fail** | **fail** | 工程质量问题，永远 fail |
| WARN | fail | 不 fail | 业务问题，由 strict 决定 |
| WARN_SOFT | 不 fail | 不 fail | 热启动期/低样本，永远不 fail |
| INFO | 不 fail | 不 fail | 提示信息 |

**修改 strict 行为必须**：
1. 更新 MAINTENANCE.md
2. 更新 expected 快照
3. 更新测试用例

### baseline 来源审计（强制执行）

**规则**：
- baseline 只能来自同一 `config_hash` 下的日报序列
- 跨 `config_hash` 时必须触发 `BASELINE_RESET`

**实现**：
1. 检查历史记录的 `config_hash` 是否一致
2. 不一致 → 标记 `baseline_reset: true`，重新进入 warmup
3. 报告显示 `config_hash_match: false`

**目的**：防止口径变化后的历史数据污染新基线。

**示例**：
```json
{
  "config_hash": "b9681d0f",
  "baseline_config_hash": "b9681d0f",
  "config_hash_match": true,
  "baseline_reset": false
}
```

```json
{
  "config_hash": "c1234567",
  "baseline_config_hash": "b9681d0f", 
  "config_hash_match": false,
  "baseline_reset": true,
  "baseline_warmup": true
}
```
