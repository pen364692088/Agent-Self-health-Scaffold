# Memory Conflict Boundary

## 三层边界定义

Memory Kernel 采用严格的分层边界，任何冲突按优先级裁决：

```
Truth Memory > Knowledge Memory > Retrieval Memory
```

## Truth Memory（真相层）

### 职责
- ledger 事件
- runtime state 运行状态
- recovery state 恢复状态
- checkpoints 检查点
- execution truth 执行真相
- transcript rebuild truth 重建真相

### 边界规则
1. **只作为 authority source** - 不允许被 recall 结果反向覆盖
2. **不允许向量检索结果直接改写** - 保持原始真实性
3. **精确引用优先** - 不允许总结后冒充原文

### 冲突裁决
- 与 Knowledge 冲突时：Truth 优先
- 与 Retrieval 冲突时：Truth 优先
- 任何情况下不可被覆盖

## Knowledge Memory（知识层）

### 职责
- 稳定规则
- 用户长期偏好
- 决策结论
- 项目约束
- 可复用经验
- trust-anchor 信任锚点
- 高价值 notes / decisions / status

### 边界规则
1. **可结构化** - 支持导出和审计
2. **可升级成检索对象** - 但不可降级为 Retrieval
3. **需要确认后晋升** - 自动捕获只能进入 pending 状态

### 冲突裁决
- 与 Truth 冲突时：Truth 优先
- 与 Retrieval 冲突时：Knowledge 优先

## Retrieval Memory（召回层）

### 职责
- keyword search 关键词搜索
- semantic search 语义搜索
- hybrid rank 混合排序
- scope filter 范围过滤
- recall plan 召回计划
- capture plan 捕获计划
- mirror/export 镜像导出
- observability 可观测性

### 边界规则
1. **只负责"何时取回什么"** - 不直接成为 authority
2. **失败时必须 fail-open** - 不影响主系统运行
3. **必须有 trace** - 可解释召回原因

### 冲突裁决
- 与任何层冲突时：服从上层
- 自身冲突时：按 relevance + authority 双排序

## 跨层冲突处理

### 冲突检测
```python
def detect_conflict(record_a, record_b):
    if record_a.source_path == record_b.source_path:
        if record_a.authority_level != record_b.authority_level:
            return resolve_by_authority(record_a, record_b)
    return None

def resolve_by_authority(record_a, record_b):
    priority = {"truth": 3, "knowledge": 2, "retrieval": 1}
    if priority[record_a.authority_level] > priority[record_b.authority_level]:
        return record_a
    return record_b
```

### 冲突日志
所有冲突必须记录到 `observability/memory/conflict_log.jsonl`：
```json
{
  "timestamp": "ISO8601",
  "record_a_id": "...",
  "record_b_id": "...",
  "conflict_type": "content_mismatch | authority_clash | source_overlap",
  "resolution": "record_a_wins | record_b_wins | merged",
  "reason": "..."
}
```

## 禁止事项

1. **禁止 Retrieval 冒充 Truth** - 任何召回结果不能声称是真相
2. **禁止自动晋升** - Knowledge 必须经过确认才能晋升
3. **禁止跨层覆盖** - 上层不能被下层覆盖
4. **禁止无 trace 召回** - 所有召回必须有可解释原因

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-03-15 | 初始边界定义 |
