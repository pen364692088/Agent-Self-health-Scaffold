# MODULE_ARCHITECTURE.md

**版本**: v1.0  
**日期**: 2026-03-17  
**状态**: 正式模块架构文档

---

## 0. 模块总览

Agent-Self-health-Scaffold 收敛为 **四个主模块**：

```
Agent-Self-health-Scaffold/
├── memory_runtime/       # 持久化记忆与记忆恢复
├── execution_runtime/    # 可靠任务执行与执行前约束
├── health_runtime/       # 运行健康监控与异常恢复
└── agent_profiles/       # Agent 实例化配置与私有空间
```

---

## 1. memory_runtime/

### 职责

提供所有 Agent 的持久化记忆与记忆恢复能力。

### 子模块

| 子模块 | 职责 |
|--------|------|
| `session_bootstrap` | 新会话启动时的记忆加载入口 |
| `memory_loader` | 加载长期记忆、handoff、execution_state |
| `memory_writer` | 写回记忆、状态、handoff |
| `memory_resolver` | 解析记忆来源、分类、优先级 |
| `instruction_rules_resolver` | 解析长期指令规则 |
| `handoff_state_manager` | 管理会话交接状态 |
| `execution_state_manager` | 管理运行时执行状态 |
| `memory_evidence_logger` | 记录记忆操作证据链 |

### 负责的问题

- 新会话为什么会忘
- 记忆如何持久化
- 记忆如何恢复
- 长期规则如何被读取
- 如何保证记忆操作可审计

### 现有能力映射

| 目标 | 现有位置 | 操作 |
|------|----------|------|
| memory_loader | `core/memory/memory_recall.py` | 抽取接口 |
| memory_writer | `core/memory/memory_capture.py` | 抽取接口 |
| instruction_rules_resolver | 无 | 新建 |
| handoff_state_manager | `tools/handoff-create` | 整合 |
| execution_state_manager | 分散 | 新建统一加载器 |

---

## 2. execution_runtime/

### 职责

提供所有 Agent 的可靠任务执行能力。

### 子模块

| 子模块 | 职责 |
|--------|------|
| `task_runtime` | 任务生命周期管理 |
| `runtime_preflight` | 执行前检查（memory、repo、state） |
| `mutation_guard` | 变更约束与审计 |
| `canonical_source_guard` | 仓库/路径/状态源验证 |
| `repo_root_guard` | 仓库根目录保护 |
| `checkpoint_manager` | 检查点管理 |
| `retry_manager` | 重试策略管理 |
| `receipt_artifact_audit` | 执行凭证、产物、审计日志 |

### 负责的问题

- 为什么执行会跑偏
- 为什么会写错仓库/错文件
- 为什么会重复 create
- 为什么 task 结果不可审计

### 现有能力映射

| 目标 | 现有位置 | 操作 |
|------|----------|------|
| task_runtime | `runtime/step_executor.py` | 重命名 |
| runtime_preflight | `runtime/memory_preflight.py` | 整合 |
| mutation_guard | `runtime/mutation_gate.py` | 重命名 |
| canonical_source_guard | `core/canonical_adapter.py` | 抽取 |
| repo_root_guard | `runtime/repo_root_preflight.py` | 整合 |
| retry_manager | `core/execution/retry_policy.py` | 迁移 |

### 建议结构

```
execution_runtime/
├── __init__.py
├── task_runtime.py          # 从 runtime/step_executor.py 抽取
├── preflight.py             # 整合 memory_preflight + repo_root_preflight
├── mutation_guard.py        # 从 runtime/mutation_gate.py 迁移
├── canonical_guard.py       # 从 core/canonical_adapter.py 抽取
├── checkpoint.py            # 新建统一检查点管理
├── retry.py                 # 从 core/execution/retry_policy.py 迁移
└── receipt.py               # 从 schemas/execution_receipt 抽取运行时
```

---

## 3. health_runtime/

### 职责

提供所有 Agent 的运行健康监控与异常恢复能力。

### 子模块

| 子模块 | 职责 |
|--------|------|
| `session_health_monitor` | 会话健康监控 |
| `task_health_monitor` | 任务健康监控 |
| `memory_health_monitor` | 记忆健康监控 |
| `repo_health_monitor` | 仓库/工作区健康监控 |
| `drift_detector` | 状态漂移检测 |
| `self_healing_hooks` | 自愈触发钩子 |
| `block_warn_recovery_policy` | 阻断/警告/恢复策略 |

### 负责的问题

- 为什么 agent 停掉了
- 为什么状态漂移
- 为什么没加载记忆
- 为什么没按规则执行
- 为什么没写回状态

### 现有能力映射

| 目标 | 现有位置 | 操作 |
|------|----------|------|
| session_health_monitor | `tools/agent-health-check` | 整合为模块 |
| drift_detector | `tools/context-budget-watcher` | 抽取接口 |
| self_healing_hooks | `tools/agent-self-heal` | 整合为框架 |
| block_warn_recovery_policy | `core/governor/risk_classifier.py` | 抽取 |

