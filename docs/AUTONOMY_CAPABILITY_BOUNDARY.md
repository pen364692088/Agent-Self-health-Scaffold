# Autonomy Capability Boundary

## 文档目的

明确系统当前自治能力边界，防止"能力描述跑在证据前面"。

---

## 允许宣称的能力

### 已验证的自治能力

| 能力 | 验证状态 | 证据 |
|------|----------|------|
| 可自动启动 | ✅ Verified | runtime/autonomous_runner.py + pilot_autonomous_v3d |
| 可自动扫描待办任务 | ✅ Verified | PendingTaskScanner 测试通过 |
| 可自动推进低风险任务 | ✅ Verified | artifacts/policy_evidence/allowed_evidence.json |
| 可自动处理部分常见失败 | ✅ Verified | config/failure_taxonomy.yaml + tests |
| 高风险动作会被阻断 | ✅ Verified | artifacts/policy_evidence/forbidden_evidence.json |
| 连续阻断触发安全停止 | ✅ Verified | artifacts/policy_evidence/safe_stop_evidence.json |
| 中断后可恢复执行 | ✅ Verified | pilot_autonomous_v3d 中断恢复验证 |
| 父子任务可编排 | ✅ Verified | pilot_v3b_parent_child |
| Slot/Lease 调度正常 | ✅ Verified | pilot_v3a_scheduling |

### 当前可支持的运行模式

| 模式 | 行为 | 推荐场景 |
|------|------|----------|
| shadow | 只观测，不执行高风险操作 | 新环境测试 |
| guarded-auto | 低风险自动执行，高风险需审批 | 生产环境推荐 |
| full-auto | 全自动执行 | 禁止默认启用 |

---

## 禁止宣称的能力

### 明确不支持的宣称

| 禁止宣称 | 原因 |
|----------|------|
| 可在任意问题上无人监管自动解决 | 当前验证仅覆盖有限场景 |
| 已达到生产级自治 | 缺乏长期稳定运行验证 |
| 可默认执行高风险 destructive 动作 | 与设计目标冲突 |
| 已完成全部 v3 并可长期稳定运行所有真实场景 | 仍需更多真实负载验证 |
| 可替代人工决策 | 系统设计为辅助而非替代 |
| 可保证 100% 任务成功率 | 任何系统都有失败可能 |

---

## 当前未覆盖的场景

### 技术边界

| 场景 | 当前状态 | 计划 |
|------|----------|------|
| 跨仓库操作 | 未验证 | 需要额外安全策略 |
| 长时间运行任务（>24h） | 未验证 | 需要持久化增强 |
| 高并发任务（>10 并行） | 部分验证 | 需要负载测试 |
| 外部 API 依赖 | 未验证 | 需要超时和重试策略 |
| 敏感数据处理 | 未验证 | 需要安全审计 |
| 多用户并发访问 | 未验证 | 需要隔离机制 |

### 验证边界

| 验证类型 | 已验证 | 未验证 |
|----------|--------|--------|
| 单元测试 | ✅ 158+ tests | - |
| 集成测试 | ✅ Pilot tasks | 长期运行测试 |
| 压力测试 | ⚠️ 部分 | 高并发场景 |
| 真实环境验证 | ⚠️ 有限 | 生产负载 |
| 长期稳定性 | ❌ 未验证 | 7-14 天观察期 |

---

## 验收标准说明

### Implemented vs Accepted

| 状态 | 定义 | 条件 |
|------|------|------|
| **Implemented** | 代码已落地，测试通过 | 有代码和测试文件 |
| **Accepted** | 验收通过，有公开证据 | 有 pilot task + gate_report + receipt |

### 各阶段状态

| 阶段 | 代码状态 | 验收状态 | 口径 |
|------|----------|----------|------|
| v3-A | ✅ Implemented | ✅ Accepted | pilot_v3a_scheduling 已公开 |
| v3-B | ✅ Implemented | ✅ Accepted | pilot_v3b_parent_child 已公开 |
| v3-C | ✅ Implemented | ✅ Accepted | pilot_v3c_failure_policy 已公开 |
| v3-D | ✅ Implemented | ✅ Accepted | pilot_autonomous_v3d 已公开 |
| v3-E | ✅ Implemented | ✅ Accepted | artifacts/policy_evidence 已公开 |

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-03-15 | 初始能力边界定义 |

---

## 审核要求

**在更新本文档前，必须确保：**

1. 新增的"允许宣称"能力有公开验收证据
2. 不删除任何"禁止宣称"项
3. 新增的"未覆盖场景"有明确的验证计划
4. 口径变更需与公开证据一致
