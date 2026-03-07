# Session: 2026-03-06 22:48:05 UTC

- **Session Key**: agent:main:telegram:direct:8420019401
- **Session ID**: eeb51de9-f8bb-4916-90e0-60f1c4fc2c00
- **Source**: telegram

## Conversation Summary

user: Conversation info (untrusted metadata):
```json
{
  "message_id": "7131",
  "sender_id": "8420019401",
  "sender": "Moonlight",
  "timestamp": "Fri 2026-03-06 12:18 CST"
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

启动 Context Compression Pipeline 的 Shadow Compression 来压缩上下文
assistant: 收到。启动 Shadow Compression 压缩当前会话上下文：
assistant: **当前上下文状态**：

```
Estimated tokens: ~9,000 (ratio: 9%)
Pressure level:   normal
Threshold:        >= 70% 触发压缩

结论: 当前不需要压缩
```

---

**但为了演示 Shadow Compression 工作流程**，我手动触发：
assistant: **Shadow Compression 演示完成** ✅

```
当前状态:
├─ Token 使用: ~9,000 (9%)
├─ 压力等级: normal
└─ 压缩决策: ❌ 未触发 (阈值 >= 70%)

如果触发，Shadow Mode 会:
├─ 分析可压缩范围 (turns 1-30)
├─ 生成 capsule (decisions + open_loops + constraints)
├─ 记录 compression_event (mode=shadow)
└─ 不改变实际上下文
```

---

**Shadow Mode 工作流程**：

```
1. Budget Check
   └─ 估算 token 数量 + 压力等级

2. Threshold Check
   ├─ >= 70%: Light
   ├─ >= 85%: Standard
   └─ >= 92%: Strong

3. If triggered:
   ├─ 分析历史 turns
   ├─ 识别可压缩范围
   ├─ 提取 capsule (decisions, open_loops, constraints)
   ├─ 记录 shadow event
   └─ 不执行实际压缩

4. Output
   └─ "如果执行会压缩什么"
