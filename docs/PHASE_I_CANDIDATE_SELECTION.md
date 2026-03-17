# Phase I: 扩容对象选择

**版本**: 1.0  
**日期**: 2026-03-17  
**状态**: 已确认

---

## 概述

本文档定义本轮扩容的候选 Agent 列表、选择理由和风险评估。

---

## 当前 default_enabled Agent

| Agent | 角色 | 状态 |
|-------|------|------|
| implementer | 执行型 | ✅ default_enabled |
| planner | 规划型 | ✅ default_enabled |
| verifier | 验证型 | ✅ default_enabled |

---

## 候选 Agent 列表

本轮选择 **2 个新 Agent** 进入受控扩容：

### 候选 1: scribe

**角色**: 记录型  
**职责**: 文档和决策记录、handoff 准备

**选择理由**:
1. 职责清晰、边界稳定
2. 代表新的角色类型（记录型），与现有执行/规划/验证型互补
3. 未来会频繁用到（每次任务都需要文档记录）
4. 风险较低（不直接修改代码）

**风险等级**: 低

**预期接入模式**: pilot_enabled → 观察 → default_enabled

**不适合原因**: 无

---

### 候选 2: merger

**角色**: 合并型  
**职责**: 集成多个 Agent 的工作、发布管理

**选择理由**:
1. 职责清晰、边界稳定
2. 代表新的角色类型（合并型）
3. 在实际工作流中有明确价值
4. 可以与现有 Agent 形成完整工作流闭环

**风险等级**: 中
- 原因：涉及 git 操作和发布决策
- 缓解：mutation guard 会保护关键路径

**预期接入模式**: pilot_enabled → 观察 → 根据指标决定

**不适合原因**: 无

---

## 不选择的 Agent

暂无其他已定义但未启用的 Agent。

---

## 扩容规模控制

- **本轮扩容数量**: 2 个新 Agent
- **当前 default_enabled 数量**: 3 个
- **本轮不超过当前数量**: ✅ 2 < 3

---

## 接入计划

| Agent | 阶段 1 | 阶段 2 | 阶段 3 | 阶段 4 |
|-------|-------|-------|-------|-------|
| scribe | Onboarding | pilot_enabled | 观察 | 决策 |
| merger | Onboarding | pilot_enabled | 观察 | 决策 |

---

## 风险缓解

| 风险 | 缓解措施 |
|------|---------|
| 新 Agent 不稳定 | 通过 pilot_enabled 观察，不直接 default_enabled |
| 指标异常 | 回退到 manual_enable_only 或隔离 |
| 影响现有 Agent | 独立 memory 空间，隔离性验证 |
| 扩容失败 | 可随时 rollback |

---

## 更新记录

| 日期 | 变更 |
|-----|-----|
| 2026-03-17 | 初始版本，选择 scribe 和 merger |
