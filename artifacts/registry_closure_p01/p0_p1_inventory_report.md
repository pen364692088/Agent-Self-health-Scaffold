# Phase A: P0/P1 未注册入口盘点报告

**执行时间**: 2026-03-16T22:05:00Z
**状态**: ✅ 完成

---

## 1. 盘点目标

将 23 个 P0/P1 未注册入口拉成明确清单，成为本次任务主表。

---

## 2. 盘点统计

| 指标 | 值 |
|------|-----|
| 总 P0/P1 候选 | **23** |
| P0 数量 | 12 |
| P1 数量 | 11 |

---

## 3. 裁决结果汇总

| 裁决结果 | 数量 |
|----------|------|
| register_now | **11** |
| register_after_fix | **2** |
| exclude_non_mainline | **6** |
| exclude_dead_or_false_positive | **4** |
| **总计** | **23** |

---

## 4. P0 入口清单（12 个）

| 入口路径 | 裁决 | 理由 |
|----------|------|------|
| tools/session-start-recovery | register_now | 会话启动恢复核心入口 |
| tools/agent-self-health-scheduler | register_now | 自愈调度器核心 |
| tools/callback-worker-doctor | register_now | 关键诊断入口 |
| tools/session-recovery-check | register_now | 恢复检查核心 |
| tools/agent-recovery-verify | register_now | 恢复验证核心 |
| tools/gate-self-health-check | register_now | Gate 自检核心 |
| tools/resume_readiness_calibration.py | register_now | 恢复就绪校准 |
| tools/resume_readiness_evaluator_v2.py | register_now | 恢复就绪评估 |
| tools/agent-recovery-summary | exclude_non_mainline | 汇总报告，重新分类 P2 |
| tools/probe-callback-worker-doctor | exclude_non_mainline | 探测工具，重新分类 P2 |
| tools/demo-auto-resume-restart-test | exclude_dead_or_false_positive | 演示/测试脚本 |
| tools/session-start-recovery.bak | exclude_dead_or_false_positive | 备份文件 |

---

## 5. P1 入口清单（11 个）

| 入口路径 | 裁决 | 理由 |
|----------|------|------|
| tools/subagent-completion-handler | register_now | 子代理完成处理核心 |
| tools/subagent-callback-hook | register_now | 回调钩子核心 |
| tools/callback-handler-auto-advance | register_now | 回调自动推进 |
| tools/spawn-with-callback | register_after_fix | 需补治理接入 |
| tools/memory-scope-router | register_after_fix | 需审查并补治理接入 |
| tools/callback-daily-summary | exclude_non_mainline | 汇总报告，重新分类 P2 |
| tools/test-callback-acceptance | exclude_dead_or_false_positive | 测试脚本 |
| tools/test-callback-auto | exclude_dead_or_false_positive | 测试脚本 |
| tools/test-callback-regression | exclude_dead_or_false_positive | 回归测试脚本 |
| tools/probe-callback-delivery | exclude_non_mainline | 探测工具，重新分类 P2 |
| tools/verify-callback-guards | exclude_non_mainline | 验证工具，重新分类 P2 |

---

## 6. 关键发现

### 6.1 需立即纳管（11 个）

- 8 个 P0 入口：恢复、自愈、诊断、检查相关
- 3 个 P1 入口：子代理完成、回调钩子、回调推进

### 6.2 需修复后纳管（2 个）

- tools/spawn-with-callback
- tools/memory-scope-router

### 6.3 应排除（10 个）

- 6 个非主链入口（重新分类为 P2）
- 4 个废弃/误报入口

---

## 7. 交付物

| 产物 | 路径 |
|------|------|
| P0/P1 清单 JSON | artifacts/registry_closure_p01/p0_p1_inventory.json |
| P0/P1 盘点报告 | artifacts/registry_closure_p01/p0_p1_inventory_report.md |

---

**交付人**: Manager (Coordinator AI)
**交付时间**: 2026-03-16T22:05:00Z
