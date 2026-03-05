---
name: agentic-engineering
description: "Agentic Engineering 工程规范脚手架。测试导航、上下文记忆、并行分治、专业化分工、可重复性。当启动长任务、多agent协作、或需要可重复工作流时自动应用。"
version: 2.0.0
---

# Agentic Engineering Skill

**让长任务变得可控、可重复、可交接。**

> **注意**：此 skill 是 [LongRunKit](https://github.com/pen364692088/LongRunKit) 的 Agentic 扩展包装器。

## 自动触发条件

当任务符合以下**任一**条件时，自动应用此框架：

1. 用户明确说："长任务"、"多步骤"、"并行"、"多agent"
2. 任务需要 **3+ 文件修改** 或 **5+ 步骤**
3. 使用 cc-godmode 或其他多 agent 协作
4. 用户要求"可重复"、"可回放"
5. 任务涉及编译/测试/修复循环

## 使用方式

```bash
# 初始化项目
longrun init --project /path/to/project --with-agentic

# 测试
longrun test-smoke    # 10-30s
longrun test-fast     # 1-3min
longrun test-full     # comprehensive

# 进度管理
longrun checkpoint "note"
longrun status
longrun run-once

# 报告
longrun report "pytest tests/"
```

## 核心能力

| 能力 | 说明 |
|------|------|
| **测试导航** | smoke/fast/full 三层测试 |
| **上下文记忆** | STATUS/TODO/DECISIONS/HANDOFF |
| **并行分治** | worktree + oracle diff |
| **角色分工** | planner/implementer/verifier/scribe/merger |
| **可重复性** | seed + structured reports |

## 生成的目录结构

```
project/
├── scripts/         # agent_run.sh, worktree_new.sh, oracle_diff.sh
├── docs/            # STATUS, TODO, DECISIONS, HANDOFF, ROLES
├── agents/          # 5 role prompts
├── tests/           # test_smoke.sh, test_fast.sh, test_full.sh
├── reports/         # summary.json, full.log, run_meta.json
├── memory/          # checkpoints
├── logs/            # run-once logs
├── TASK.md          # 任务追踪
├── HEARTBEAT.md     # 心跳检查
└── .github/workflows/ci.yml
```

## 硬规则

1. 没有 failing test 不允许开始修复（纯重构/文档除外）
2. 终端不得刷屏：详细日志落盘到 `reports/full.log`
3. 每轮结束更新 `docs/STATUS.md`
4. 修改测试记录到 `docs/DECISIONS.md`
5. 并行时按所有权规范执行
6. 支持 SEED 确保可重复

## 与其他 Skill 协作

- **cc-godmode**: 多 agent 协作时，每个 agent 绑定角色 prompt
- **session-wrap-up**: 会话结束时调用 `longrun checkpoint`

## 安装位置

- CLI: `/home/moonlight/Project/Github/MyProject/LongRunKit/bin/longrun`
- 全局: `~/.local/bin/longrun`
- 扩展: `LongRunKit/extensions/agentic/`

---

_Powered by [LongRunKit v2.0](https://github.com/pen364692088/LongRunKit)_