### 建议结构

```
health_runtime/
├── __init__.py
├── session_health.py        # 整合 agent-health-*
├── task_health.py           # 新建
├── memory_health.py         # 新建
├── repo_health.py           # 新建
├── drift_detector.py        # 抽取 context-budget-watcher 接口
├── self_healing.py          # 整合 agent-self-heal
└── policy.py                # 整合 risk_classifier + recovery_policy
```

---

## 4. agent_profiles/

### 职责

让不同 Agent 共用底座能力，但实例化自己的配置和记忆空间。

### Profile Schema

每个 Agent 必须定义：

| 字段 | 类型 | 说明 |
|------|------|------|
| `agent_id` | string | Agent 唯一标识 |
| `project_scope` | string | 项目范围 |
| `canonical_repo` | string | 主仓库路径 |
| `memory_root` | string | 私有记忆根目录 |
| `read_scopes` | list | 允许读取的范围 |
| `write_scopes` | list | 允许写入的范围 |
| `allow_mutation` | bool | 是否允许变更 |
| `allow_git` | bool | 是否允许 git 操作 |
| `allow_state_update` | bool | 是否允许状态更新 |
| `startup_mode` | enum | 启动模式 (auto/manual) |

### 建议结构

```
agent_profiles/
├── __init__.py
├── schema.py                # Profile schema 定义
├── loader.py                # Profile 加载器
├── validator.py             # Profile 验证器
└── templates/
    ├── default.yaml         # 默认 profile 模板
    └── examples/
        ├── main.yaml        # Main agent profile
        └── ceo.yaml         # CEO agent profile
```

### Agent 私有记忆空间

每个 Agent 实例化：

```
agents/
  <agent_id>/
    memory/
      long_term_memory.yaml
      instruction_rules.yaml
      handoff_state.yaml
      execution_state.yaml
    evidence/
```

---

## 5. 模块交互图

```
┌─────────────────────────────────────────────────────────────┐
│                        Agent 启动                            │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   agent_profiles/                            │
│              加载 agent_id + profile                         │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   memory_runtime/                            │
│   1. instruction_rules_resolver                              │
│   2. memory_loader (long_term_memory)                        │
│   3. handoff_state_manager                                   │
│   4. execution_state_manager                                 │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   execution_runtime/                         │
│   runtime_preflight → mutation_guard → task_runtime          │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    health_runtime/                           │
│   session_health + task_health + memory_health + repo_health│
│   drift_detector → self_healing_hooks                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 6. 模块职责边界

| 模块 | 输入 | 输出 | 边界 |
|------|------|------|------|
| `memory_runtime` | agent_id, profile | 记忆数据 | 只负责记忆，不负责执行 |
| `execution_runtime` | 任务描述 | 执行结果 | 只负责执行，不负责业务逻辑 |
| `health_runtime` | 状态快照 | 健康报告/恢复动作 | 只负责监控，不负责业务决策 |
| `agent_profiles` | agent_id | profile | 只负责配置，不负责运行时 |

---

## 7. 模块依赖关系

```
agent_profiles/
      │
      ▼
memory_runtime/
      │
      ▼
execution_runtime/
      │
      ▼
health_runtime/
```

依赖规则：
- 依赖单向向下
- 下层不依赖上层
- 同层模块不互相依赖

---

## 8. 与现有架构的关系

| 现有目录 | 新模块 | 操作 |
|----------|--------|------|
| `runtime/` | `execution_runtime/` | 重命名 + 整合 |
| `core/memory/` | `memory_runtime/` | 抽取接口层 |
| `core/governor/` | `health_runtime/policy.py` | 整合 |
| `tools/agent-health-*` | `health_runtime/session_health.py` | 整合 |
| `agents/` | 保留为角色文档 | 新建 `agent_profiles/` |

---

## 9. 迁移策略

### Phase B 执行顺序

1. **execution_runtime** - 重命名 `runtime/`，调整模块名
2. **memory_runtime** - 从 `core/memory/` 抽取接口，新建缺失组件
3. **health_runtime** - 新建模块，整合现有工具
4. **agent_profiles** - 新建 schema + 模板

### 不建议大搬家

- 保持 `runtime/` 的物理位置，只做逻辑重命名
- `core/memory/` 保持现有实现，抽取接口层
- 工具整合为模块入口，不删除原工具（兼容期）

---

## 10. 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-03-17 | 初始版本，定义四大模块 |

---

## 11. 参考

- `docs/SYSTEM_RESPONSIBILITY_BOUNDARY.md` - 系统职责边界
- `docs/ARCHITECTURE_MODULE_MAPPING_A0.md` - 现有能力映射
- `docs/ARCHITECTURE.md` - 现有架构文档（v2）
