{
  "source_file": "/home/moonlight/.openclaw/workspace/memory.md",
  "source_size_bytes": 1730,
  "distilled_at": "2026-03-13T10:19:23.435173",
  "model": "baiduqianfancodingplan/qianfan-code-latest",
  "compression_ratio": "61.5%",
  "content": "## 核心要点\n- 子代理编排主入口：`subtask-orchestrate` (run/status/resume)。\n- 记忆检索层级：主入口 `session-query`，兜底 `openviking find`，遵循最小范围原则。\n- 硬性规则：主链路为 `subtask-orchestrate` + `subagent-inbox`，本文件仅留简版规则。\n- Context Compression v1.0 (2026-03-06)：S1 Shadow Validation 状态，Gate 0 通过，Gate 1 待定。\n- Execution Policy v1 (2026-03-09)：写入主入口 `safe-write`/`safe-replace`，`~/.openclaw/**` 禁用 `edit`。\n\n## 关键决策\n- 确立 `subtask-orchestrate` 为正式主链路，废弃 `sessions_send` 作为关键回执。\n- 实施记忆检索最小化策略，禁止整库灌入 prompt。\n- 规定 `~/.openclaw/**` 目录禁用 `edit` 工具，强制使用安全写入工具。\n\n## 重要结果\n- Context Compression Pipeline v1.0：Gate 0 验证通过 (PASSED)，功能冻结。\n\n## 待办/下一步\n- 等待 Context Compression Pipeline Gate 1 验证结果。\n- 任务关闭前必须执行 Gate 检查。"
}