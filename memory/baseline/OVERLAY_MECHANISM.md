# Agent-Specific Overlay Mechanism

## 概述

Agent-specific rules 通过 **overlay** 机制继承和扩展全局 baseline rules。

## 继承模型

```
Global Baseline Rules (不可覆盖部分)
         ↓
Global Baseline Rules (可覆盖部分)
         ↓
Agent-Specific Overlay Rules
         ↓
Effective Rules for Agent
```

## 规则优先级

1. **硬性约束 (hard_constraints)**: 全局定义，不可被 agent overlay 覆盖
2. **工作流规则 (workflow_rules)**: 全局定义默认值，可被 agent overlay 覆盖
3. **变更约束 (mutation_rules)**: 全局定义默认策略，agent overlay 可扩展
4. **隔离规则 (isolation_rules)**: 全局定义，不可被 agent overlay 覆盖

## Overlay 合并策略

### hard_constraints
- **合并方式**: 并集
- **冲突处理**: 全局优先
- **行为**: Agent 只能添加新约束，不能移除全局约束

### workflow_rules
- **合并方式**: 按 ID 合并
- **冲突处理**: Agent-specific 覆盖全局
- **行为**: Agent 可自定义工作流

### mutation_rules
- **合并方式**: 交集
- **冲突处理**: 更严格优先
- **行为**: Agent 的 allowed_paths 与全局 allowed_paths 取交集

### memory_rules
- **合并方式**: 并集
- **冲突处理**: Agent-specific 优先
- **行为**: Agent 可添加额外记忆规则

## Overlay 文件结构

Agent-specific overlay 文件位于:
```
memory/agents/{agent_id}/instruction_rules.yaml
```

### 示例: implementer overlay

```yaml
version: "1.0"
agent_id: implementer
base: global  # 继承全局 baseline

# Agent-specific workflow overlay
workflow_rules:
  - id: read-design-before-impl
    description: "实现前必须阅读设计文档"
    priority: 2
    override: true  # 标记为覆盖型

# Agent-specific mutation rules (与全局取交集)
mutation_rules:
  allowed_paths:
    - "src/"
    - "tests/"
  forbidden_paths:
    - "*.env"
    - "*.key"
```

## 解析流程

1. 加载全局 baseline rules
2. 加载 agent-specific overlay
3. 按 merge strategy 合并:
   - hard_constraints: 并集，全局优先
   - workflow_rules: 按 ID 合并，agent 优先
   - mutation_rules: 交集，更严格优先
   - memory_rules: 并集，agent 优先
4. 输出 effective rules

## 验证规则

- Overlay 文件必须声明 `base: global`
- Overlay 不能移除全局 hard_constraints
- Overlay 的 allowed_paths 必须是全局 allowed_paths 的子集
- Overlay 的 forbidden_paths 必须包含全局 forbidden_paths

## 实现参考

见 `core/instruction_rules_merger.py`
