# Deferred Behavioral Changes

Date: 2026-03-10
Reason: Memory-LanceDB 观察窗期间禁止行为改变

---

## 观察窗约束

**Memory-LanceDB 冻结期**: 2026-03-10 ~ 2026-03-17

**禁止的行为改变**:
1. 修改默认路由逻辑
2. 修改工具选择优先级
3. 合并会改变 runtime 行为的入口
4. 触碰 memory capture/recall 主逻辑
5. 影响 Memory-LanceDB 观察窗结果

---

## 延期变更清单

### D1. 统一记忆检索路由

**当前状态**: 多入口并存
- `session-query` (推荐主入口)
- `context-retrieve` (S1 专用)
- `session-start-recovery` (自动调用)
- `openviking find` (底层)

**计划变更**:
- `session-query` 内部集成 `context-retrieve` 逻辑
- 统一检索参数和返回格式
- 移除冗余调用路径

**风险**: 可能影响 Context Compression Pipeline 行为

**依赖**: Gate 1 通过（S1 指标达标）

**状态**: ⏸️ DEFERRED

---

### D2. 子代理创建入口收口

**当前状态**: 多入口并存
- `subtask-orchestrate` (推荐主入口)
- `spawn-with-callback` (调试)
- `sessions_spawn` (底层)

**计划变更**:
- `spawn-with-callback` 添加弃用警告
- 更新所有内部调用使用 `subtask-orchestrate`
- 逐步移除 `spawn-with-callback`

**风险**: 可能影响现有脚本和工作流

**依赖**: 用户确认迁移计划

**状态**: ⏸️ DEFERRED

---

### D3. 状态写入入口统一

**当前状态**: 两套写入系统
- `safe-write` / `safe-replace` (Execution Policy)
- `state-write-atomic` (Session Continuity)

**计划变更**:
- 统一两套系统的策略检查
- `state-write-atomic` 内部调用 `safe-write`
- 或 `safe-write` 支持 SESSION-STATE 专用模式

**风险**: 可能影响状态持久化可靠性

**依赖**: 执行策略稳定运行

**状态**: ⏸️ DEFERRED

---

### D4. Memory-Lancedb 增强

**当前状态**: 冻结观察
- Source Isolation Fix 已应用
- 等待 3-7 天观察数据

**计划变更**:
- 增强 MEMORY_TRIGGERS 覆盖率
- 添加自动分类逻辑
- 支持 importance 动态调整

**风险**: 可能改变 capture 行为

**依赖**: 观察窗结束，确认无 false capture

**状态**: ⏸️ FROZEN

---

### D5. Heartbeat 流程优化

**当前状态**: 多个检查串行执行
- Session Recovery Check
- Self-Health Quick Mode
- Execution Policy Check
- Route Rebind Guard
- Shadow Mode Check

**计划变更**:
- 并行化无依赖检查
- 添加优先级中断机制
- 优化超时处理

**风险**: 可能影响 heartbeat 响应时间

**依赖**: 性能基准测试

**状态**: ⏸️ DEFERRED

---

### D6. 回执处理流程简化

**当前状态**: 多层回执系统
- `subagent-inbox` (正式通道)
- `callback-worker` (自动发送)
- `subagent-completion-handler` (处理回执)

**计划变更**:
- 简化回执格式
- 统一处理入口
- 减少中间状态

**风险**: 可能影响现有回执兼容性

**依赖**: 回执系统稳定运行

**状态**: ⏸️ DEFERRED

---

## 执行时机

| 变更 | 最早执行 | 前置条件 |
|------|----------|----------|
| D1 | 观察窗结束后 | Gate 1 通过 |
| D2 | 用户确认后 | 迁移计划制定 |
| D3 | 策略稳定后 | 无冲突验证 |
| D4 | 观察窗结束后 | 无 false capture |
| D5 | 性能测试后 | 基准数据 |
| D6 | 回执稳定后 | 兼容性测试 |

---

## 决策流程

```
观察窗结束
  ↓
评估观察数据
  ↓
┌─────────────────┐
│ 是否发现异常？   │
└────────┬────────┘
         │
    ┌────┴────┐
    ↓         ↓
   否         是
    │         │
    ↓         ↓
 启动变更   修复异常
    │         │
    ↓         ↓
逐步实施   重新观察
```

---

## 监控指标

### 观察窗期间

| 指标 | 目标 | 当前 |
|------|------|------|
| autoCapture hits | >= 0 | 监控中 |
| false captures | 0 | 0 |
| duplicate captures | 0 | 0 |
| recall injection rate | > 0% | 正常 |
| embedding errors | 0 | 0 |

### 变更前后对比

| 指标 | 变更前 | 变更后 | 差异 |
|------|--------|--------|------|
| capture success rate | TBD | TBD | - |
| recall latency | TBD | TBD | - |
| entry point usage | TBD | TBD | - |

---

## 文档更新

- [ ] 更新 TOOLS.md 行为说明
- [ ] 更新 SOUL.md 规则
- [ ] 更新 memory.md 入口推荐
- [ ] 创建迁移指南

---

## 审批要求

任何行为改变型变更需要：
1. 观察窗数据评估报告
2. 影响范围分析
3. 回滚计划
4. 用户确认（重大变更）

