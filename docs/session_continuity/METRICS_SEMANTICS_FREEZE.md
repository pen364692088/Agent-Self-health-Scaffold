# Session Continuity v1.1.1a 度量语义冻结说明

版本：v1.1.1a 
适用范围：Session Continuity 观测层 / 事件层 / 日报与观察期统计 
生效日期：2026-03-07 
状态：FROZEN 
关联运行时基线：Session Continuity v1.1.1 STABLE

---

## 一、目的

本说明用于冻结 Session Continuity v1.1.1a 的度量语义，明确：

1. 哪些指标是 Source of Truth
2. 事件如何唯一标识
3. Raw 与 Unique 指标分别表示什么
4. 观察期目标应映射到哪些指标
5. 哪些版本数据可以比较，哪些不能混算

本文件冻结的是 **观测与统计口径**，不是运行时核心逻辑。

---

## 二、版本定位

### 运行时版本
- Session Continuity v1.1.1
- 状态：STABLE
- 作用：恢复、冲突裁决、WAL、并发保护、handoff、pre-reply guard 等核心连续性逻辑

### 度量语义版本
- Session Continuity Metrics Semantics v1.1.1a
- 状态：FROZEN
- 作用：统一事件身份、去重规则、Raw/Unique 口径、日报与观察期指标解释

### 结论
- **v1.1.1 = runtime baseline**
- **v1.1.1a = observability semantics patch**

v1.1.1a 不改变核心连续性行为，只修正统计口径与事件身份语义。

---

## 三、冻结范围

本次冻结包含：

1. 事件唯一身份规则
2. 去重键定义
3. Raw Metrics 定义
4. Unique Metrics 定义
5. 观察期目标指标映射
6. 报表解释规范
7. 跨版本比较边界

本次冻结不包含：

1. recovery / WAL / conflict resolution 的运行时逻辑
2. 新事件类型扩展
3. 新状态文件引入
4. 新 rollout 策略

---

## 四、Source of Truth

### 1. 真相源
Session Continuity 的度量真相源为：

- append-only 事件日志

推荐路径：
- `state/session_continuity_events.jsonl`

### 2. 原则
- 所有计数、日报、观察期统计必须从事件日志聚合产生
- 分散的裸 count 文件不得作为最终真相源
- 日报、摘要、看板都是派生视图，不是 Source of Truth

### 3. 要求
每条事件至少应包含：
- `ts`
- `event_type`
- `session_id`
- `source_tool`
- `dedupe_key`
- `meta`
- `metric_semantics_version`

建议额外包含：
- `agent_id`
- `task_id`
- `event_schema_version`

---

## 五、事件身份冻结规则

本节冻结 v1.1.1a 的事件去重语义。

### 1. recovery_success
#### 含义
一次成功完成的恢复事件。

#### 去重键
- `recovery_id`

#### 解释
- 允许同一 session 在不同恢复实例中被多次恢复
- 不再使用 `session:date`
- 目标：避免多次恢复被低估

---

### 2. handoff_created
#### 含义
一次成功创建的 handoff 实体。

#### 去重键
- `handoff_id`

#### 解释
- 允许同一 session 在同一天内创建多个 handoff
- 不再使用 `session:date`
- 目标：正确统计真实 handoff 次数

---

### 3. conflict_resolution_applied
#### 含义
一次确定的冲突裁决案例。

#### 去重键
- `conflict_id`

#### 解释
- 同一个 conflict 的重试、重复执行、重复写摘要不应重复计数
- 不再使用 `timestamp`
- 目标：避免重试导致虚高

---

### 4. high_context_trigger
#### 含义
某 session 进入某个上下文压力阈值带时触发的高上下文事件。

#### 去重键
- `session_id:threshold_band`

#### 解释
- 同一 session 可对不同 band 各计一次
- 同一 band 内重复检测不重复累计
- 目标：防止长时间停留高压区导致无限累加，同时支持多阈值观察

---

## 六、Threshold Band 冻结定义

为了保证 high_context 指标可横向比较，threshold band 定义冻结如下：

### 1. `60_80`
- 表示 context ratio > 60% 且 <= 80%

### 2. `80_plus`
- 表示 context ratio > 80%

### 3. 规则
- band 定义在 v1.1.1a 下冻结，不得随意修改
- 若未来引入新 band，必须提升语义版本
- 报表必须标明使用的 metric semantics version

---

## 七、Raw / Unique 双层指标语义

v1.1.1a 冻结采用双层视图：

```
Event Log (Source of Truth)
        │
        ├── Raw Metrics (事件次数)
        │
        └── Unique Metrics (覆盖面)
```

### 1. Raw Metrics 定义
反映事件发生次数，用于衡量系统活动量。

| 指标名 | 含义 | 计算方式 |
|--------|------|----------|
| raw_recovery_success_count | 成功恢复事件数 | count(events where event_type == "recovery_success") |
| raw_handoff_created_count | Handoff 创建事件数 | count(events where event_type == "handoff_created") |
| raw_high_context_trigger_count | 高 context 触发数 | count(events where event_type == "high_context_trigger") |
| raw_interruption_recovery_count | 中断恢复事件数 | count(events where event_type == "interruption_recovery") |
| raw_recovery_uncertainty_count | 不确定恢复事件数 | count(events where event_type == "recovery_uncertainty") |
| raw_conflict_resolution_count | 冲突裁决事件数 | count(events where event_type == "conflict_resolution_applied") |
| raw_recovery_failure_count | 恢复失败事件数 | count(events where event_type == "recovery_failure") |

### 2. Unique Metrics 定义
反映影响范围，用于衡量覆盖面。

| 指标名 | 含义 | 计算方式 |
|--------|------|----------|
| unique_sessions_recovered_count | 被恢复的唯一 session 数 | count(distinct session_id where event_type == "recovery_success") |
| unique_sessions_with_handoff_count | 有 handoff 的唯一 session 数 | count(distinct session_id where event_type == "handoff_created") |
| unique_sessions_high_context_count | 触发高 context 的唯一 session 数 | count(distinct session_id where event_type == "high_context_trigger") |
| unique_sessions_interruption_recovered_count | 中断恢复的唯一 session 数 | count(distinct session_id where event_type == "interruption_recovery") |
| unique_handoff_ids_count | 唯一 handoff 实体数 | count(distinct handoff_id) |
| unique_conflict_cases_count | 唯一冲突案例数 | count(distinct conflict_id) |

---

## 八、观察期目标指标映射

| 目标 | 推荐指标 | 理由 |
|------|----------|------|
| 10+ 新 session 恢复 | unique_sessions_recovered_count | 看覆盖面 |
| 5+ handoff | raw_handoff_created_count | 看实际次数 |
| 3+ 高 context 触发 | unique_sessions_high_context_count | 看影响范围 |
| 2+ 中断恢复 | raw_interruption_recovery_count | 看事件数 |

---

## 九、跨版本比较边界

### 可比较
- v1.1.1a 之后的事件，可按 v1.1.1a 口径聚合
- 同一口径下不同时段的数据可比较

### 不可混算
- v1.1.1（旧口径）与 v1.1.1a（新口径）的 raw 指标不能直接相加
- 需要根据 `metric_semantics_version` 字段分别聚合

---

## 十、冻结承诺

在 v1.1.1a 有效期内：

1. 不修改已冻结的事件身份定义
2. 不修改 threshold band 定义
3. 不修改 Raw / Unique 计算规则
4. 不修改观察期目标映射

任何变更需提升版本号并发布新的冻结说明。

---

*End of Metrics Semantics Freeze Document*
