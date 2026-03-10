# R3 Document Alignment

Date: 2026-03-10
Phase: 1 of 4
Status: ✅ COMPLETE

---

## 完成的对齐操作

### 1. memory.md ✅

**修改内容**:
- 添加 "Memory Retrieval (入口层级)" 表格
- 明确 `session-query` 为主入口
- 明确 `openviking find` 为底层兜底
- 移除分散的检索推荐

**对齐前**:
```
# Memory retrieval
~/.openclaw/workspace/tools/session-query "<query>"
openviking find "<query>" -u viking://resources/user/memory/

推荐顺序：
1. `session-query`
2. 必要时 `openviking find`
```

**对齐后**:
```
## Memory Retrieval (入口层级)

| 层级 | 工具 | 用途 |
|------|------|------|
| 主入口 | `session-query` | 日常检索 |
| 底层兜底 | `openviking find` | session-query 不可用时 |
```

---

### 2. SOUL.md ✅

**修改内容**:
- 精简 Section 3 为引用
- 保持 Section 9 为详细规范

**对齐前**:
```
### 3) 写入规则
修改 `.openclaw` 目录下的文件时：
- 优先用 `exec` + shell / heredoc
- 避免脆弱的精确替换
- 共享规则文件保持短、小、单一职责
```

**对齐后**:
```
### 3) 写入规则
详见 **Section 9) ~/.openclaw/ 写入策略**
```

---

### 3. TOOLS.md ✅

**无需修改**:
- 已包含清晰的入口层级
- Low-level tools 明确标记
- 主入口优先级明确

---

## 入口层级统一

### 记忆检索

| 层级 | 工具 | 文档位置 |
|------|------|----------|
| 主入口 | `session-query` | TOOLS.md, memory.md |
| 底层兜底 | `openviking find` | TOOLS.md, memory.md |
| 专用 | `context-retrieve` | memory.md (S1) |

### 子代理编排

| 层级 | 工具 | 文档位置 |
|------|------|----------|
| 主入口 | `subtask-orchestrate` | TOOLS.md, SOUL.md, memory.md |
| 调试 | `spawn-with-callback` | TOOLS.md (marked) |
| 底层 | `sessions_spawn` | TOOLS.md (marked) |

### 状态写入

| 层级 | 工具 | 文档位置 |
|------|------|----------|
| 主入口 | `safe-write` | TOOLS.md, SOUL.md, memory.md |
| 主入口 | `safe-replace` | TOOLS.md, SOUL.md |
| 底层 | `exec + heredoc` | TOOLS.md, SOUL.md |
| 专用 | `state-write-atomic` | (专用场景) |

---

## 验证清单

- [x] TOOLS.md 入口层级明确
- [x] memory.md 检索入口统一
- [x] SOUL.md 写入规则精简
- [x] 所有文档使用一致术语

---

## Phase 1 完成

**成果**:
- 3 个文档对齐
- 入口层级术语统一
- 消除歧义指引

**下一步**: Phase 2 - 入口标记 (工具内部添加层级说明)
