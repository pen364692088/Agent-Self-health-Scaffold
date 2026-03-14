{
  "source_file": "/home/moonlight/.openclaw/workspace/memory.md",
  "source_size_bytes": 1730,
  "distilled_at": "2026-03-14T07:05:12.871887",
  "model": "baiduqianfancodingplan/qianfan-code-latest",
  "compression_ratio": "62.1%",
  "content": "## 核心要点\n- 子代理主入口：`subtask-orchestrate` (run/status/resume)。\n- 内存检索：主入口 `session-query`，兜底 `openviking find`，遵循最小范围原则。\n- 主链路定义：`subtask-orchestrate` + `subagent-inbox`，非 `sessions_send`。\n- 维护原则：Bootstrap 仅留简版规则/入口，历史细节存入 archive/OpenViking。\n- 用户原则：稳定优先，里程碑可回溯，数据任务走确定性流程。\n\n## 关键决策\n- 确立 `subtask-orchestrate` 为子代理正式主链路，`session-query` 为内存检索主入口。\n- 禁止在 `~/.openclaw/**` 使用 `edit` 工具，仅限 `safe-write`/`safe-replace`/`exec`。\n- Context Compression Pipeline v1.0 (2026-03-06) 进入 S1 Shadow Validation 状态。\n\n## 重要结果\n- Context Compression Pipeline Gate 0 已通过 (✅ PASSED)，Gate 1 待定 (⏳ PENDING)。\n\n## 待办/下一步\n- 任务关闭前必须通过 Gate 检查。\n- 推进 Context Compression Pipeline Gate 1 验证。"
}