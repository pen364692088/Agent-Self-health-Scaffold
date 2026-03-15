# Memory Capability Audit

> M0 产出物：全量盘点现有记忆资产
> 创建时间: 2026-03-15
> 目标：为 Memory Kernel 统一整合提供基线

---

## 1. memory/ 目录资产盘点

### 1.1 文件统计

| 类型 | 数量 | 说明 |
|------|------|------|
| .md 文件 | 170 | 会话日志、决策记录、技术笔记 |
| .json 文件 | 13 | 统计、缓存、配置 |
| .jsonl 文件 | 5 | 事件日志、进化记录 |
| 其他 | 3 | events.log 等 |

### 1.2 内容分类

#### A. 会话日志 (Session Logs)
**特征**: 按日期命名 (YYYY-MM-DD.md 或 YYYY-MM-DD-HHMM.md)
**数量**: ~140 个
**示例**:
- 2026-02-22.md
- 2026-03-11.md
- 2026-03-06-1423.md

**内容模式**:
- 任务执行记录
- 决策过程
- 遇到的问题和解决方案
- 提交记录

#### B. 决策/策略文档 (Policy/Decision Documents)
**特征**: 描述性命名，定义规则或流程
**数量**: ~20 个
**示例**:
- context-management-policy.md
- manager-callback-policy-2026-02-21.md
- SESSION-STATE.md

**内容模式**:
- 系统规则定义
- 协议规范
- 操作流程

#### C. 技术笔记 (Technical Notes)
**特征**: 特定主题的技术实现记录
**数量**: ~10 个
**示例**:
- 2026-03-04-rlock-deadlock-fix.md
- 2026-03-06-trust-anchor.md
- 2026-03-05-tool-gate-check.md

**内容模式**:
- 问题诊断
- 修复方案
- 验证结果

#### D. 模板与元文档 (Templates & Meta-Documents)
**特征**: 定义格式、流程、维护指南
**数量**: 5 个
**示例**:
- ENTRY_TEMPLATE.md - 记忆条目模板
- EVENT_SCHEMA.md - 事件 schema 定义
- MAINTENANCE.md - 维护指南

#### E. 状态文件 (State Files)
**特征**: 运行时状态，频繁更新
**数量**: 3 个
**示例**:
- SESSION-STATE.md
- working-buffer.md
- .bootstrap_state.json

#### F. 事件日志 (Event Logs)
**特征**: JSONL 格式，记录系统事件
**数量**: 5 个
**示例**:
- events.log - 检索/召回事件
- events_drift.jsonl - 漂移事件
- evolution/prevention_rules.jsonl - 预防规则
- evolution/successes.jsonl - 成功记录

#### G. 统计与缓存 (Statistics & Cache)
**特征**: JSON 格式，维护统计数据
**数量**: 13 个
**示例**:
- sweeper_stats.json
- .dedup_cache.json
- retrieval_regression.json
- expected_alerts.json

---

## 2. 现有记忆机制盘点

### 2.1 记忆条目模板 (ENTRY_TEMPLATE.md)

**元数据字段**:
```yaml
id: mem_YYYYMMDD_XXX
type: RULE | FACT | PREFERENCE | REFLECTION
scope: global | projects/{name} | domains/{name}
tier: HOT | WARM | COLD
created_at: YYYY-MM-DD
last_used: YYYY-MM-DD
use_count: N
correction_count: N
confidence: 0.0-1.0
importance: 0.0-1.0
pinned: false
conflict_penalty: 0.0
sources:
  - session: YYYY-MM-DD
    evidence: "..."
    task_id: "..."
```

**条目类型**:
- RULE: 规则（如编码规范、流程规则）
- FACT: 事实（如配置、环境信息）
- PREFERENCE: 偏好（如用户习惯）
- REFLECTION: 反思（如经验教训）

**作用域**:
- global: 全局通用
- projects/{name}: 项目专用
- domains/{name}: 领域专用

**分层**:
- HOT: 高频使用，高价值
- WARM: 中等使用
- COLD: 低频或待清理

### 2.2 事件 Schema (EVENT_SCHEMA.md)

