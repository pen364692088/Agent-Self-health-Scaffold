{
  "source_file": "/home/moonlight/.openclaw/workspace/memory.md",
  "source_size_bytes": 1730,
  "distilled_at": "2026-03-13T20:29:28.904876",
  "model": "baiduqianfancodingplan/qianfan-code-latest",
  "compression_ratio": "53.6%",
  "content": "## 核心要点\n- 子代理入口：`subtask-orchestrate` (run/status/resume)。\n- 记忆检索：主入口 `session-query`，兜底 `openviking find`；遵循最小范围原则。\n- 硬性规则：主链路为 `subtask-orchestrate` + `subagent-inbox`；保持 bootstrap 短小。\n- 检索触发：涉及历史决策、参数、配置、故障、协议时先检索。\n- 项目原则：稳定优先，里程碑需证据，数据/工具任务走确定性流程。\n- 维护策略：规则/入口留此，历史/细节归档至 OpenViking。\n- 写入策略：主入口 `safe-write`/`safe-replace`；`~/.openclaw` 禁用 `edit` 工具。\n\n## 关键决策\n- 确立 `subtask-orchestrate` 为子代理正式入口，`sessions_send` 不作主链路。\n- 设定记忆检索层级：优先 `session-query`，其次 `openviking find`。\n- Context Compression Pipeline v1.0 (2026-03-06) 进入 S1 Shadow Validation 状态。\n- Execution Policy Framework v1 (2026-03-09) 确立写入工具层级与禁用规则。\n\n## 重要结果\n- Context Compression Pipeline Gate 0 通过 (2026-03-06)。\n- Execution Policy Framework v1 发布 (2026-03-09)。\n\n## 待办/下一步\n- Context Compression Pipeline Gate 1 状态：PENDING。\n- 任务关闭前必须过 Gate。"
}