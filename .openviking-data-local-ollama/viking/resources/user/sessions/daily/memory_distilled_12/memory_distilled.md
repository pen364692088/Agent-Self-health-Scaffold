{
  "source_file": "/home/moonlight/.openclaw/workspace/memory.md",
  "source_size_bytes": 1730,
  "distilled_at": "2026-03-14T18:00:33.974313",
  "model": "baiduqianfancodingplan/qianfan-code-latest",
  "compression_ratio": "69.7%",
  "content": "## 核心要点\n- 子代理主入口：`subtask-orchestrate` (run/status/resume)。\n- 记忆检索：主用 `session-query`，兜底 `openviking find`，禁整库灌入。\n- 硬性规则：主链路为 `subtask-orchestrate` + `subagent-inbox`，文件保持短小。\n- 写入策略：主入口 `safe-write`/`safe-replace`，`~/.openclaw/**` 禁用 `edit`。\n- 维护原则：稳定优先，里程碑需可回溯，细节归档不堆砌。\n\n## 关键决策\n- (2026-03-06) 启动上下文压缩流水线 v1.0，锁定 S1 Shadow Validation 状态。\n- (2026-03-09) 确立执行策略框架 v1，规范写入工具链与权限边界。\n\n## 重要结果\n- Context Pipeline Gate 0: ✅ PASSED\n- Context Pipeline Gate 1: ⏳ PENDING\n\n## 待办/下一步\n- 推进 Context Pipeline Gate 1 验证。\n- 任务关闭前执行 Gate 检查。"
}