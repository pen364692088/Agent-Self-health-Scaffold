# Anchor Priority Schema

**Version**: 1.0  
**Created**: 2026-03-09

---

## 评分维度

| 维度 | 权重 | 评分方法 |
|------|------|----------|
| decision_impact | 0.30 | 是否影响后续决策（0/1）|
| dependency_weight | 0.25 | 后续步骤是否依赖（0/1）|
| recency | 0.15 | 接近断点程度（0-1）|
| scarcity | 0.15 | 不可推断程度（0/1）|
| execution_relevance | 0.15 | 是否影响继续执行（0/1）|

---

## 综合分数计算

```python
def calculate_anchor_score(anchor, context):
    score = (
        anchor.decision_impact * 0.30 +
        anchor.dependency_weight * 0.25 +
        anchor.recency * 0.15 +
        anchor.scarcity * 0.15 +
        anchor.execution_relevance * 0.15
    )
    return score
```

---

## 锚点类型默认分数

| 类型 | decision_impact | dependency_weight | recency | scarcity | execution_relevance | 总分 |
|------|----------------|-------------------|---------|----------|---------------------|------|
| 关键决策 | 1.0 | 1.0 | 0.8 | 1.0 | 1.0 | 0.95 |
| 文件路径 | 0.5 | 1.0 | 0.8 | 1.0 | 1.0 | 0.90 |
| 工具状态（进行中）| 0.5 | 1.0 | 1.0 | 0.8 | 1.0 | 0.90 |
| 最新约束 | 0.8 | 0.8 | 1.0 | 0.8 | 0.9 | 0.85 |
| ID/引用 | 0.3 | 0.8 | 0.5 | 1.0 | 0.7 | 0.75 |
| Open Loop | 0.6 | 0.8 | 0.8 | 0.6 | 0.9 | 0.75 |
| 工具状态（已完成）| 0.3 | 0.6 | 0.8 | 0.7 | 0.8 | 0.70 |
| 时间锚点 | 0.1 | 0.3 | 0.9 | 0.6 | 0.3 | 0.50 |
| 实体提及 | 0.2 | 0.4 | 0.5 | 0.5 | 0.4 | 0.45 |
| 背景信息 | 0.1 | 0.2 | 0.3 | 0.3 | 0.2 | 0.30 |

---

## 选择算法

```
1. 提取所有候选锚点
2. 计算每个锚点的综合分数
3. 按分数排序
4. 同类型去重（保留最高分）
5. 按优先级分层选择：
   - Tier 1: 全部保留
   - Tier 2: top 5
   - Tier 3: top 3
6. 验证 resume-readiness
```

---