**事件类型**:
| 类型 | 触发 | 含义 |
|------|------|------|
| use | 使用记忆条目 | use_count += 1 |
| correction | 用户纠正 | correction_count += 1 |
| conflict | 规则导致错误输出 | conflict_penalty += 0.5 |
| pin | 手动标记高价值 | pinned = true |
| forget | 手动删除 | status = deleted |
| reflection | 自我反思 | 记录但不影响评分 |
| deprecate | 规则弃用 | status = deprecated |
| supersede | 规则替换 | status = superseded |

**评分模型**:
```python
score = (
    2.0 * log(use_count + 1) +
    1.5 * recency_boost(days_ago) +
    3.0 * min(max(importance, 0), 1) -
    2.0 * max(conflict_penalty, 0)
)
```

**状态管理**:
- active: 正常使用
- deprecated: 已弃用
- superseded: 已被替换
- deleted: 已删除

### 2.3 维护流程 (MAINTENANCE.md)

**核心机制**:
1. Golden Fixture 更新流程
2. config_hash 计算规则
3. orphan_recall_rate 拆分定义
4. 场景分桶（A/B 桶）
5. broken_link 豁免项
6. 漂移检测
7. 热启动期处理
8. 操作章程

### 2.4 检索机制 (events.log)

**检索事件格式**:
```json
{
  "event": "retrieval",
  "ts": "ISO8601",
  "query": "...",
  "stage": "pinned | semantic",
  "returned_doc_ids": [],
  "used_doc_ids": [],
  "latency_ms": N
}
```

**召回事件格式**:
```json
{
  "event": "recall",
  "recall_id": "...",
  "query": "...",
  "candidates": [],
  "used": []
}
```

---

## 3. Truth/Knowledge/Retrieval 三层分类

### 3.1 Truth Layer (确定性事实层)

**定义**: 确定性、不易变的事实信息

**现有资产**:
| 文件 | 内容 | Truth 类型 |
|------|------|------------|
| EVENT_SCHEMA.md | 事件 schema 定义 | Schema Truth |
| ENTRY_TEMPLATE.md | 条目模板定义 | Template Truth |
| SESSION-STATE.md | 会话状态 | State Truth |
| .bootstrap_state.json | 启动状态 | State Truth |
| sweeper_stats.json | 清扫统计 | Metrics Truth |

**特征**:
- 结构化
- 可验证
- 不依赖上下文
- 可作为系统输入

### 3.2 Knowledge Layer (知识规则层)

**定义**: 规则、决策、偏好等知识性内容

**现有资产**:
| 文件 | 内容 | Knowledge 类型 |
|------|------|----------------|
| MAINTENANCE.md | 维护规则和流程 | Rule Knowledge |
| context-management-policy.md | 上下文管理策略 | Policy Knowledge |
| manager-callback-policy-*.md | 回调策略 | Policy Knowledge |
| evolution/prevention_rules.jsonl | 预防规则 | Rule Knowledge |
| 2026-03-04-rlock-deadlock-fix.md | 修复方案 | Solution Knowledge |
| 2026-03-06-trust-anchor.md | 技术决策 | Decision Knowledge |

**特征**:
- 有适用范围（scope）
- 可能过时或被替代
- 需要置信度评估
- 可被纠正或更新

**子分类**:
- Rule Knowledge: 编码规范、流程规则
- Policy Knowledge: 策略、配置决策
- Solution Knowledge: 问题解决方案
- Decision Knowledge: 技术决策记录

### 3.3 Retrieval Layer (检索召回层)

**定义**: 记忆的检索、召回、排序机制

**现有资产**:
| 文件 | 内容 | Retrieval 类型 |
|------|------|----------------|
| events.log | 检索/召回事件 | Retrieval Events |
| events_drift.jsonl | 漂移事件 | Drift Events |
| retrieval_regression.json | 回归测试 | Retrieval Metrics |
| expected_alerts.json | 预期告警 | Retrieval Alerts |
| .dedup_cache.json | 去重缓存 | Retrieval Cache |

