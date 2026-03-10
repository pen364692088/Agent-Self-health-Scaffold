# Duplication Report - 重复建设报告

**审计日期**: 2026-03-09 21:25 CST

---

## 1. 记忆检索入口

### 现状

| 入口 | 位置 | 用途 | 状态 |
|------|------|------|------|
| context-retrieve | tools/ | 通用检索工具 | ✅ 主入口 |
| session-start-recovery | tools/ | 集成约束恢复 | ✅ 集成入口 |
| openviking find | CLI | 直接向量检索 | ⚠️ 底层 |
| session-query | tools/ | 会话历史检索 | ⚠️ 独立 |

### 分析

- **合理性**: context-retrieve 作为通用入口，session-start-recovery 作为特定场景入口
- **问题**: openviking find 和 session-query 是底层工具，不应被直接调用
- **建议**: 保持现状，但更新文档明确入口优先级

---

## 2. 子代理创建入口

### 现状

| 入口 | 位置 | 用途 | 状态 |
|------|------|------|------|
| subtask-orchestrate | tools/ | 正式编排入口 | ✅ 主入口 |
| sessions_spawn | OpenClaw API | 底层 spawn | ⚠️ 底层 |
| spawn-with-callback | tools/ | 带 callback 的 spawn | ⚠️ 底层 |

### 分析

- **合理性**: subtask-orchestrate 是正式入口
- **问题**: 12 个工具直接调用底层 API
- **建议**: 逐步迁移到 subtask-orchestrate

---

## 3. 状态持久化入口

### 现状

| 入口 | 位置 | 用途 | 状态 |
|------|------|------|------|
| state-write-atomic | tools/ | 原子写入 | ✅ 通用 |
| safe-write | tools/ | 受控写入 | ✅ 受限路径 |

### 分析

- **合理性**: 两个工具有不同用途
- **state-write-atomic**: 通用原子写入
- **safe-write**: 受 Execution Policy 约束的写入
- **建议**: 保持现状，职责清晰

---

## 4. 健康检查入口

### 现状

| 入口 | 位置 | 用途 | 状态 |
|------|------|------|------|
| policy-daily-check | tools/ | 每日策略检查 | ✅ |
| policy-doctor | tools/ | 策略系统诊断 | ✅ |
| session-state-doctor | tools/ | 会话状态诊断 | ✅ |
| continuity-doctor | tools/ | 连续性诊断 | ⚠️ 可能重复 |

### 分析

- **问题**: 多个 doctor 工具可能功能重叠
- **建议**: 合并或明确职责边界

---

## 5. 事件日志入口

### 现状

| 入口 | 位置 | 用途 | 状态 |
|------|------|------|------|
| continuity-event-log | tools/ | 连续性事件 | ✅ |
| state-journal-append | tools/ | 状态日志追加 | ⚠️ 可能重复 |

### 分析

- **问题**: 两个日志入口可能功能重叠
- **建议**: 统一到 continuity-event-log

---

## 总结

| 重复类型 | 严重程度 | 影响 | 建议 |
|----------|----------|------|------|
| 记忆检索 4 入口 | 低 | 维护复杂度 | 保持现状 |
| 子代理创建 3 入口 | 中 | 绕过主入口风险 | 逐步迁移 |
| 状态持久化 2 入口 | 无 | 职责清晰 | 保持现状 |
| 健康检查多 doctor | 低 | 可能重复 | 合并评估 |
| 事件日志 2 入口 | 低 | 可能重复 | 统一评估 |

**建议**: 优先处理子代理创建入口的统一
