# Session: 2026-03-06 16:53:11 UTC

- **Session Key**: agent:main:telegram:direct:8420019401
- **Session ID**: ae29b061-a6ef-4125-8450-b33f9411121a
- **Source**: telegram

## Conversation Summary

assistant: ✅ New session started · model: baiduqianfancodingplan/qianfan-code-latest
user: A new session was started via /new or /reset. Execute your Session Startup sequence now - read the required files before responding to the user. Then greet the user in your configured persona, if one is provided. Be yourself - use your defined voice, mannerisms, and mood. Keep it to 1-3 sentences and ask what they want to do. If the runtime model differs from default_model in the system prompt, mention the default model. Do not mention internal steps, files, tools, or reasoning.
assistant: Morning. SRAP Phase A+B is done, Shadow Mode is running, and Execution Policy v2.1 is frozen. What's next?
user: [media attached: /home/moonlight/.openclaw/media/inbound/CONTEXT_PRESSURE_MEMORY_GOVERNANCE_SPEC---d74f0e1e-b71d-4ad0-80c6-21366570b990.md (text/markdown) | /home/moonlight/.openclaw/media/inbound/CONTEXT_PRESSURE_MEMORY_GOVERNANCE_SPEC---d74f0e1e-b71d-4ad0-80c6-21366570b990.md]
To send an image back, prefer the message tool (media/path/filePath). If you must inline, use MEDIA:https://example.com/image.jpg (spaces ok, quote if needed) or a safe relative path like MEDIA:./image.jpg. Avoid absolute paths (MEDIA:/...) and ~ paths — they are blocked for security. Keep caption in the text body.
Conversation info (untrusted metadata):
```json
{
  "message_id": "7057",
  "sender_id": "8420019401",
  "sender": "Moonlight",
  "timestamp": "Fri 2026-03-06 10:49 CST"
}
```

Sender (untrusted metadata):
```json
{
  "label": "Moonlight (8420019401)",
  "id": "8420019401",
  "name": "Moonlight"
}
```

[Telegram Moonlight id:8420019401 +9s Fri 2026-03-06 10:49 CST] <media:document>

<file name="CONTEXT_PRESSURE_MEMORY_GOVERNANCE_SPEC---d74f0e1e-b71d-4ad0-80c6-21366570b990.md" mime="text/markdown">
# CONTEXT_PRESSURE_MEMORY_GOVERNANCE_SPEC.md

> 面向 cc-godmode 的实施任务文档
> 主题：在上下文接近紧张额度时，自动完成“分层保留 / 结构化压缩 / 向量索引 / 检索回填 / 可审计回放”
> 建议版本归属：**MVP11.5-C（基础设施支线）**，并作为 **MVP12 / MVP13 的前置底座**

---

## 0. 一句话定义

不要做“上下文快满了就让 LLM 写个摘要”。

要做的是一条**受治理的上下文压力管理链路**：

**Context Pressure Manager**
→ **分类保留 / 压缩 / 淘汰**
→ **Session Capsule 结构化胶囊**
→ **向量索引 + Artifact 指针**
→ **按需检索回填**
→ **全程写 trace / 可 replay / 可 gate**

---

## 1. 战略定位（为什么现在做）

这项能力不应被定义成普通“记忆摘要功能”，而应被定义成：

**为状态主权、表达主权、发育核、连续自我模型提供上下文连续性的基础设施。**

理由：

1. 当前主线仍应优先收稳 `MVP11.5`：先解决“LLM 不要替 agent 胡说”，再解决“LLM 不要替 agent 改写原意”。
2. 后续 `MVP12` 的 developmental core 与 `MVP13` 的 persistent self-model 都要求：
 - 长时间运行
 - 输出可记录、可比较、可 replay
 - 长期记忆不只是可回忆，而是会影响后续行为
3. 如果没有上下文压力治理，长任务一旦靠近 token 上限，系统就会退化成：
 - 只靠近几轮文本临时发挥
 - 丢失 response_plan / open loops / commitments
 - 用模糊检索替代精确真值
 - 无法区分“临时上下文”与“稳定不变量”

因此，这项工作应作为 **基础设施先行**，而不是最后补丁。

---

## 2. 必须遵守的总原则

### P1. 不允许把“向量索引”当成真值本体

向量库只能帮助“找回可能相关内容”，不能代替：

- 当前任务目标
- 当前阶段 Gate / Mode
- response_plan / intent_contract
- 未闭环承诺与 open loops
- 当前工具状态 / 错误状态
- 精确数值、阈值、开关位
- 程序端权威状态源

**结论：不能只留 embedding，必须保留结构化 session capsule。**

### P2. Dot / Cycle 必须分离治理

- **Dot**：短期高熵上下文脚手架，允许高比例压缩/淘汰
- **Cycle**：稳定低熵不变量，必须结构化保留并可重入

### P3. 反漂移优先于压缩率

宁可压缩率低一点，也不能把：

- 真值链压掉
- replay 所需信息压掉
- 程序端表达主权压掉
- 对后续行为有因果作用的结构压掉

### P4. 压缩事件本身必须可审计

每一次压缩、回填、淘汰，都必须形成可追踪记录，而不是“偷偷发生”。

### P5. Governor v2 / Gate / deterministic 不得被破坏

该能力只能做：

- prompt 负载治理
- 记忆回填辅助
- 历史上下文组织

**不得改变既有裁决权威链。**

---

## 3. 本功能在路线图中的正确位置

建议命名：

**MVP11.5-C — Context Pressure & Memory Governance**

它不是单独版本，而是贯穿三段：

### 对 MVP11.5 的价值

- 保护 `response_plan / intent_contract`
- 防止 certainty / commitment / tone 在长会话中因上下文漂移而升级
- 保护未完成承诺与 checker 真值

