# Autonomy Policy Layer (v3-E)

> 让系统拥有"默认自动推进"的能力，同时明确什么不能自动做

## 概述

Autonomy Policy Layer 是 Agent-Self-health-Scaffold 的 v3-E 特性，提供自治策略管理能力。它与现有的 RiskGate 协同工作，在风险评估基础上叠加策略规则，实现"默认自动推进，明确边界阻断"的能力。

## 核心概念

### 1. 三类动作

| 类型 | 说明 | 示例 |
|------|------|------|
| **Allowed** | 默认可自治的动作 | 读文档、跑测试、小范围代码修复 |
| **Approval-Required** | 需要人工确认的动作 | 大范围代码修改、部署操作 |
| **Forbidden** | 必须阻断的动作 | 大规模删除、修改 Gate 规则 |

### 2. 风险等级

| 等级 | 说明 | 默认处理 |
|------|------|----------|
| **Low** | 低风险，安全执行 | 允许自动执行 |
| **Medium** | 中等风险 | 允许执行但记录日志 |
| **High** | 高风险 | 需要审批 |
| **Critical** | 关键风险 | 阻断 |

### 3. 运行模式

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| **shadow** | 只记录不执行 | 测试、观察 |
| **guarded-auto** | 高风险需要审批 | 生产环境 |
| **full-auto** | 仅阻断关键风险 | 受控环境 |

### 4. 安全停止条件

触发安全停止后，系统进入保护状态，所有操作被暂停：
- 连续阻断超过阈值
- RiskGate 不可用
- 基线完整性被破坏
- 策略配置损坏
- 证据日志满

## 架构

```
┌─────────────────────────────────────────────────────────────┐
│                      Autonomy Policy Layer                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐   │
│  │   Allowed    │    │Approval-Req  │    │  Forbidden   │   │
│  │   Actions    │    │   Actions    │    │   Actions    │   │
│  └──────────────┘    └──────────────┘    └──────────────┘   │
│          │                  │                   │           │
│          └──────────────────┼───────────────────┘           │
│                             ▼                               │
│                  ┌──────────────────┐                       │
│                  │   Policy Decide  │                       │
│                  └──────────────────┘                       │
│                             │                               │
│                             ▼                               │
│                  ┌──────────────────┐                       │
│                  │ Safe-Stop Check  │                       │
│                  └──────────────────┘                       │
│                             │                               │
│                             ▼                               │
│                  ┌──────────────────┐                       │
│                  │    Risk Gate     │◄──── 集成             │
│                  └──────────────────┘                       │
│                             │                               │
│                             ▼                               │
│                  ┌──────────────────┐                       │
│                  │  Evidence Log    │                       │
│                  └──────────────────┘                       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## 决策流程

```
输入: action_type, operation, context
           │
           ▼
   ┌───────────────────┐
   │ Safe-Stop Check   │──── 触发 ───▶ SAFE_STOP
   └───────────────────┘
           │ 未触发
           ▼
   ┌───────────────────┐
   │ Forbidden Check   │──── 匹配 ───▶ BLOCK
   └───────────────────┘
           │ 未匹配
           ▼
   ┌───────────────────┐
   │  Risk Assessment  │──── CRITICAL ──▶ BLOCK
   └───────────────────┘
           │ LOW/MEDIUM/HIGH
           ▼
   ┌───────────────────┐
   │Approval-Req Check │──── 匹配 ───▶ REQUIRE_APPROVAL
   └───────────────────┘
           │ 未匹配
           ▼
   ┌───────────────────┐
   │  Allowed Check    │──── 匹配 ───▶ ALLOW_AUTO/ALLOW_WITH_LOG
   └───────────────────┘
           │ 未匹配
           ▼
   ┌───────────────────┐
   │  Default Policy   │──── 根据 mode 决定
   └───────────────────┘
```

## 使用示例

### 基本使用

```python
from runtime.autonomy_policy import AutonomyPolicy, ActionType

# 创建策略实例
policy = AutonomyPolicy()

# 检查动作是否允许
evidence = policy.decide(ActionType.READ_DOCUMENT.value)
print(evidence.decision)  # allow_auto

# 检查禁止动作
evidence = policy.decide(ActionType.MASS_DELETE.value)
print(evidence.decision)  # block
```

### 与操作描述结合

```python
from runtime.autonomy_policy import AutonomyPolicy, ActionType
from runtime.risk_gate import Operation

policy = AutonomyPolicy()

# 创建操作描述
operation = Operation(
    type="shell_command",
    description="Run tests",
    command="pytest tests/"
)

# 决策
evidence = policy.decide(ActionType.RUN_TEST.value, operation)
print(evidence.decision)  # allow_auto
print(evidence.risk_level)  # low
```

### 使用配置文件

```python
from runtime.autonomy_policy import AutonomyPolicy

# 从配置文件加载
policy = AutonomyPolicy(config_path="config/autonomy_policy.yaml")

# 获取策略摘要
summary = policy.get_policy_summary()
print(f"模式: {summary['mode']}")
print(f"允许动作数: {summary['allowed_actions_count']}")
print(f"禁止动作数: {summary['forbidden_actions_count']}")
```

### 动态修改策略

```python
policy = AutonomyPolicy()

# 添加允许动作
policy.add_allowed_action("custom_action")

# 添加禁止动作
policy.add_forbidden_action("dangerous_custom_action")

# 临时修改
from runtime.autonomy_policy import AutonomyPolicyContext

with AutonomyPolicyContext(policy, {"mode": "full-auto"}):
    # 在此上下文中使用 full-auto 模式
    evidence = policy.decide("some_action")

