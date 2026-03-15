# Memory Asset Map

> M0 产出物：现有资产到 MemoryRecord 的映射计划
> 创建时间: 2026-03-15
> 目标：定义如何将现有 memory/ 文件映射为 MemoryRecord

---

## 1. 映射策略概述

### 1.1 核心原则

1. **只做映射，不做迁移**
   - 不删除现有 memory/ 文件
   - 不修改现有文件内容
   - 映射是只读操作

2. **不影响现有系统运行**
   - 映射过程不阻塞现有记忆系统
   - 映射结果可独立使用

3. **可追溯性**
   - 每个 MemoryRecord 记录来源文件
   - 保留原始元数据

### 1.2 映射流程

```
memory/ 目录文件
      ↓
  SourceMapper.scan_directory()
      ↓
  SourceMapper.map_file_to_record()
      ↓
  MemoryRecord 对象
      ↓
  TruthKnowledgeRetrievalClassifier.classify()
      ↓
  带分类的 MemoryRecord
```

---

## 2. 文件类型映射规则

### 2.1 Markdown 文件 (.md)

| 文件模式 | MemorySourceKind | TruthKnowledgeRetrieval | 说明 |
|---------|------------------|------------------------|------|
| `YYYY-MM-DD.md` | SESSION_LOG | KNOWLEDGE | 按日期命名的会话日志 |
| `YYYY-MM-DD-HHMM.md` | SESSION_LOG | KNOWLEDGE | 带时间的会话日志 |
| `YYYY-MM-DD-*-fix.md` | TECHNICAL_NOTE | KNOWLEDGE | 技术修复笔记 |
| `YYYY-MM-DD-*-debug.md` | TECHNICAL_NOTE | KNOWLEDGE | 调试笔记 |
| `*policy*.md` | POLICY | KNOWLEDGE | 策略文档 |
| `*POLICY*.md` | POLICY | KNOWLEDGE | 策略文档 |
| `SESSION-STATE.md` | STATE | TRUTH | 会话状态 |
| `working-buffer.md` | STATE | TRUTH | 工作缓冲区 |
| `EVENT_SCHEMA.md` | SCHEMA | TRUTH | 事件 Schema |
| `ENTRY_TEMPLATE.md` | TEMPLATE | TRUTH | 条目模板 |
| `MAINTENANCE.md` | RULE | KNOWLEDGE | 维护规则 |
| `context-management-policy.md` | POLICY | KNOWLEDGE | 上下文管理策略 |

### 2.2 JSON 文件 (.json)

| 文件模式 | MemorySourceKind | TruthKnowledgeRetrieval | 说明 |
|---------|------------------|------------------------|------|
| `sweeper_stats*.json` | METRICS | RETRIEVAL | 清扫统计 |
| `retrieval_regression.json` | METRICS | RETRIEVAL | 检索回归测试 |
| `expected_alerts.json` | METRICS | RETRIEVAL | 预期告警 |
| `*.config.json` | CONFIG | TRUTH | 配置文件 |
| `.bootstrap_state.json` | STATE | TRUTH | 启动状态 |

### 2.3 JSONL 文件 (.jsonl)

| 文件模式 | MemorySourceKind | TruthKnowledgeRetrieval | 说明 |
|---------|------------------|------------------------|------|
| `events.log` | RETRIEVAL_EVENT | RETRIEVAL | 检索事件 |
| `events_drift.jsonl` | DRIFT_EVENT | RETRIEVAL | 漂移事件 |
| `evolution/successes.jsonl` | EVOLUTION_EVENT | RETRIEVAL | 成功记录 |
| `evolution/prevention_rules.jsonl` | RULE | KNOWLEDGE | 预防规则 |

### 2.4 其他文件

| 文件模式 | MemorySourceKind | TruthKnowledgeRetrieval | 说明 |
|---------|------------------|------------------------|------|
| `*.log` | RETRIEVAL_EVENT | RETRIEVAL | 日志文件 |

---

## 3. 作用域推断规则

### 3.1 项目作用域 (PROJECTS)

**触发条件**：
- 文件路径包含项目名（openemotion, emotiond, openclaw-core 等）
- 文件内容包含项目特定关键词