### 对 MVP12 的价值

- 让 developmental core 的候选输出不必长期塞在主 prompt 里
- 可写 trace / artifacts / memory pointers
- 支持长期运行但不直接说话、不直接执行

### 对 MVP13 的价值

- 为 persistent self-model 提供“跨时间但受治理”的连续性底座
- 区分“可重建的历史细节”与“必须常驻的 identity-relevant invariants”

---

## 4. 目标与非目标

## 4.1 目标

实现一个运行时子系统，使 agent 在上下文接近紧张额度时，能够自动完成：

1. 检测上下文压力
2. 对现有上下文分层分类
3. 生成结构化 `session_capsule`
4. 将可外存内容写入 memory/artifacts/vector index
5. 从 active prompt 中移除可淘汰内容
6. 在后续需要时按需检索回填
7. 将所有动作写入 trace，并能 replay / audit / gate

## 4.2 非目标

当前阶段不做：

- 不做“全自动无限长记忆”
- 不做“向量库替代程序状态源”
- 不做“直接修改 Governor 决策链”
- 不做“developmental core 直接拥有表达权或执行权”
- 不做“只靠大模型自由摘要来决定什么重要”

---

## 5. 架构设计

## 5.1 新增模块

建议新增以下模块（名称可微调，但职责应保持清晰）：

### A. `context_pressure_manager`
职责：
- 监测 token / prompt 压力
- 决定是否触发压缩
- 决定压缩级别（light / standard / hard）

### B. `context_classifier`
职责：
- 对当前上下文条目做分层分类
- 判断属于：resident / capsule / retrievable / evictable

### C. `session_capsule_builder`
职责：
- 产出结构化 `session_capsule`
- 维护版本号、来源范围、摘要槽位、memory pointers

### D. `memory_pointer_emitter`
职责：
- 把可外存的信息写入：
 - vector index
 - artifact refs
 - run/tape refs
 - optional structured memory store

### E. `context_rehydrator`
职责：
- 在需要历史信息时，从 capsule + vector + artifacts 中回填最小必要上下文
- 保证只回填“当前决策所需的最小集”

### F. `compression_audit_writer`
职责：
- 记录压缩与回填事件
- 输出 trace / report / metrics

---

## 5.2 运行时三层上下文模型

### Layer A. Active Context（主 prompt 常驻区）
仅保留最小必要集：

- 最新用户消息
- 最近 N 轮高相关交互
- 当前 task_goal
- current_phase / current_mode
- open_loops
- response_plan / intent_contract
- 当前工具状态 / 当前错误状态
- 当前回填结果
- 当前必须原样保留的约束

### Layer B. Session Capsule（结构化会话胶囊）
保留本会话骨架：

- 会话目标
- 已做决定
- 关键实体
- 硬约束
- 失败尝试
- response contract 摘要
- stable invariants
- memory pointers
- evicted ranges

### Layer C. Long-term Memory / Vector / Artifacts
保留可检索细节：

- 旧讨论细节
- 长分析过程
- 备选方案
- 已完成分支推理
- trace 片段
- artifact 路径与引用

---

## 6. 上下文分类标准

每条上下文项必须归入以下四类之一：

### Class 1. `resident`
必须常驻，禁止自动淘汰：

- task_goal
- current_phase / gate_state
- response_plan / intent_contract
- must_include / must_not_upgrade / tone_bounds
- open loops / pending commitments
- 当前工具执行状态
- 当前错误与恢复上下文
- 高优先级用户约束
- 会改变当前回答真值的状态源

### Class 2. `capsule_only`
允许压缩为结构化胶囊，但不可完全丢失：

- 关键决定
- 关键实体与关系
- 已确认偏好
- 历史失败尝试
- 当前会话中已形成的中间结论
- identity-relevant provisional notes

### Class 3. `retrievable`
允许外存并按需检索：

- 长篇论证
- 已完成的分支分析
- 历史方案对比
- 较早的非关键细节
- 长日志片段
- 可通过 artifact/run/tape 重建的内容

### Class 4. `evictable`
允许直接淘汰：

- 寒暄
- 重复解释
- 与当前任务无关的噪声
- 已经被 capsule 充分覆盖的冗余表述

---

## 7. 触发机制

## 7.1 触发阈值

建议初始配置：

- `pressure < 0.70`：不触发
- `0.70 <= pressure < 0.85`：`light_compress`
- `0.85 <= pressure < 0.93`：`standard_compress`
- `pressure >= 0.93`：`hard_compress`

其中 `pressure` 可由以下组合计算：

- prompt token usage ratio
- resident 区增长速度
- 最近 10 轮平均新增 token
- 检索回填后的回胀风险

### 7.2 特殊强制触发条件

即使 token 比例未超阈值，也应触发压缩：

- open loops 数量超过上限
- 当前 session capsule 长期未刷新
- 同一主题连续长跑
- tool chain 产生大量日志性文本
- 进入 multi-stage task 且近期历史已显著膨胀

---

## 8. Session Capsule 结构

建议 schema：

