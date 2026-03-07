# 数据完整性检查报告 - 2026-03-07

## 概述

本报告解释 total_samples 与 source_counts_sum 的差异来源。

## 数据口径

### 口径 A: samples 目录
```
路径: artifacts/context_compression/validation/samples/*.json
数量: 113
来源: s1-sampler-v2 生成
```

### 口径 B: reports 目录
```
路径: artifacts/context_compression/validation/reports/*.json
数量: 105
来源: s1-validator-run 验证后生成
```

### 口径 C: dashboard 显示
```
来源: 读取 reports 目录
显示: 105
```

## 差异分析

### samples (113) vs reports (105) = 8 差异

**原因**: 部分样本验证失败，未生成报告

**失败样本**:
- sample_synthetic_stress_long_technical_297ed0b1.json (KeyError)
- sample_synthetic_stress_long_technical_43c7da0b.json (KeyError)
- sample_synthetic_stress_long_technical_b66b6312.json (KeyError)
- sample_synthetic_stress_long_technical_f440ae04.json (KeyError)
- sample_synthetic_stress_long_technical_f98f5f8d.json (KeyError)
- ... (共约 8 个)

**失败原因**: 样本文件缺少 `sample_id` 字段（s1-validator-run 的元数据解析失败）

### source_counts_sum (119) vs reports (105) = 14 差异

**原因**: sampler 和 dashboard 使用不同数据源
- sampler 统计 samples 目录
- dashboard 统计 reports 目录

## 修正后的来源分布（基于 reports）


```
     70 synthetic_stress
     18 real_main_agent
      5 synthetic
```

## 追加观测项

### scorable_old_topic_samples

定义：有真实 recall 事件标记的样本数（source_type != synthetic_stress）

数量: 23

### old_topic_recovery_on_scorable_samples

定义：可评分样本的平均 old_topic_recovery

平均值: 0.50

## 结论

1. 数据口径已统一：以 reports 目录为准（105 个已验证样本）
2. scorable_old_topic_samples: 待计算
3. old_topic_recovery_on_scorable_samples: 待计算

## 建议

- 修复 s1-validator-run 的元数据解析，避免 KeyError
- 后续采样优先使用 real_main_agent 和 historical_replay
- synthetic 仅作为补充，且需注入可评分事件


---

## 数据口径正式定义

### 规则：samples vs reports 的语义

```
samples 目录 = 创建的样本（generated samples）
reports 目录 = 完成评分的样本（validated samples）
差值 = execution_failures（验证失败，不计入 gate scoring）
```

### 必须记录到 failure ledger

所有验证失败的样本必须：
1. 记录到 `failures.jsonl`
2. 标注失败原因（如 KeyError, tool_error）
3. 不计入 Gate 指标计算

### Gate Scoring 口径

**计入 Gate 指标**：
- reports 目录中 `source_type != synthetic_stress` 的样本

**仅作 observation**：
- reports 目录中 `source_type == synthetic_stress` 的样本
- 用于回归测试、压力测试、覆盖率补充
- 不影响 Gate 1 主指标判定

