# Memory Bootstrap (Minimal)

**Purpose**: session bootstrap cheat sheet only. Full history lives in indexed memory/OpenViking.

## Core tools
```bash
# Preferred subagent orchestration
~/.openclaw/workspace/tools/subtask-orchestrate run "<task>" -m baiduqianfancodingplan/qianfan-code-latest
~/.openclaw/workspace/tools/subtask-orchestrate status
~/.openclaw/workspace/tools/subtask-orchestrate resume

# Memory retrieval
~/.openclaw/workspace/tools/session-query "<query>"
openviking find "<query>" -u viking://resources/user/memory/
```

## Hard rules
- 子代理正式主链路：`subtask-orchestrate` + `subagent-inbox`
- 不把 `sessions_send` 当关键完成回执主链路
- 先检索最小范围，再读取最小片段
- 不在 bootstrap 文件里堆历史细节
- 归档 = 每日日志 + bootstrap 摘要 + 索引/向量归档 + 顶层备份提交

## Retrieval triggers
以下情况先检索：
- 历史决策
- 参数/阈值
- 配置位置
- 旧故障模式
- 协议细节

推荐顺序：
1. `session-query`
2. 必要时 `openviking find`

## User/project reminders
- 稳定优先于花哨
- 重要里程碑要能回溯证据
- 数据/工具类任务优先走确定性流程

## Maintenance rule
如果新增内容：
- 规则/入口：这里只留简版
- 历史/细节：写到 archive、docs、POLICIES 或 OpenViking
- 目标：保持这个文件短小、可快速注入