```json
{
 "session_id": "string",
 "capsule_version": 1,
 "created_at": "iso8601",
 "updated_at": "iso8601",
 "source_turn_range": [1, 72],
 "compression_level": "light|standard|hard",
 "task_goal": "string",
 "current_phase": "string",
 "current_mode": "string",
 "open_loops": [
 {
 "id": "loop_001",
 "text": "string",
 "priority": "high|medium|low",
 "owner": "agent|user|tool",
 "status": "open|blocked|done"
 }
 ],
 "hard_constraints": ["string"],
 "response_contract": {
 "speaker_mode": "string",
 "epistemic_status": "string",
 "commitment_level": "string",
 "core_points": ["string"],
 "must_include": ["string"],
 "must_not_upgrade": ["string"],
 "tone_bounds": ["string"]
 },
 "stable_invariants": [
 {
 "key": "string",
 "value": "string",
 "confidence": 0.0,
 "source": "cycle|self_model|policy|other"
 }
 ],
 "recent_decisions": [
 {
 "decision": "string",
 "why": "string",
 "impact": "string"
 }
 ],
 "failed_attempts": [
 {
 "what": "string",
 "why_failed": "string"
 }
 ],
 "key_entities": [
 {
 "name": "string",
 "type": "project|module|person|file|branch|tool|concept",
 "role": "string"
 }
 ],
 "memory_pointers": [
 {
 "kind": "vector|artifact|run|tape|file",
 "ref": "string",
 "reason": "string"
 }
 ],
 "evicted_ranges": [
 {
 "turn_start": 12,
 "turn_end": 34,
 "reconstructable": true,
 "via": ["vector", "artifact", "tape"]
 }
 ],
 "integrity": {
 "capsule_hash": "sha256",
 "parent_capsule_hash": "sha256|null"
 }
}
```

---

## 9. 检索回填策略

## 9.1 什么时候回填

只在以下条件发生时触发：

1. 当前问题引用旧决定 / 旧模块 / 旧 artifact
2. 当前 response_plan 发现缺关键真值
3. tool 调用前需要历史参数或状态
4. 用户切回之前话题
5. current capsule 明示某 open loop 依赖外存内容

## 9.2 不应该回填的情况

- 只是“可能有点相关”
- 只是模型想多拿点历史增强发挥
- 没有明确决策需要
- 当前 resident 已能支撑回答

## 9.3 回填上限

每次回填必须有限流：

- 最多回填 K 个片段
- 片段必须带 relevance score
- 回填后若 pressure 再次逼近阈值，必须先压缩再继续

---

## 10. 审计与可回放设计

## 10.1 新增 trace 事件类型

建议写入 `run.jsonl` / tape / runtime trace：

- `context_pressure_snapshot`
- `compression_triggered`
- `compression_applied`
- `capsule_written`
- `memory_pointer_emitted`
- `context_evicted`
- `rehydration_requested`
- `rehydration_applied`
- `rehydration_rejected`

## 10.2 每个压缩事件至少记录

- trigger reason
- token pressure before / after
- compression level
- resident kept count
- capsule items count
- retrievable items emitted count
- evicted items count
- capsule hash
- parent capsule hash
- retrieval dependencies

## 10.3 replay 约束

replay 时必须优先读取：

1. 当时的 capsule
2. 当时写入的 memory pointers
3. 当时的 compression decision

**不得使用未来更新后的 memory store 去重构旧 run 的压缩决策。**

---

## 11. Metrics 与 Gate

## 11.1 关键指标

建议新增：

- `compression_trigger_count`
- `avg_tokens_before_compress`
- `avg_tokens_after_compress`
- `compression_ratio`
- `resident_survival_rate`
- `capsule_recall_hit_rate`
- `rehydration_precision`
- `rehydration_waste_rate`
- `lost_open_loop_rate`
- `post_compress_regression_rate`
- `capsule_drift_rate`
- `replay_context_integrity_pass_rate`

## 11.2 必须重点盯的坏指标

- open loops 被压丢
- must_include / must_not_upgrade 丢失
- tool state 丢失
- 历史真值被模糊改写
- 回填后 prompt 立刻再次爆炸
- 压缩后出现 certainty / commitment / tone 漂移

## 11.3 Gate 策略

### Gate A（Contract）
验证：
- schema 固化
- resident/capsule/retrievable/evictable 分类规则固化
- response_plan 常驻规则固化
- replay 约束写入 spec

### Gate B（E2E）
验证：
- 长会话触发压缩后，核心任务仍能继续
- open loops 不丢
- old topic re-entry 能正确回填
- testbot / longrun 基本通过

### Gate C（Preflight / doctor）
验证：
- 配置有效
- 阈值合理
- capsule schema 兼容
- 索引通道可达
- metrics 与 artifacts 路径可写

---

## 12. 分阶段实施计划

## Phase 0 — Spec Freeze

### 目标
冻结协议与边界，先防止做偏。

### 交付物
- `POLICIES/CONTEXT_PRESSURE_GOVERNANCE.md`
- `schemas/session_capsule.v1.schema.json`
- `schemas/context_compression_event.v1.schema.json`
- `docs/runbooks/CONTEXT_PRESSURE_RUNBOOK.md`

### 验收
- resident / capsule / retrievable / evictable 四分类写清楚
- replay 不允许使用未来 memory store 重算旧压缩决策
- response_plan 与 open_loops 被列为 resident hard rules

---

## Phase 1 — Passive Observation（只观测，不压缩）

### 目标
先采样现有会话真实膨胀模式，别一上来就自动改写 prompt。

### 实现
- 记录每轮 token pressure
- 记录上下文组成比例
- 记录哪些条目理论上属于四类
- 不实际淘汰，只做 shadow classification

### 交付物
- `tools/context-pressure-observer`
- `artifacts/context_pressure/shadow/*.json`
- `reports/context_pressure_baseline.md`

### 验收
- 至少采集一批长任务样本
- 识别 resident / retrievable 热点来源
- 形成阈值初稿

---

## Phase 2 — Capsule Build（只生成胶囊，不驱动主 prompt）

### 目标
验证 capsule 是否能稳定表达会话骨架。

### 实现
- 根据 shadow classification 生成 `session_capsule`
- 写 hash / parent hash
- 写 memory pointers
- 仍不实际淘汰 active context

### 交付物
- `context_classifier`
- `session_capsule_builder`
- `memory_pointer_emitter`

### 验收
- capsule schema 稳定
- 同一会话多次构建结果 drift 可控
- 人工 spot check 证明 open loops / hard constraints 未丢

