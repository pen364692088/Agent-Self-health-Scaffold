{
  "source_file": "/home/moonlight/.openclaw/workspace/memory.md",
  "source_size_bytes": 1730,
  "distilled_at": "2026-03-14T11:40:37.062985",
  "model": "baiduqianfancodingplan/qianfan-code-latest",
  "compression_ratio": "62.5%",
  "content": "## 核心要点\n- **定位**: 会话引导速查表，完整历史存于 OpenViking\n- **子代理入口**: `subtask-orchestrate` (run/status/resume)\n- **检索策略**: 主入口 `session-query`，兜底 `openviking find`，遵循最小范围原则\n- **写入策略 (2026-03-09)**: 主入口 `safe-write`/`safe-replace`，`~/.openclaw/**` 禁用 `edit` 工具\n- **维护原则**: 规则/入口留简版，历史/细节存档，保持文件短小\n\n## 关键决策\n- **主链路确立**: 正式链路为 `subtask-orchestrate` + `subagent-inbox`，非 `sessions_send`\n- **检索触发**: 涉及历史决策、参数、配置、故障模式时必须先检索\n- **归档定义**: 每日日志 + bootstrap 摘要 + 索引/向量归档 + 顶层备份提交\n\n## 重要结果\n- **Context Compression Pipeline v1.0 (2026-03-06)**: S1 Shadow Validation 状态，Gate 0 ✅ PASSED，Gate 1 ⏳ PENDING\n\n## 待办/下一步\n- 任务关闭前必须过 Gate\n- 关注 Context Compression Pipeline Gate 1 状态"
}