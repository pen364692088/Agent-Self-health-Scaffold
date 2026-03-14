{
  "source_file": "/home/moonlight/.openclaw/workspace/memory.md",
  "source_size_bytes": 1730,
  "distilled_at": "2026-03-13T08:39:13.144483",
  "model": "baiduqianfancodingplan/qianfan-code-latest",
  "compression_ratio": "63.5%",
  "content": "## 核心要点\n- 子代理主入口：`subtask-orchestrate` (run/status/resume)。\n- 内存检索层级：主入口 `session-query`，兜底 `openviking find`，遵循最小范围原则。\n- 硬性规则：主链路为 `subtask-orchestrate` + `subagent-inbox`，归档含日志/摘要/索引/备份。\n- 维护原则：Bootstrap 仅留简版规则，历史细节存入 archive/OpenViking。\n- 压缩管道 v1.0 (2026-03-06)：S1 Shadow Validation 状态，Gate 0 通过，Gate 1 待定。\n- 执行策略 v1 (2026-03-09)：写入主入口 `safe-write`/`safe-replace`，`~/.openclaw` 禁用 `edit`。\n\n## 关键决策\n- 确立 `subtask-orchestrate` 为子代理正式主链路，废弃 `sessions_send` 作为关键回执。\n- 禁止在 `~/.openclaw/**` 使用 `edit` 工具，强制使用 `safe-write` 系列确保安全。\n\n## 重要结果\n- 上下文压缩管道 v1.0 Gate 0 已通过 (2026-03-06)。\n\n## 待办/下一步\n- 等待上下文压缩管道 Gate 1 验证结果。\n- 任务关闭前必须执行 Gate 检查。"
}