---

## Phase 3 — Light Compression Shadow

### 目标
开始真实压缩，但只做轻压缩。

### 实现
- 仅淘汰 `evictable`
- `capsule_only` 写 capsule 但暂不大规模移出
- 记录前后 token 差异
- 保留完整 audit

### 验收
- 不影响当前任务连续性
- response_plan / must_not_upgrade 无丢失
- 压缩后回答质量无明显下降

---

## Phase 4 — Standard Compression + Rehydration

### 目标
实现完整闭环：压缩 + 回填。

### 实现
- `capsule_only` 可从 active 移出，只保留 capsule
- `retrievable` 外存索引
- 引入 `context_rehydrator`
- old topic / tool state / artifact ref 可按需回填

### 验收
- 长会话可持续运行
- 旧话题切回成功率高
- 回填精准度达标，waste rate 可控

---

## Phase 5 — Enforced + Gate Integration

### 目标
将该能力纳入正式治理壳。

### 实现
- metrics 接入 dashboard
- doctor / preflight 检查
- longrun / testbot / replay 集成
- 定义 fail / warn / warn_soft 规则

### 验收
- Gate A/B/C 全通过
- regression 稳定
- replay integrity 不下降

---

## 13. 文件与目录建议

```text
POLICIES/
 CONTEXT_PRESSURE_GOVERNANCE.md

schemas/
 session_capsule.v1.schema.json
 context_compression_event.v1.schema.json

openemotion/runtime/
 context_pressure_manager.py
 context_classifier.py
 session_capsule_builder.py
 memory_pointer_emitter.py
 context_rehydrator.py
 compression_audit_writer.py

tools/
 context-pressure-observer
 context-capsule-build
 context-rehydrate
 context-pressure-doctor

tests/
 test_context_classifier.py
 test_session_capsule_builder.py
 test_context_rehydrator.py
 test_context_pressure_manager.py
 test_context_replay_integrity.py
 test_context_open_loops_survival.py
 test_context_response_contract_survival.py

artifacts/
 context_pressure/
 shadow/
 capsules/
 metrics/
 reports/
```

---

## 14. 必做测试集

### T1. resident 不丢失
验证：
- task_goal
- open_loops
- response_plan
- must_include / must_not_upgrade
- tool state
在压缩前后保持一致。

### T2. 胶囊可恢复会话骨架
给定旧会话，使用 capsule 能重构：
- 正在做什么
- 已决定什么
- 还差什么
- 有什么约束

### T3. 检索回填不会乱灌历史噪声
只回填与当前问题直接相关的片段。

### T4. replay integrity
旧 run 的压缩/回填行为在 replay 下可重现。

### T5. old topic re-entry
用户切回旧主题时，系统能恢复关键信息而不是泛泛而谈。

### T6. longrun degradation
长跑多次压缩后，不出现明显的：
- commitment drift
- tone drift
- state truth drift
- lost_open_loop

### T7. failure injection
人为损坏：
- 缺 vector index
- capsule schema mismatch
- retrieval timeout
- artifact missing
验证降级策略是否正确。

---

## 15. 降级策略

发生以下问题时，必须安全降级：

### Case A. vector index 不可用
- 禁止假装检索成功
- 退回 capsule-only 模式
- 标记 retrievable 内容暂不可回填

### Case B. capsule 损坏 / schema 不兼容
- 拒绝加载损坏 capsule
- 回退到最近一个可验证 capsule
- 写审计告警

### Case C. rehydration 失败
- 不允许编造缺失上下文
- 仅用 resident + 当前输入继续
- 标记信息不足

### Case D. compression 后 resident 缺项
- 视为 P0 缺陷
- 立即 fail fast 或至少 hard warn

---

## 16. 对 cc-godmode 的执行要求

1. 先做 **Phase 0–2**，不要直接上全自动强压缩。
2. 所有协议、schema、artifact 路径先冻结，再写运行时代码。
3. 先跑 shadow 样本，观察真实膨胀分布，再定阈值。
4. `response_plan / intent_contract / open_loops / tool_state` 必须列为 resident，不得在 v1 放宽。
5. 回填必须最小化；默认宁缺勿滥，禁止为了“回答更丰富”而乱灌历史。
6. replay 必须读取当时的 capsule 与 compression event，禁止用未来 store 重构旧压缩逻辑。
7. 所有输出必须走 Gate A / Gate B / Gate C。

---

## 17. 完成定义（Definition of Done）

只有同时满足以下条件，才算完成：

1. 已有 spec / schema / runbook / doctor
2. 已有 shadow observation 数据
3. 已有稳定 `session_capsule.v1`
4. 已有 light + standard compression 实现
5. 已有按需回填实现
6. replay integrity 测试通过
7. open loops / response contract 生存测试通过
8. longrun 不出现明显上下文漂移退化
9. Gate A/B/C 全通过
10. 能给出一份 metrics + risk report，证明该能力提升了长任务连续性，而不是只降低 token

---

## 18. 给项目负责人的最终判断

这是一个**必须做**的底层能力，但它现在的正确做法是：

- 先作为 **MVP11.5-C 基础设施支线** 落地
- 直接服务 **状态主权 / 表达主权稳定化**
- 为 **MVP12 developmental core** 提供长期运行容器
- 为 **MVP13 persistent self-model** 提供跨时间连续性的治理底座

不要把它做成“聊天摘要器”。

要把它做成：

**可治理、可回放、可检索、可持续运行的上下文主存系统。**
</file>
assistant: This is a solid infrastructure spec. The key insight is correct: context pressure management isn't "summarization" — it's a governed memory hierarchy with replay integrity.

**Quick assessment:**

