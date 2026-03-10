{
  "source_file": "/home/moonlight/.openclaw/workspace/memory.md",
  "source_size_bytes": 1730,
  "distilled_at": "2026-03-10T05:59:02.547692",
  "model": "baiduqianfancodingplan/qianfan-code-latest",
  "compression_ratio": "62.9%",
  "content": "## 核心要点\n- 主入口：`subtask-orchestrate` (run/status/resume) + `subagent-inbox`\n- 内存检索：主用 `session-query`，兜底 `openviking find`，遵循最小范围原则\n- 硬性规则：Bootstrap 仅留简版，历史细节归档至外部，不堆砌历史\n- 原则：稳定优先，里程碑需可回溯，数据任务走确定性流程\n- 压缩管道 v1.0 (2026-03-06)：S1 Shadow Validation 状态，Gate 0 已通过\n- 执行策略 v1 (2026-03-09)：主用 `safe-write/replace`，`~/.openclaw` 禁用 `edit` 工具\n\n## 关键决策\n- 确立 `subtask-orchestrate` + `subagent-inbox` 为正式主链路，替代 `sessions_send`\n- 禁止在 `~/.openclaw` 使用 `edit` 工具，强制使用 `safe-write` 系列以确保安全\n\n## 重要结果\n- Context Compression Pipeline v1.0 Gate 0: ✅ PASSED (2026-03-06)\n- Gate 1 状态: ⏳ PENDING\n\n## 待办/下一步\n- 推进 Context Compression Pipeline Gate 1 验证\n- 任务关闭前执行 Gate 检查"
}