# ROOT_CAUSE_ASSESSMENT
## Message Ordering Conflict 根因评估

**评估时间**: 2026-03-11 03:05 UTC  
**评估者**: Manager (Coordinator AI)  
**置信度**: HIGH (基于日志证据和代码分析)

---

## 评估结论

### 最可能根因 Top 3

| 排名 | 根因 | 置信度 | 证据强度 | 状态 |
|------|------|--------|----------|------|
| **#1** | **compaction-bridge trim 策略未验证消息角色顺序** | **95%** | **强** | **CONFIRMED** |
| #2 | resetSessionAfterRoleOrderingConflict 恢复机制未触发 | 60% | 中等 | LIKELY |
| #3 | compaction-safeguard 过于严格导致频繁 fallback 到 trim | 40% | 弱 | POSSIBLE |

---

## 根因 #1: trim 策略未验证消息角色顺序 (CONFIRMED)

### 证据链

```
[日志证据]
1. 所有 3 次错误都发生在 trim 策略后
2. trim 删除了 20% 的消息 (12→10, 112→90, 114→92)
3. 错误信息为 "roles must alternate" (LLM API 返回)

[代码证据]
1. compaction-bridge.ts:181-208 executeTrimStrategy 函数
   - 使用 messages.splice(0, trimCount) 删除消息
   - 无角色顺序验证逻辑
   
2. run.ts:1166-1175 错误处理
   - 捕获 "roles must alternate" 错误
   - 包装为 "Message ordering conflict" 返回给用户

[逻辑证据]
1. trim 删除前 20% 消息后，剩余消息可能：
   - 以 assistant 消息开头 (违反 Anthropic/百度要求)
   - 包含连续的 user 或 assistant 消息 (违反角色交替要求)
```

### 触发条件

| 条件 | 说明 |
|------|------|
| Context Guard 检测到高压 | ratio >= 0.1% |
| compact 策略不可用 | safeguard 取消 (no real conversation messages) |
| summarize 策略不可用 | 未实现或失败 |
| trim 作为最后手段执行 | 删除前 20% 消息 |
| 删除后角色顺序损坏 | 未验证和修复 |

### 影响范围

- **受影响模型**: 所有使用 compaction-bridge 的模型
- **受影响提供商**: baiduqianfancodingplan (确认), 可能包括 anthropic
- **触发频率**: 当 context 压力高且 compact/summarize 不可用时

---

## 根因 #2: 恢复机制未触发 (LIKELY)

### 证据

```
[代码分析]
agent-runner-execution.ts:
1. 检测到 role ordering 错误后调用 resetSessionAfterRoleOrderingConflict
2. 如果返回 false，则执行 break 并返回 fallbackText
3. fallbackText 包含 "Message ordering conflict" 提示用户 /new

[日志观察]
- 用户收到了 "Message ordering conflict" 错误
- 未收到 "I've reset the conversation" 成功消息
- 说明 resetSessionAfterRoleOrderingConflict 返回了 false
```

### 可能原因

| 原因 | 说明 |
|------|------|
| sessionKey 为空 | 某些场景下 sessionKey 未正确传递 |
| activeSessionStore 为空 | 内存中无会话数据 |
| storePath 为空 | 持久化路径未配置 |
| resetSession 内部出错 | 异常被捕获但返回 false |

---

## 根因 #3: safeguard 过于严格 (POSSIBLE)

### 证据

```
[日志]
19:02:31 [compaction-safeguard] cancelling compaction with no real conversation messages

[分析]
- safeguard 取消了 compact 策略
- 导致频繁 fallback 到 trim
- trim 作为"最后手段"更容易产生问题
```

### 影响

- 增加了 trim 策略的使用频率
- 间接增加了角色顺序错误的可能性
- 但不是直接根因

---

## 排除的根因

| 根因假设 | 排除理由 | 证据 |
|----------|----------|------|
| 并发写同一 session | 未发现并发冲突日志 | 日志中无并发写入冲突 |
| 过期 parent/previous id | 错误与消息顺序相关，非 parent ID | 错误信息为 "roles must alternate" |
| restore/replay 顺序错位 | 未发生 restore/replay | 日志中无 restore 记录 |
| handoff anchor 断裂 | 未发生 handoff | 日志中无 handoff 记录 |
| 上下文太长 | 错误与长度无关 | trim 后消息数量减少但仍出错 |

