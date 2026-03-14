{
  "source_file": "/home/moonlight/.openclaw/workspace/memory.md",
  "source_size_bytes": 1730,
  "distilled_at": "2026-03-13T01:33:09.633757",
  "model": "baiduqianfancodingplan/qianfan-code-latest",
  "compression_ratio": "64.5%",
  "content": "## 核心要点\n- 子代理主入口：`subtask-orchestrate` (run/status/resume)\n- 内存检索：主用 `session-query`，兜底 `openviking find`，遵循最小范围原则\n- 硬性规则：主链路为 `subtask-orchestrate` + `subagent-inbox`，不依赖 `sessions_send` 作回执\n- 维护原则：Bootstrap 仅留简版规则，历史细节归档至 OpenViking\n- 上下文压缩 v1.0 (2026-03-06)：S1 状态，Gate 0 通过，Gate 1 待定\n- 执行策略 v1 (2026-03-09)：写入主入口 `safe-write`/`safe-replace`，`~/.openclaw/**` 禁用 `edit`\n\n## 关键决策\n- 确立 `subtask-orchestrate` 为正式主链路，避免使用 `sessions_send`\n- 内存检索采用分级策略，禁止整库灌入 prompt\n- `~/.openclaw/**` 目录强制使用 `safe-write` 系列工具，禁用 `edit`\n\n## 重要结果\n- 上下文压缩管道 v1.0 Gate 0 已通过 (2026-03-06)\n\n## 待办/下一步\n- 推进上下文压缩管道 Gate 1 验证\n- 任务关闭前执行 Gate 检查"
}