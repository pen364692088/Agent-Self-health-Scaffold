# Gate 1 修复 · 范围与目标

## 背景

- 样本数量：111（目标 80）✅
- 分桶覆盖：6/6 ✅
- old_topic_recovery：0.51（目标 >= 0.70）❌

**核心问题**：不是样本不够，是 capsule 提取质量不够。

---

## 本轮目标

把 capsule 从"摘要包"升级为"可执行恢复包（continuation state package）"。

### 量化目标

- old_topic_recovery: 0.51 → >= 0.70
- correct_topic_wrong_anchor 下降 >= 50%

---

## 优先级顺序

1. **anchor selection** - P0
2. **tool_state persistence** - P1
3. **constraint tracking** - P1
4. **open_loop persistence** - P1

---

## 非目标

- ❌ 不继续补样本
- ❌ 不做大架构重写
- ❌ 不引入复杂模型替换
- ❌ 不做与 Gate 1 无关的优化

---

## Phase 完成情况

| Phase | 状态 | 交付物 |
|-------|------|--------|
| Phase 1: 失败样本对照集 | ✅ 完成 | correct_topic_wrong_anchor_labeled.jsonl |
| Phase 2: Anchor Selection | 🔄 进行中 | - |
| Phase 3: Tool State | 待开始 | - |
| Phase 4: Constraint | 待开始 | - |
| Phase 5: Open Loop | 待开始 | - |

---

## 关键文件

- `failure_sets/correct_topic_wrong_anchor_labeled.jsonl` - 失败样本标注
- `failure_sets/ANCHOR_ERROR_TAXONOMY.md` - 错误分类

---
Created: 2026-03-09 10:15 CST
