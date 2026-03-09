# Resume Readiness Specification

**Version**: 1.0  
**Created**: 2026-03-09

---

## 定义

> 在压缩恢复后，agent 是否具备足够上下文，可直接从断点处继续执行下一步。

---

## 评估维度

| 维度 | 权重 | 检查项 |
|------|------|--------|
| decision | 0.25 | 是否有决策锚点 |
| file_path | 0.25 | 是否有文件路径锚点 |
| tool_state | 0.25 | 是否有工具状态锚点 |
| constraint/open_loop | 0.25 | 是否有约束或待办 |

---

## 评分公式

```
readiness_score = has_decision * 0.25
                + has_file_path * 0.25
                + has_tool_state * 0.25
                + (has_constraint OR has_open_loop) * 0.25
```

---

## 等级

| 分数 | 等级 | 说明 |
|------|------|------|
| >= 0.75 | High | 恢复后可直接继续 |
| 0.50-0.74 | Medium | 需要补充部分上下文 |
| 0.25-0.49 | Low | 缺失关键信息 |
| < 0.25 | Critical | 几乎需要重新开始 |

---

## 当前评估结果

| 样本类型 | 平均 readiness | 等级 |
|---------|---------------|------|
| post_tool_chat | 0.25 | Low |
| with_open_loops | 0.24 | Low |
| user_correction | 0.03 | Critical |
| old_topic_recall | 0.11 | Critical |

---

## 目标

- **Medium 以上样本占比 >= 50%**
- **old_topic_recall 提升 >= 0.10**

---
