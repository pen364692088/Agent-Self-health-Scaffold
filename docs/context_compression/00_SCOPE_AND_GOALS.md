# Auto-Compaction Waterline Control · Scope & Goals

**Created**: 2026-03-09T14:25:00-06:00
**Gate**: A · Contract

---

## 1. Core Objective

把 Context Compression 从"可手动调用的能力"升级成"会话运行中的自动水位管理能力"。

**User's Real Goal**:

> 当单个会话上下文占用接近上限时，系统自动触发压缩，将 context ratio 从高水位打回安全区，然后继续当前工作。

---

## 2. What This Is

✅ **In Scope**:

1. **Budget Watcher** — 持续监控 context ratio
2. **Trigger Policy** — 定义何时触发、何时阻断、何时升级
3. **Auto Compaction Executor** — 自动调用压缩链
4. **Post-Compaction Handoff** — 压缩后状态持久化
5. **Guardrails/Monitoring** — 可观测、可回滚、可审计

**Quantified Goals**:

| Condition | Behavior |
|-----------|----------|
| ratio >= 0.80 | 自动触发正常压缩 |
| ratio >= 0.90 | 进入紧急压缩模式 |
| 压后目标 | 回落到 0.55~0.65 安全区 |
| 紧急压后目标 | 回落到 0.45~0.55 |
| cooldown | 防止短时间内重复压缩 |

---

## 3. What This Is NOT

❌ **Explicitly Out of Scope**:

1. 不重做 readiness evaluator (V3 已为生产默认)
2. 不重开 Gate 1 / Post-Close 主链验证
3. 不做复杂自适应学习控制
4. 不把目标写死成"每次必须压到 50%"
5. 不依赖用户手动执行 capsule-builder
6. 不通过"强制开新会话"伪装成自动压缩

---

## 4. Key Design Principles

### Principle 1 · 安全区优先
目标不是机械压到 50%，而是在保证恢复质量的前提下回落到安全区。

### Principle 2 · Hysteresis
触发线 >= 0.80，回落安全线 <= 0.65，避免抖动。

### Principle 3 · Cooldown
两次自动压缩之间必须有最小间隔。

### Principle 4 · Quality First
若当前会话处于高风险状态，应降级或延迟压缩。

---

## 5. Implementation Phases

| Phase | Name | Key Deliverable |
|-------|------|-----------------|
| 1 | Ratio Observability | BUDGET_WATCHER_SPEC.md |
| 2 | Trigger Policy | AUTO_COMPACTION_POLICY.md |
| 3 | Executor Integration | tools/auto-context-compact |
| 4 | Threshold Tests | 04_THRESHOLD_REPLAY_RESULTS.md |
| 5 | Shadow Validation | 05_SHADOW_VALIDATION_REPORT.md |
| 6 | Default Enablement | FINAL_AUTO_COMPACTION_VERDICT.md |

---

## 6. Success Criteria

本轮成功的充要条件：

1. ✅ ratio >= 0.80 时可自动触发压缩
2. ✅ 压后能回落到安全区
3. ✅ ratio >= 0.90 有紧急压缩路径
4. ✅ cooldown/hysteresis 有效
5. ✅ 自动压缩后 recovery quality 未明显下降
6. ✅ 整个链路可观测、可回滚、可审计

---

## 7. Failure Criteria

出现以下任一情况视为失败：

- 只能手动执行，不能自动触发
- 触发了但没真正压缩
- 压完没有写回新状态
- 经常连续重复压缩
- 为了打低 ratio 明显破坏恢复质量
- 只有文档，没有真实 shadow/e2e 证据

---

## 8. Gate A Deliverable

**This Document**: `docs/context_compression/00_SCOPE_AND_GOALS.md`

**Confirmation**: 
- ✅ 范围已锁定：自动压缩水位控制
- ✅ 非目标已明确排除
- ✅ 成功/失败判定已定义
- ✅ 阶段规划已确定

**Gate A Status**: ✅ PASSED

---

## Next Step

启动 **Phase 1 · Ratio Observability**:
- 实现 Budget Watcher
- 定义 ratio 观测规范
- 验证 ratio 可被稳定读取

