# Agent Onboarding 规约文档

**版本**: 1.0  
**创建日期**: 2026-03-17  
**状态**: 已验证

---

## 概述

本文档定义了新 Agent 接入系统的标准化流程。通过工具化、自动化的 onboarding 能力，确保新 Agent 快速、可靠地接入。

---

## Onboarding 流程

### 1. 生成 Agent Profile

使用 `tools/agent_profile_generator.py`:

```bash
python tools/agent_profile_generator.py \
  --agent-id my_agent \
  --name "My Agent" \
  --role implementer \
  --pilot
```

**支持的角色**:
- `planner` - 规划型
- `implementer` - 执行型
- `verifier` - 验证型
- `merger` - 合并型
- `scribe` - 记录型
- `coordinator` - 协调型
- `specialist` - 专家型

### 2. 生成私有记忆空间

使用 `tools/memory_template_generator.py`:

```bash
python tools/memory_template_generator.py \
  --agent-id my_agent \
  --role implementer
```

**生成内容**:
- `instruction_rules.yaml` - 指令规则 overlay
- `handoff_state.yaml` - 交接状态
- `execution_state.yaml` - 执行状态
- `long_term/` - 长期记忆目录

### 3. 执行接入验证

使用 `tools/agent_onboarding_validator.py`:

```bash
python tools/agent_onboarding_validator.py --agent-id my_agent
```

**验证项**:
1. Schema 校验
2. Memory 完整性检查
3. 冷启动样本
4. 最小 E2E
5. 隔离性检查

---

## 规则继承模型

### 全局 Baseline

位置: `memory/baseline/instruction_rules.yaml`

包含:
- **hard_constraints**: 硬性边界约束，所有 Agent 必须遵守
- **workflow_rules**: 默认工作流规则，可被 overlay 覆盖
- **memory_rules**: 记忆持久化规则
- **mutation_rules**: 默认变更约束
- **isolation_rules**: 多 Agent 隔离规则

### Agent-Specific Overlay

位置: `memory/agents/{agent_id}/instruction_rules.yaml`

必须声明:
```yaml
version: "1.0"
agent_id: {agent_id}
base: global  # 继承全局 baseline
```

### 合并策略

| 规则类型 | 合并方式 | 冲突处理 |
|---------|---------|---------|
| hard_constraints | 并集 | 全局优先 |
| workflow_rules | 按 ID 合并 | Agent 优先 |
| memory_rules | 并集 | Agent 优先 |
| mutation_rules | 交集 | 更严格优先 |

---

## 验证清单

### ✅ Schema 校验

- [ ] Profile 文件存在
- [ ] 必需字段完整
- [ ] agent_id 格式正确
- [ ] role 有效

### ✅ Memory 完整性

- [ ] instruction_rules.yaml 存在
- [ ] handoff_state.yaml 存在
- [ ] execution_state.yaml 存在
- [ ] long_term/ 目录存在
- [ ] agent_id 匹配
- [ ] base: global 声明

### ✅ 冷启动样本

- [ ] Profile 加载成功
- [ ] Memory 空间创建成功
- [ ] Bootstrap 成功
- [ ] Rules 加载成功
- [ ] State 写回验证

### ✅ 最小 E2E

- [ ] Preflight 检查通过
- [ ] Mutation Guard 正常工作

### ✅ 隔离性检查

- [ ] 记忆空间独立
- [ ] 无文件交叉
- [ ] agent_id 隔离

---

## 工具参考

| 工具 | 用途 |
|-----|-----|
| `agent_profile_generator.py` | 生成 Agent Profile |
| `memory_template_generator.py` | 生成私有记忆空间模板 |
| `agent_onboarding_validator.py` | 验证接入合规性 |
| `instruction_rules_merger.py` | 合并 baseline + overlay |

---

## 禁止事项

- ❌ 不直接全量铺到所有 Agent
- ❌ 不跳过接入验证
- ❌ 不把所有规则硬编码到单个模板
- ❌ 不移除全局 hard_constraints
- ❌ 不提前做完整 health_runtime

---

## 示例：新 Agent 接入

```bash
# 1. 生成 profile
python tools/agent_profile_generator.py \
  --agent-id scribe \
  --name "Scribe" \
  --role scribe \
  --pilot

# 2. 生成 memory 模板
python tools/memory_template_generator.py \
  --agent-id scribe \
  --role scribe

# 3. 验证接入
python tools/agent_onboarding_validator.py --agent-id scribe

# 如果全部通过，Agent 即可接入系统
```

---

## 更新记录

| 日期 | 版本 | 变更 |
|-----|-----|-----|
| 2026-03-17 | 1.0 | 初始版本 |
