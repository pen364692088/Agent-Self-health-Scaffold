# Config Alignment Gate

**Gate ID**: CAG-20260308-001
**Status**: ✅ PASSED
**Created**: 2026-03-08T00:29:00-06:00
**Closed**: 2026-03-08T00:45:00-06:00

---

## Purpose

将 OpenClaw 运行时压缩策略对齐到目标策略，但不缩小 context window。

---

## Hard Decisions (LOCKED)

| Parameter | Before | After |
|-----------|--------|-------|
| contextWindow | 200k | 200k (保留) |
| threshold_enforced | 0.92 | **0.85** ✅ |
| threshold_strong | 0.92 | 0.92 |
| pre-assemble | 未执行 | **必须执行** |

## Target Policy

```
< 0.75    → observe
0.75-0.85 → candidate
0.85-0.92 → pre-assemble standard compression ✅
>= 0.92   → strong compression
```

## Critical Rule

**不允许跨过 0.85 后继续拖延。** ✅

压缩判定必须发生在 prompt assemble 前。

---

## Constraints (NON-NEGOTIABLE)

- ✅ 保留四层记忆架构（Stable / Working / Capsule / Retrieval）
- ✅ 不混入 OpenViking/L2 修复线
- ✅ 不扩大到 high-risk scope
- ✅ 不重做 scoring / metrics / schema
- ✅ 不引入新的大 patch set
- ✅ kill switch 保留可用

---

## Execution Phases

| Phase | Purpose | Status |
|-------|---------|--------|
| A. Config Alignment Gate | 定义配置对齐 | ✅ PASSED |
| B. Runtime Policy Implementation | 实现运行时策略 | ✅ DONE |
| C. Controlled Validation | 受控验证 | ⏳ PENDING |
| D. Natural Validation | 自然验证 | ⏳ PENDING |
| E. Default Rollout | 默认推出 | ⏳ PENDING |

---

## Gate Pass Conditions

- [x] runtime_compression_policy.json 创建 ✅
- [x] OpenClaw 运行时读取并应用策略 ✅
- [x] pre-assemble 压缩决策点确认 ✅
- [x] threshold_enforced = 0.85 生效 ✅
- [x] 安全计数器归零 ✅

---

## Deliverables

- [x] CONFIG_ALIGNMENT_GATE.md ✅
- [x] runtime_policy_source_of_truth.md ✅
- [x] runtime_compression_policy.json ✅
- [x] runtime_policy_patch_report.md ✅

---

## Patches Applied

| File | Change |
|------|--------|
| `handler.ts` | max_tokens: 100k → 200k |
| `handler.ts` | threshold: 0.70 → 0.85 |

---

## Rollback Plan

如果验证失败，回退到：
```
threshold_enforced: 0.92
pre-assemble: disabled
max_tokens: 100000
```

Backup file: `handler.ts.backup`

---

*Gate passed: 2026-03-08T00:45:00-06:00*
