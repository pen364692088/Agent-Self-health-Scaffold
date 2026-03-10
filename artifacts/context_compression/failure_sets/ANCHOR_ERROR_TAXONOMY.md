# Anchor Error Taxonomy

**Version**: 1.0  
**Created**: 2026-03-09  
**Purpose**: 分类和诊断 capsule anchor 选择错误

---

## 核心问题

**当前现象**：old_topic_recovery = 0.51，目标 >= 0.70

**根本原因**：topic 能正确 recall，但 anchor 选错了，导致恢复后上下文不完整。

---

## Anchor Error 分类

### 1. missing_critical_decision ⚠️ HIGH

**描述**：缺少关键决策锚点

**表现**：
- 系统记录了"我们决定..."
- 但 capsule 中没有提取出这个决策
- 恢复后不知道走了哪条路

**典型例子**：
```
用户: 我们用方案 A 还是方案 B？
Agent: 决定用方案 B，因为更简单
→ Capsule 缺失: "决定用方案 B"
```

**影响**：恢复后可能走回方案 A 的路线

**修复优先级**：P0

---

### 2. missing_file_path ⚠️ HIGH

**描述**：缺少关键文件路径锚点

**表现**：
- 对话中提到了具体文件
- capsule 中没有保留文件路径
- 恢复后不知道操作的是哪个文件

**典型例子**：
```
用户: 修改 config.yaml
Agent: 好的，我修改了 config.yaml，添加了...
→ Capsule 缺失: "config.yaml"
```

**影响**：恢复后不知道之前操作的是哪个文件

**修复优先级**：P0

---

### 3. missing_tool_result ⚠️ MEDIUM

**描述**：缺少工具执行结果锚点

**表现**：
- 执行了工具（如 exec, write, edit）
- capsule 中没有保留执行状态
- 恢复后不知道工具执行到哪一步

**典型例子**：
```
Agent: 运行 verify-and-check
Tool: PASS - Gate A/B/C 通过
→ Capsule 缺失: "verify-and-check: PASS"
```

**影响**：恢复后不知道工具是否成功，可能重复执行

**修复优先级**：P1

---

### 4. missing_id_reference ⚠️ MEDIUM

**描述**：缺少 ID/引用锚点

**表现**：
- 对话中提到了具体 ID（session ID, issue #, PR #）
- capsule 中没有保留这些引用
- 恢复后无法定位具体对象

**典型例子**：
```
用户: 查看 issue #123
Agent: Issue #123 是关于...
→ Capsule 缺失: "#123"
```

**影响**：恢复后不知道之前讨论的是哪个具体对象

**修复优先级**：P1

---

### 5. missing_constraint_update ⚠️ MEDIUM

**描述**：缺少约束更新锚点

**表现**：
- 用户追加/修改了约束
- capsule 中没有反映最新约束
- 恢复后用过时约束继续

**典型例子**：
```
用户: 对了，不要修改任何文件
Agent: 明白，只做分析不修改
→ Capsule 缺失: "不要修改任何文件"
```

**影响**：恢复后可能继续修改文件

**修复优先级**：P1

---

### 6. wrong_priority_anchor ⚠️ LOW

**描述**：选择了低优先级锚点而非高优先级

**表现**：
- capsule 中有很多锚点
- 但关键锚点被背景信息淹没
- 恢复时抓不住重点

**典型例子**：
```
Capsule 包含:
- "项目背景是..."（背景）
- "使用 Python 3.12"（技术栈）
- 但缺少 "决定使用 SQLite 而非 PostgreSQL"
```

**影响**：恢复后上下文太泛，抓不住关键决策

**修复优先级**：P2

---

### 7. stale_anchor ⚠️ LOW

**描述**：选择了过时锚点

**表现**：
- capsule 保留了早期决策
- 但后来决策已更新
- 恢复后用过时决策继续

**典型例子**：
```
早期: 决定用方案 A
后来: 改用方案 B
→ Capsule 保留: "决定用方案 A"
```

**影响**：恢复后走错方向

**修复优先级**：P2

---

## 当前诊断结果

基于 30 个 old_topic_recall 样本：

| 错误类型 | 样本数 | 优先级 |
|---------|-------|--------|
| missing_file_path | 5 | P0 |
| missing_tool_result | 5 | P1 |
| missing_id_reference | 2 | P1 |
| missing_constraint_update | 2 | P1 |
| missing_critical_decision | 1 | P0 |

---

## 修复方向

### 短期（Phase 2）

1. **改进 anchor selection 规则**
   - 添加 "decision impact" 评分
   - 文件路径优先级提升
   - 工具状态绑定

### 中期（Phase 3-5）

2. **tool_state persistence**
   - 工具调用时自动记录状态
   - 成功/失败状态绑定

3. **constraint tracking**
   - 约束变化时更新 capsule
   - 最新约束覆盖旧约束

4. **open_loop persistence**
   - 未完成事项追踪
   - 下一步动作绑定

---

## Anchor Priority Schema

**评分维度**：

| 维度 | 权重 | 说明 |
|------|------|------|
| decision_impact | 0.30 | 是否影响后续决策 |
| dependency_weight | 0.25 | 后续步骤是否依赖它 |
| recency | 0.15 | 是否接近当前断点 |
| scarcity | 0.15 | 是否稀缺、不可推回 |
| execution_relevance | 0.15 | 是否影响继续执行 |

**计算公式**：
```
anchor_score = decision_impact * 0.30
             + dependency_weight * 0.25
             + recency * 0.15
             + scarcity * 0.15
             + execution_relevance * 0.15
```

---

## 禁止高权重的信息类型

以下信息不应被选为高权重 anchor：

- ❌ 大段背景解释
- ❌ 纯总结性话术
- ❌ 不影响下一步行动的泛化状态
- ❌ 冗余的项目上下文
- ❌ 可从其他信息推断的内容

---

## 验收标准

Phase 2 完成后，应满足：

1. missing_critical_decision 样本数下降 >= 50%
2. missing_file_path 样本数下降 >= 50%
3. old_topic_recovery 提升 >= 0.10

---
