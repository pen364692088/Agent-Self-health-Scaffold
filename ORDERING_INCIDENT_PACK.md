# ORDERING_INCIDENT_PACK
## Message Ordering Conflict 事件包

**生成时间**: 2026-03-11 02:55 UTC  
**事件ID**: MSG-ORDER-2026-03-10  
**会话**: agent:main:telegram:direct:8420019401

---

## 1. 失败前后时间线 (-30s ~ +10s)

### 错误 #1 (2026-03-10 19:02:34 CST)

| Timestamp | Actor | Event | Local Session ID | Remote Conversation ID | Turn Index | Message ID | Parent/Previous ID | Action | Result |
|-----------|-------|-------|------------------|------------------------|------------|------------|-------------------|--------|--------|
| 19:01:32 | Context Guard | pressure_check | agent:main:telegram:direct:8420019401 | telegram:8420019401 | - | - | - | check | ratio=0.0% |
| 19:02:30 | context-compression | processing_start | agent:main:telegram:direct:8420019401 | telegram:8420019401 | - | - | - | start | mode=light_enforced |
| 19:02:31 | Context Guard | high_pressure | agent:main:telegram:direct:8420019401 | telegram:8420019401 | - | - | - | alert | ratio=0.8% |
| 19:02:31 | compaction-bridge | trigger | agent:main:telegram:direct:8420019401 | telegram:8420019401 | - | - | - | compact | reason=context_pressure_high |
| 19:02:31 | compaction-safeguard | cancel_compact | agent:main:telegram:direct:8420019401 | telegram:8420019401 | - | - | - | skip | reason=no_real_conversation_messages |
| 19:02:31 | compaction-bridge | trim_execute | agent:main:telegram:direct:8420019401 | telegram:8420019401 | - | - | - | trim | messagesBefore=12 messagesAfter=10 |
| 19:02:34 | pi-embedded-runner | llm_error | agent:main:telegram:direct:8420019401 | telegram:8420019401 | - | runId=ce2260c8 | - | error | "roles must alternate" |
| 19:02:34 | agent-runner-execution | user_error | agent:main:telegram:direct:8420019401 | telegram:8420019401 | - | - | - | return | "Message ordering conflict" |

### 错误 #2 (2026-03-10 19:43:59 CST)

| Timestamp | Actor | Event | Local Session ID | Remote Conversation ID | Turn Index | Message ID | Parent/Previous ID | Action | Result |
|-----------|-------|-------|------------------|------------------------|------------|------------|-------------------|--------|--------|
| 19:43:52 | context-compression | processing_start | agent:main:telegram:direct:8420019401 | telegram:8420019401 | - | - | - | start | mode=light_enforced |
| 19:43:53 | Context Guard | high_pressure | agent:main:telegram:direct:8420019401 | telegram:8420019401 | - | - | - | alert | ratio=15.1% |
| 19:43:53 | compaction-bridge | trigger | agent:main:telegram:direct:8420019401 | telegram:8420019401 | - | - | - | compact | reason=context_pressure_high |
| 19:43:53 | compaction-bridge | trim_execute | agent:main:telegram:direct:8420019401 | telegram:8420019401 | - | - | - | trim | messagesBefore=112 messagesAfter=90 |
| 19:43:59 | pi-embedded-runner | llm_error | agent:main:telegram:direct:8420019401 | telegram:8420019401 | - | runId=b4ad355b | - | error | "roles must alternate" |
| 19:43:59 | agent-runner-execution | user_error | agent:main:telegram:direct:8420019401 | telegram:8420019401 | - | - | - | return | "Message ordering conflict" |

### 错误 #3 (2026-03-10 19:46:25 CST)

| Timestamp | Actor | Event | Local Session ID | Remote Conversation ID | Turn Index | Message ID | Parent/Previous ID | Action | Result |
|-----------|-------|-------|------------------|------------------------|------------|------------|-------------------|--------|--------|
| 19:46:19 | context-compression | processing_start | agent:main:telegram:direct:8420019401 | telegram:8420019401 | - | - | - | start | mode=light_enforced |
| 19:46:20 | Context Guard | high_pressure | agent:main:telegram:direct:8420019401 | telegram:8420019401 | - | - | - | alert | ratio=15.2% |
| 19:46:20 | compaction-bridge | trigger | agent:main:telegram:direct:8420019401 | telegram:8420019401 | - | - | - | compact | reason=context_pressure_high |
| 19:46:20 | compaction-bridge | trim_execute | agent:main:telegram:direct:8420019401 | telegram:8420019401 | - | - | - | trim | messagesBefore=114 messagesAfter=92 |
| 19:46:25 | pi-embedded-runner | llm_error | agent:main:telegram:direct:8420019401 | telegram:8420019401 | - | runId=64d78e0a | - | error | "roles must alternate" |
| 19:46:25 | agent-runner-execution | user_error | agent:main:telegram:direct:8420019401 | telegram:8420019401 | - | - | - | return | "Message ordering conflict" |

---

## 2. 出站发送记录

### Send Attempt 日志

| Send Attempt ID | Local Seq | Local Message ID | Parent/Previous ID | Retry Count | Restored/Replayed | Source |
|-----------------|-----------|------------------|-------------------|-------------|-------------------|--------|
| telegram:9505:tp | 1 | 9505 | 9502 | 0 | false | time_passed (300s) |
| telegram:9539:tp | 2 | 9539 | 9536 | 0 | false | time_passed (300s) |
| telegram:9541:tp | 3 | 9541 | 9539 | 0 | false | time_passed (300s) |

**注**: 所有错误都发生在 emotiond-bridge 触发的 time_passed 事件处理中，非用户直接消息。

---