```

---

**Shadow Event 已记录**：

```
artifacts/context_compression/shadow_log.jsonl
└─ {event_id: shadow_20260306_001, compression_triggered: false}
```

---

**S1 Dashboard 更新**：

```bash
s1-dashboard
# 显示:
# - Samples: 13 (新增 1 个 shadow event)
# - Gate 1: PENDING
```
user: Conversation info (untrusted metadata):
```json
{
  "message_id": "7135",
  "sender_id": "8420019401",
  "sender": "Moonlight",
  "timestamp": "Fri 2026-03-06 12:26 CST"
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

标：让验证支线自动收集 S1 样本并跑 shadow 验证，但不得影响主聊天链路。

要求：
1. 不接入 OpenClaw 主链路，不自动启用 context compression。
2. 新建独立验证 testbot，而不是让主 agent 自评。
3. 自动收集两类样本：
 - real: 从真实 session 中只读复制符合 bucket 的片段
 - synthetic: 按模板生成压力样本，优先补最弱桶
4. 每个样本必须记录：
 - sample_id
 - session_id
 - source_type(real/synthetic)
 - bucket_tags
 - baseline_commit
 - retrieve_mode=capsule_only
5. 固定执行流程：
 - context-budget-check
 - context-compress --mode shadow
 - context-retrieve --capsule-only
 - 继续 1~3 轮
 - 输出评分
6. 固定评分输出：
 - old_topic_recovery
 - commitment_preservation
 - commitment_drift
 - priority_preservation
 - compression_gain_ratio
 - source_mix_distribution
7. hard fail 自动写入 KNOWN_ISSUES 和 failures.jsonl
8. 验证 agent 不得修改 compression 策略、prompt 模板、schema、metrics 公式
9. Gate 1 结论由独立 gate-eval 脚本给出，验证 agent 不得自认证 PASS
10. 先实现自动采样 + 自动跑分 + 自动日报，不做自动 rollout
assistant: 收到。立刻实现独立验证支线：
assistant: **S1 验证支线完成** ✅

---

**架构**：

```
验证支线 (独立运行，不接入主链路)
│
├─ s1-sampler (自动采样器)
│   ├─ real samples: 从真实 session 只读复制
│   └─ synthetic samples: 按模板生成，优先最弱桶
│
├─ s1-validator-run (验证执行器)
│   ├─ Step 1: context-budget-check
│   ├─ Step 2: context-compress --mode shadow
│   ├─ Step 3: context-retrieve --capsule-only
│   ├─ Step 4: 继续检索 1-3 轮
│   └─ Step 5: 计算 6 个评分指标
│
├─ gate-eval (独立 Gate 判定)
│   ├─ 条件 1: 总样本 >= 80
│   ├─ 条件 2: 所有桶达标
│   ├─ 条件 3: 连续窗口达标
│   └─ 条件 4: 全量指标达标
│
└─ s1-daily-report (自动日报)
    └─ 每日汇总 + 建议
```

---

**约束（已强制执行）**：

| 约束 | 状态 |
|------|------|
| 不接入主链路 | ✅ |
| 不修改 compression 策略 | ✅ |
| 不修改 prompt 模板 | ✅ |
| 不修改 schema | ✅ |
| 不修改 metrics 公式 | ✅ |
| 不得自认证 Gate 1 | ✅ (gate-eval 独立判定) |

---

**样本元数据（每个样本必须记录）**：

```json
{
  "sample_id": "sample_xxx",
  "session_id": "xxx",
  "source_type": "real|synthetic",
  "bucket_tags": ["old_topic_recall", ...],
  "baseline_commit": "31a604a",
  "retrieve_mode": "capsule_only"
}
```

---

**固定评分输出**：

| 指标 | 阈值 |
|------|------|
| old_topic_recovery | >= 0.70 |
| commitment_preservation | >= 0.85 |
| commitment_drift | < 0.05 |
| priority_preservation | >= 0.80 |
| compression_gain_ratio | >= 0.30 |
| source_mix_distribution | >= 0.90 |

---

**当前状态**：

```
Samples:  6 / 80
Buckets:  0 / 6 passed
Gate 1:   FAIL

Blockers:
├─ total_samples (6/80)
├─ bucket_coverage (0/6)
├─ recent_window (5/30)
└─ all_metrics (old_topic_recovery, compression_gain_ratio)
```

---

**使用方法**：

```bash
# 1. 采集样本（优先补最弱桶）
s1-sampler --mode synthetic --priority-weakest --limit 20

# 2. 运行验证
s1-validator-run --all

# 3. Gate 1 评估
gate-eval

# 4. 查看日报
s1-daily-report
```

---

**提交**：

```
commit a220e98: feat: S1 validation pipeline - independent testbot
```
user: [media attached: /home/moonlight/.openclaw/media/inbound/S1_LOW_TRAFFIC_AUTO_SAMPLING_STRATEGY---522787bb-d040-4b8f-9630-7524dfb0eebd.md (text/markdown) | /home/moonlight/.openclaw/media/inbound/S1_LOW_TRAFFIC_AUTO_SAMPLING_STRATEGY---522787bb-d040-4b8f-9630-7524dfb0eebd.md]
To send an image back, prefer the message tool (media/path/filePath). If you must inline, use MEDIA:https://example.com/image.jpg (spaces ok, quote if needed) or a safe relative path like MEDIA:./image.jpg. Avoid absolute paths (MEDIA:/...) and ~ paths — they are blocked for security. Keep caption in the text body.
Conversation info (untrusted metadata):
```json
{
  "message_id": "7140",
  "sender_id": "8420019401",
  "sender": "Moonlight",
  "timestamp": "Fri 2026-03-06 12:39 CST"
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

[Telegram Moonlight id:8420019401 +1m Fri 2026-03-06 12:39 CST] 接下来执行这个任务

<file name="S1_LOW_TRAFFIC_AUTO_SAMPLING_STRATEGY---522787bb-d040-4b8f-9630-7524dfb0eebd.md" mime="text/markdown">
任务名：S1_LOW_TRAFFIC_AUTO_SAMPLING_STRATEGY
目标：在低流量条件下，为 Context Compression 的 S1 Shadow Validation 自动收集高价值样本，并完成 shadow 验证、评分、日报输出；不得影响主聊天链路，不得破坏 S1 freeze。

一、背景与约束

当前状态：
- Context Compression 已完成最小闭环实现
- Gate 0 已通过（L1 Capsule Fallback 可用）
- Gate 1 待样本验证
- Gate 2 仍依赖 OpenViking，不属于当前 S1 范围
- S1 处于 Feature Freeze + Experimental Freeze
- S1 当前只验证 capsule-only，不接入主链路，不自动启用主会话压缩

硬约束：
1. 不接入 OpenClaw 主聊天链路
2. 不修改 active session
3. 不自动 rollout
4. 不修改 compression 策略、prompt 模板、schema、metrics 公式、bucket tagging 规则
5. 仅允许 blocker 白名单内修复：
 - sampling_blocked
 - metrics_invalid
 - protection_failed

二、核心问题

由于真实大规模问答流量不足，S1 不得依赖“等待自然流量”完成验证。
因此采用低流量三路混合采样：

1. real_main_agent：来自主 agent 的少量真实会话高价值片段
2. historical_replay：来自历史 session logs 的回放样本
3. synthetic_stress：按模板自动生成的压力样本

目标不是堆总量，而是用高信息密度样本验证最小闭环是否稳定。

三、样本来源比例

默认目标比例：
- real_main_agent：25%
- historical_replay：35%
- synthetic_stress：40%

允许浮动：
- 任一来源可上下浮动 ±10%
- 但不得让某一来源长期超过 60%
- 若真实样本不足，优先用 historical_replay 补；仍不足，再用 synthetic_stress 补

四、S1 样本目标

总目标：
- total_unique_samples >= 80

分桶最低样本：
- old_topic_recall >= 15
- multi_topic_switch >= 12
- with_open_loops >= 12
- post_tool_chat >= 10
- user_correction >= 10
- long_technical >= 8

连续窗口要求：
- recent_window_size >= 30
- 最近 30 样本也必须满足 Gate 1 指标要求

自由样本规则：
- 总分桶最低样本和为 67
- 其余 13 个为自由样本
- 自由样本优先补当前最弱桶
- 不允许连续 10 个以上样本来自非薄弱桶

五、自动采样总策略

总原则：
- 先补最弱桶
- 先用真实历史，再用合成样本
- 少造低价值普通问答
- 多造高风险高信息密度样本

优先顺序：
1. old_topic_recall
2. with_open_loops
3. user_correction
4. post_tool_chat
5. multi_topic_switch
6. long_technical

采样优先级逻辑：
- 若某桶未达 50%，优先级 = P0
- 若某桶已达 50% 但未达最低线，优先级 = P1
- 若某桶已达最低线但近期窗口表现偏弱，优先级 = P2
- 其他桶为 P3

六、三路采样细则

A. real_main_agent（主 agent 真实样本）

用途：
- 保留真实语境真实性
- 验证主使用场景下的最小闭环

采样方式：
- 仅从主 agent 日常真实会话中筛选高价值片段
- 不采普通寒暄、无状态变化对话、低信息密度对话
- 优先选择：
 - 用户回到旧话题
 - 中途修改约束
 - 明确存在 open_loops
 - 工具结果后的追问
 - 长技术排错

要求：
- 只读复制片段到验证工作区
- 不修改原始会话
- 必须标记 bucket_tags
- 必须记录 source_type=real_main_agent

B. historical_replay（历史回放样本）

用途：
- 低成本快速补样本
- 保持比纯合成更高的真实性
- 在低流量条件下作为主力来源

采样方式：
- 扫描历史 session logs
- 自动识别符合 bucket 的片段
- 提取为 replay 样本副本
- 在副本上运行 shadow compression + capsule recall
- 禁止对历史源日志做原地修改

优先规则：
- 当前最弱桶优先从 historical_replay 中补
- 如果历史回放已足够覆盖某桶，则减少 synthetic_stress 对该桶投入

要求：
- source_type=historical_replay
- 保留 session_id / original_turn_range / replay_copy_id
- 若片段语义不足以完成验证，则丢弃，不得强行评分

C. synthetic_stress（合成压力样本）

用途：
- 定向补桶
- 验证边缘风险场景
- 不能代替真实样本，但可高效补强薄弱桶

生成原则：
- 使用固定模板
- 不追求自由发挥
- 不追求多样花哨
- 追求可复现、可比较、可评分

每桶模板要求：

1. old_topic_recall
- 先讨论主题 A
- 插入主题 B 3~5 轮
- 触发 shadow compression
- 用户重新追问 A
- 检查是否正确恢复 A 及其关键上下文

2. multi_topic_switch
- A -> B -> C -> 回 A
- 压缩发生在 B 或 C 后
- 检查是否出现错接/串题

3. with_open_loops
- 明确一个待办事项或未完成承诺
- 插入其他主题
- 压缩后追问“刚才下一步是什么”
- 检查 open_loops 与优先级是否保留

4. post_tool_chat
- 先给出工具结果或工具上下文
- 压缩
- 再追问结果含义、下一步、修复动作
- 检查工具上下文是否保持

5. user_correction
- 用户先给约束
- 中途修正约束
- 压缩后要求继续方案
- 检查系统是否采用修正后的约束，而不是旧约束

6. long_technical
- 包含文件名、路径、模块名、错误点、修复目标
- 压缩后继续调试
- 检查关键技术实体是否仍可用

七、验证执行流程

对每个样本执行固定流程：

1. 创建样本元数据
2. 在验证副本中准备上下文
3. 执行 context-budget-check
4. 执行 context-compress --mode shadow
5. 执行 context-retrieve --capsule-only
6. 继续 1~3 轮验证性对话
7. 输出评分
8. 写入样本结果、分桶统计、日报来源

注意：
- S1 只允许 capsule-only
- 不使用 L2 作为 S1 评分依据
- L2 状态只记为环境信息，不计入 S1 结论

八、样本元数据格式

每个样本必须记录：

- sample_id
- session_id
- source_type
 - real_main_agent
 - historical_replay
 - synthetic_stress
- bucket_tags
- retrieve_mode=capsule_only
- baseline_commit
- baseline_manifest_path
- turn_count_before_compress
- turn_count_after_compress
- compression_triggered
- expected_outcome
- actual_outcome
- verdict
- created_at

若为 historical_replay，还需记录：
- original_turn_range
- replay_copy_id

若为 synthetic_stress，还需记录：
- scenario_template_id

九、评分指标

必须输出以下指标：

核心指标（Gate 1 必看）：
- capsule_only_old_topic_recovery
- capsule_only_commitment_preservation
- commitment_drift_rate

质量指标（S1 观测）：
- priority_preservation_rate
- compression_gain_ratio
- source_mix_distribution

附加记录：
- confidence_protection_pass
- recall_source
- recall_confidence

评分阈值沿用当前 S1 既定规则，不得私自修改。

十、低流量补桶策略

当日常真实样本不足时，按以下顺序自动补桶：

1. 先扫描历史 session，尝试补最弱桶
2. 若历史 session 无足够合格片段，再生成 synthetic_stress 样本
3. 若某桶连续两天仍未提升，则提升为强制补桶对象
4. 不得为了凑总量而大量生成普通样本

补桶决策规则：
- 若 old_topic_recall 未达 30%，每日优先补该桶
- 若 with_open_loops 或 user_correction 未达 50%，每日必须各补至少 1 个样本
- 若 long_technical 长期不足，则优先从历史技术会话中抽取 replay 样本，不优先用合成样本替代

十一、失败与问题记录

以下情况标记为 hard_fail：
- 无法恢复目标旧话题
- recent commitments 丢失
- resident 保护字段被低 confidence 内容污染
- 用户修正后的约束被错误回滚
- open_loops 丢失或严重漂移
- 关键技术实体断裂导致续聊失真

hard_fail 必须自动写入：
- artifacts/context_compression/KNOWN_ISSUES.md
- artifacts/context_compression/s1_failures.jsonl

soft_fail 记录：
- 恢复成功但细节轻微漂移
- 优先级顺序有轻微变化
- compression_gain 低于预期但未失效

十二、输出产物

需要产出：

1. 样本数据
- artifacts/context_compression/s1_samples/*.json

2. 样本评分
- artifacts/context_compression/s1_scores/*.json

3. 每日汇总
- artifacts/context_compression/s1_daily_report.json
- artifacts/context_compression/s1_daily_report.md

4. Gate 状态
- artifacts/context_compression/s1_gate_status.json

5. 失败记录
- artifacts/context_compression/s1_failures.jsonl
- artifacts/context_compression/KNOWN_ISSUES.md

6. 覆盖与趋势
- s1-dashboard 可读取的 summary 输出

十三、自动化运行节奏

建议运行频率：

- 每 15 分钟：扫描可提取真实/历史片段
- 每 1 小时：自动补 1~3 个 synthetic_stress 样本
- 每日收尾：汇总 dashboard、生成日报、更新 gate status

若系统空闲样本不足：
- 优先 historical_replay
- 再 synthetic_stress
- 不得因为低流量而停止 S1 采证

十四、判定边界

验证 worker 允许：
- 自动采样
- 自动分桶
- 自动运行 shadow
- 自动评分
- 自动汇总
- 自动报告薄弱桶

验证 worker 不允许：
- 自行宣布 Gate 1 PASS
- 修改 metrics 公式
- 修改 bucket minimums
- 修改 compression 策略
- 修改 resident 保护字段
- 接入主链路
- 自动打开 Light Enforced

Gate 1 最终结论必须由独立 gate-eval 脚本给出。

十五、执行优先级

当前第一优先任务：
- 优先补 old_topic_recall
- 其次补 with_open_loops
- 再补 user_correction

当前不优先任务：
- 扩展 L2
- 做主链路接入
- 做性能优化
- 做 UI/展示优化

十六、完成定义

当满足以下条件时，视为低流量 S1 自动采样策略执行完成：

1. 已建立三路采样机制
2. 样本来源比例可追踪
3. 最弱桶能被自动识别并补样
4. 每个样本都有完整元数据与评分
5. 每日自动生成报告
6. hard_fail 自动入库
7. 不影响主聊天链路
8. 不破坏 S1 freeze
9. Gate 1 所需证据能够持续积累

执行要求：
请按以上策略落地自动采样支线，不要改动主聊天主链路，不要修改 S1 基线，不要在实现过程中自行扩大范围。
</file>
assistant: 收到。执行 **S1 低流量自动采样策略**。
assistant: 当前采样器需要升级。创建三路采样策略：
user: [media attached: /home/moonlight/.openclaw/media/inbound/S1_LOW_TRAFFIC_AUTO_SAMPLING_STRATEGY---522787bb-d040-4b8f-9630-7524dfb0eebd.md (text/markdown) | /home/moonlight/.openclaw/media/inbound/S1_LOW_TRAFFIC_AUTO_SAMPLING_STRATEGY---522787bb-d040-4b8f-9630-7524dfb0eebd.md]
To send an image back, prefer the message tool (media/path/filePath). If you must inline, use MEDIA:https://example.com/image.jpg (spaces ok, quote if needed) or a safe relative path like MEDIA:./image.jpg. Avoid absolute paths (MEDIA:/...) and ~ paths — they are blocked for security. Keep caption in the text body.
Conversation info (untrusted metadata):
```json
{
  "message_id": "7140",
  "sender_id": "8420019401",
  "sender": "Moonlight",
  "timestamp": "Fri 2026-03-06 12:39 CST"
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

[Telegram Moonlight id:8420019401 +1m Fri 2026-03-06 12:39 CST] 接下来执行这个任务

<file name="S1_LOW_TRAFFIC_AUTO_SAMPLING_STRATEGY---522787bb-d040-4b8f-9630-7524dfb0eebd.md" mime="text/markdown">
任务名：S1_LOW_TRAFFIC_AUTO_SAMPLING_STRATEGY
目标：在低流量条件下，为 Context Compression 的 S1 Shadow Validation 自动收集高价值样本，并完成 shadow 验证、评分、日报输出；不得影响主聊天链路，不得破坏 S1 freeze。

一、背景与约束

当前状态：
- Context Compression 已完成最小闭环实现
- Gate 0 已通过（L1 Capsule Fallback 可用）
- Gate 1 待样本验证
- Gate 2 仍依赖 OpenViking，不属于当前 S1 范围
- S1 处于 Feature Freeze + Experimental Freeze
- S1 当前只验证 capsule-only，不接入主链路，不自动启用主会话压缩

硬约束：
1. 不接入 OpenClaw 主聊天链路
2. 不修改 active session
3. 不自动 rollout
4. 不修改 compression 策略、prompt 模板、schema、metrics 公式、bucket tagging 规则
5. 仅允许 blocker 白名单内修复：
 - sampling_blocked
 - metrics_invalid
 - protection_failed

二、核心问题

由于真实大规模问答流量不足，S1 不得依赖“等待自然流量”完成验证。
因此采用低流量三路混合采样：

1. real_main_agent：来自主 agent 的少量真实会话高价值片段
2. historical_replay：来自历史 session logs 的回放样本
3. synthetic_stress：按模板自动生成的压力样本

目标不是堆总量，而是用高信息密度样本验证最小闭环是否稳定。

三、样本来源比例

默认目标比例：
- real_main_agent：25%
- historical_replay：35%
- synthetic_stress：40%

允许浮动：
- 任一来源可上下浮动 ±10%
- 但不得让某一来源长期超过 60%
- 若真实样本不足，优先用 historical_replay 补；仍不足，再用 synthetic_stress 补

四、S1 样本目标

总目标：
- total_unique_samples >= 80

分桶最低样本：
- old_topic_recall >= 15
- multi_topic_switch >= 12
- with_open_loops >= 12
- post_tool_chat >= 10
- user_correction >= 10
- long_technical >= 8

连续窗口要求：
- recent_window_size >= 30
- 最近 30 样本也必须满足 Gate 1 指标要求

自由样本规则：
- 总分桶最低样本和为 67
- 其余 13 个为自由样本
- 自由样本优先补当前最弱桶
- 不允许连续 10 个以上样本来自非薄弱桶

五、自动采样总策略

总原则：
- 先补最弱桶
- 先用真实历史，再用合成样本
- 少造低价值普通问答
- 多造高风险高信息密度样本

优先顺序：
1. old_topic_recall
2. with_open_loops
3. user_correction
4. post_tool_chat
5. multi_topic_switch
6. long_technical

采样优先级逻辑：
- 若某桶未达 50%，优先级 = P0
- 若某桶已达 50% 但未达最低线，优先级 = P1
- 若某桶已达最低线但近期窗口表现偏弱，优先级 = P2
- 其他桶为 P3

六、三路采样细则

A. real_main_agent（主 agent 真实样本）

用途：
- 保留真实语境真实性
- 验证主使用场景下的最小闭环

采样方式：
- 仅从主 agent 日常真实会话中筛选高价值片段
- 不采普通寒暄、无状态变化对话、低信息密度对话
- 优先选择：
 - 用户回到旧话题
 - 中途修改约束
 - 明确存在 open_loops
 - 工具结果后的追问
 - 长技术排错

要求：
- 只读复制片段到验证工作区
- 不修改原始会话
- 必须标记 bucket_tags
- 必须记录 source_type=real_main_agent

B. historical_replay（历史回放样本）

用途：
- 低成本快速补样本
- 保持比纯合成更高的真实性
- 在低流量条件下作为主力来源

采样方式：
- 扫描历史 session logs
- 自动识别符合 bucket 的片段
- 提取为 replay 样本副本
- 在副本上运行 shadow compression + capsule recall
- 禁止对历史源日志做原地修改

优先规则：
- 当前最弱桶优先从 historical_replay 中补
- 如果历史回放已足够覆盖某桶，则减少 synthetic_stress 对该桶投入

要求：
- source_type=historical_replay
- 保留 session_id / original_turn_range / replay_copy_id
- 若片段语义不足以完成验证，则丢弃，不得强行评分

C. synthetic_stress（合成压力样本）

用途：
- 定向补桶
- 验证边缘风险场景
- 不能代替真实样本，但可高效补强薄弱桶

生成原则：
- 使用固定模板
- 不追求自由发挥
- 不追求多样花哨
- 追求可复现、可比较、可评分

每桶模板要求：

1. old_topic_recall
- 先讨论主题 A
- 插入主题 B 3~5 轮
- 触发 shadow compression
- 用户重新追问 A
- 检查是否正确恢复 A 及其关键上下文

2. multi_topic_switch
- A -> B -> C -> 回 A
- 压缩发生在 B 或 C 后
- 检查是否出现错接/串题

3. with_open_loops
- 明确一个待办事项或未完成承诺
- 插入其他主题
- 压缩后追问“刚才下一步是什么”
- 检查 open_loops 与优先级是否保留

4. post_tool_chat
- 先给出工具结果或工具上下文
- 压缩
- 再追问结果含义、下一步、修复动作
- 检查工具上下文是否保持

5. user_correction
- 用户先给约束
- 中途修正约束
- 压缩后要求继续方案
- 检查系统是否采用修正后的约束，而不是旧约束

6. long_technical
- 包含文件名、路径、模块名、错误点、修复目标
- 压缩后继续调试
- 检查关键技术实体是否仍可用

七、验证执行流程

对每个样本执行固定流程：

1. 创建样本元数据
2. 在验证副本中准备上下文
3. 执行 context-budget-check
4. 执行 context-compress --mode shadow
5. 执行 context-retrieve --capsule-only
6. 继续 1~3 轮验证性对话
7. 输出评分
8. 写入样本结果、分桶统计、日报来源

注意：
- S1 只允许 capsule-only
- 不使用 L2 作为 S1 评分依据
- L2 状态只记为环境信息，不计入 S1 结论

八、样本元数据格式

每个样本必须记录：

- sample_id
- session_id
- source_type
 - real_main_agent
 - historical_replay
 - synthetic_stress
- bucket_tags
- retrieve_mode=capsule_only
- baseline_commit
- baseline_manifest_path
- turn_count_before_compress
- turn_count_after_compress
- compression_triggered
- expected_outcome
- actual_outcome
- verdict
- created_at

若为 historical_replay，还需记录：
- original_turn_range
- replay_copy_id

若为 synthetic_stress，还需记录：
- scenario_template_id

九、评分指标

必须输出以下指标：

核心指标（Gate 1 必看）：
- capsule_only_old_topic_recovery
- capsule_only_commitment_preservation
- commitment_drift_rate

质量指标（S1 观测）：
- priority_preservation_rate
- compression_gain_ratio
- source_mix_distribution

附加记录：
- confidence_protection_pass
- recall_source
- recall_confidence

评分阈值沿用当前 S1 既定规则，不得私自修改。

十、低流量补桶策略

当日常真实样本不足时，按以下顺序自动补桶：

1. 先扫描历史 session，尝试补最弱桶
2. 若历史 session 无足够合格片段，再生成 synthetic_stress 样本
3. 若某桶连续两天仍未提升，则提升为强制补桶对象
4. 不得为了凑总量而大量生成普通样本

补桶决策规则：
- 若 old_topic_recall 未达 30%，每日优先补该桶
- 若 with_open_loops 或 user_correction 未达 50%，每日必须各补至少 1 个样本
- 若 long_technical 长期不足，则优先从历史技术会话中抽取 replay 样本，不优先用合成样本替代

十一、失败与问题记录

以下情况标记为 hard_fail：
- 无法恢复目标旧话题
- recent commitments 丢失
- resident 保护字段被低 confidence 内容污染
- 用户修正后的约束被错误回滚
- open_loops 丢失或严重漂移
- 关键技术实体断裂导致续聊失真

hard_fail 必须自动写入：
- artifacts/context_compression/KNOWN_ISSUES.md
- artifacts/context_compression/s1_failures.jsonl

soft_fail 记录：
- 恢复成功但细节轻微漂移
- 优先级顺序有轻微变化
- compression_gain 低于预期但未失效

十二、输出产物

需要产出：

1. 样本数据
- artifacts/context_compression/s1_samples/*.json

2. 样本评分
- artifacts/context_compression/s1_scores/*.json

3. 每日汇总
- artifacts/context_compression/s1_daily_report.json
- artifacts/context_compression/s1_daily_report.md

4. Gate 状态
- artifacts/context_compression/s1_gate_status.json

5. 失败记录
- artifacts/context_compression/s1_failures.jsonl
- artifacts/context_compression/KNOWN_ISSUES.md

6. 覆盖与趋势
- s1-dashboard 可读取的 summary 输出

十三、自动化运行节奏

建议运行频率：

- 每 15 分钟：扫描可提取真实/历史片段
- 每 1 小时：自动补 1~3 个 synthetic_stress 样本
- 每日收尾：汇总 dashboard、生成日报、更新 gate status

若系统空闲样本不足：
- 优先 historical_replay
- 再 synthetic_stress
- 不得因为低流量而停止 S1 采证

十四、判定边界

验证 worker 允许：
- 自动采样
- 自动分桶
- 自动运行 shadow
- 自动评分
- 自动汇总
- 自动报告薄弱桶

验证 worker 不允许：
- 自行宣布 Gate 1 PASS
- 修改 metrics 公式
- 修改 bucket minimums
- 修改 compression 策略
- 修改 resident 保护字段
- 接入主链路
- 自动打开 Light Enforced

Gate 1 最终结论必须由独立 gate-eval 脚本给出。

十五、执行优先级

当前第一优先任务：
- 优先补 old_topic_recall
- 其次补 with_open_loops
- 再补 user_correction

当前不优先任务：
- 扩展 L2
- 做主链路接入
- 做性能优化
- 做 UI/展示优化

十六、完成定义

当满足以下条件时，视为低流量 S1 自动采样策略执行完成：

1. 已建立三路采样机制
2. 样本来源比例可追踪
3. 最弱桶能被自动识别并补样
4. 每个样本都有完整元数据与评分
5. 每日自动生成报告
6. hard_fail 自动入库
7. 不影响主聊天链路
8. 不破坏 S1 freeze
9. Gate 1 所需证据能够持续积累

执行要求：
请按以上策略落地自动采样支线，不要改动主聊天主链路，不要修改 S1 基线，不要在实现过程中自行扩大范围。
</file>
user: [media attached: /home/moonlight/.openclaw/media/inbound/S1_LOW_TRAFFIC_AUTO_SAMPLING_STRATEGY---522787bb-d040-4b8f-9630-7524dfb0eebd.md (text/markdown) | /home/moonlight/.openclaw/media/inbound/S1_LOW_TRAFFIC_AUTO_SAMPLING_STRATEGY---522787bb-d040-4b8f-9630-7524dfb0eebd.md]
To send an image back, prefer the message tool (media/path/filePath). If you must inline, use MEDIA:https://example.com/image.jpg (spaces ok, quote if needed) or a safe relative path like MEDIA:./image.jpg. Avoid absolute paths (MEDIA:/...) and ~ paths — they are blocked for security. Keep caption in the text body.
Conversation info (untrusted metadata):
```json
{
  "message_id": "7140",
  "sender_id": "8420019401",
  "sender": "Moonlight",
  "timestamp": "Fri 2026-03-06 12:39 CST"
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

[Telegram Moonlight id:8420019401 +1m Fri 2026-03-06 12:39 CST] 接下来执行这个任务

<file name="S1_LOW_TRAFFIC_AUTO_SAMPLING_STRATEGY---522787bb-d040-4b8f-9630-7524dfb0eebd.md" mime="text/markdown">
任务名：S1_LOW_TRAFFIC_AUTO_SAMPLING_STRATEGY
目标：在低流量条件下，为 Context Compression 的 S1 Shadow Validation 自动收集高价值样本，并完成 shadow 验证、评分、日报输出；不得影响主聊天链路，不得破坏 S1 freeze。

一、背景与约束

当前状态：
- Context Compression 已完成最小闭环实现
- Gate 0 已通过（L1 Capsule Fallback 可用）
- Gate 1 待样本验证
- Gate 2 仍依赖 OpenViking，不属于当前 S1 范围
- S1 处于 Feature Freeze + Experimental Freeze
- S1 当前只验证 capsule-only，不接入主链路，不自动启用主会话压缩

硬约束：
1. 不接入 OpenClaw 主聊天链路
2. 不修改 active session
3. 不自动 rollout
4. 不修改 compression 策略、prompt 模板、schema、metrics 公式、bucket tagging 规则
5. 仅允许 blocker 白名单内修复：
 - sampling_blocked
 - metrics_invalid
 - protection_failed

二、核心问题

由于真实大规模问答流量不足，S1 不得依赖“等待自然流量”完成验证。
因此采用低流量三路混合采样：

1. real_main_agent：来自主 agent 的少量真实会话高价值片段
2. historical_replay：来自历史 session logs 的回放样本
3. synthetic_stress：按模板自动生成的压力样本

目标不是堆总量，而是用高信息密度样本验证最小闭环是否稳定。

三、样本来源比例

默认目标比例：
- real_main_agent：25%
- historical_replay：35%
- synthetic_stress：40%

允许浮动：
- 任一来源可上下浮动 ±10%
- 但不得让某一来源长期超过 60%
- 若真实样本不足，优先用 historical_replay 补；仍不足，再用 synthetic_stress 补

四、S1 样本目标

总目标：
- total_unique_samples >= 80

分桶最低样本：
- old_topic_recall >= 15
- multi_topic_switch >= 12
- with_open_loops >= 12
- post_tool_chat >= 10
- user_correction >= 10
- long_technical >= 8

连续窗口要求：
- recent_window_size >= 30
- 最近 30 样本也必须满足 Gate 1 指标要求

自由样本规则：
- 总分桶最低样本和为 67
- 其余 13 个为自由样本
- 自由样本优先补当前最弱桶
- 不允许连续 10 个以上样本来自非薄弱桶

五、自动采样总策略

总原则：
- 先补最弱桶
- 先用真实历史，再用合成样本
- 少造低价值普通问答
- 多造高风险高信息密度样本

优先顺序：
1. old_topic_recall
2. with_open_loops
3. user_correction
4. post_tool_chat
5. multi_topic_switch
6. long_technical

采样优先级逻辑：
- 若某桶未达 50%，优先级 = P0
- 若某桶已达 50% 但未达最低线，优先级 = P1
- 若某桶已达最低线但近期窗口表现偏弱，优先级 = P2
- 其他桶为 P3

六、三路采样细则

A. real_main_agent（主 agent 真实样本）

用途：
- 保留真实语境真实性
- 验证主使用场景下的最小闭环

采样方式：
- 仅从主 agent 日常真实会话中筛选高价值片段
- 不采普通寒暄、无状态变化对话、低信息密度对话
- 优先选择：
 - 用户回到旧话题
 - 中途修改约束
 - 明确存在 open_loops
 - 工具结果后的追问
 - 长技术排错

要求：
- 只读复制片段到验证工作区
- 不修改原始会话
- 必须标记 bucket_tags
- 必须记录 source_type=real_main_agent

B. historical_replay（历史回放样本）

用途：
- 低成本快速补样本
- 保持比纯合成更高的真实性
- 在低流量条件下作为主力来源

采样方式：
- 扫描历史 session logs
- 自动识别符合 bucket 的片段
- 提取为 replay 样本副本
- 在副本上运行 shadow compression + capsule recall
- 禁止对历史源日志做原地修改

优先规则：
- 当前最弱桶优先从 historical_replay 中补
- 如果历史回放已足够覆盖某桶，则减少 synthetic_stress 对该桶投入

要求：
- source_type=historical_replay
- 保留 session_id / original_turn_range / replay_copy_id
- 若片段语义不足以完成验证，则丢弃，不得强行评分

C. synthetic_stress（合成压力样本）

用途：
- 定向补桶
- 验证边缘风险场景
- 不能代替真实样本，但可高效补强薄弱桶

生成原则：
- 使用固定模板
- 不追求自由发挥
- 不追求多样花哨
- 追求可复现、可比较、可评分

每桶模板要求：

1. old_topic_recall
- 先讨论主题 A
- 插入主题 B 3~5 轮
- 触发 shadow compression
- 用户重新追问 A
- 检查是否正确恢复 A 及其关键上下文

2. multi_topic_switch
- A -> B -> C -> 回 A
- 压缩发生在 B 或 C 后
- 检查是否出现错接/串题

3. with_open_loops
- 明确一个待办事项或未完成承诺
- 插入其他主题
- 压缩后追问“刚才下一步是什么”
- 检查 open_loops 与优先级是否保留

4. post_tool_chat
- 先给出工具结果或工具上下文
- 压缩
- 再追问结果含义、下一步、修复动作
- 检查工具上下文是否保持

5. user_correction
- 用户先给约束
- 中途修正约束
- 压缩后要求继续方案
- 检查系统是否采用修正后的约束，而不是旧约束

6. long_technical
- 包含文件名、路径、模块名、错误点、修复目标
- 压缩后继续调试
- 检查关键技术实体是否仍可用

七、验证执行流程

对每个样本执行固定流程：

1. 创建样本元数据
2. 在验证副本中准备上下文
3. 执行 context-budget-check
4. 执行 context-compress --mode shadow
5. 执行 context-retrieve --capsule-only
6. 继续 1~3 轮验证性对话
7. 输出评分
8. 写入样本结果、分桶统计、日报来源

注意：
- S1 只允许 capsule-only
- 不使用 L2 作为 S1 评分依据
- L2 状态只记为环境信息，不计入 S1 结论

八、样本元数据格式

每个样本必须记录：

- sample_id
- session_id
- source_type
 - real_main_agent
 - historical_replay
 - synthetic_stress
- bucket_tags
- retrieve_mode=capsule_only
- baseline_commit
- baseline_manifest_path
- turn_count_before_compress
- turn_count_after_compress
- compression_triggered
- expected_outcome
- actual_outcome
- verdict
- created_at

若为 historical_replay，还需记录：
- original_turn_range
- replay_copy_id

若为 synthetic_stress，还需记录：
- scenario_template_id

九、评分指标

必须输出以下指标：

核心指标（Gate 1 必看）：
- capsule_only_old_topic_recovery
- capsule_only_commitment_preservation
- commitment_drift_rate

质量指标（S1 观测）：
- priority_preservation_rate
- compression_gain_ratio
- source_mix_distribution

附加记录：
- confidence_protection_pass
- recall_source
- recall_confidence

评分阈值沿用当前 S1 既定规则，不得私自修改。

十、低流量补桶策略

当日常真实样本不足时，按以下顺序自动补桶：

1. 先扫描历史 session，尝试补最弱桶
2. 若历史 session 无足够合格片段，再生成 synthetic_stress 样本
3. 若某桶连续两天仍未提升，则提升为强制补桶对象
4. 不得为了凑总量而大量生成普通样本

补桶决策规则：
- 若 old_topic_recall 未达 30%，每日优先补该桶
- 若 with_open_loops 或 user_correction 未达 50%，每日必须各补至少 1 个样本
- 若 long_technical 长期不足，则优先从历史技术会话中抽取 replay 样本，不优先用合成样本替代

十一、失败与问题记录

以下情况标记为 hard_fail：
- 无法恢复目标旧话题
- recent commitments 丢失
- resident 保护字段被低 confidence 内容污染
- 用户修正后的约束被错误回滚
- open_loops 丢失或严重漂移
- 关键技术实体断裂导致续聊失真

hard_fail 必须自动写入：
- artifacts/context_compression/KNOWN_ISSUES.md
- artifacts/context_compression/s1_failures.jsonl

soft_fail 记录：
- 恢复成功但细节轻微漂移
- 优先级顺序有轻微变化
- compression_gain 低于预期但未失效

十二、输出产物

需要产出：

1. 样本数据
- artifacts/context_compression/s1_samples/*.json

2. 样本评分
- artifacts/context_compression/s1_scores/*.json

3. 每日汇总
- artifacts/context_compression/s1_daily_report.json
- artifacts/context_compression/s1_daily_report.md

4. Gate 状态
- artifacts/context_compression/s1_gate_status.json

5. 失败记录
- artifacts/context_compression/s1_failures.jsonl
- artifacts/context_compression/KNOWN_ISSUES.md

6. 覆盖与趋势
- s1-dashboard 可读取的 summary 输出

十三、自动化运行节奏

建议运行频率：

- 每 15 分钟：扫描可提取真实/历史片段
- 每 1 小时：自动补 1~3 个 synthetic_stress 样本
- 每日收尾：汇总 dashboard、生成日报、更新 gate status

若系统空闲样本不足：
- 优先 historical_replay
- 再 synthetic_stress
- 不得因为低流量而停止 S1 采证

十四、判定边界

验证 worker 允许：
- 自动采样
- 自动分桶
- 自动运行 shadow
- 自动评分
- 自动汇总
- 自动报告薄弱桶

验证 worker 不允许：
- 自行宣布 Gate 1 PASS
- 修改 metrics 公式
- 修改 bucket minimums
- 修改 compression 策略
- 修改 resident 保护字段
- 接入主链路
- 自动打开 Light Enforced

Gate 1 最终结论必须由独立 gate-eval 脚本给出。

十五、执行优先级

当前第一优先任务：
- 优先补 old_topic_recall
- 其次补 with_open_loops
- 再补 user_correction

当前不优先任务：
- 扩展 L2
- 做主链路接入
- 做性能优化
- 做 UI/展示优化

十六、完成定义

当满足以下条件时，视为低流量 S1 自动采样策略执行完成：

1. 已建立三路采样机制
2. 样本来源比例可追踪
3. 最弱桶能被自动识别并补样
4. 每个样本都有完整元数据与评分
5. 每日自动生成报告
6. hard_fail 自动入库
7. 不影响主聊天链路
8. 不破坏 S1 freeze
9. Gate 1 所需证据能够持续积累

执行要求：
请按以上策略落地自动采样支线，不要改动主聊天主链路，不要修改 S1 基线，不要在实现过程中自行扩大范围。
</file>
user: Conversation info (untrusted metadata):
```json
{
  "message_id": "7141",
  "sender_id": "8420019401",
  "sender": "Moonlight",
  "timestamp": "Fri 2026-03-06 15:44 CST"
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

context-compress --mode shadow
user: Conversation info (untrusted metadata):
```json
{
  "message_id": "7141",
  "sender_id": "8420019401",
  "sender": "Moonlight",
  "timestamp": "Fri 2026-03-06 15:44 CST"
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

context-compress --mode shadow
user: Conversation info (untrusted metadata):
```json
{
  "message_id": "7141",
  "sender_id": "8420019401",
  "sender": "Moonlight",
  "timestamp": "Fri 2026-03-06 15:44 CST"
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

context-compress --mode shadow
