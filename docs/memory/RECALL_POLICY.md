# Recall Policy

**Version**: 1.0.0
**Created**: 2026-03-15

---

## Overview

Memory Kernel 的召回策略定义了如何从记忆库中检索信息，确保召回结果可靠、可追溯。

---

## Core Principles

### 1. Default from Approved Only

默认只从 approved 记忆召回，不包含未审核的候选。

### 2. Candidate Shadow Visibility

候选记录仅在 shadow/debug 模式下可见，不影响生产召回。

### 3. Top-K Small Traffic

使用 top-k 限制召回数量，避免过载。

### 4. Fail-Open

召回失败时主链继续执行，不阻塞业务流程。

---

## Recall Modes

| Mode | Description | Candidate Visibility | Use Case |
|------|-------------|---------------------|----------|
| production | 生产模式 | Hidden | 正常业务 |
| shadow | 影子模式 | Visible (tagged) | 灰度测试 |
| debug | 调试模式 | Visible | 开发调试 |

---

## Recall Flow

```
Query → RecallEngine → Filter(approved only) → Top-K → Trace Output
                ↓
            Fail-Open → Continue on error
```

### Stage 1: Search Approved

从 approved 记录中搜索，使用 M3 统一查询服务。

### Stage 2: Search Candidates (Optional)

在 shadow/debug 模式下，从 candidate 记录中搜索。

---

## Truth Record Handling

Truth 层记录的特殊处理规则：

### Exact Quote Only

Truth 记录只允许精确引用原文，不允许摘要或改写。

```python
@dataclass
class TruthQuote:
    record_id: str
    exact_quote: str  # 精确引用原文
    source_ref: Dict[str, Any]
    verified: bool
```

### Verification

Truth 引用需要验证：

```python
quote.verify(original_content)  # 检查是否在原文中
```

### No Summary

不允许使用摘要代替原文：

- ❌ "配置文件在 ~/.openclaw 下"
- ✅ "所有配置文件位于 ~/.openclaw/ 目录"

---

## Fail-Open Behavior

当召回失败时：

1. 记录错误日志
2. 输出 trace 信息
3. 返回空结果
4. 主链继续执行（不抛异常）

### Example

```python
try:
    result = engine.recall(query)
except Exception as e:
    # Fail-open: 不抛异常，返回空结果
    result = RecallResult(records=[], errors=[str(e)])
```

---

## Trace Information

### RecallTrace

```python
@dataclass
class RecallTrace:
    query: str
    mode: str
    total_scanned: int
    approved_count: int
    candidate_count: int
    filtered_count: int
    top_k: int
    returned_count: int
    timing_ms: float
    errors: List[str]
    warnings: List[str]
    stages: List[TraceStage]
    approved_records: List[str]
    candidate_records: List[str]
    truth_quotes: List[Dict]
```

### TraceStage

```python
@dataclass
class TraceStage:
    name: str
    input_count: int
    output_count: int
    timing_ms: float
    details: Dict[str, Any]
```

---

## API Reference

### RecallEngine

```python
engine = RecallEngine(
    approved_records=approved_list,
    candidate_records=candidate_list,
    config=RecallConfig(mode="production"),
)

# 基本召回
result = engine.recall(query="memory kernel")

# 带 Truth 引用的召回
result = engine.recall_with_truth_quote(query="truth layer")

# 切换模式
engine.set_mode("shadow")
```

### RecallResult

```python
result = engine.recall(query)

# 访问结果
for record in result.records:
    print(record.title)

# 访问追踪
if result.trace:
    print(result.trace.to_dict())

# 访问 Truth 引用
for quote in result.truth_quotes:
    print(quote.exact_quote)
```

---

## Configuration

### RecallConfig

| Parameter | Default | Description |
|-----------|---------|-------------|
| mode | production | 召回模式 |
| top_k | 10 | top-k 召回数量 |
| include_candidates | False | 是否包含候选 |
| fail_open | True | 失败时是否继续 |
| enable_trace | True | 是否启用追踪 |

---

## Metrics

| Metric | Description |
|--------|-------------|
| total_scanned | 扫描总数 |
| approved_count | approved 记录数 |
| candidate_count | candidate 记录数 |
| filtered_count | 过滤后数量 |
| returned_count | 返回数量 |
| timing_ms | 耗时（毫秒）|

---

## Best Practices

1. **Use production mode by default** - 默认使用生产模式
2. **Enable trace for debugging** - 调试时启用追踪
3. **Verify Truth quotes** - 验证 Truth 引用
4. **Handle fail-open** - 处理 fail-open 场景
5. **Limit top-k** - 限制 top-k 避免过载

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-03-15 | Initial version |
