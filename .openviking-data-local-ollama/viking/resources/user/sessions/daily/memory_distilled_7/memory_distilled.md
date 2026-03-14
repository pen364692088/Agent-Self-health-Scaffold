{
  "source_file": "/home/moonlight/.openclaw/workspace/memory.md",
  "source_size_bytes": 1730,
  "distilled_at": "2026-03-13T20:30:21.301856",
  "model": "baiduqianfancodingplan/qianfan-code-latest",
  "compression_ratio": "64.7%",
  "content": "## 核心要点\n- 目的：仅作会话引导速查表，完整历史存于 OpenViking。\n- 子代理主入口：`subtask-orchestrate` (run/status/resume)。\n- 记忆检索：优先 `session-query`，兜底 `openviking find`，遵循最小范围原则。\n- 写入入口：主入口 `safe-write`/`safe-replace`，底层 `exec + heredoc`。\n- 检索触发：涉及历史决策、参数、配置、旧故障、协议细节时先检索。\n\n## 关键决策\n- 确立主链路为 `subtask-orchestrate` + `subagent-inbox`，不依赖 `sessions_send`。\n- `~/.openclaw/**` 目录禁用 `edit` 工具，任务关闭前必须过 Gate。\n- 维护策略：本文件仅保留简版规则，历史细节归档至外部，保持短小。\n\n## 重要结果\n- Context Compression v1.0 (2026-03-06)：S1 Shadow Validation 状态，Gate 0 ✅ 通过，Gate 1 ⏳ 待定。\n- Execution Policy v1 (2026-03-09)：定义写入工具层级与禁用规则。\n\n## 待办/下一步\n- 跟进 Context Compression Pipeline Gate 1 状态。"
}