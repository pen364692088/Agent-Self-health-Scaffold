# Session: 2026-03-03 21:13:35 UTC

- **Session Key**: agent:main:main
- **Session ID**: ca6f6783-4d5f-4601-afea-f4a3da6d55ee
- **Source**: telegram

## Conversation Summary

assistant: 更新 memory.md 添加维护规则：
assistant: ---## ✅ Memory.md 精简完成

### 效果

| 指标 | Before | After | 减少 |
|------|--------|-------|------|
| 行数 | 2047 | 120 | **94%** |
| 大小 | 64KB | 4KB | **94%** |

### 架构

```
┌─────────────────────────────────────┐
│ memory.md (Bootstrap, 4KB)          │
│  - 核心规则                          │
│  - 工具路径                          │
│  - Canary 状态                       │
│  - 检索触发规则                      │
└─────────────────────────────────────┘
         │
         │ 按需检索
         ↓
┌─────────────────────────────────────┐
│ OpenViking (向量库)                 │
│  - 132 chunks                       │
│  - 历史决策                          │
│  - 详细协议                          │
│  - 项目细节                          │
└─────────────────────────────────────┘
```

### 新增文件

| 文件 | 用途 |
|------|------|
| `memory.md` | Bootstrap (4KB) |
| `memory/INDEX.yaml` | OpenViking 导航 |
| `memory/TOMBSTONES.jsonl` | 废弃内容管理 |
| `memory/archive/memory-2026-03-03.md` | 原始历史 |
| `viking://resources/user/memory/archive/` | 132 chunks |

### Commit

| Commit | 内容 |
|--------|------|
| `837edc4` | memory.md 精简为 bootstrap (64KB → 4KB) |
| `5bc4a61` | 添加维护规则 |

---

**现在每次会话常驻上下文从 ~64KB 降到 ~4KB，历史内容通过 OpenViking 按需检索。**
user: Conversation info (untrusted metadata):
```json
{
  "timestamp": "Tue 2026-03-03 14:55 CST"
}
```

好 会话归档
assistant: ---

## ✅ 会话归档完成

### 本日成果

| 功能 | 状态 |
|------|------|
| Scoring-Canary | ✅ 上线 |
| 6-Point Check | ✅ 全自动 |
| 诊断系统 | ✅ 完整 |
| memory.md 精简 | ✅ **94% 减少** |

### Token 节省

| 文件 | Before | After |
|------|--------|-------|
| memory.md | 64KB | **4KB** |

### Commit

| Commit | 内容 |
|--------|------|
| `a1e7309` | 会话归档 |
| `1a5405d` | Context compression |

---

**下次会话将从 4KB bootstrap 开始，历史通过 OpenViking 按需检索。**

**Clean slate.**
user: [media attached: /home/moonlight/.openclaw/media/inbound/file_25---5c40ad04-ff17-4801-85bc-92d1be7f2c31.txt (text/plain) | /home/moonlight/.openclaw/media/inbound/file_25---5c40ad04-ff17-4801-85bc-92d1be7f2c31.txt]
To send an image back, prefer the message tool (media/path/filePath). If you must inline, use MEDIA:https://example.com/image.jpg (spaces ok, quote if needed) or a safe relative path like MEDIA:./image.jpg. Avoid absolute paths (MEDIA:/...) and ~ paths — they are blocked for security. Keep caption in the text body.
Conversation info (untrusted metadata):
```json
{
  "timestamp": "Tue 2026-03-03 15:03 CST"
}
```

