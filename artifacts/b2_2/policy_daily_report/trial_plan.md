# B2-2 试运行计划：每日策略观察报告生成

## 1. 任务定义

**任务名称**: 每日策略观察报告生成

**任务描述**: 执行 `policy-daily-report --save`，生成策略观察报告并写入文件。

## 2. 口径定义

### 2.1 输入真源

| 数据源 | 路径 | 用途 |
|--------|------|------|
| Policy Doctor | `tools/policy-doctor` | 健康检查状态 |
| Policy Violation Summary | `tools/policy-violation-summary` | 违规统计 |
| Policy Shadow Tracker | `tools/policy-shadow-tracker` | Shadow 规则命中 |
| Violations Log | `artifacts/execution_policy/violations/violations_*.jsonl` | 违规记录 |

### 2.2 输出真源

| 输出 | 路径 |
|------|------|
| 主报告 | `artifacts/execution_policy/daily_reports/daily_YYYY-MM-DD.md` |
| 备份报告 | `artifacts/b2_2/policy_daily_report/reports/daily_YYYY-MM-DD.md` |

### 2.3 幂等规则

```
同一 date 重复运行时：
1. 若目标文件不存在 → 生成新文件
2. 若目标文件已存在 → 覆盖（不追加）
3. 禁止：重复段落、重复附录、重复审计项
4. 最终状态：仅保留一个最终报告文件
```

### 2.4 验证规则

```
A. 文件存在性：目标路径有且仅有一个 .md 文件
B. 格式合法性：Markdown 结构正确，包含 6 个标准 Section
C. 关键字段齐全：
   - Policy Doctor 状态
   - 样本成熟度（Deny/Warn/Fallback）
   - 核心指标（Fallback rate/False positive/Warn follow）
   - 今日结论（Status/Grade/Actions）
D. 内容一致性：报告数据与事实源（violations log）一致
E. 无重复内容：段落不重复、附录不重复、审计项不重复
```

## 3. 风险评估

| 风险项 | 等级 | 说明 |
|--------|------|------|
| 文件写入 | 低 | 非破坏性，可删除恢复 |
| 状态覆盖 | 低 | 每次生成覆盖，不追加 |
| 依赖工具缺失 | 低 | 工具已验证存在 |

## 4. 试运行流程

### Run 1: 正常生成
- 执行报告生成
- 验证文件创建
- 记录证据

### Run 2: 幂等验证（同 date 重复执行）
- 再次执行同 date 报告生成
- 验证文件被正确覆盖（非追加）
- 验证内容无重复

### Run 3: 稳定性验证
- 第三次执行
- 验证结果与 Run 2 一致
- 验证副作用稳定

### Run 4 (可选): 半成品恢复验证
- 构造半成品文件
- 验证覆盖行为
- 验证无残留

## 5. 通过标准

| 标准 | 要求 |
|------|------|
| 成功率 | 100% |
| 幂等性 | 同 date 多次运行只保留一个最终报告 |
| 状态一致性 | 报告数据与事实源一致 |
| 无重复副作用 | 不出现重复文件、重复内容 |
| 证据链完整 | 每次运行有日志、验证记录、产物快照 |

## 6. B0-5 触发条件

若出现以下任一情况，触发 B0-5：
- 副作用已发生但状态未同步
- 重复执行导致重复副作用（多文件、内容重复）
- 恢复后进入错误 step
- 失败后无法安全结束

---

**创建时间**: 2026-03-17T01:54:00Z
**状态**: 待执行
