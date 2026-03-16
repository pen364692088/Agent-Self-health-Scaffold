# Phase A: 两入口缺口核实报告

**执行时间**: 2026-03-16T22:15:00Z
**状态**: ✅ 完成

---

## 1. 核实目标

对 `spawn-with-callback` 与 `memory-scope-router` 两个入口进行真实治理缺口核实。

---

## 2. Entry-020: spawn-with-callback

### 2.1 基本信息

| 字段 | 值 |
|------|-----|
| entry_id | entry-020 |
| entry_path | tools/spawn-with-callback |
| class | P1 |
| status | pending_fix |
| 工具用途 | 调试用底层 spawn，创建带回调的子任务 |
| 工具层级 | debug |
| 警告 | 不推荐直接使用，请用 subtask-orchestrate |

### 2.2 当前治理状态

| 治理项 | 状态 |
|--------|------|
| policy_bind_connected | ❌ false |
| guard_connected | ❌ false |
| hard_judge_connected | ❌ false |
| boundary_checked | ❌ false |
| preflight_covered | ❌ false |
| ci_covered | ❌ false |

### 2.3 实际缺口分析

**风险等级**: 中风险 - 可直接触发子代理执行

**缺口列表**:
1. `policy_bind_not_connected` - 未接入策略绑定
2. `guard_not_connected` - 未接入 guard 保护
3. `boundary_not_checked` - 未检查边界

**已有治理**:
- ✅ 双通道回调机制（sessions_send + subagent-inbox）
- ✅ 自动识别 parent_session_key
- ✅ 超时控制（timeout 参数）

**缺失治理**:
- ❌ 没有检查是否允许 spawn
- ❌ 没有检查子代理数量限制
- ❌ 没有边界检查（如资源限制）

### 2.4 建议补齐

| 治理项 | 建议值 | 理由 |
|--------|--------|------|
| policy_bind_connected | **true** | P1 入口必须有策略绑定 |
| guard_connected | **true** | 可触发子代理执行，需要 guard |
| hard_judge_connected | **false** | P1 入口不强制 hard_judge |
| boundary_checked | **true** | 需要边界检查（资源限制） |
| preflight_covered | **false** | 非必需 |
| ci_covered | **false** | 非必需 |

---

## 3. Entry-021: memory-scope-router

### 3.1 基本信息

| 字段 | 值 |
|------|-----|
| entry_id | entry-021 |
| entry_path | tools/memory-scope-router |
| class | P1 |
| status | pending_fix |
| 工具用途 | 轻量主题路由器，识别用户消息涉及的 scope |
| 工具层级 | auxiliary |
| 警告 | 无 |

### 3.2 当前治理状态

| 治理项 | 状态 |
|--------|------|
| policy_bind_connected | ❌ false |
| guard_connected | ❌ false |
| hard_judge_connected | ❌ false |
| boundary_checked | ❌ false |
| preflight_covered | ❌ false |
| ci_covered | ❌ false |

### 3.3 实际缺口分析

**风险等级**: 低风险 - 只做 scope 识别，不执行写操作

**功能特点**:
- 纯读取操作
- 基于关键词匹配识别 scope
- 无副作用
- 无资源消耗

**缺口列表**:
1. `policy_bind_not_connected` - 未接入策略绑定
2. `boundary_not_checked` - 未检查边界

**已有治理**:
- ✅ 纯函数实现，无副作用
- ✅ 无外部依赖

**缺失治理**:
- ❌ 没有策略绑定（P1 入口必须有）

### 3.4 建议补齐

| 治理项 | 建议值 | 理由 |
|--------|--------|------|
| policy_bind_connected | **true** | P1 入口必须有策略绑定 |
| guard_connected | **false** | 只做识别，无风险 |
| hard_judge_connected | **false** | P1 入口不强制 hard_judge |
| boundary_checked | **true** | 需要边界检查（输入验证） |
| preflight_covered | **false** | 非必需 |
| ci_covered | **false** | 非必需 |

---

## 4. 缺口汇总

### 4.1 共同缺口

| 缺口 | spawn-with-callback | memory-scope-router |
|------|---------------------|---------------------|
| policy_bind_not_connected | ✅ 缺失 | ✅ 缺失 |
| boundary_not_checked | ✅ 缺失 | ✅ 缺失 |

### 4.2 差异缺口

| 缺口 | spawn-with-callback | memory-scope-router |
|------|---------------------|---------------------|
| guard_not_connected | ✅ 缺失（需补） | ❌ 不需（低风险） |

### 4.3 hard_judge 状态

**两者均不需要 hard_judge**：
- spawn-with-callback: P1 入口，不强制
- memory-scope-router: P1 入口 + 低风险，不强制

---

## 5. 补齐计划

### 5.1 spawn-with-callback

1. 接入 policy_bind（策略绑定）
2. 接入 guard（执行保护）
3. 添加 boundary check（边界检查）

### 5.2 memory-scope-router

1. 接入 policy_bind（策略绑定）
2. 添加 boundary check（边界检查）

---

## 6. 交付物

| 产物 | 路径 |
|------|------|
| 两入口当前状态 JSON | artifacts/registry_closure_final/two_entries_current_state.json |
| 缺口核实报告 | artifacts/registry_closure_final/two_entries_gap_report.md |

---

**交付人**: Manager (Coordinator AI)
**交付时间**: 2026-03-16T22:15:00Z