| Aspect | Status |
|--------|--------|
| Strategic positioning | ✅ Correct (MVP11.5-C foundation) |
| P1-P5 principles | ✅ Sound (no vector-as-truth, Dot/Cycle split) |
| 4-class taxonomy | ✅ Clear (resident/capsule/retrievable/evictable) |
| Phase 0-5 approach | ✅ Conservative (shadow first, enforce later) |
| Gate integration | ✅ Aligned with existing patterns |

**One clarification needed before starting Phase 0:**

The spec references `openemotion/runtime/` for module placement. Given the current codebase structure:
- `emotiond/` is the core package
- `integrations/openclaw/` for hooks
- `tools/` for CLI tools

Should I place the new modules under `emotiond/runtime/` or create a new `context_pressure/` top-level package? The former keeps it with emotiond core; the latter treats it as cross-cutting infrastructure.

Also: this is substantial work (Phase 0-5). Should I spawn a sub-agent to execute Phase 0 in parallel with our current conversation, or do you want to walk through it interactively?
user: Conversation info (untrusted metadata):
```json
{
  "message_id": "7059",
  "sender_id": "8420019401",
  "sender": "Moonlight",
  "timestamp": "Fri 2026-03-06 10:51 CST"
}
```

Sender (untrusted metadata):
```json
{
  "label": "Moonlight (8420019401)",
  "id": "8420019401",
  "name": "Moonlight"
}
```

先不做 我发错了
assistant: Got it. Filed for later — MVP11.5-C Context Pressure spec is saved. What else?
user: [media attached: /home/moonlight/.openclaw/media/inbound/OPENCLAW_CHAT_CONTEXT_COMPRESSION_PLAN---68fa2668-1a99-4269-b115-bda3fc8c5a58.md (text/markdown) | /home/moonlight/.openclaw/media/inbound/OPENCLAW_CHAT_CONTEXT_COMPRESSION_PLAN---68fa2668-1a99-4269-b115-bda3fc8c5a58.md]
To send an image back, prefer the message tool (media/path/filePath). If you must inline, use MEDIA:https://example.com/image.jpg (spaces ok, quote if needed) or a safe relative path like MEDIA:./image.jpg. Avoid absolute paths (MEDIA:/...) and ~ paths — they are blocked for security. Keep caption in the text body.
Conversation info (untrusted metadata):
```json
{
  "message_id": "7061",
  "sender_id": "8420019401",
  "sender": "Moonlight",
  "timestamp": "Fri 2026-03-06 10:51 CST"
}
```

Sender (untrusted metadata):
```json
{
  "label": "Moonlight (8420019401)",
  "id": "8420019401",
  "name": "Moonlight"
}
```

[Telegram Moonlight id:8420019401 +1m Fri 2026-03-06 10:51 CST] <media:document>

<file name="OPENCLAW_CHAT_CONTEXT_COMPRESSION_PLAN---68fa2668-1a99-4269-b115-bda3fc8c5a58.md" mime="text/markdown">
# OpenClaw 日常聊天自动压缩上下文工程方案

版本：v1.0 
定位：OpenClaw 主链路基础设施 
适用范围：日常聊天 / 长会话 / 多轮问答 / 工具辅助对话 
建议归属：MVP11.5-X（聊天主链路治理支线）

---

## 1. 文档目标

本方案专门解决一个务实问题：

**当 OpenClaw 的日常聊天会话变长、上下文接近额度上限时，系统能够自动压缩旧上下文，只保留继续对话真正需要的信息，并在需要时通过检索回填历史细节。**

这不是新的“意识模块”，也不是让 LLM 自己临场决定删什么。

这是一个放在 **OpenClaw 会话编排层 / prompt builder 前面** 的基础设施能力，用来保证：

- 长对话不中断
- 模型不因为上下文膨胀而失稳
- 不丢失任务目标、未完成承诺、关键约束
- 不把历史原文全部常驻塞进 prompt
- 压缩行为可审计、可 replay、可影子观测

---

## 2. 一句话定义

**Recent Window + Resident State + Session Capsule + Vector Recall**

也就是：

- 最近几轮原始对话保留
- 当前任务/承诺/表达边界常驻
- 更早的对话压缩成结构化 capsule
- 更细节的旧内容放入向量库或索引库
- 需要时按主题或实体检索回填

---

## 3. 设计边界

### 3.1 本方案要解决的问题

1. 聊天轮数增长后 prompt 逐渐膨胀
2. 旧消息越堆越多，推理成本上升
3. 模型开始遗忘真正关键的承诺与当前目标
4. 对旧主题的恢复依赖“整段历史还在上下文里”
5. 一旦人工截断历史，系统容易断片

### 3.2 本方案不解决的问题

1. 不声称解决长期自我连续性问题
2. 不直接替代长期人格/身份模型
3. 不代替业务知识库检索系统
4. 不把“向量库召回”误当成“真正记忆”
5. 不让 LLM 自主决定治理规则

### 3.3 核心判断

**只保留 embedding / 向量索引是不够的。**

因为向量库只能帮助“找回相关内容”，不能保证保住：

- 当前未完成事项
- 当前任务目标
- 当前话语意图与表达边界
- 当前工具状态
- 哪些内容必须原样保留为真值

因此必须引入 **Resident State（常驻状态）** 和 **Session Capsule（结构化压缩胶囊）**。

---

## 4. 总体原则

### P1. 程序治理优先，LLM 不负责裁决压缩规则
压缩发生在编排层，不发生在语言层“顺手总结一下”。

### P2. Dot / Cycle 分离
- Dot：短暂、高熵、容易漂移的聊天脚手架
- Cycle：稳定、可重入、跨轮仍重要的不变量

压缩时应大量压缩 Dot，谨慎保留 Cycle。