**特征**:
- 动态更新
- 用于评估检索质量
- 支持回归测试
- 监控系统健康

**核心指标**:
- pinned_hit_rate: 精确匹配命中率
- stage2_usage_rate: 语义召回使用率
- adoption_rate: 采用率
- orphan_recall_rate: 孤立召回率

---

## 4. 现有架构集成点

### 4.1 与 memory.md 的关系

**memory.md 定义**:
- 子代理编排入口 (subtask-orchestrate)
- 记忆检索入口 (session-query, openviking find)
- 硬规则
- 归档策略

**集成方式**:
- memory.md 是记忆系统的 bootstrap/入口文档
- memory/ 目录是实际记忆存储
- ENTRY_TEMPLATE.md 定义条目格式
- EVENT_SCHEMA.md 定义事件格式

### 4.2 与 contracts/ 的关系

**现有 contracts/**:
- BOUNDARIES.md - 边界定义
- LEVELS.md - 级别定义
- SELF_HEALING_CONTRACT.md - 自愈契约

**集成方式**:
- 记忆系统需要遵守自愈契约
- 记忆操作有边界约束
- 记忆层级与系统级别对应

### 4.3 与 core/ 的关系

**现有 core/**:
- canonical_adapter.py
- child_result_collector.py
- consistency_checker.py
- lease_manager.py
- materialized_state_v0.py
- prompt_pilot_runner.py

**集成方式**:
- Memory Kernel 需要在 core/memory/ 下实现
- 与现有核心组件解耦
- 通过 contract/ 定义接口

---

## 5. 遗留问题与改进方向

### 5.1 当前问题

1. **格式不统一**
   - 会话日志格式各异
   - 缺乏统一的 id 分配机制
   - 元数据不一致

2. **检索能力分散**
   - 多种检索入口
   - 缺乏统一的语义索引
   - 回归测试与生产数据分离

3. **生命周期管理缺失**
   - 缺乏统一的过期策略
   - 手动清理风险
   - 状态转换不明确

4. **作用域模糊**
   - global/projects/domains 边界不清
   - 缺乏自动作用域推断
   - 跨作用域冲突处理缺失

### 5.2 Memory Kernel 改进方向

1. **统一数据模型**
   - 定义 MemoryRecord 类型
   - 统一 id 生成规则
   - 标准化元数据字段

2. **统一检索接口**
   - 定义 MemorySourceKind
   - 实现统一的 source_mapper
   - 支持多层检索策略

3. **生命周期策略**
   - 定义 RetentionPolicy
   - 定义 ConflictResolutionPolicy
   - 自动状态转换

4. **分层分类增强**
   - Truth/Knowledge/Retrieval 清晰分层
   - 自动分类器
   - 分层存储策略

---

## 6. 审计结论

### 6.1 资产总览

| 分类 | 数量 | Truth | Knowledge | Retrieval |
|------|------|-------|-----------|-----------|
| 会话日志 | ~140 | - | ✓ | - |
| 决策/策略文档 | ~20 | - | ✓ | - |
| 技术笔记 | ~10 | - | ✓ | - |
| 模板与元文档 | 5 | ✓ | ✓ | - |
| 状态文件 | 3 | ✓ | - | - |
| 事件日志 | 5 | - | - | ✓ |
| 统计与缓存 | 13 | ✓ | - | ✓ |

### 6.2 Memory Kernel 设计建议

1. **保留现有资产**: 不删除现有 memory/ 文件
2. **建立映射层**: 将现有文件映射为 MemoryRecord
3. **实现分类器**: 自动 Truth/Knowledge/Retrieval 分类
4. **统一接口**: 通过 contract/ 定义标准接口

---

## 附录

### A. 完整文件列表

执行 `find memory -type f | sort` 获取完整列表。

### B. 相关文档

- memory.md - 记忆系统 bootstrap
- ENTRY_TEMPLATE.md - 条目模板
- EVENT_SCHEMA.md - 事件 schema
- MAINTENANCE.md - 维护指南

### C. 下一步

参见 `MEMORY_ASSET_MAP.md` - 现有资产到 MemoryRecord 的映射计划。
