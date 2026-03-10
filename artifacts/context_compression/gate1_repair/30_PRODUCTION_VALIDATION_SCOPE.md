# Production Validation Scope

**Date**: 2026-03-09 10:45 CST  
**Phase**: V2 Production Validation + Gate 1 Closure

---

## 当前状态

**已完成**:
- Phase 1-5: Anchor/Tool/Constraint/OpenLoop 修复 ✅
- V2 集成到默认 pipeline ✅
- Unit/Self-test 通过 ✅

**未完成**:
- 真实场景验证 ❌
- old_topic_recovery 达标验证 ❌
- Resume-readiness 校准 ❌

---

## 本轮目标

**核心目标**: 证明 V2 不只是"更会写 capsule"，而是真的"更能把任务从断点接着做下去"。

**量化目标**:
1. old_topic_recovery >= 0.70
2. resume-readiness 与人工判断一致
3. correct_topic_wrong_anchor 不再主导
4. 无明显回归

---

## 验证范围

### Phase A: Before/After Replay
- 在 6 个桶上对比 V1 vs V2
- 记录逐样本 delta

### Phase B: Shadow Run
- 真实压缩场景观察
- 记录恢复行为

### Phase C: Resume-Readiness 校准
- 机器 vs 人工判定对比
- 分析误判模式

### Phase D: 回归审计
- 检查副作用
- 确认无新问题

---

## 非目标

- ❌ 不继续大改 schema
- ❌ 不开发新特性
- ❌ 不做过重监控

---

## 验收标准

Gate 1 正式通过条件：
1. V2 在真实样本上显著优于 V1
2. old_topic_recovery 达标或接近目标
3. resume-readiness 可信
4. 主失败类型迁移
5. 无重大回归

---
