# Memory Bootstrap (Minimal)

**Purpose**: session bootstrap cheat sheet only. Full history lives in indexed memory/OpenViking.

---

## Subagent Orchestration (主入口)

```bash
# 正式入口
~/.openclaw/workspace/tools/subtask-orchestrate run "<task>" -m <model>
~/.openclaw/workspace/tools/subtask-orchestrate status
~/.openclaw/workspace/tools/subtask-orchestrate resume
```

---

## Memory Retrieval (入口层级)

| 层级 | 工具 | 用途 |
|------|------|------|
| 主入口 | `session-query` | 日常检索 |
| 底层兜底 | `openviking find` | session-query 不可用时 |

**使用规则**:
1. 先 `session-query`
2. 必要时 `openviking find`
3. 先检索最小范围，再读取最小片段
4. 不整库灌入 prompt

---

## Hard Rules

- 子代理正式主链路：`subtask-orchestrate` + `subagent-inbox`
- 不把 `sessions_send` 当关键完成回执主链路
- 不在 bootstrap 文件里堆历史细节
- 归档 = 每日日志 + bootstrap 摘要 + 索引/向量归档 + 顶层备份提交

---

## Retrieval Triggers

以下情况先检索：
- 历史决策
- 参数/阈值
- 配置位置
- 旧故障模式
- 协议细节

---

## User/Project Reminders

- 稳定优先于花哨
- 重要里程碑要能回溯证据
- 数据/工具类任务优先走确定性流程

---

## Maintenance Rule

如果新增内容：
- 规则/入口：这里只留简版
- 历史/细节：写到 archive、docs、POLICIES 或 OpenViking
- 目标：保持这个文件短小、可快速注入

---

## Context Compression Pipeline v1.0 (2026-03-06)

**状态**: S1 Shadow Validation (Feature Frozen)
**Gate 0**: ✅ PASSED
**Gate 1**: ⏳ PENDING

**专用工具** (S1 专用，非通用入口):
```bash
tools/context-budget-check    # Token 压力估算
tools/capsule-builder         # 结构化胶囊提取
tools/context-compress        # 压缩执行器
tools/context-retrieve        # 两级检索 (S1 专用)
tools/prompt-assemble         # Prompt 组装器
```

---

## Execution Policy Framework v1 (2026-03-09)

**写入入口** (详见 TOOLS.md):
| 层级 | 工具 | 用途 |
|------|------|------|
| 主入口 | `safe-write` | 完整文件写入 |
| 主入口 | `safe-replace` | 精确内容替换 |
| 底层 | `exec + heredoc` | Shell 写入 |

**关键规则**:
- `~/.openclaw/**` 禁用 `edit` 工具
- 任务关闭前必须过 Gate
