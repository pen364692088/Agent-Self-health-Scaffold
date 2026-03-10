# Module Health Matrix

**审计日期**: 2026-03-09 21:25 CST

---

## 评估维度定义

| 维度 | 定义 |
|------|------|
| Exists | 文件/工具物理存在 |
| Configured | 有配置文件或配置项 |
| Declared Enabled | 文档声明已启用 |
| Wired Enabled | 代码中有调用点 |
| Runtime Active | 实际运行时有活动 |
| E2E Effective | 端到端功能验证通过 |

---

## Session Continuity

| 组件 | Exists | Configured | Declared | Wired | Runtime | E2E |
|------|--------|------------|----------|-------|---------|-----|
| session-start-recovery | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| continuity-event-log | ✅ | ✅ | ✅ | ✅ | ✅ | - |
| state-write-atomic | ✅ | ✅ | ✅ | ✅ | ✅ | - |
| SESSION-STATE.md | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| working-buffer.md | ✅ | ✅ | ✅ | ✅ | ✅ | - |
| handoff.md | ✅ | ✅ | ✅ | ✅ | ✅ | - |
| WAL | ✅ | ✅ | ✅ | ✅ | ✅ | - |

**整体健康度**: 100%

---

## Execution Policy

| 组件 | Exists | Configured | Declared | Wired | Runtime | E2E |
|------|--------|------------|----------|-------|---------|-----|
| policy-eval | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ |
| policy-doctor | ✅ | ✅ | ✅ | ⚠️ | ✅ | - |
| safe-write | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| safe-replace | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| verify-and-close | ✅ | ✅ | ✅ | ⚠️ | - | - |
| probe-execution-policy-v2 | ✅ | ✅ | ✅ | ❌ | - | - |

**整体健康度**: 75%

**问题**: probe-execution-policy-v2 未集成到 Heartbeat

---

## 子代理编排

| 组件 | Exists | Configured | Declared | Wired | Runtime | E2E |
|------|--------|------------|----------|-------|---------|-----|
| subtask-orchestrate | ✅ | ✅ | ✅ | ✅ | ✅ | - |
| subagent-inbox | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| subagent-completion-handler | ✅ | ✅ | ✅ | ✅ | ✅ | - |
| callback-worker.service | ✅ | ✅ | ✅ | ✅ | ⚠️ | - |
| callback-worker.path | ✅ | ✅ | ✅ | ✅ | ✅ | - |

**整体健康度**: 95%

**注**: callback-worker inactive 是预期状态（事件驱动）

---

## 记忆系统

| 组件 | Exists | Configured | Declared | Wired | Runtime | E2E |
|------|--------|------------|----------|-------|---------|-----|
| context-retrieve | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| capsule-builder | ✅ | ✅ | ✅ | ⚠️ | - | - |
| session-indexer | ✅ | ✅ | ✅ | ⚠️ | - | - |
| capsules/ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| session_index/ | ❌ | - | - | - | - | - |
| OpenViking | ✅ | ✅ | ✅ | ✅ | ⚠️ | ✅ |

**整体健康度**: 80%

**问题**: Session Index 为 0，OpenViking embedding 错误

---

## Heartbeat & 自健康

| 组件 | Exists | Configured | Declared | Wired | Runtime | E2E |
|------|--------|------------|----------|-------|---------|-----|
| HEARTBEAT.md | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| agent-self-health-scheduler | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| route-rebind-guard-heartbeat | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| shadow_watcher | ✅ | ✅ | ⚠️ | ⚠️ | ❌ | - |
| session-continuity-daily-check | ✅ | ✅ | ✅ | ✅ | ✅ | - |

**整体健康度**: 85%

**问题**: shadow_watcher 未启用

---

## Cron & 自动化

| 组件 | Exists | Configured | Declared | Wired | Runtime | E2E |
|------|--------|------------|----------|-------|---------|-----|
| proactive-check.sh | ✅ | ✅ | ✅ | ✅ | ✅ | - |
| retrieval-regression-runner | ✅ | ✅ | ✅ | ✅ | ✅ | - |
| subagent-inbox cleanup | ✅ | ✅ | ✅ | ✅ | ✅ | - |
| session cleanup | ✅ | ✅ | ✅ | ✅ | ✅ | - |
| openclaw-gateway.service | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

**整体健康度**: 100%

---

## 总体矩阵

| 系统 | Exists | Wired | Effective | 健康度 |
|------|--------|-------|-----------|--------|
| Session Continuity | 100% | 100% | 100% | 100% |
| Execution Policy | 100% | 50% | 75% | 75% |
| 子代理编排 | 100% | 100% | 100% | 95% |
| 记忆系统 | 83% | 80% | 90% | 80% |
| Heartbeat/自健康 | 100% | 80% | 85% | 85% |
| Cron/自动化 | 100% | 100% | 100% | 100% |

**加权平均**: 87/100
