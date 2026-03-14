{
  "source_file": "/home/moonlight/.openclaw/workspace/memory.md",
  "source_size_bytes": 1730,
  "distilled_at": "2026-03-13T22:18:34.526487",
  "model": "baiduqianfancodingplan/qianfan-code-latest",
  "compression_ratio": "55.7%",
  "content": "## 核心要点\n- **目的定位**：仅作会话引导速查表，完整历史存于 OpenViking。\n- **编排入口**：主入口为 `subtask-orchestrate` (run/status/resume)。\n- **检索策略**：优先 `session-query`，兜底 `openviking find`，遵循最小范围/片段原则。\n- **硬性规则**：主链路为 `subtask-orchestrate` + `subagent-inbox`，禁用 `sessions_send` 作回执。\n- **维护原则**：规则留简版，细节归档，保持文件短小可注入。\n- **压缩管道 v1.0 (2026-03-06)**：处于 S1 Shadow Validation，Gate 0 通过，Gate 1 待定。\n- **执行策略 v1 (2026-03-09)**：写入主入口 `safe-write`/`safe-replace`，`~/.openclaw/**` 禁用 `edit`。\n\n## 关键决策\n- 确立 `subtask-orchestrate` + `subagent-inbox` 为正式主链路，摒弃 `sessions_send` 作为关键回执。\n- 实施两级检索机制，防止整库灌入 prompt 导致上下文溢出。\n- 在 `~/.openclaw/**` 目录下禁用 `edit` 工具，强制使用安全写入接口。\n\n## 重要结果\n- Context Compression Pipeline v1.0 Gate 0 已通过 (2026-03-06)。\n\n## 待办/下一步\n- 推进 Context Compression Pipeline Gate 1 验证。\n- 任务关闭前必须通过 Gate 检查。"
}