{
  "source_file": "/home/moonlight/.openclaw/workspace/memory.md",
  "source_size_bytes": 1730,
  "distilled_at": "2026-03-10T06:40:09.793227",
  "model": "baiduqianfancodingplan/qianfan-code-latest",
  "compression_ratio": "67.4%",
  "content": "## 核心要点\n- 主入口：`subtask-orchestrate` (run/status/resume)。\n- 检索层级：主 `session-query`，兜底 `openviking find`，遵循最小范围原则。\n- 维护原则：本文件仅保留简版入口，历史细节归档至外部。\n- 执行原则：稳定优先，里程碑可溯，数据/工具任务走确定性流程。\n\n## 关键决策\n- 确定主链路为 `subtask-orchestrate` + `subagent-inbox`，不依赖 `sessions_send`。\n- `~/.openclaw/**` 禁用 `edit` 工具，改用 `safe-write`/`safe-replace`。\n- Context Compression Pipeline v1.0 (2026-03-06) 进入 S1 Shadow Validation。\n\n## 重要结果\n- Context Compression Pipeline Gate 0: ✅ PASSED。\n- Execution Policy Framework v1 (2026-03-09) 定义写入层级。\n\n## 待办/下一步\n- Context Compression Pipeline Gate 1: ⏳ PENDING。"
}