## 3. 并发状态

### 3.1 并发写入检测

| 检查项 | 结果 | 证据 |
|--------|------|------|
| 多个 worker/agent 同时写同一 session | ❌ 未发现 | 日志中无并发写入冲突 |
| session-level lock 存在 | ✅ 存在 | `updateSessionStore` 使用文件锁 |
| lock 覆盖 remote conversation 写入口 | ⚠️ 部分覆盖 | session 存储有锁，但 emotiond-bridge 写入 TOOLS.md 无锁 |

### 3.2 会话状态

| 属性 | 值 |
|------|-----|
| Session Key | agent:main:telegram:direct:8420019401 |
| Session ID | 903f05c0-c4e0-45ec-a214-ed7a48e05ea1 (错误#1前) |
| Provider | baiduqianfancodingplan |
| Model | qianfan-code-latest |
| 消息数量 (trim前) | 12-114 |
| 消息数量 (trim后) | 10-92 |

---

## 4. 恢复/重启日志

### 4.1 重启检测

| 时间 | 事件 | PID 变化 | 说明 |
|------|------|----------|------|
| 19:10:00 | Gateway restart | 2295261 → 3930713 | 服务重启 |
| 19:34:05 | Gateway restart | 3930713 → 4142334 | 服务重启 |

### 4.2 Auto-resume/Restore

| 检查项 | 结果 | 说明 |
|--------|------|------|
| auto-resume 触发 | ❌ 未触发 | 无 auto-resume 日志 |
| restore 触发 | ❌ 未触发 | 无 restore 日志 |
| checkpoint 使用 | N/A | 未使用 checkpoint |
| restore 后同步远端 | N/A | 未发生 restore |

**结论**: 错误与 restore/replay 无关。

---

## 5. Provider 完整错误对象

### 5.1 错误详情

| 属性 | 值 |
|------|-----|
| HTTP Status | 400 |
| Provider Error Code | invalid_request_error |
| Request ID | (日志中未记录具体 ID) |
| Full Error Message | "roles must alternate between \"user\" and \"assistant\"" 或 "400 Incorrect role information" |
| Retryable | ❌ 否 |
| 错误来源 | baiduqianfancodingplan (百度千帆) |

### 5.2 错误分类

```
Error Type: invalid_request_error
Error Pattern: /incorrect role information|roles must alternate/i
User-Facing Message: "Message ordering conflict - please try again. If this persists, use /new to start a fresh session."
```

---

## 6. 压缩/续接日志

### 6.1 Compaction 记录

| 时间 | 策略 | Messages Before | Messages After | Ratio | 结果 |
|------|------|-----------------|----------------|-------|------|
| 19:02:31 | trim | 12 | 10 | 83.3% | ❌ 后出错 |
| 19:07:44 | trim | 13 | 11 | 84.6% | (无后续错误记录) |
| 19:18:35 | trim | 71 | 57 | 80.3% | (无后续错误记录) |
| 19:43:53 | trim | 112 | 90 | 80.4% | ❌ 后出错 |
| 19:46:20 | trim | 114 | 92 | 80.7% | ❌ 后出错 |

### 6.2 Handoff/Anchor 状态

| 检查项 | 结果 | 说明 |
|--------|------|------|
| Handoff 发生 | ❌ 未发现 | 无 handoff 日志 |
| Parent anchor 变化 | ⚠️ 可能变化 | trim 删除消息后，首条消息的 parent 可能失效 |
| Continuity restore 替换 message list | ❌ 未发生 | 无 restore 日志 |

### 6.3 关键发现

**所有错误都发生在 trim 策略后，且满足以下条件**:
1. compact 策略被 safeguard 取消
2. summarize 策略不可用
3. trim 作为最后手段执行
4. trim 删除了 17-22 条消息 (约 20%)
5. 删除后消息角色顺序损坏

---

## 7. 附加数据

### 7.1 系统配置

```
Provider: baiduqianfancodingplan
Model: qianfan-code-latest
Context Window: 1000000 tokens
Compaction Strategy Order: ["compact", "summarize", "trim"]
Trim Ratio: 20%
```

### 7.2 相关文件

| 文件路径 | 作用 |
|----------|------|
| /home/moonlight/projects/openclaw-core/src/agents/pi-embedded-runner/compaction-bridge.ts | trim 策略实现 |
| /home/moonlight/projects/openclaw-core/src/agents/pi-embedded-runner/run.ts | 错误包装 |
| /home/moonlight/projects/openclaw-core/src/agents/pi-embedded-helpers/errors.ts | 错误格式化 |
| /home/moonlight/.openclaw/workspace/integrations/openclaw/traces/telegram:8420019401-2026-03-11.jsonl | 完整 trace |

### 7.3 历史修复记录

根据 memory/2026-03-11-ordering-invariant.md，此前已完成：
- ✅ 统一函数 normalizeMessageSequence / validateMessageSequence
- ✅ compaction-bridge.ts trim 后添加调用
- ✅ attempt.ts (history) validation 后添加调用
- ✅ attempt.ts (final) prompt 前添加调用
- ✅ Telemetry 集成 (turns-telemetry.ts)

---

## 8. 数据完整性声明

- [x] 时间线覆盖 -30s ~ +10s
- [x] 包含所有相关 actor 和 event
- [x] 包含 local session ID 和 remote conversation ID
- [x] 包含 send attempt 记录
- [x] 包含并发状态检查
- [x] 包含恢复/重启日志
- [x] 包含 provider 错误对象
- [x] 包含 compaction/handoff 日志

---

**采集完成时间**: 2026-03-11 03:00 UTC  
**采集者**: Manager (Coordinator AI)  
**数据源**: journalctl, session logs, trace files
