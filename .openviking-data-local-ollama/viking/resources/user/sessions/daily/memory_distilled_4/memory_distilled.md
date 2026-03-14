{
  "source_file": "/home/moonlight/.openclaw/workspace/memory.md",
  "source_size_bytes": 1730,
  "distilled_at": "2026-03-13T15:03:22.342294",
  "model": "baiduqianfancodingplan/qianfan-code-latest",
  "compression_ratio": "60.9%",
  "content": "## 核心要点\n- 定位：会话引导速查表，完整历史存于 OpenViking。\n- 子代理入口：`subtask-orchestrate` (run/status/resume)。\n- 检索策略：主入口 `session-query`，兜底 `openviking find`，遵循最小范围原则。\n- 主链路：`subtask-orchestrate` + `subagent-inbox`，非 `sessions_send`。\n- 维护原则：本文件仅保留简版规则/入口，细节存入归档。\n- 写入工具：主入口 `safe-write`/`safe-replace`，底层 `exec`。\n- 写入限制：`~/.openclaw/**` 禁用 `edit` 工具。\n- 检索触发：决策、参数、配置、故障、协议等场景。\n\n## 关键决策\n- 确立 `subtask-orchestrate` 为子代理唯一正式主链路。\n- 禁止整库灌入 prompt，强制最小化检索范围。\n- 禁止在 bootstrap 文件堆砌历史细节，保持短小。\n\n## 重要结果\n- Context Compression Pipeline v1.0 (2026-03-06)：S1 状态，Gate 0 ✅，Gate 1 ⏳。\n- Execution Policy Framework v1 (2026-03-09)：定义写入层级与工具。\n\n## 待办/下一步\n- 任务关闭前必须过 Gate。\n- 关注 Context Compression Pipeline Gate 1 状态。"
}