---

## 核心问题回答

### 1. 有没有并发写？

**答案**: ❌ **没有**

**证据**:
- 日志中无并发写入冲突
- session 存储使用文件锁
- 错误发生在单线程处理流程中

### 2. 有没有过期 parent/previous id？

**答案**: ❌ **没有**

**证据**:
- 错误信息为 "roles must alternate"，非 parent ID 相关
- 未观察到消息丢失或错位
- trim 删除的是最旧的消息，不影响 parent 链

### 3. 有没有 restore/replay 顺序错位？

**答案**: ❌ **没有**

**证据**:
- 日志中无 restore/replay 记录
- 错误发生在正常会话流程中
- 无 checkpoint 使用记录

### 4. 有没有 compaction/handoff anchor 断裂？

**答案**: ⚠️ **部分相关 (compaction)**

**证据**:
- ❌ handoff 未发生
- ✅ compaction 确实发生 (trim 策略)
- ✅ trim 后消息 anchor 可能失效 (首条消息的 parent)
- ✅ 但主要问题是角色顺序，非 anchor 断裂

### 5. "上下文太长"是主因、次因，还是放大器？

**答案**: **放大器**

**分析**:
- ❌ **不是主因**: 错误与上下文长度无关，trim 后消息减少仍出错
- ❌ **不是次因**: 长度本身不直接导致错误
- ✅ **是放大器**: 
  - 长上下文触发 compaction
  - compaction 触发 trim
  - trim 导致角色顺序问题
  - 没有 trim 的验证逻辑，问题才会暴露

---

## 根因机制图解

```
用户消息
    │
    ▼
Context Guard 检测压力
    │
    ├── ratio < 0.1% ──► 正常处理
    │
    └── ratio >= 0.1% ──► 触发 compaction
                              │
                              ▼
                    ┌─────────────────┐
                    │ 策略选择        │
                    └─────────────────┘
                              │
            ┌─────────────────┼─────────────────┐
            ▼                 ▼                 ▼
      compact 策略      summarize 策略      trim 策略
      (被取消)          (不可用)            (执行)
            │                 │                 │
            ▼                 ▼                 ▼
      ❌ 未执行          ❌ 未执行          ✅ 执行
                                                │
                                                ▼
                                          messages.splice(0, 20%)
                                                │
                                                ▼
                                          ┌─────────────┐
                                          │ 角色顺序损坏 │ ◄── 根因 #1
                                          │ (未验证)    │
                                          └─────────────┘
                                                │
                                                ▼
                                          LLM API 调用
                                                │
                                                ▼
                                          "roles must alternate" 错误
                                                │
                                                ▼
                                          ┌─────────────┐
                                          │ 恢复机制     │
                                          │ 未触发      │ ◄── 根因 #2
                                          │ (返回 false)│
                                          └─────────────┘
                                                │
                                                ▼
                                          返回 "Message ordering conflict" 给用户
```

---

## 修复验证

### 已实施的修复

根据历史记录 (memory/2026-03-11-ordering-invariant.md):

| 修复项 | 状态 | 提交 |
|--------|------|------|
| normalizeMessageSequence 统一函数 | ✅ | 1f18c61 |
| compaction-bridge.ts trim 后调用 | ✅ | 1f18c61 |
| attempt.ts (history) 调用 | ✅ | 6bd10c9 |
| attempt.ts (final) 调用 | ✅ | c847031 |
| Telemetry 集成 | ✅ | ee93d94 |

### 修复效果

- ✅ 修复后 trim 策略会验证和修复角色顺序
- ✅ 自动修复，无需用户执行 /new
- ✅ 13 个测试用例通过

---

## 建议

### 短期 (已完成)
- ✅ 在 trim 策略后添加角色顺序验证

### 中期 (待跟进)
- [ ] 修复 resetSessionAfterRoleOrderingConflict 触发问题
- [ ] 优化 compaction-safeguard 逻辑
- [ ] 添加更多入口点的验证 (session-manager-init, session-file-repair)

### 长期
- [ ] 重构 compaction 策略选择逻辑
- [ ] 统一消息格式验证层

---

**评估完成**: 2026-03-11 03:10 UTC  
**下次审查**: 观察 24h 后复查 telemetry 数据