### P3. 常驻状态不可被向量库替代
以下信息必须常驻或以结构化状态强保留：
- 当前任务目标
- 当前 open loops / commitments
- response plan / intent contract
- 当前工具状态
- 当前阶段/模式/硬约束

### P4. Anti-drift
压缩后不能导致系统“忘了自己刚刚已经决定过什么”。

### P5. 可 replay / 可审计
压缩事件本身必须记录，不能偷偷发生。

### P6. Shadow → Enforced
先做影子观测，再上线真正替换 prompt 的压缩。

---

## 5. 总体架构

```text
User Message
 │
 ▼
Session Loader
 │
 ▼
Context Budget Checker
 │
 ├── below threshold ──► Retrieval (optional) ──► Prompt Assembler ──► Model
 │
 └── exceeds threshold
 │
 ▼
 Context Compressor
 │
 ├── update resident_state.json
 ├── append capsules.jsonl
 ├── append compression_events.jsonl
 ├── write retrieval index / vector index
 ▼
 Retrieval Planner
 ▼
 Prompt Assembler
 ▼
 Model
```

---

## 6. 三层上下文模型

每次真正发给模型的上下文由三层组成。

### 6.1 Resident Layer（常驻层）
必须始终进入 prompt，且不能被普通摘要替代。

包括：

- system prompt / agent identity
- 当前会话目标
- 最近尚未完成的承诺
- response plan / intent contract
- 当前模式（例如 chat / coding / audit）
- 当前工具状态与最近关键结果
- 当前禁止越界项

### 6.2 Active Layer（活动层）
与当前对话直接相关的短期原始上下文。

建议保留：

- 最近 6–12 轮原始消息
- 最近 1–3 次关键工具返回
- 当前轮最相关的最近上下文块

### 6.3 Recall Layer（回填层）
平时不常驻，只在需要时检索回填。

包括：

- 旧会话压缩 capsule
- 向量召回的历史细节块
- 旧决策与历史方案
- 过去出错记录与修复记录

---

## 7. 需要持久化的文件与状态

建议在 OpenClaw 的每个 session 目录中维护以下文件：

```text
sessions/<session_id>/
 raw.jsonl # 原始对话与工具事件真值日志
 active_state.json # 当前常驻状态
 capsules.jsonl # 压缩胶囊日志
 compression_events.jsonl # 每次压缩事件
 retrieval_cache.jsonl # 回填记录与命中来源
 budget_snapshots.jsonl # token预算观测
```

若已有统一 memory / vector 层，则另外维护：

```text
memory/
 vector/session_capsules/
 vector/chat_chunks/
 symbolic/open_loops/
 symbolic/decisions/
```

---

## 8. 核心数据结构

### 8.1 active_state.json

```json
{
 "session_id": "sess_abc",
 "task_goal": "修复 OpenClaw 上下文压缩主链路",
 "mode": "engineering",
 "response_contract": {
 "speaker_mode": "advisor",
 "core_points": [
 "先给可实施方案",
 "不要把压缩当长期自我模块"
 ],
 "must_not_upgrade": [
 "certainty",
 "commitment",
 "tone"
 ]
 },
 "open_loops": [
 {
 "id": "loop_1",
 "text": "还未决定是否先 shadow 再 enforced",
 "priority": "high",
 "status": "open"
 }
 ],
 "hard_constraints": [
 "不能只靠向量库保存当前状态",
 "压缩事件必须可审计"
 ],
 "recent_tools": [
 {
 "tool": "memory_search",
 "status": "ok",
 "summary": "找到2条相关历史决策"
 }
 ]
}
```

### 8.2 capsule record

```json
{
 "capsule_id": "cap_20260306_001",
 "session_id": "sess_abc",
 "source_turn_range": [12, 31],
 "topic": "OpenClaw 会话压缩设计",
 "summary": "讨论了 resident layer、open loops、向量回填边界。",
 "decisions": [
 "压缩发生在编排层",
 "只靠 embedding 不够"
 ],
 "open_loops": [
 "是否增加 retrieval cache TTL"
 ],
 "hard_constraints": [
 "response plan 必须常驻"
 ],
 "entities": [
 "OpenClaw",
 "session capsule",
 "vector recall"
 ],
 "retrieval_keys": [
 "context compression",
 "session capsule",
 "open loops"
 ],
 "reconstructable": true,
 "created_at": "2026-03-06T10:00:00-06:00"
}
```

### 8.3 compression event

```json
{
 "event_id": "cmp_20260306_001",
 "session_id": "sess_abc",
 "trigger": "token_ratio_threshold",
 "pressure_level": "standard",
 "before": {
 "estimated_tokens": 92000,
 "ratio": 0.86
 },
 "after": {
 "estimated_tokens": 41000,
 "ratio": 0.38
 },
 "resident_kept": [
 "task_goal",
 "open_loops",
 "response_contract",
 "recent_tools"
 ],
 "capsules_created": [
 "cap_20260306_001"
 ],
 "evicted_turn_ranges": [
 [12, 31]
 ],
 "vector_indexed": true,
 "mode": "shadow",
 "created_at": "2026-03-06T10:00:02-06:00"
}
```

---

## 9. 压缩分类策略

### 9.1 必须保留（Resident）

永远不可直接淘汰：

- 当前任务目标
- 当前未完成承诺（open loops）
- response_plan / intent_contract
- 当前模式与边界
- 当前工具状态
- 最近一轮用户消息
- 最近一轮模型回应

### 9.2 应保留为原文（Active Window）

- 最近 6–12 轮原始对话
- 最近关键工具结果
- 当前主题正在推进的关键上下文

### 9.3 应压缩为 capsule

- 超出活动窗口的普通对话
- 已完成的讨论展开
- 较长的解释过程
- 历史比较与备选路线

### 9.4 可入向量库 / 索引库

