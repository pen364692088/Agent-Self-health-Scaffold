# S1 Phase Progress Report - 2026-03-07

## Status: GATE 1 PENDING (阶段性进度，非通过证据)

## 完成的工作

### 样本采集
- 采集批次：s1-sampler-v2 --priority-weakest --limit 68
- 验证批次：s1-validator-run --all --limit 80
- 总报告数：105

### 分桶覆盖
| 桶 | 数量 | 目标 | 状态 |
|---|---|---|---|
| old_topic_recall | 26 | 15 | ✅ |
| multi_topic_switch | 17 | 12 | ✅ |
| with_open_loops | 15 | 12 | ✅ |
| post_tool_chat | 11 | 10 | ✅ |
| user_correction | 11 | 10 | ✅ |
| long_technical | 13 | 8 | ✅ |

### 来源分布
| 来源 | 数量 | 占比 | 目标 |
|---|---|---|---|
| real_main_agent | 32 | 26.9% | 25% |
| historical_replay | 0 | 0% | 35% ❌ |
| synthetic_stress | 87 | 73.1% | 40% |

### 指标快照
| 指标 | 当前 | 目标 | 状态 |
|---|---|---|---|
| old_topic_recovery | 0.50 | >= 0.70 | ❌ |
| commitment_preservation | ~1.0 | >= 0.85 | ✅ |
| commitment_drift | 0.030 | < 0.05 | ✅ |
| priority_preservation | ~0.96 | >= 0.80 | ✅ |

---

## 已知问题 (KNOWN_ISSUES)

### Issue #1: total_samples 与 source_counts_sum 不一致

**现象**：
- Dashboard 显示 total_samples = 105
- 但 source 分布总和 = 32 + 0 + 87 = 119

**原因分析**：
- samples 目录有 113 个样本文件
- reports 目录有 105 个报告文件
- 部分样本验证失败，未生成报告
- dashboard 读取 reports 目录，sampler 统计 samples 目录

**影响**：数据口径不一致，需统一

**修复建议**：
- 统一以 reports 为准（已验证的样本）
- 或在 sampler 输出中区分 samples vs validated

### Issue #2: old_topic_recovery 受 synthetic 默认评分影响

**现象**：
- 所有 synthetic 样本的 old_topic_recovery = 0.50
- 无样本达到 >= 0.70 阈值

**原因分析**：
- `_compute_old_topic_recovery()` 依赖 `is_recall` 事件标记
- synthetic 样本无真实 recall 事件
- 默认返回 0.50（中等分）

**影响**：当前结果不足以代表真实恢复能力

**修复建议**：
- 真实样本优先（historical_replay + real_main_agent）
- 或改进 synthetic 模板，注入可评分的 recall 事件

### Issue #3: historical_replay = 0，来源结构失衡

**现象**：
- historical_replay 占比 0%，目标 35%

**原因分析**：
- Session index 不可用（Warning: Session index not found）
- 历史回放依赖 session logs 索引

**影响**：不符合三路混合采样的预期

**修复建议**：
- 修复 session-index 路径
- 或手动提供历史片段

---

## 下一步计划

### 定向采样任务

1. **优先级 P0**：补 historical_replay 的 old_topic_recall 样本
   - 目标：>= 10 个可评分样本
   - 条件：session index 可用

2. **优先级 P1**：补 real_main_agent 的真实 recall 样本
   - 目标：>= 5 个高分样本（recovery >= 0.70）

3. **优先级 P2**：synthetic 仅保留明确可评分模板
   - 需要注入 is_recall 事件标记

### 追加观测项

- `scorable_old_topic_samples`: 有真实 recall 事件标记的样本数
- `old_topic_recovery_on_scorable_samples`: 可评分样本的平均 recovery

---

## 数据完整性检查报告

### 口径定义

| 数据源 | 路径 | 数量 |
|---|---|---|
| samples 目录 | artifacts/context_compression/validation/samples/*.json | 113 |
| reports 目录 | artifacts/context_compression/validation/reports/*.json | 105 |
| dashboard 显示 | tools/s1-dashboard 读取 reports | 105 |

### 差异来源

1. **samples - reports = 8**
   - 部分样本验证时出错（KeyError: 'sample_id'）
   - 未生成报告文件

2. **source_counts_sum (119) vs reports (105)**
   - sampler 统计的是 samples 目录
   - dashboard 统计的是 reports 目录
   - 口径不一致

### 建议统一口径

**以 reports 为准**：
- 只统计已验证成功的样本
- 来源信息从报告的 `source_type` 字段提取

### 修正后的来源分布（基于 reports）

```bash
# 待执行
grep -h '"source_type"' reports/*.json | sort | uniq -c
```

---

## 重要声明

⚠️ 本报告为阶段性进度提交，不得标记为 Gate 1 通过证据。

⚠️ Gate 1 保持 PENDING 状态，直到：
- old_topic_recovery >= 0.70（基于可评分样本）
- historical_replay 占比 >= 20%
- 数据口径一致

---

Generated: 2026-03-07T01:48 CST
Baseline Commit: 31a604a
Feature Freeze: S1 期间禁止功能变更
