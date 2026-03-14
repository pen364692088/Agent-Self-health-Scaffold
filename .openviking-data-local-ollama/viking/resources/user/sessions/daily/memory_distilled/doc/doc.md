{
  "source_file": "/home/moonlight/.openclaw/workspace/memory.md",
  "source_size_bytes": 1730,
  "distilled_at": "2026-03-13T03:24:08.624265",
  "model": "baiduqianfancodingplan/qianfan-code-latest",
  "compression_ratio": "70.3%",
  "content": "## 核心要点\n- 子代理主入口：`subtask-orchestrate` (run/status/resume)\n- 内存检索：主入口 `session-query`，兜底 `openviking find`，遵循最小化原则\n- 归档与维护：日志+摘要+索引+备份；本文件仅留简版规则，细节归档\n- Context Compression v1.0 (2026-03-06)：S1 Shadow Validation，含专用工具链\n- Execution Policy v1 (2026-03-09)：写入主入口 `safe-write`/`safe-replace`\n\n## 关键决策\n- 确立 `subtask-orchestrate` + `subagent-inbox` 为正式主链路\n- `~/.openclaw/**` 禁用 `edit` 工具，任务关闭前须过 Gate\n\n## 重要结果\n- Context Compression Gate 0: ✅ PASSED；Gate 1: ⏳ PENDING\n\n## 待办/下一步\n- 推进 Context Compression Pipeline Gate 1 验证"
}