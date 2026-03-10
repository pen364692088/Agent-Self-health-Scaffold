# Findings - 问题发现清单

**审计日期**: 2026-03-09 21:25 CST

---

## P0 - 阻断性问题

无

---

## P1 - 高优先级问题

### 1. Execution Policy 未集成到 Heartbeat

**问题**: probe-execution-policy-v2 存在但未接入 HEARTBEAT.md

**影响**:
- Execution Policy 违规无法在 Heartbeat 中检测
- 依赖外部调用或手动检查

**证据**:
```
$ grep -l "probe-execution-policy" HEARTBEAT.md
(无结果)
```

**修复建议**:
在 HEARTBEAT.md 的 Self-Health Quick Mode Hook 之后添加：
```bash
~/.openclaw/workspace/tools/probe-execution-policy-v2 --quick --json >/dev/null 2>&1 || true
```

**风险**: 中

---

### 2. verify-and-close 未被强制执行

**问题**: SOUL.md 规定任务完成必须通过 verify-and-close，但无强制机制

**影响**:
- 任务可能绕过验证直接声明完成
- 缺少 receipt 证据链

**证据**:
```
$ ls artifacts/receipts/*.json 2>/dev/null | wc -l
0
```

**修复建议**:
1. 在输出层添加检查（output-interceptor）
2. 或在 message tool 调用前验证 receipt 存在

**风险**: 中

---

## P2 - 中优先级问题

### 3. Shadow Mode 未启用

**问题**: shadow_config.json 存在但 AUTO_COMPACTION_SHADOW_MODE 环境变量未设置

**影响**: 自动压缩 shadow mode 未运行

**证据**:
```
$ echo $AUTO_COMPACTION_SHADOW_MODE
(空)
```

**修复建议**:
设置环境变量或删除相关配置

**风险**: 低

---

### 4. Session Index 为 0

**问题**: artifacts/session_index/ 目录为空

**影响**: L1 检索多样性降低

**证据**:
```
$ ls artifacts/session_index/*.json 2>/dev/null | wc -l
0
```

**修复建议**:
运行 session-indexer 重建索引（可选）

**风险**: 低

---

### 5. OpenViking Embedding 错误

**问题**: 26 个文件因超长无法 embedding

**影响**: L2 搜索效果受限

**证据**:
```
$ openviking status | jq '.result.components.queue.status'
| Embedding | 0 | 0 | 41 | 26 | 41 |
```

**修复建议**:
技术债跟踪，暂不修复（L1 兜底正常）

**风险**: 低

---

### 6. memory-lancedb 404 错误

**问题**: Gateway 内置 LanceDB 返回 404

**影响**: 日志噪音

**证据**:
```
$ journalctl --user -u openclaw-gateway --since "10 min ago" | grep -c "404"
20+
```

**修复建议**:
忽略（有 context-retrieve 替代）或禁用

**风险**: 低

---

## P3 - 低优先级问题

### 7. 多入口重复建设

**问题**: 同一功能有多个入口

| 功能 | 入口数 | 说明 |
|------|--------|------|
| 记忆检索 | 4 | context-retrieve, session-start-recovery, openviking find, session-query |
| 子代理创建 | 3 | subtask-orchestrate, sessions_spawn, spawn-with-callback |
| 状态写入 | 2 | state-write-atomic, safe-write |

**影响**: 维护复杂度增加

**修复建议**:
记录技术债，逐步收口

**风险**: 低

---

### 8. Legacy 路径引用

**问题**: check-subagent-mailbox 被标记为旧但仍有引用

**证据**:
```
$ grep -r "check-subagent-mailbox" tools/ | grep -v "deprecated"
tools/check-subagent-mailbox:  - check-subagent-mailbox 缺少原子写入
```

**修复建议**:
更新引用或删除工具

**风险**: 低

---

## 问题统计

| 优先级 | 数量 | 说明 |
|--------|------|------|
| P0 | 0 | 无阻断问题 |
| P1 | 2 | 需要修复 |
| P2 | 4 | 技术债 |
| P3 | 2 | 低风险 |
| **总计** | 8 | - |
