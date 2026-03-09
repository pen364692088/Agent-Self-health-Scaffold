# Budget Watcher Specification v1.0

## Overview

Budget Watcher 是 `context-budget-check` 的增强版，提供持续监控、区间判定和趋势分析能力，用于 Auto-Compaction Waterline Control 系统。

---

## Inputs

### Primary Input
- **Ratio**: 当前 context 使用比例 (0.0 ~ 1.0)
  - 来源: `session_status` 内部 API
  - 格式: `Context: X/Yk (Z%)` 解析得出

### Secondary Inputs (Optional)
- **State File**: `active_state.json` 路径
- **History File**: 对话历史 JSONL 路径
- **Max Tokens**: 预算上限 (默认 100000)

---

## Outputs

### Standard Output (Human-Readable)
```
Ratio: 0.75
Zone: normal
Trend: stable
Samples: 42
```

### JSON Output (`--json`)
```json
{
  "timestamp": "2026-03-09T14:30:00Z",
  "ratio": 0.7523,
  "zone": "normal",
  "trend": "stable",
  "thresholds": {
    "warning": 0.80,
    "emergency": 0.90
  },
  "samples_count": 42,
  "session_id": "agent:main:..."
}
```

### Sample Log Entry (`--sample-log`)
```json
{
  "timestamp": "2026-03-09T14:30:00.123Z",
  "ratio": 0.7523,
  "zone": "normal",
  "trend": "stable"
}
```

---

## Zone Classification

### Thresholds (v1.0)
| Zone | Ratio Range | Description |
|------|-------------|-------------|
| **normal** | ratio < 0.80 | 正常运行区，无需干预 |
| **warning** | 0.80 ≤ ratio < 0.90 | 警戒区，准备压缩 |
| **emergency** | ratio ≥ 0.90 | 紧急区，立即压缩 |

### Zone Transitions
```
normal → warning: ratio >= 0.80
warning → normal: ratio < 0.75 (hysteresis)
warning → emergency: ratio >= 0.90
emergency → warning: ratio < 0.85 (hysteresis)
```

---

## Trend Analysis

### Trend Types
| Trend | Description |
|-------|-------------|
| **stable** | 近 N 次采样波动 < 0.02 |
| **rising** | 连续上升，变化率 > 0.01/sample |
| **falling** | 连续下降，变化率 > 0.01/sample |
| **volatile** | 波动 > 0.05 |

### Sample Window
- 默认窗口: 最近 10 次采样
- 最小样本: 3 次（不足则返回 `insufficient_data`）

---

## Relationship with `context-budget-check`

| Feature | context-budget-check | context-budget-watcher |
|---------|---------------------|------------------------|
| 单次检查 | ✅ | ✅ |
| 区间判定 | pressure_level | zone (waterline-aware) |
| 趋势分析 | ❌ | ✅ |
| 持续监控 | ❌ | ✅ (via heartbeat) |
| 采样日志 | ❌ | ✅ |
| 集成目标 | 通用工具 | Auto-Compaction 系统 |

### Reuse Strategy
- 复用 `estimate_tokens()`, `estimate_jsonl_tokens()` 函数
- 复用 JSON 解析逻辑
- watcher 是增强版封装，非替代品

---

## Integration Points

### 1. Heartbeat Integration
```bash
# In heartbeat
context-budget-watcher --sample-log --json
```

- 每次心跳采样一次
- 写入 `ratio_samples.jsonl`
- 返回 zone/trend 供 trigger policy 决策

### 2. Trigger Policy Integration (Phase 2)
```python
# Pseudocode
result = context_budget_watcher()
if result['zone'] == 'emergency':
    trigger_compaction(mode='emergency')
elif result['zone'] == 'warning' and result['trend'] == 'rising':
    trigger_compaction(mode='standard')
```

### 3. CLI Usage
```bash
# 单次检查
context-budget-watcher

# JSON 输出
context-budget-watcher --json

# 写入采样日志
context-budget-watcher --sample-log

# 指定采样文件
context-budget-watcher --sample-log --samples-file custom.jsonl

# 健康检查
context-budget-watcher --health

# 自检
context-budget-watcher --test
```

---

## Error Handling

### Error Types
| Error | Code | Description |
|-------|------|-------------|
| `ratio_unavailable` | 1 | 无法获取 ratio |
| `sample_write_failed` | 2 | 无法写入采样日志 |
| `insufficient_data` | 3 | 样本不足，无法计算趋势 |

### Fallback Behavior
- ratio 获取失败 → 返回 null，不写采样
- 采样写入失败 → 记录 warning，继续输出
- 样本不足 → trend = `insufficient_data`

---

## Performance Requirements

| Metric | Target |
|--------|--------|
| 单次执行时间 | < 100ms |
| 内存占用 | < 10MB |
| 采样文件大小 | < 1MB (默认保留最近 1000 条) |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-03-09 | Initial specification |

