# ARCHITECTURE_MODULE_MAPPING_A0.md

**版本**: A0 (轻量评估)  
**日期**: 2026-03-17  
**目的**: 现有代码 → 目标模块映射，区分"能力缺失"与"能力分散"

---

## 评估结论

| 目标模块 | 状态 | 说明 |
|----------|------|------|
| `memory_runtime/` | ⚠️ 分散 | 能力已存在，散落在 core/memory/, memory/, tools/ |
| `execution_runtime/` | ⚠️ 部分模块化 | runtime/ 已有核心能力，命名和组织需调整 |
| `health_runtime/` | ❌ 缺失 | 仅有单点工具（agent-health-*），无统一监控层 |
| `agent_profiles/` | ❌ 缺失 | agents/ 是角色定义文档，非 profile schema |

---

## 1. memory_runtime/ 映射

### 目标能力 vs 现有位置

| 目标能力 | 现有位置 | 状态 | 备注 |
|----------|----------|------|------|
| session_bootstrap | `tools/session-bootstrap-retrieve` | ✅ 存在 | 独立脚本，需标准化入口 |
| memory_loader | `core/memory/memory_recall.py`, `memory_search.py`, `memory_service.py` | ✅ 存在 | 已模块化，在 core/memory/ |
| memory_writer | `core/memory/memory_capture.py`, `memory_lifecycle.py` | ✅ 存在 | 已模块化，在 core/memory/ |
| memory_resolver | `core/memory/source_mapper.py`, `truth_classifier.py` | ✅ 存在 | 需统一接口 |
| instruction_rules_resolver | `memory/*.md` (markdown 文件) | ⚠️ 分散 | 无统一 resolver，规则散落在文档 |
| handoff_state_manager | `tools/handoff-create`, `handoff.md` | ⚠️ 部分 | 工具存在，但无统一状态管理器 |
| execution_state_manager | `SESSION-STATE.md`, `artifacts/tasks/*/state/` | ⚠️ 分散 | 状态文件分散，无统一加载器 |
| memory_evidence_logger | `core/memory/recall_trace.py` | ⚠️ 部分 | 有 trace，但证据链不完整 |

**结论**: 能力已存在，但缺少统一入口层。建议：
1. 新增 `memory_runtime/` 目录
2. 从 `core/memory/` 抽取核心模块
3. 统一 instruction_rules_resolver
4. 新增 execution_state_manager 统一加载器

---

## 2. execution_runtime/ 映射

### 目标能力 vs 现有位置

| 目标能力 | 现有位置 | 状态 | 备注 |
|----------|----------|------|------|
| task_runtime | `runtime/step_executor.py`, `runtime/step_scheduler.py` | ✅ 存在 | 已模块化 |
| runtime_preflight | `runtime/memory_preflight.py`, `runtime/repo_root_preflight.py` | ✅ 存在 | 已模块化 |
| mutation_guard | `runtime/mutation_gate.py` | ✅ 存在 | 已模块化 |
| canonical_source_guard | `core/canonical_adapter.py`, `config/canonical_repos.yaml` | ✅ 存在 | 配置驱动，adapter 存在 |
| repo_root_guard | `tools/repo-root-guard`, `runtime/repo_root_preflight.py` | ✅ 存在 | 工具+运行时双实现 |
| checkpoint_manager | 分散在多处 | ⚠️ 分散 | 有 checkpoint 逻辑，但无统一管理器 |
| retry_manager | `core/execution/retry_policy.py` | ✅ 存在 | 已模块化 |
| receipt/artifact/audit | `schemas/execution_receipt.schema.json`, `artifacts/` | ✅ 存在 | schema 和目录都有 |

**结论**: `runtime/` 目录已承担大部分职责，但：
1. 命名不完全符合目标（如 `mutation_gate` vs `mutation_guard`）
2. checkpoint 缺少统一管理器
3. 建议重命名/重组而非新建

---

## 3. health_runtime/ 映射

### 目标能力 vs 现有位置

| 目标能力 | 现有位置 | 状态 | 备注 |
|----------|----------|------|------|
| session_health_monitor | `tools/agent-health-check`, `tools/agent-health-snapshot` | ⚠️ 单点工具 | 有检查脚本，无持续监控层 |
| task_health_monitor | 分散 | ❌ 缺失 | 无统一入口 |
| memory_health_monitor | 分散 | ❌ 缺失 | 无统一入口 |
| repo_health_monitor | 分散 | ❌ 缺失 | 无统一入口 |
| drift_detector | `tools/context-budget-watcher` 部分覆盖 | ⚠️ 部分 | 有 budget watcher，但无通用 drift detector |
| self_healing_hooks | `tools/agent-self-heal`, `tools/agent-recovery-*` | ⚠️ 单点工具 | 有自愈工具，但无统一 hook 框架 |
| block/warn/recovery_policy | `docs/RECOVERY_POLICY.md`, `core/governor/risk_classifier.py` | ⚠️ 部分 | 有文档和分类器，但无统一 policy 执行层 |

