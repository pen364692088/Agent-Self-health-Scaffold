{
  "source_file": "/home/moonlight/.openclaw/workspace/memory.md",
  "source_size_bytes": 1730,
  "distilled_at": "2026-03-13T15:04:36.409702",
  "model": "baiduqianfancodingplan/qianfan-code-latest",
  "compression_ratio": "62.9%",
  "content": "## 核心要点\n- 子代理主入口：`subtask-orchestrate` (run/status/resume)\n- 内存检索：主入口 `session-query`，兜底 `openviking find`，遵循最小范围原则\n- 硬性规则：主链路为 `subtask-orchestrate` + `subagent-inbox`，`sessions_send` 非关键回执\n- 维护原则：Bootstrap 仅留简版规则，历史细节归档至 OpenViking/docs\n- 上下文压缩 v1.0 (2026-03-06)：S1 状态，Gate 0 通过，Gate 1 待定，含专用工具链\n- 执行策略 v1 (2026-03-09)：写入主入口 `safe-write`/`safe-replace`，`~/.openclaw/**` 禁用 `edit`\n\n## 关键决策\n- 确立 `subtask-orchestrate` + `subagent-inbox` 为子代理正式主链路\n- 规定内存检索优先级：`session-query` > `openviking find`\n- 禁止在 `~/.openclaw/**` 使用 `edit` 工具，强制使用安全写入工具\n\n## 重要结果\n- 上下文压缩管道 v1.0 Gate 0 已通过 (2026-03-06)\n\n## 待办/下一步\n- 推进上下文压缩管道 Gate 1 验证\n- 任务关闭前必须通过 Gate 检查"
}