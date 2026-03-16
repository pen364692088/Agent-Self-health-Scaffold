# Phase C: P0/P1 入口人工复核与裁决报告

**执行时间**: 2026-03-16T21:45:00Z
**状态**: ✅ 完成

---

## 1. Phase C 目标

对 23 个 P0/P1 入口逐项裁决，决定纳管或排除。

---

## 2. 裁决标准

根据任务单定义：

| 裁决结果 | 说明 |
|----------|------|
| register_now | 立即纳入 registry |
| register_after_fix | 修复后纳入 |
| exclude_non_mainline | 排除（非主链入口） |
| exclude_dead_or_false_positive | 排除（废弃/误报） |

---

## 3. P0 入口裁决（12 个）

### 3.1 纳管入口

| 入口 | 裁决 | 理由 | 治理要求 |
|------|------|------|----------|
| tools/session-start-recovery | **register_now** | 会话启动恢复核心入口，影响所有新会话 | P0 全套治理 |
| tools/agent-self-health-scheduler | **register_now** | 自愈调度核心，影响自动恢复 | P0 全套治理 |
| tools/callback-worker-doctor | **register_now** | callback-worker 诊断入口，影响回调处理 | P0 全套治理 |
| tools/session-recovery-check | **register_now** | 会话恢复检查入口 | P0 全套治理 |
| tools/agent-recovery-verify | **register_now** | 恢复验证入口 | P0 全套治理 |
| tools/gate-self-health-check | **register_now** | Gate 自检核心 | P0 全套治理 |
| tools/resume_readiness_calibration.py | **register_now** | 恢复就绪校准 | P0 全套治理 |
| tools/resume_readiness_evaluator_v2.py | **register_now** | 恢复就绪评估 v2 | P0 全套治理 |

**小计**: 8 个纳管

### 3.2 排除入口

| 入口 | 裁决 | 理由 |
|------|------|------|
| tools/agent-recovery-summary | exclude_non_mainline | 汇总报告生成，不触发执行，重新分类为 P2 |
| tools/probe-callback-worker-doctor | exclude_non_mainline | 诊断探测工具，重新分类为 P2 |
| tools/demo-auto-resume-restart-test | exclude_dead_or_false_positive | 演示/测试脚本，非生产入口 |
| tools/session-start-recovery.bak | exclude_dead_or_false_positive | 备份文件，已废弃 |

**小计**: 4 个排除

---

## 4. P1 入口裁决（11 个）

### 4.1 纳管入口

| 入口 | 裁决 | 理由 | 治理要求 |
|------|------|------|----------|
| tools/subagent-completion-handler | **register_now** | 子代理完成处理核心，影响回调链 | P1 治理 |
| tools/subagent-callback-hook | **register_now** | 回调钩子核心 | P1 治理 |
| tools/callback-handler-auto-advance | **register_now** | 回调自动推进 | P1 治理 |
| tools/spawn-with-callback | **register_after_fix** | 带 spawn 回调，需补治理接入后纳管 | P1 治理 |
| tools/memory-scope-router | **register_after_fix** | 内存作用域路由，需审查后纳管 | P1 治理 |

**小计**: 5 个纳管

### 4.2 排除入口

| 入口 | 裁决 | 理由 |
|------|------|------|
| tools/callback-daily-summary | exclude_non_mainline | 汇总报告，非执行入口 |
| tools/test-callback-acceptance | exclude_dead_or_false_positive | 测试脚本 |
| tools/test-callback-auto | exclude_dead_or_false_positive | 测试脚本 |
| tools/test-callback-regression | exclude_dead_or_false_positive | 测试脚本 |
| tools/probe-callback-delivery | exclude_non_mainline | 探测工具，重新分类为 P2 |
| tools/verify-callback-guards | exclude_non_mainline | 验证工具，重新分类为 P2 |

**小计**: 6 个排除

---

## 5. 裁决汇总

### 5.1 总体统计

| 裁决结果 | P0 | P1 | 总计 |
|----------|----|----|------|
| register_now | 8 | 3 | **11** |
| register_after_fix | 0 | 2 | **2** |
| exclude_non_mainline | 2 | 4 | **6** |
| exclude_dead_or_false_positive | 2 | 2 | **4** |
| **总计** | **12** | **11** | **23** |

### 5.2 待纳管入口

**立即纳管（11 个）**:
- tools/session-start-recovery
- tools/agent-self-health-scheduler
- tools/callback-worker-doctor
- tools/session-recovery-check
- tools/agent-recovery-verify
- tools/gate-self-health-check
- tools/resume_readiness_calibration.py
- tools/resume_readiness_evaluator_v2.py
- tools/subagent-completion-handler
- tools/subagent-callback-hook
- tools/callback-handler-auto-advance

**修复后纳管（2 个）**:
- tools/spawn-with-callback
- tools/memory-scope-router

### 5.3 排除入口

**非主链入口（6 个）**:
- tools/agent-recovery-summary → P2
- tools/probe-callback-worker-doctor → P2
- tools/callback-daily-summary → P2
- tools/probe-callback-delivery → P2
- tools/verify-callback-guards → P2

**废弃/误报（4 个）**:
- tools/demo-auto-resume-restart-test
- tools/session-start-recovery.bak
- tools/test-callback-acceptance
- tools/test-callback-auto
- tools/test-callback-regression

---

## 6. Phase C 完成条件

| 条件 | 状态 |
|------|------|
| 所有 P0 已裁决 | ✅ 通过 |
| 所有 P1 已裁决 | ✅ 通过 |
| 无长期 pending 项 | ✅ 通过 |
| 所有裁决有理由 | ✅ 通过 |

---

## 7. 下一步

**进入 Phase D**: 应纳管入口补录与治理接入校正

目标：
- 将 13 个纳管入口（11 + 2）补录到 registry
- 标记治理接入状态
- 识别治理缺口

---

**交付人**: Manager (Coordinator AI)
**交付时间**: 2026-03-16T21:45:00Z