**结论**: 
1. **真缺失**：无统一的 `health_runtime/` 模块
2. 现有工具是单点脚本，不是可组合的 runtime 层
3. 需要新建模块，整合现有工具为统一监控框架

---

## 4. agent_profiles/ 映射

### 目标能力 vs 现有位置

| 目标能力 | 现有位置 | 状态 | 备注 |
|----------|----------|------|------|
| agent_id | `agents/implementer.md`, `agents/planner.md` 等 | ❌ 不匹配 | agents/ 是角色定义文档，非 profile schema |
| project_scope | `config/canonical_repos.yaml` | ⚠️ 部分 | 有 repo 配置，但无 agent-scope 映射 |
| canonical_repo | `config/canonical_repos.yaml` | ✅ 存在 | 配置存在 |
| memory_root | 无 | ❌ 缺失 | 每个 agent 无独立 memory_root 定义 |
| read_scopes | 无 | ❌ 缺失 | 无 scope 定义 |
| write_scopes | 无 | ❌ 缺失 | 无 scope 定义 |
| allow_mutation | 无 | ❌ 缺失 | 无 per-agent 权限配置 |
| allow_git | 无 | ❌ 缺失 | 无 per-agent 权限配置 |
| allow_state_update | 无 | ❌ 缺失 | 无 per-agent 权限配置 |
| startup_mode | 无 | ❌ 缺失 | 无 per-agent 启动模式配置 |

**结论**: 
1. **真缺失**：无 agent profile schema
2. `agents/` 目录是角色文档，需要迁移/重定义
3. 需要新建 `agent_profiles/` + schema

---

## 5. 关键发现

### 真缺失 (需新建)

1. **health_runtime/** - 整个模块缺失
2. **agent_profiles/** - 整个模块缺失
3. **instruction_rules_resolver** - 无统一规则解析器
4. **execution_state_manager** - 无统一状态加载器
5. **checkpoint_manager** - 无统一 checkpoint 管理

### 能力分散 (需整合)

1. **memory_runtime** 核心能力在 `core/memory/`，但 instruction/state 管理分散
2. **health 监控** 以单点工具存在，无统一框架

### 已模块化 (可重命名/调整)

1. **execution_runtime** 的大部分能力已在 `runtime/` 中
2. **memory 核心层** 在 `core/memory/` 中已模块化

---

## 6. 重构策略建议

### Phase B 执行顺序

| 优先级 | 模块 | 策略 |
|--------|------|------|
| P0 | execution_runtime | 重命名 `runtime/` → `execution_runtime/`，调整命名 |
| P1 | memory_runtime | 抽取 `core/memory/` + 新增 instruction/state 管理器 |
| P2 | health_runtime | 新建模块，整合现有单点工具 |
| P3 | agent_profiles | 新建 schema + 模板 |

### 不建议大搬家

1. `runtime/` 已有良好组织，建议原地调整为 `execution_runtime/`
2. `core/memory/` 已模块化，建议抽接口层而非物理迁移
3. `agents/` 保留为角色文档，新建 `agent_profiles/` 为配置层

---

## 7. Gate A 准备状态

| Gate A 要求 | 当前状态 | 阻塞项 |
|-------------|----------|--------|
| 系统职责边界文档存在 | ❌ 缺失 | 需新建 `docs/SYSTEM_RESPONSIBILITY_BOUNDARY.md` |
| 模块划分文档存在 | ⚠️ 部分 | 有 `docs/ARCHITECTURE.md`，但无新模块架构图 |
| Scaffold/EgoCore/OpenEmotion 边界明确 | ⚠️ 部分 | 有口头共识，无正式文档 |
| Memory/Execution/Health 三层职责明确 | ⚠️ 部分 | Memory/Execution 有实现，Health 缺失 |

**结论**: Gate A 可在 A0 完成后立即推进。

---

## 8. 下一步

Phase A 任务：
1. 输出 `docs/SYSTEM_RESPONSIBILITY_BOUNDARY.md`
2. 更新 `docs/MODULE_ARCHITECTURE.md`（基于本映射）

完成后进入 Phase B 抽取公共层。