# 退出上下文后恢复原模式
```

### 快速决策

```python
from runtime.autonomy_policy import quick_decide, ActionType

# 快速决策
decision = quick_decide(ActionType.READ_DOCUMENT.value)
print(decision)  # allow_auto

# 指定模式
decision = quick_decide("unknown_action", mode="shadow")
print(decision)  # allow_with_log
```

## 默认动作列表

### 允许自动执行

| 动作 | 说明 |
|------|------|
| `read_document` | 读取文档 |
| `run_test` | 运行测试 |
| `small_code_fix` | 小范围代码修复 (< 50 行) |
| `write_report` | 写报告 |
| `task_split` | 任务拆分 |
| `task_schedule` | 任务调度 |
| `retry` | 重试失败操作 |
| `reclaim` | 回收资源 |
| `rollback` | 回滚到上一状态 |

### 需要审批

| 动作 | 说明 |
|------|------|
| `large_code_change` | 大范围代码修改 (> 50 行) |
| `external_api_call` | 外部 API 调用 |
| `new_feature_implement` | 新功能实现 |
| `deploy_operation` | 部署操作 |

### 禁止执行

| 动作 | 说明 |
|------|------|
| `mass_delete` | 大规模删除文件 (> 10 个文件) |
| `modify_gate_rules` | 修改 Gate 硬规则 |
| `destroy_baseline` | 破坏 baseline 受保护产物 |
| `external_destructive` | 外部高风险 destructive 操作 |
| `credential_operation` | 涉及敏感凭据操作 |
| `payment_operation` | 涉及支付操作 |
| `account_operation` | 涉及账号操作 |

## 与 RiskGate 的关系

### 集成方式

```
┌─────────────────────────────────────────────────────────────┐
│                    Autonomy Policy Layer                     │
│                                                              │
│   ┌─────────────────────────────────────────────────────┐   │
│   │                     决策逻辑                         │   │
│   │                                                      │   │
│   │   1. 检查 Safe-Stop Conditions                      │   │
│   │   2. 检查 Forbidden Actions                         │   │
│   │   3. 调用 RiskGate.assess() ──────────────────┐     │   │
│   │                                                │     │   │
│   └────────────────────────────────────────────────│─────┘   │
│                                                    │         │
│   ┌────────────────────────────────────────────────▼─────┐   │
│   │                    Risk Gate                          │   │
│   │                                                       │   │
│   │   - 模式匹配 (危险命令检测)                          │   │
│   │   - 关键文件检查                                     │   │
│   │   - 风险等级评估                                     │   │
│   │                                                       │   │
│   └───────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 不修改 Gate 规则

Autonomy Policy Layer 通过以下方式保持与 RiskGate 的边界：

1. **使用 RiskGate 进行风险评估**：不重新实现风险评估逻辑
2. **叠加策略规则**：在 RiskGate 结果之上应用策略规则
3. **可配置性**：策略通过配置文件管理，不修改 RiskGate 代码

## 配置说明

### 配置文件结构

```yaml
# 运行模式
mode: "guarded-auto"

# 允许的动作
allowed_actions:
  - read_document
  - run_test

# 禁止的动作
forbidden_actions:
  - mass_delete
  - modify_gate_rules

# 需要审批的动作
approval_required_actions:
  - large_code_change
  - deploy_operation

# 自定义规则
custom_rules:
  - action_type: "git_push"
    category: "approval_required"
    risk_threshold: "medium"
    conditions:
      blocked_branches:
        - "main"
        - "master"

# 安全停止条件
safe_stop_conditions:
  - name: "consecutive_blocks_exceeded"
    description: "连续被阻断的操作超过阈值"
    severity: "critical"
```

## 策略证据日志

每次决策都会生成策略证据，记录：
- 决策 ID
- 时间戳
- 动作类型
- 操作摘要
- 决策结果
- 风险等级
- 匹配规则

```json
{
  "evidence_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2026-03-15T12:00:00Z",
  "action_type": "read_document",
  "operation_summary": "Read documentation file",
  "decision": "allow_auto",
  "risk_level": "low",
  "matched_rules": ["allowed:read_document", "risk_assessment:low"],
  "context": {}
}
```

## 测试

运行测试：

```bash
pytest tests/test_autonomy_policy.py -v
```

测试覆盖：
- 基础功能测试
- 允许动作测试
- 禁止动作测试
- 审批动作测试
- 风险评估集成测试
- 安全停止条件测试
- 策略模式测试
- 证据日志测试
- 配置加载测试
- 边缘情况测试

## 最佳实践

### 1. 选择合适的模式

| 场景 | 推荐模式 |
|------|----------|
| 测试新策略 | shadow |
| 生产环境 | guarded-auto |
| 受控 CI/CD | full-auto |

### 2. 监控策略指标

```python
summary = policy.get_policy_summary()
if summary["consecutive_blocks"] > 0:
    print(f"警告: 连续阻断 {summary['consecutive_blocks']} 次")
```

### 3. 定期审查策略

- 检查 evidence log 中的决策分布
- 调整 allowed/forbidden/approval_required 列表
- 根据实际运行情况优化阈值

### 4. 使用上下文管理器

对于临时策略修改，使用 `AutonomyPolicyContext` 确保状态恢复：

```python
with AutonomyPolicyContext(policy, {"mode": "full-auto"}):
    # 执行高风险操作
    pass
# 自动恢复原模式
```

## 变更历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v3-E | 2026-03-15 | 初始实现：自治策略层 |

## 参考

- `runtime/risk_gate.py` - 风险门禁
- `config/autonomy_policy.yaml` - 策略配置
- `tests/test_autonomy_policy.py` - 测试套件