- 历史技术细节
- 旧 bug 与修复
- 长篇方案讨论
- 旧会话主题块
- 历史 capsule

### 9.5 可直接淘汰

- 寒暄
- 重复感谢
- 无状态变化的重复确认
- 与当前任务无关的岔题

---

## 10. 压缩触发阈值

建议采用三档压力等级。

### Level 1：轻压缩
触发：token 使用率 ≥ 70%

动作：
- 生成候选 capsule
- 记录 budget snapshot
- shadow 模式下只观测，不替换 prompt

### Level 2：标准压缩
触发：token 使用率 ≥ 85%

动作：
- 将最旧的原始对话块压缩为 capsule
- 仅保留最近活动窗口
- 关键细节写入向量索引
- prompt 中移除被压缩原文

### Level 3：强压缩
触发：token 使用率 ≥ 92%

动作：
- 只保留最近 4–6 轮原文
- resident state 强制常驻
- 历史细节全部依赖 capsule + retrieval 回填
- 若仍超限，降低 recall 注入量

---

## 11. 回填策略（Retrieval）

压缩后不是每轮都检索，只在真正需要时回填。

### 11.1 触发条件

满足任一条件时触发检索：

- 用户重新提到旧主题
- 消息中出现模块名 / 文件名 / 分支名 / 任务名
- 用户说“之前提过”“上次说过”
- 当前任务需要历史参数
- 当前 active context 无法支撑正确回答

### 11.2 检索源优先级

1. 当前 session 的 capsules
2. 当前 session 的历史 raw chunk 索引
3. 跨 session 的相关 capsule
4. 外部业务知识库（如有）

### 11.3 回填上限

必须限制回填量，避免“省下的 token 又被历史全吃回去”。

建议：

- 每次最多回填 2–4 个片段
- 每个片段控制在短块
- 优先回填结构化决策而非长原文

---

## 12. Prompt Assembler 规则

最终 prompt 组装顺序建议如下：

1. system / policy / identity
2. resident state
3. 当前用户消息
4. active window
5. retrieval snippets（若触发）
6. 最近关键工具结果

并明确加入一段机器可读约束：

```text
Use resident_state as authority for current commitments and task context.
Use retrieval snippets as supporting history, not as license to upgrade certainty or commitment.
Do not infer missing commitments from compressed history.
```

---

## 13. 建议新增模块

### 13.1 context-budget-check
职责：
- 估算当前 prompt token 预算
- 输出 pressure level
- 生成 budget snapshot

### 13.2 context-compress
职责：
- 根据策略从 raw/history 中选择可压缩范围
- 触发 capsule 构建
- 更新 active_state
- 写 compression event

### 13.3 capsule-builder
职责：
- 从对话范围中提取 decisions/open_loops/constraints/entities
- 输出结构化 capsule

### 13.4 context-retrieve
职责：
- 根据当前用户消息与 active_state 生成 retrieval query
- 从 capsule/vector/source 中回填最相关片段

### 13.5 prompt-assemble
职责：
- 按顺序拼装最终 prompt
- 控制 resident/active/recall 三层预算

### 13.6 context-shadow-report
职责：
- 汇总压缩命中率、回填命中率、误压缩率
- 输出 readiness 报告

---

## 14. 最小算法流程

```text
on_user_message(msg):
 state = load_active_state(session)
 history = load_recent_history(session)
 budget = estimate_budget(state, history, msg)

 if budget.ratio >= threshold:
 plan = build_compression_plan(state, history)
 if mode == shadow:
 log_shadow_plan(plan)
 else:
 apply_compression(plan)
 index_capsules(plan.capsules)

 retrieval = maybe_retrieve(msg, state)
 prompt = assemble_prompt(state, msg, history, retrieval)
 response = call_model(prompt)
 persist_turn(msg, response, tool_events)
```

---

## 15. Rollout 方案

### Phase 0：Spec Freeze
目标：冻结 schema、模块边界、压缩分类规则。

交付：
- 本文档
- capsule schema
- compression event schema
- budget snapshot schema

### Phase 1：Shadow Observation
目标：只观测，不真正替换 prompt。

动作：
- 每轮估算预算
- 达阈值时生成“如果要压缩，将会压什么”
- 记录 capsule 候选与影子报告

过关标准：
- 能稳定识别应压缩范围
- 不误判 resident state
- open loops 抽取准确率达标

### Phase 2：Light Enforced
目标：只压缩最旧普通对话块。

动作：
- 保留较大的 active window
- capsule 写入并参与少量回填
- 验证真实对话连续性

过关标准：
- 聊天连续性不明显下降
- 用户追问旧话题可恢复
- 无明显 commitments 丢失

### Phase 3：Standard Enforced
目标：标准化三层上下文模型。

动作：
- resident/active/recall 正式生效
- 引入 retrieval cache
- 引入多档阈值

### Phase 4：Hardening + Gate
目标：把误压缩、漏回填、commitment 丢失纳入 gate。

---

## 16. 质量指标

### 16.1 预算类
- avg_prompt_tokens
- p95_prompt_tokens
- compression_trigger_rate
- compression_gain_ratio

### 16.2 连续性类
- old_topic_recovery_rate
- commitment_preservation_rate
- open_loop_recall_rate
- tool_state_preservation_rate

### 16.3 风险类
- false_compression_rate
- over_retrieval_rate
- hallucinated_commitment_rate
- stale_recall_rate

### 16.4 用户体验类
- long_chat_success_rate
- user_correction_rate
- “你忘了/你刚才说过” 触发率

---

## 17. 测试设计

### T1. 长会话膨胀测试
构造 100+ 轮对话，验证能否在阈值触发后稳定压缩。

### T2. 旧主题恢复测试
前 30 轮讨论 A，后 40 轮讨论 B，第 71 轮回到 A，验证 capsule + retrieval 能否恢复关键信息。

