# Phase B: 全量发现结果清洗与分级报告

**执行时间**: 2026-03-16T21:40:00Z
**状态**: ✅ 完成

---

## 1. Phase B 目标

对 234 个候选入口完成初步清洗，形成 P0/P1/P2/P3 分类台账。

---

## 2. 分类统计

| 分类 | 数量 | 说明 |
|------|------|------|
| **P0** | **12** | 主链强相关入口 |
| **P1** | **11** | 潜在主链旁路入口 |
| **P2** | **86** | 辅助治理/运维/诊断入口 |
| **P3** | **117** | 测试/示例/废弃/误报入口 |
| **总计** | **226** | 未注册候选入口 |

---

## 3. P0 入口清单（12 个）

| 入口路径 | 分类 | 说明 |
|----------|------|------|
| tools/session-start-recovery | P0 | 会话启动恢复入口 |
| tools/resume_readiness_calibration.py | P0 | 恢复就绪校准 |
| tools/agent-recovery-summary | P0 | 恢复汇总入口 |
| tools/probe-callback-worker-doctor | P0 | callback-worker 诊断 |
| tools/demo-auto-resume-restart-test | P0 | 自动恢复演示/测试 |
| tools/session-start-recovery.bak | P0 | 会话启动恢复备份 |
| tools/gate-self-health-check | P0 | Gate 自检入口 |
| tools/agent-self-health-scheduler | P0 | 自愈调度器 |
| tools/callback-worker-doctor | P0 | callback-worker 诊断 |
| tools/session-recovery-check | P0 | 会话恢复检查 |
| tools/resume_readiness_evaluator_v2.py | P0 | 恢复就绪评估 v2 |
| tools/agent-recovery-verify | P0 | 恢复验证入口 |

---

## 4. P1 入口清单（11 个）

| 入口路径 | 分类 | 说明 |
|----------|------|------|
| tools/test-callback-acceptance | P1 | 回调验收测试 |
| tools/probe-callback-delivery | P1 | 回调投递探测 |
| tools/subagent-callback-hook | P1 | 子代理回调钩子 |
| tools/verify-callback-guards | P1 | 回调 guard 验证 |
| tools/subagent-completion-handler | P1 | 子代理完成处理 |
| tools/test-callback-auto | P1 | 自动回调测试 |
| tools/memory-scope-router | P1 | 内存作用域路由 |
| tools/test-callback-regression | P1 | 回调回归测试 |
| tools/spawn-with-callback | P1 | 带回调 spawn |
| tools/callback-handler-auto-advance | P1 | 回调自动推进 |
| tools/callback-daily-summary | P1 | 回调日汇总 |

---

## 5. P2 入口清单（86 个）

辅助治理/运维/诊断入口，包括：
- policy-* 类工具（策略检查、诊断）
- probe-* 类工具（探测、监控）
- check-* 类工具（检查、验证）
- monitor-* 类工具（监控）
- session-* 类诊断工具

---

## 6. P3 入口清单（117 个）

测试/示例/废弃/误报入口，包括：
- test-* 类测试脚本
- *.bak 备份文件
- demo-* 演示脚本
- threshold_test_runner 等测试工具
- *.original 原始备份
- *.mjs Node.js 脚本

---

## 7. 初步裁决建议

### 7.1 P0 入口

| 入口 | 建议裁决 | 理由 |
|------|----------|------|
| tools/session-start-recovery | register_now | 主链关键入口 |
| tools/agent-self-health-scheduler | register_now | 自愈调度核心 |
| tools/callback-worker-doctor | register_now | 关键诊断入口 |
| tools/session-recovery-check | register_now | 恢复检查入口 |
| tools/agent-recovery-verify | register_now | 恢复验证入口 |
| tools/gate-self-health-check | register_now | Gate 自检核心 |
| tools/resume_readiness_calibration.py | register_now | 恢复就绪校准 |
| tools/resume_readiness_evaluator_v2.py | register_now | 恢复就绪评估 |
| tools/agent-recovery-summary | exclude_non_mainline | 汇总报告，非执行入口 |
| tools/probe-callback-worker-doctor | exclude_non_mainline | 诊断工具，P2 重新分类 |
| tools/demo-auto-resume-restart-test | exclude_dead_or_false_positive | 演示/测试 |
| tools/session-start-recovery.bak | exclude_dead_or_false_positive | 备份文件 |

### 7.2 P1 入口

| 入口 | 建议裁决 | 理由 |
|------|----------|------|
| tools/subagent-completion-handler | register_now | 子代理完成处理核心 |
| tools/subagent-callback-hook | register_now | 回调钩子核心 |
| tools/callback-handler-auto-advance | register_now | 回调自动推进 |
| tools/callback-daily-summary | exclude_non_mainline | 汇总报告，非执行入口 |
| tools/spawn-with-callback | register_after_fix | 需要治理接入 |
| tools/test-callback-* | exclude_dead_or_false_positive | 测试脚本 |
| tools/probe-callback-delivery | exclude_non_mainline | 探测工具，P2 重新分类 |
| tools/verify-callback-guards | exclude_non_mainline | 验证工具，P2 重新分类 |
| tools/memory-scope-router | register_after_fix | 路由入口，需审查 |

---

## 8. 交付物

| 产物 | 路径 |
|------|------|
| 入口清单 JSON | artifacts/registry_closure/discovered_entries_inventory.json |
| Phase B 报告 | artifacts/registry_closure/phase_b_classification_report.md |

---

## 9. 下一步

**进入 Phase C**: P0/P1 入口人工复核与裁决

目标：
- 对 23 个 P0/P1 入口逐项裁决
- 决定纳管或排除
- 输出裁决报告

---

**交付人**: Manager (Coordinator AI)
**交付时间**: 2026-03-16T21:40:00Z
