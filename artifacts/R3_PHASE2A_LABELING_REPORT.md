# R3 Phase 2A Labeling Report

Date: 2026-03-10
Phase: 2A of 4
Status: ✅ COMPLETE

---

## 执行约束

**非行为改变型工作**:
- ✅ 工具内部添加层级标记
- ✅ 补充入口说明与调用关系
- ✅ 增加可观测性字段、日志标签、审计标识
- ✅ 继续文档与命名对齐

**禁止执行**:
- ❌ 修改默认路由逻辑
- ❌ 修改工具选择优先级
- ❌ 合并会改变 runtime 行为的入口
- ❌ 触碰 memory capture/recall 主逻辑
- ❌ 影响 Memory-LanceDB 观察窗结果

---

## 完成的工作

### 1. 工具层级映射 ✅

**输出**: `TOOL_LAYER_MAP.md`

**内容**:
- 定义了 6 个层级：MAIN, SPECIALIZED, LOW-LEVEL, DEBUG, DEPRECATED, INTERNAL
- 分类了 190+ 个工具
- 统计了各层级占比

**统计**:
| 层级 | 数量 | 占比 |
|------|------|------|
| MAIN | 12 | ~6% |
| SPECIALIZED | 35 | ~18% |
| LOW-LEVEL | 15 | ~8% |
| DEBUG | 60 | ~31% |
| INTERNAL | 70 | ~36% |
| DEPRECATED | 1 | ~1% |

---

### 2. 调用路径注释 ✅

**输出**: `CALLPATH_ANNOTATION_REPORT.md`

**内容**:
- 记录了 7 个主要调用链
- 定义了调用符号约定
- 说明了调用层级隔离规则
- 提供了可观测性建议

**主要调用链**:
1. 子代理编排
2. 记忆检索
3. 状态写入
4. 任务完成
5. Context Compression
6. Execution Policy
7. 自动化调用

---

### 3. 延期行为变更清单 ✅

**输出**: `DEFERRED_BEHAVIORAL_CHANGES.md`

**内容**:
- 记录了 6 个延期变更
- 说明了延期原因
- 定义了执行时机
- 提供了监控指标

**延期变更**:
| ID | 变更 | 状态 |
|----|------|------|
| D1 | 统一记忆检索路由 | ⏸️ DEFERRED |
| D2 | 子代理创建入口收口 | ⏸️ DEFERRED |
| D3 | 状态写入入口统一 | ⏸️ DEFERRED |
| D4 | Memory-Lancedb 增强 | ⏸️ FROZEN |
| D5 | Heartbeat 流程优化 | ⏸️ DEFERRED |
| D6 | 回执处理流程简化 | ⏸️ DEFERRED |

---

### 4. 工具层级标记 ✅

**已添加标记的工具**:

| 工具 | 层级 | 标记内容 |
|------|------|----------|
| `subtask-orchestrate` | MAIN | 子代理编排正式入口 |
| `session-query` | MAIN | 统一检索入口 |
| `safe-write` | MAIN | 安全文件写入 |
| `verify-and-close` | MAIN | 任务收尾入口 |
| `spawn-with-callback` | DEBUG | 调试用底层 spawn + 警告 |

**标记格式**:
```bash
#!/usr/bin/env python3
# LAYER: main
# PURPOSE: ...
# DOCS: TOOLS.md, SOUL.md
```

---

## 验证清单

- [x] 创建工具层级映射
- [x] 创建调用路径注释
- [x] 创建延期变更清单
- [x] 为 MAIN 工具添加层级标记
- [x] 为 DEBUG 工具添加警告标记
- [x] 所有工作为非行为改变型

---

## 未执行的工作（延后）

### Phase 2B: 工具返回值增强

**计划**:
- 为工具返回值添加 `layer` 字段
- 为工具返回值添加 `source` 字段

**原因**: 可能影响现有调用方，延后到观察窗结束

### Phase 2C: 日志格式统一

**计划**:
- 统一日志格式包含 `[LAYER:xxx]` 标签
- 添加审计标识字段

**原因**: 可能影响日志解析，延后到观察窗结束

---

## 下一步

### 可立即执行 (Phase 3)
- 扫描所有对调试入口的不当引用
- 更新文档引用

### 需延后执行
- 工具返回值增强
- 日志格式统一
- 任何行为改变型收口

---

## 输出物

```
artifacts/
├── TOOL_LAYER_MAP.md              # 工具层级映射
├── CALLPATH_ANNOTATION_REPORT.md  # 调用路径注释
├── DEFERRED_BEHAVIORAL_CHANGES.md # 延期变更清单
└── R3_PHASE2A_LABELING_REPORT.md  # 本报告
```

---

## 总结

**Phase 2A 完成**: 所有工作均为非行为改变型，不影响 Memory-LanceDB 观察窗。

**已标记工具**: 5 个关键工具添加了层级标记。

**已记录延期变更**: 6 个行为改变型变更延后到观察窗结束。