### T3. open loops 保留测试
会话中插入多个未完成事项，验证压缩后仍能继续推进。

### T4. commitment 边界测试
验证压缩后不会把“建议”升级成“承诺”，不会把“暂定结论”升级成“最终结论”。

### T5. 工具状态连续性测试
验证最近工具结果与当前工具状态不会因为压缩而丢失。

### T6. 强压缩回退测试
在 92% 以上压力下验证系统仍能保住 resident state。

### T7. replay / audit 测试
验证 compression_events 与 capsule 日志可被追踪、可复现分析。

---

## 18. 主要风险与防护

### 风险 1：摘要漂移
问题：capsule 把原意改写了。

防护：
- capsule 以结构化字段为主
- 决策/约束字段尽量抽取而非自由重写
- shadow 阶段先观察误差

### 风险 2：只靠向量库导致当前状态丢失
防护：
- resident state 单独持久化
- open loops 与 response contract 强常驻

### 风险 3：检索过量导致再次爆 context
防护：
- retrieval 上限
- 短块优先
- 召回后再做 relevance 截断

### 风险 4：过度压缩导致聊天断片
防护：
- 先 light enforced
- 活动窗口不要一上来压得太短
- 追踪 old_topic_recovery_rate

### 风险 5：压缩逻辑不可审计
防护：
- 每次压缩必须写 compression_events.jsonl
- 保留 source_turn_range 与 capsule_id 映射

---

## 19. 建议交付清单

### 文档 / 协议
- `POLICIES/CONTEXT_COMPRESSION.md`
- `schemas/session_capsule.v1.schema.json`
- `schemas/compression_event.v1.schema.json`
- `schemas/active_state.v1.schema.json`

### 工具 / 模块
- `tools/context-budget-check`
- `tools/context-compress`
- `tools/context-retrieve`
- `tools/prompt-assemble`
- `tools/context-shadow-report`

### 测试
- `tests/context/test_budget_thresholds.py`
- `tests/context/test_capsule_builder.py`
- `tests/context/test_open_loop_preservation.py`
- `tests/context/test_old_topic_recall.py`
- `tests/context/test_commitment_boundary_after_compress.py`

### 产物
- `artifacts/context_compression/shadow_report.json`
- `artifacts/context_compression/readiness.md`
- `artifacts/context_compression/metrics.json`

---

## 20. cc-godmode 任务拆分建议

### Task 1：冻结协议与 schema
目标：定义 active_state / capsule / compression_event 三类 schema。

验收：
- schema 可校验
- 示例数据可通过

### Task 2：实现 budget checker
目标：在每轮 prompt 组装前估算 token 压力等级。

验收：
- 输出 70/85/92 三档阈值结果
- 生成 budget snapshot

### Task 3：实现 capsule builder
目标：从历史对话段中抽取 decisions/open_loops/constraints/entities。

验收：
- 结构化字段完整
- open loops 抽取可测试

### Task 4：实现 shadow compression
目标：先只记录“将要压缩什么”，不改主 prompt。

验收：
- shadow 报告可读
- resident 状态未误删

### Task 5：实现 retrieval planner
目标：在旧主题回归时从 capsule/vector 中回填短片段。

验收：
- old_topic_recovery 测试通过
- 检索量受控

### Task 6：实现 light enforced
目标：先把最旧普通对话块真正压缩替换。

验收：
- 长会话不中断
- commitment/open loops 无明显丢失

### Task 7：接入 metrics 与 gate
目标：把误压缩、漏回填、承诺丢失率纳入治理链。

验收：
- readiness 报告产出
- 可决定是否进入更强 enforced

---

## 21. 最终建议

对 OpenClaw 日常聊天来说，最优方案不是“上下文快满时让 LLM 写一段总结”，而是：

**用程序侧治理把聊天历史拆成：常驻状态、最近原文窗口、结构化压缩胶囊，以及按需回填的检索层。**

这样做有四个直接好处：

1. 能稳定支撑长会话
2. 不会把真正关键的承诺和状态丢掉
3. 能在旧主题回归时恢复历史细节
4. 能把压缩行为纳入审计与 gate，而不是黑箱发生

---

## 22. 一句话交付定义

**把 OpenClaw 从“全靠长聊天上下文硬撑”的模式，升级成“会话状态常驻 + 历史可压缩 + 细节可回填”的可治理聊天系统。**
</file>
assistant: This one's more concrete — OpenClaw-specific implementation blueprint for chat context compression. 

**Key differences from the previous spec:**
- This targets the **session orchestration layer** (not emotiond runtime)
- Focuses on **daily chat UX** rather than developmental core
- Practical rollout: Shadow → Light → Standard → Gate

**Notable design choices:**
- `active_state.json` as the resident authority
- `capsules.jsonl` for compressed history
- Retrieval triggered by explicit signals (topic mention, "之前说过")

Filed alongside the previous spec. Want me to review both for consistency gaps, or save them for later execution?
user: Conversation info (untrusted metadata):
```json
{
  "message_id": "7063",
  "sender_id": "8420019401",
  "sender": "Moonlight",
  "timestamp": "Fri 2026-03-06 10:52 CST"
}
```

Sender (untrusted metadata):
```json
{
  "label": "Moonlight (8420019401)",
  "id": "8420019401",
  "name": "Moonlight"
}
```

请用中文
assistant: 明白。两份 spec 已存档：

1. **CONTEXT_PRESSURE_MEMORY_GOVERNANCE_SPEC** — 治理框架层，服务 MVP11.5-C / MVP12 / MVP13
2. **OPENCLAW_CHAT_CONTEXT_COMPRESSION_PLAN** — OpenClaw 主链路实现层，日常聊天场景

后续需要执行时再展开。还有其他事吗？