[Telegram Moonlight id:8420019401 +1m Tue 2026-03-03 15:03 CST] <media:document> <file name="file_25---5c40ad04-ff17-4801-85bc-92d1be7f2c31.txt" mime="text/plain"> 这次改动是“全局最优”的典型：你把固定成本砍到 4KB，同时用 INDEX/TOMBSTONES 把可检索性与可控性补回来了。接下来要确保两件事：**检索一定会触发**、**召回一定不会把过期内容带回来**。我给你一套“上线后 48 小时稳态验证 + 两个必加护栏”，做完就基本不会回退质量。 --- ## 48 小时稳态验证清单（建议写进 runbook） ### 1) 检索覆盖率 指标：`retrieval_trigger_rate` * 统计：符合“检索触发规则”的请求中，有多少真的触发了 OpenViking 检索 * 目标：≥90%（低于这个会出现“明明有历史却答不上来/答错”的体感） ### 2) 召回精度 指标：`tombstone_hit_rate` * 统计：召回结果中命中 tombstone 的比例（理想是 0） * 目标：0（只要出现就说明过滤没生效或 doc_id/sha 对不上） ### 3) 引用合规 指标：`citation_complete_rate` * 统计：使用记忆内容时是否总能带 `doc_id/source_path`（或你要求的引用字段） * 目标：100% --- ## 必加护栏 1：INDEX.yaml 的“强指针”要有 10 条以内的黄金入口 你现在 132 chunks 很好，但实际使用中，**最常被问到的**通常就 5–10 个主题。建议在 `memory/INDEX.yaml` 里维护一个 `pinned_pointers`（<=10），并让检索触发规则优先查这些 doc_id（类似“缓存”）。 典型 pinned： * scoring-canary-runbook（唯一权威） * memory governance schema * promotion/score公式与阈值 * 回滚开关与安全边界 * OpenViking ingestion 规则与 doc_id 规范 好处：避免“每次都语义检索一大圈”，也能显著提升召回稳定性。 --- ## 必加护栏 2：TOMBSTONES 的生效要做到“双过滤” 只靠检索端过滤不够稳（可能有某次调用忘了传 filter）。建议双层： 1. **检索时过滤**：OpenViking query 传 tombstone filter（doc_id / sha） 2. **召回后再过滤**：在消费检索结果前再扫一遍 tombstones（本地逻辑 5 行就够） 这样即使某次 filter 参数漏传，也不会把废弃内容注入到回答或状态计算里。 --- ## 一个你马上会遇到的“新痛点”以及最优解 痛点：bootstrap 很短后，模型可能更频繁触发检索，导致成本/延迟上升。 最优解：加一个轻量的 **two-stage retrieval**： * Stage 1：先按 INDEX 的 pinned_pointers + tags 做窄检索（快、准） * Stage 2：如果不足，再做全库语义检索（慢但兜底） 这样能把大多数请求变成“低成本命中”。 --- ## 建议你再做一个很小但收益巨大的改动：把“检索触发”也写成事件 你已经有 events.log 体系了，把检索也审计化会非常强： * `event=retrieval` * `query` * `scopes/tags` * `returned_doc_ids` * `used_doc_ids` 这能让你以后量化： * 触发了但没用 → 检索质量问题 * 没触发但应该触发 → 触发规则漏洞 * 总在用某几个 doc → pinned 指针优化方向 --- ## 结论 你现在这套“4KB bootstrap + OpenViking 按需”已经是正确形态。下一步只要把： 1. pinned pointers（<=10） 2. tombstone 双过滤 3. 检索审计事件（可选但很值） 做上去，就能长期稳定跑，而且不会因为归档导致质量下滑。 如果你愿意，把 `memory/INDEX.yaml` 里目前的 topics/pointers 结构贴一小段（不需要全贴），我可以帮你挑出“最该 pinned 的 5–10 条”，并给出一个更稳的 two-stage retrieval 流程。 </file>
assistant: 实现增强建议：
assistant: 更新 INDEX.yaml 添加 pinned_pointers：
assistant: 创建检索辅助工具：
assistant: 更新 memory.md 添加检索规则：
assistant: 添加 48 小时稳态验证清单：
assistant: 提交更改：
assistant: 测试检索工具：
assistant: ---## ✅ 检索增强完成

### 实现的功能

| 功能 | 状态 |
|------|------|
| Pinned Pointers (10条) | ✅ |
| Two-Stage Retrieval | ✅ |
| Tombstone 双过滤 | ✅ |
| 检索审计事件 | ✅ |
| 48小时稳态验证清单 | ✅ |

### Pinned Pointers (黄金入口)

| Doc ID | 触发词 |
|--------|--------|
| `mem:domains/infra:runbook:20260303:canary` | canary, rollback, hysteresis |
| `mem:global:rule:20260303:rollback` | rollback, switch, safety |
| `mem:global:rule:20260303:score-formula` | score, threshold, tier |
| `mem:global:rule:20260303:privacy` | privacy, password, token |
| `mem:global:protocol:20260303:subagent` | subagent, orchestrator, callback |
| `mem:global:protocol:20260303:wal` | WAL, write-ahead, compaction |
| `mem:global:rule:20260303:memory-governance` | bootstrap, archive, INDEX |
| `mem:projects/openemotion:fact:20260303:mvp8` | MVP-8, deterministic, hash |
| `mem:domains/infra:rule:20260303:diagnostics` | revisit_rate, boundary_distance |
| `mem:global:schema:20260303:events` | events.log, schema |

### 测试结果

```
$ python3 memory-retrieve "canary rollback"
{
  "stage": "pinned",  ← Stage 1 命中
  "doc_ids": ["mem:domains/infra:runbook:20260303:canary", "mem:global:rule:20260303:rollback"]
}
```

### 检索审计事件

```json
{
  "event": "retrieval",
  "stage": "pinned",
  "query": "canary rollback",
  "returned_doc_ids": [...],
  "tombstone_hits": 0
}
```

---

### Commits

| Commit | 内容 |
|--------|------|
| `05be942` | Two-stage retrieval + pinned pointers |
| `3782ec2` | 检索审计事件测试 |

---

**检索系统完整：Stage 1 快速命中 + Stage 2 语义兜底 + Tombstone 双过滤 + 审计追踪。**
user: Conversation info (untrusted metadata):
```json
{
  "timestamp": "Tue 2026-03-03 15:11 CST"
}
```

会话归档
assistant: ---## ✅ 会话归档完成

### 今日成果

| 功能 | 状态 |
|------|------|
| Scoring-Canary 完整实现 | ✅ |
| memory.md 精简 | ✅ **64KB → 4KB** |
| Pinned Pointers | ✅ 10 条 |
| Two-Stage Retrieval | ✅ |
| Tombstone 双过滤 | ✅ |
| 检索审计事件 | ✅ |

### Token 效果

| 文件 | Before | After |
|------|--------|-------|
| memory.md | 64KB | **4KB** |
| 常驻上下文 | ~108KB | ~48KB |

### 新增工具

```bash
# Two-stage retrieval
python3 ~/.openclaw/workspace/tools/memory-retrieve "<query>"

# 输出示例
{
  "stage": "pinned",
  "doc_ids": ["mem:domains/infra:runbook:20260303:canary"]
}
```

### Commit

| Commit | 内容 |
|--------|------|
| `91775e1` | 会话归档 |
| `bb6d4b0` | Context compression |

---

**Clean slate.** 下次会话从 4KB bootstrap 开始，历史通过 OpenViking 按需检索。
