# Memory Mapping Rules

## 映射原则

1. **先映射，再整合** - 不删除现有文件
2. **先桥接，再替换** - 新旧系统并存
3. **先 shadow，再 main** - 新功能先观察
4. **未完成映射，不得删旧链** - 保护现有资产

## Truth 层映射规则

### ledger → MemoryRecord

```python
def map_ledger_to_memory(ledger_path: str) -> MemoryRecord:
    return MemoryRecord(
        id=generate_id_from_path(ledger_path),
        source_kind=MemorySourceKind.LEDGER,
        authority_level="truth",
        source_path=ledger_path,
        retrieval_eligibility=False,  # Truth 不走自由召回
        retention=RetentionPolicy(ttl_days=None)  # 永久保留
    )
```

### task_state → MemoryRecord

```python
def map_task_state_to_memory(state_path: str) -> MemoryRecord:
    return MemoryRecord(
        id=generate_id_from_path(state_path),
        source_kind=MemorySourceKind.TASK_STATE,
        authority_level="truth",
        source_path=state_path,
        retrieval_eligibility=False,
        retention=RetentionPolicy(ttl_days=None)
    )
```

### checkpoints → MemoryRecord

```python
def map_checkpoint_to_memory(checkpoint_path: str) -> MemoryRecord:
    return MemoryRecord(
        id=generate_id_from_path(checkpoint_path),
        source_kind=MemorySourceKind.CHECKPOINT,
        authority_level="truth",
        source_path=checkpoint_path,
        retrieval_eligibility=False,
        retention=RetentionPolicy(ttl_days=None)
    )
```

## Knowledge 层映射规则

### 用户偏好 (USER.md, preferences)

```python
def map_user_preference_to_memory(pref_path: str) -> MemoryRecord:
    return MemoryRecord(
        id=generate_id_from_path(pref_path),
        source_kind=MemorySourceKind.USER_PREFERENCE,
        authority_level="knowledge",
        source_path=pref_path,
        retrieval_eligibility=True,
        retention=RetentionPolicy(ttl_days=None),
        tags=["user_preference", "stable"]
    )
```

### 项目规则 (POLICIES/, config/)

```python
def map_project_rule_to_memory(rule_path: str) -> MemoryRecord:
    return MemoryRecord(
        id=generate_id_from_path(rule_path),
        source_kind=MemorySourceKind.PROJECT_RULE,
        authority_level="knowledge",
        source_path=rule_path,
        retrieval_eligibility=True,
        retention=RetentionPolicy(ttl_days=None),
        tags=["project_rule", "config"]
    )
```

### 决策记录 (DECISIONS.md, decisions/)

```python
def map_decision_to_memory(decision_path: str) -> MemoryRecord:
    return MemoryRecord(
        id=generate_id_from_path(decision_path),
        source_kind=MemorySourceKind.DECISION,
        authority_level="knowledge",
        source_path=decision_path,
        retrieval_eligibility=True,
        retention=RetentionPolicy(ttl_days=None),
        tags=["decision"]
    )
```

### 信任锚点 (trust-anchor/)

```python
def map_trust_anchor_to_memory(anchor_path: str) -> MemoryRecord:
    return MemoryRecord(
        id=generate_id_from_path(anchor_path),
        source_kind=MemorySourceKind.TRUST_ANCHOR,
        authority_level="knowledge",
        source_path=anchor_path,
        retrieval_eligibility=True,
        importance=1.0,  # 最高重要性
        retention=RetentionPolicy(ttl_days=None),
        tags=["trust_anchor", "critical"]
    )
```

## Retrieval 层映射规则

### 日常笔记 (memory/*.md)

```python
def map_daily_note_to_memory(note_path: str) -> MemoryRecord:
    # 解析文件名获取日期
    date_str = extract_date_from_filename(note_path)
    age_days = calculate_age(date_str)
    
    return MemoryRecord(
        id=generate_id_from_path(note_path),
        source_kind=MemorySourceKind.DAILY_NOTE,
        authority_level="retrieval",
        source_path=note_path,
        retrieval_eligibility=True,
        retention=RetentionPolicy(
            ttl_days=365,
            hot_tier_days=30,
            warm_tier_days=90
        ),
        tags=["daily_note", date_str]
    )
```

### 会话日志

```python
def map_session_log_to_memory(log_path: str) -> MemoryRecord:
    return MemoryRecord(
        id=generate_id_from_path(log_path),
        source_kind=MemorySourceKind.SESSION_LOG,
        authority_level="retrieval",
        source_path=log_path,
        retrieval_eligibility=True,
        retention=RetentionPolicy(ttl_days=90),
        tags=["session_log"]
    )
```

## 分层判断规则

### HOT / WARM / COLD 判断

```python
def determine_tier(record: MemoryRecord) -> str:
    age_days = calculate_age(record.created_at)
    
    if age_days <= record.retention.hot_tier_days:
        return "HOT"
    elif age_days <= record.retention.warm_tier_days:
        return "WARM"
    else:
        return "COLD"
```

### 是否可召回判断

```python
def determine_retrieval_eligibility(record: MemoryRecord) -> bool:
    # Truth 层默认不可召回
    if record.authority_level == "truth":
        return False
    
    # Knowledge 层默认可召回
    if record.authority_level == "knowledge":
        return True
    
    # Retrieval 层检查保留策略
    if record.authority_level == "retrieval":
        age_days = calculate_age(record.created_at)
        if record.retention.ttl_days and age_days > record.retention.ttl_days:
            return False
        return True
    
    return False
```

## 映射执行流程

```
1. 扫描文件系统
   - memory/
   - checkpoints/
   - trust-anchor/
   - config/
   - POLICIES/

2. 识别文件类型
   - 扩展名匹配
   - 路径模式匹配
   - 内容特征匹配

3. 分类到三层
   - Truth: ledger, task_state, checkpoints
   - Knowledge: preferences, rules, decisions, anchors
   - Retrieval: notes, logs, docs

4. 生成 MemoryRecord
   - 填充必需字段
   - 设置保留策略
   - 计算重要性

5. 验证记录完整性
   - 必需字段检查
   - 权威级别约束检查

6. 输出映射报告
   - MEMORY_ASSET_MAP.json
```

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-03-15 | 初始映射规则 |
