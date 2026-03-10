# R3: 多入口重复建设收口计划

Date: 2026-03-10
Status: PLANNING
Priority: P2

---

## 背景

Gate 系列审计发现多处功能有多个入口，增加了维护复杂度和定义漂移风险。

---

## 问题清单

### 1. 记忆检索入口 (4 个)

| 入口 | 用途 | 状态 |
|------|------|------|
| `context-retrieve` | Context Compression 两级检索 | S1 专用 |
| `session-start-recovery` | 会话恢复时检索 | 自动化 |
| `session-query` | 统一检索入口 | 主入口 |
| `openviking find` | 语义检索兜底 | 底层 |

**当前推荐**:
```
1. session-query
2. 必要时 openviking find
```

**问题**:
- `context-retrieve` 与 `session-query` 职责重叠
- `session-start-recovery` 内部实现可能独立于主入口

---

### 2. 子代理创建入口 (3 个)

| 入口 | 用途 | 状态 |
|------|------|------|
| `subtask-orchestrate` | 正式编排入口 | 主入口 |
| `spawn-with-callback` | 底层 spawn + 回调 | 调试/维护 |
| `sessions_spawn` | OpenClaw 内置 API | 底层 |

**当前推荐**:
```
Preferred: subtask-orchestrate
Debug only: spawn-with-callback, sessions_spawn
```

**问题**:
- `spawn-with-callback` 标记为调试但仍有引用
- `sessions_spawn` 在 AGENTS.md 中被禁止直接使用

---

### 3. 状态写入入口 (3 个)

| 入口 | 用途 | 状态 |
|------|------|------|
| `state-write-atomic` | SESSION-STATE.md 原子写入 | 专用 |
| `safe-write` | 执行策略安全写入 | 主入口 |
| `safe-replace` | 执行策略安全替换 | 主入口 |

**当前推荐**:
```
~/.openclaw/** 写入:
  - safe-write
  - safe-replace
  - exec + heredoc
```

**问题**:
- `state-write-atomic` 与 `safe-write` 功能重叠
- 两者的策略检查机制不同

---

## 收口策略

### 原则

1. **不继续做零碎补丁扩散**
2. **统一入口，明确职责**
3. **底层入口保留但标记为 internal**
4. **更新文档消除歧义**

---

### Phase 1: 文档对齐 (Day 1)

**目标**: 在所有规则文件中明确入口层级

**任务**:
1. 更新 TOOLS.md，明确标注每个入口的层级
2. 更新 SOUL.md，移除歧义指引
3. 更新 memory.md，统一检索推荐

**输出**: `R3_DOCUMENT_ALIGNMENT.md`

---

### Phase 2: 入口标记 (Day 2-3)

**目标**: 在工具内部添加层级标记

**任务**:
1. 为每个工具添加 `--help` 层级说明
2. 为调试级工具添加 warning banner
3. 更新工具返回值，包含 `source` 字段

**输出**: `R3_ENTRY_MARKING.md`

---

### Phase 3: 依赖清理 (Day 4-5)

**目标**: 移除对调试入口的不当引用

**任务**:
1. 扫描所有对 `spawn-with-callback` 的引用
2. 扫描所有对 `sessions_spawn` 的直接调用
3. 更新或移除不当引用

**输出**: `R3_DEPENDENCY_CLEANUP.md`

---

### Phase 4: 验证 (Day 6-7)

**目标**: 验证收口效果

**任务**:
1. 运行全量测试
2. 检查是否有遗漏入口
3. 确认文档一致性

**输出**: `R3_VERIFICATION.md`

---

## 不做什么

1. **不删除底层工具** - 保留调试/维护能力
2. **不改变现有行为** - 只标记和文档化
3. **不强制迁移** - 允许逐步过渡
4. **不增加新入口** - 收口而非扩散

---

## 成功指标

| 指标 | 当前 | 目标 |
|------|------|------|
| 主入口明确度 | 部分 | 100% |
| 调试入口警告 | 0 | 100% |
| 文档一致性 | 部分 | 100% |
| 不当引用数 | 未知 | 0 |

---

## 风险

| 风险 | 影响 | 缓解 |
|------|------|------|
| 破坏现有工作流 | 中 | Phase 渐进执行 |
| 文档与代码不同步 | 低 | 持续验证 |
| 遗留脚本依赖旧入口 | 低 | 扫描后单独处理 |

---

## 下一步

1. 确认收口计划
2. 启动 Phase 1: 文档对齐
3. 每日进度汇报

---

## 参考

- `artifacts/health_audit/FINDINGS.md` - 问题发现
- `TOOLS.md` - 当前工具推荐
- `SOUL.md` - 核心规则