**推断逻辑**：
```python
project_indicators = {
    "openemotion": "openemotion",
    "emotiond": "emotiond",
    "openclaw": "openclaw",
    "agent-self-health": "agent_self_health",
}
```

### 3.2 领域作用域 (DOMAINS)

**触发条件**：
- 文件路径包含领域关键词（infra, security, frontend 等）

**推断逻辑**：
```python
domain_indicators = {
    "infra": "infra",
    "security": "security",
    "frontend": "frontend",
    "backend": "backend",
    "telegram": "telegram",
}
```

### 3.3 全局作用域 (GLOBAL)

**触发条件**：
- 不符合项目或领域特征
- 通用规则、模板、Schema

---

## 4. 内容类型推断规则

### 4.1 RULE（规则）

**触发条件**：
- 内容包含：must, should, required, 禁止, 强制
- 文件名包含：policy, rule, 规范

**特征**：
- 确定性指导原则
- 通常有明确的适用条件

### 4.2 FACT（事实）

**触发条件**：
- 内容包含：version, config, schema, definition
- 文件是状态、配置、Schema 类型

**特征**：
- 可验证
- 不依赖上下文
- 不易变

### 4.3 PREFERENCE（偏好）

**触发条件**：
- 内容包含：prefer, like, favorite, 习惯, 偏好

**特征**：
- 主观性
- 可被用户纠正

### 4.4 REFLECTION（反思）

**触发条件**：
- 默认类型
- 会话日志、技术笔记

**特征**：
- 经验总结
- 问题回顾

---

## 5. Truth/Knowledge/Retrieval 分层规则

### 5.1 TRUTH 层

**定义**：确定性事实，结构化，不易变

**来源类型**：
- STATE（状态）
- CONFIG（配置）
- SCHEMA（Schema）
- TEMPLATE（模板）
- METRICS（统计）

**特征**：
- 可作为系统输入
- 不依赖上下文
- 有明确结构

### 5.2 KNOWLEDGE 层

**定义**：规则、决策、偏好，可能有冲突

**来源类型**：
- RULE（规则）
- POLICY（策略）
- DECISION_LOG（决策日志）
- PREFERENCE（偏好）
- SESSION_LOG（会话日志）
- TECHNICAL_NOTE（技术笔记）

**特征**：
- 需要置信度评估
- 可能过时或被替代
- 可被纠正或更新

### 5.3 RETRIEVAL 层

**定义**：检索事件、统计数据

**来源类型**：
- RETRIEVAL_EVENT（检索事件）
- DRIFT_EVENT（漂移事件）
- EVOLUTION_EVENT（进化事件）

**特征**：
- 动态更新
- 用于评估检索质量
- 支持回归测试

---

## 6. 分层推断规则

### 6.1 HOT 层

**触发条件**：
- `pinned=true`
- `score >= 7.0`
- 近期高频使用

### 6.2 WARM 层

**触发条件**：
- `3.0 <= score < 7.0`
- 近期有使用

### 6.3 COLD 层

**触发条件**：
- `score < 3.0`
- 长期未使用

### 6.4 ARCHIVED 层

**触发条件**：
- 已归档的条目
- 超过保留期限

---

## 7. 映射示例

### 7.1 会话日志映射

**源文件**：`memory/2026-03-11.md`

**映射结果**：
```python
MemoryRecord(
    id="mem_20260311_001",
    scope=MemoryScope.GLOBAL,
    source_kind=MemorySourceKind.SESSION_LOG,
    content_type=MemoryContentType.REFLECTION,
    tkr_layer=TruthKnowledgeRetrieval.KNOWLEDGE,
    title="Session Log 2026-03-11",
    content="...",
    source_file="2026-03-11.md",
    tier=MemoryTier.WARM,
)
```

### 7.2 Schema 文件映射

**源文件**：`memory/EVENT_SCHEMA.md`

**映射结果**：
```python
MemoryRecord(
    id="mem_20260301_001",
    scope=MemoryScope.GLOBAL,
    source_kind=MemorySourceKind.SCHEMA,
    content_type=MemoryContentType.FACT,
    tkr_layer=TruthKnowledgeRetrieval.TRUTH,
    title="Memory Event Schema v1.1",
    content="...",
    source_file="EVENT_SCHEMA.md",
    tier=MemoryTier.HOT,
    pinned=True,
)
```

