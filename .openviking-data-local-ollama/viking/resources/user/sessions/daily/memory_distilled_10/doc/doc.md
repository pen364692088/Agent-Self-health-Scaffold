{
  "source_file": "/home/moonlight/.openclaw/workspace/memory.md",
  "source_size_bytes": 1730,
  "distilled_at": "2026-03-14T08:39:59.002639",
  "model": "baiduqianfancodingplan/qianfan-code-latest",
  "compression_ratio": "63.2%",
  "content": "## 核心要点\n- 子代理正式入口：`subtask-orchestrate` (run/status/resume)。\n- 内存检索层级：主入口 `session-query`，兜底 `openviking find`。\n- 检索原则：最小范围检索，最小片段读取，禁止整库灌入。\n- 主链路定义：`subtask-orchestrate` + `subagent-inbox` (非 `sessions_send`)。\n- 维护原则：Bootstrap 仅留简版入口，历史细节存入归档或 OpenViking。\n- 用户原则：稳定优先，里程碑可回溯，数据任务走确定性流程。\n\n## 关键决策\n- (2026-03-06) 启动 Context Compression Pipeline v1.0，状态定为 S1 Shadow Validation。\n- (2026-03-09) 确立执行策略框架 v1，规范写入入口及工具禁用范围。\n\n## 重要结果\n- Context Compression Pipeline v1.0：Gate 0 通过，Gate 1 待定。\n- 确定专用工具集：`context-budget-check`, `capsule-builder`, `context-compress` 等。\n\n## 待办/下一步\n- 推进 Context Compression Pipeline 的 Gate 1 验证。\n- 任务关闭前确保通过 Gate 检查。"
}