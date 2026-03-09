{
  "source_file": "/home/moonlight/.openclaw/workspace/memory.md",
  "source_size_bytes": 2543,
  "distilled_at": "2026-03-08T23:55:34.529605",
  "model": "baiduqianfancodingplan/qianfan-code-latest",
  "compression_ratio": "76.6%",
  "content": "## 核心要点\n- 目的：会话引导速查表，完整历史存于外部索引。\n- 核心工具：`subtask-orchestrate` (子代理), `session-query`/`openviking find` (内存)。\n- 硬规则：主链路 `subtask-orchestrate` + `subagent-inbox`；检索遵循最小范围原则。\n- 维护原则：稳定优先，规则留简版，细节存档，保持文件短小。\n- [2026-03-06] 新增 Context Compression Pipeline v1.0：三层上下文模型 + 两级检索。\n\n## 关键决策\n- 检索策略：优先 `session-query`，必要时 `openviking find`。\n- 集成策略：Gate 1 通过后再接入主链路，当前仅作独立工具运行。\n\n## 重要结果\n- 当前状态：S1 Shadow Validation (Feature Frozen)，未接入主链路。\n- Gate 进度：Gate 0 PASSED，Gate 1 PENDING (样本 12/80)。\n- 已知问题：Issue #1 L2 参数错误 (非 blocker，属 Gate 2 准备项)。\n\n## 待办/下一步\n- 推进 Gate 1 样本收集至达标 (目标 80)。\n- 修复 Issue #1 为 Gate 2 做准备。"
}