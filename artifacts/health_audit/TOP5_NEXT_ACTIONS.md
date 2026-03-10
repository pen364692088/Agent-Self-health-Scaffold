# Top 5 Next Actions - 前 5 项后续行动

**审计日期**: 2026-03-09 21:25 CST

---

## Action 1: 集成 Execution Policy 到 Heartbeat

**优先级**: P1 (必须)
**预计时间**: 5 分钟
**风险**: 低

### 为什么重要
- Execution Policy 是核心保护机制
- 未集成到 Heartbeat 意味着无法周期性检测违规
- 当前只能依赖外部调用触发

### 执行步骤
1. 编辑 HEARTBEAT.md
2. 在 Self-Health Quick Mode Hook 之后添加 Execution Policy Quick Check
3. 测试 heartbeat 输出不受影响

### 验收标准
- HEARTBEAT.md 包含 Execution Policy 检查
- heartbeat 输出仍为 HEARTBEAT_OK

---

## Action 2: 增强 verify-and-close 强制执行

**优先级**: P1 (必须)
**预计时间**: 30 分钟
**风险**: 中

### 为什么重要
- 任务完成协议是质量保障的关键
- 当前可能被绕过
- 缺少 receipt 证据链

### 执行步骤
1. 增强 safe-message 工具
2. 添加 receipt 存在性检查
3. 在任务完成输出前验证

### 验收标准
- 任务完成时生成 receipt 文件
- 绕过验证时报错

---

## Action 3: 删除孤儿组件

**优先级**: P2 (建议)
**预计时间**: 1 分钟
**风险**: 低

### 为什么重要
- 减少维护负担
- 避免误用废弃工具
- 清理技术债

### 执行步骤
1. 创建 tools/legacy/ 目录
2. 移动 check-subagent-mailbox 到 legacy/
3. 更新文档引用

### 验收标准
- tools/ 无孤儿组件
- 文档引用更新或删除

---

## Action 4: 处理 Shadow Mode

**优先级**: P2 (建议)
**预计时间**: 1 分钟
**风险**: 低

### 为什么重要
- 配置存在但未启用是技术债
- 可能导致混淆

### 执行步骤
选择其一：
- 方案 A: 设置 AUTO_COMPACTION_SHADOW_MODE=true
- 方案 B: 删除 shadow_config.json

### 验收标准
- 配置与运行状态一致

---

## Action 5: 重建 Session Index

**优先级**: P2 (可选)
**预计时间**: 5 分钟
**风险**: 低

### 为什么重要
- 提升检索多样性
- 完善记忆系统

### 执行步骤
1. 运行 session-indexer --rebuild
2. 验证 artifacts/session_index/ 有文件

### 验收标准
- Session Index 有 1+ 个文件
- context-retrieve 能从 session_index 检索

---

## 执行建议

**立即执行**: Action 1, Action 2
**本周执行**: Action 3, Action 4
**可选执行**: Action 5

---

## 后续监控

| 指标 | 当前值 | 目标值 |
|------|--------|--------|
| Execution Policy 样本 | 0 | 等待自然触发 |
| Receipt 生成率 | 未知 | 100% |
| Session Index 文件数 | 0 | 1+ |
| 孤儿组件数 | 1-3 | 0 |