### 7.3 策略文档映射

**源文件**：`memory/MAINTENANCE.md`

**映射结果**：
```python
MemoryRecord(
    id="mem_20260303_001",
    scope=MemoryScope.GLOBAL,
    source_kind=MemorySourceKind.RULE,
    content_type=MemoryContentType.RULE,
    tkr_layer=TruthKnowledgeRetrieval.KNOWLEDGE,
    title="Memory Retrieval Hardening - Maintenance Guide",
    content="...",
    source_file="MAINTENANCE.md",
    tier=MemoryTier.HOT,
    confidence=0.95,
    importance=0.9,
)
```

### 7.4 事件日志映射

**源文件**：`memory/events.log`

**映射结果**：
```python
MemoryRecord(
    id="mem_20260309_001",
    scope=MemoryScope.GLOBAL,
    source_kind=MemorySourceKind.RETRIEVAL_EVENT,
    content_type=MemoryContentType.FACT,
    tkr_layer=TruthKnowledgeRetrieval.RETRIEVAL,
    title="Retrieval Events Log",
    content="...",
    source_file="events.log",
    tier=MemoryTier.WARM,
)
```

---

## 8. ID 生成规则

### 8.1 格式

```
mem_YYYYMMDD_XXX
```

- `mem_`：固定前缀
- `YYYYMMDD`：文件创建/修改日期
- `XXX`：三位序号（001-999）

### 8.2 生成逻辑

```python
def _generate_id(self, filename: str, mtime: datetime) -> str:
    self._id_counter += 1
    date_part = mtime.strftime("%Y%m%d")
    seq_part = f"{self._id_counter:03d}"
    return f"mem_{date_part}_{seq_part}"
```

---

## 9. 元数据提取

### 9.1 从 YAML 头提取

**支持的 YAML 字段**：
- confidence
- importance
- pinned
- tier
- status
- use_count
- correction_count

### 9.2 从内容推断

**confidence**：
- Schema/Template 文件：0.95
- Policy/Rule 文件：0.85
- Session Log：0.5

**importance**：
- 包含"重要"关键词：0.9
- 维护相关：0.8
- 其他：0.5

---

## 10. 使用指南

### 10.1 执行映射

```bash
cd /home/moonlight/Project/Github/MyProject/Agent-Self-health-Scaffold

# 运行映射器
python -m core.memory.source_mapper

# 输出报告
# docs/memory/MEMORY_ASSET_MAP.json
```

### 10.2 执行分类

```bash
# 运行分类器
python -m core.memory.truth_classifier

# 输出报告
# docs/memory/TKR_CLASSIFICATION.json
```

### 10.3 编程接口

```python
from core.memory.source_mapper import SourceMapper
from core.memory.truth_classifier import TruthKnowledgeRetrievalClassifier

# 映射文件
mapper = SourceMapper("memory/")
records = mapper.map_all_files()

# 分类
classifier = TruthKnowledgeRetrievalClassifier()
for record in records:
    result = classifier.classify(record)
    print(f"{record.id}: {result.layer.value} (confidence: {result.confidence:.2f})")
```

---

## 11. 后续计划

### 11.1 M3: 检索集成

- 与 openviking/lancedb 集成
- 实现语义检索
- 支持向量索引

### 11.2 M4: 生命周期管理

- 实现 RetentionPolicy
- 实现自动过期清理
- 实现状态转换

### 11.3 M5: 冲突检测

- 实现 ConflictResolutionPolicy
- 检测重复/冲突条目
- 自动解决或标记

---

## 附录

### A. 相关文件

- `MEMORY_CAPABILITY_AUDIT.md` - 全量盘点
- `contract/memory/types.py` - 类型定义
- `contract/memory/policies.py` - 策略定义
- `core/memory/source_mapper.py` - 映射实现
- `core/memory/truth_classifier.py` - 分类实现
- `tests/memory/test_source_mapper.py` - 测试

### B. 参考

- `memory/ENTRY_TEMPLATE.md` - 条目模板
- `memory/EVENT_SCHEMA.md` - 事件 Schema
- `memory/MAINTENANCE.md` - 维护指南
