# Task: Context Compression Phase 0 - Schema Freeze

## Objective
创建上下文压缩系统的核心 schema 和政策文档。

## Deliverables

### 1. schemas/active_state.v1.schema.json
- 定义 session 常驻状态结构
- 包含字段：session_id, task_goal, mode, response_contract, open_loops, hard_constraints, recent_tools
- response_contract 必须包含：speaker_mode, core_points, must_not_upgrade

### 2. schemas/session_capsule.v1.schema.json
- 定义压缩 capsule 结构
- 包含字段：capsule_id, session_id, source_turn_range, topic, summary, decisions, open_loops, hard_constraints, entities, retrieval_keys, reconstructable, created_at

### 3. schemas/compression_event.v1.schema.json
- 定义压缩事件日志结构
- 包含字段：event_id, session_id, trigger, pressure_level, before, after, resident_kept, capsules_created, evicted_turn_ranges, vector_indexed, mode, created_at

### 4. schemas/budget_snapshot.v1.schema.json
- 定义预算快照结构
- 包含字段：snapshot_id, session_id, estimated_tokens, ratio, pressure_level, threshold_type, created_at

### 5. POLICIES/CONTEXT_COMPRESSION.md
- 提取方案文档中的核心原则（P1-P6）
- 定义三层上下文模型（Resident/Active/Recall）
- 定义压缩分类策略（必须保留/应保留原文/应压缩/可入向量库/可淘汰）
- 定义阈值（70%/85%/92%）

## Constraints
- 所有 schema 必须是有效的 JSON Schema draft-07
- 政策文档必须简洁（<200行）
- 使用 $id, $schema, type, required, properties, additionalProperties

## Verification
- `jq empty schemas/*.schema.json` 通过
- 政策文件存在且可读

## Output
完成后列出所有创建的文件路径。
