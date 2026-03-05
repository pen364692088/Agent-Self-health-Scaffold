# Orchestrator v2.0 验收清单

## 检查来源
`/home/moonlight/Desktop/BetterWork/CheckCallback.txt`

## AC 验收 ✅

| AC | 状态 | 说明 |
|----|------|------|
| 不依赖回调继续执行 | ✅ | join_all() 主动轮询 |
| 指数退避 | ✅ | 1s→2s→4s→...→20s + jitter |
| 显式回执 | ✅ | subtask_done() API |
| 邮箱兜底 | ✅ | reports/subtasks/*.done.json |
| 恢复机制 | ✅ | pending_subtasks.json 原子写入 |

## 隐性坑修复 ✅

| 问题 | 修复 |
|------|------|
| spawn_subtask 语义反了 | spawn_task() 返回 (task_id, run_id, session_key) |
| JSON 写一半崩溃 | tmp → fsync → rename 原子写入 |
| 多 orchestrator 同步轮询 | ±10% jitter |

## 工程级增强 ✅

| 增强 | 实现 |
|------|------|
| 统一 JSON Schema | RECEIPT_SCHEMA 定义 |
| 双层超时 | global + per_task_timeout |
| 幂等处理 | COMPLETED 状态忽略重复回执 |
| 降级路径 | timeout → retry → fail (待补充单体降级) |
| 4 CLI 命令 | list/join/resume/gc |
| 结构化日志 | events.jsonl |

## 文件清单

```
tools/orchestrator/
├── orchestrator.py         # 24KB - 核心引擎 v2.0
├── subagent_receipt.py     # 8KB  - 回执处理器 v2.0
├── orchestrator-cli        # 9KB  - CLI v2.0
├── ACCESS_GUIDE.md         # 6KB  - 接入指南
└── README.md               # 1KB  - 系统说明

tools/subtask-orchestrate   # 11KB - Wrapper v2.0

reports/
├── subtasks/               # 邮箱目录
└── orchestrator/
    └── events.jsonl        # 结构化事件日志
```

## 使用方式

### 我（Main Agent）自动遵循

```bash
# Step 1: 注册任务
subtask-orchestrate spawn "<task>" -m <model>
# 输出: TASK_ID=... RUN_ID=... SESSION_KEY=...

# Step 2: 实际 spawn
sessions_spawn runtime=subagent model=<model> task="<task>"

# Step 3: 主动 join
subtask-orchestrate join -t 300 --per-task 600

# Step 4: (subagent) 发送回执
subtask-orchestrate receipt <task_id> <run_id> -s "Summary"
```

### 自动触发条件

- ✅ 任何 spawn subagent 后 **必须** 使用
- ✅ 并行 subagent 时 **必须** 使用
- ✅ 长时间任务 **必须** 使用

## Commits

- `daf8c45` - v1.0 初始实现
- `1bb1d3e` - Wrapper + AGENTS.md 集成
- `264ea28` - v2.0 生产级增强

---
*验收时间: 2026-03-03 01:08 CST*
