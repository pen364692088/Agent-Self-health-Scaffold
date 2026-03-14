# Phase 1 Audit — Source of Truth / State Boundary / Summary Authority

## Scope

本次审计只做边界识别与最小治理方案落盘，不直接改主功能链。

审计目标：

1. 完成 source-of-truth map 审计
2. 唯一化 live `SESSION-STATE.md` / `working-buffer.md`（先定义治理口径，不破坏现有主链）
3. 审计以下工具的读取/写入边界：
   - `tools/prompt-assemble`
   - `tools/session-start-recovery`
   - `tools/context-compress`
   - `tools/capsule-builder`
   - `tools/archive-with-distill`
   - `tools/distill-content`
4. 标出重复功能、平行状态源、summary 篡权路径
5. 产出“替换 / 改接 / 停写 / 禁用”清单，按优先级排序

---

## Executive Verdict

### 总结

当前系统**不是缺少状态机制**，而是已经形成了多套相邻机制：

- session continuity 状态链
- context compression / capsule 链
- archive distill 链
- subagent summary / receipt 链

它们各自有价值，但当前存在以下高风险问题：

1. **重复 live state 文件** 已存在
2. **工具实现与仓库内文件路径不一致**
3. **summary / capsule / handoff 被误用为恢复判断依据的风险真实存在**
4. **在线 compression 与离线 distill 尚未被硬性隔离**
5. **部分 continuity 工具仍把 `memory/working-buffer.md` 当 live buffer，而其他链路把根目录 `working-buffer.md` 当 live buffer**

### 结论级别

- **架构状态**：可治理，但当前不适合继续叠新状态层
- **最小治理建议**：先固定 hierarchy + 唯一 live source + 停写名单，再进入代码改接
- **当前 authoritative truth**：不应由任何 summary/capsule/handoff 决定

---

## Fixed Hierarchy (Phase 1 冻结口径)

```text
Ledger / Run Truth
> Materialized State (future, not yet implemented)
> SESSION-STATE.md (live continuity state, temporary bridge)
> working-buffer.md (live working memory, temporary bridge)
> handoff.md / capsule / summary / distill outputs
> transcript / UI render
```

### 强制说明

在 `state_materializer` 尚未落地前：

- `SESSION-STATE.md` 只能充当 **continuity bridge state**
- `working-buffer.md` 只能充当 **working memory / reasoning focus**
- `handoff.md` / capsule / summary / distill outputs 都只能充当 **辅助恢复材料**
- **不得将上述任何 summary-like 文件视为 authoritative truth**

---

## A. State File Inventory

### 实际发现文件

| Path | Current Content Role | Current Risk | Phase 1 Decision |
|---|---|---:|---|
| `SESSION-STATE.md` | 根级连续性状态文件 | 中 | **保留为唯一 live SESSION-STATE** |
| `working-buffer.md` | 根级 working memory | 中 | **保留为唯一 live working-buffer** |
| `handoff.md` | 交接摘要 | 中 | 保留，但降权为 summary/handoff only |
| `memory/SESSION-STATE.md` | 历史/平行状态文件 | 高 | **停写 + 归档候选** |
| `memory/working-buffer.md` | 历史/平行 working memory | 高 | **停写 + 归档候选** |

### 关键观察

#### 1. 根目录状态文件与 `memory/` 下同名文件并存
这会直接导致：

- continuity 工具读取一套
- compaction / blockers / post-handoff 读取另一套
- 人工检查时看到第三套语义

#### 2. 现有文件内容已明显分叉
- 根目录 `SESSION-STATE.md`：描述 Telegram durable outbound 修复任务
- `memory/SESSION-STATE.md`：仍保留 OpenEmotion MVP 历史任务
- 根目录 `working-buffer.md`：对应 Telegram 修复链
- `memory/working-buffer.md`：对应 self-health baseline soak 任务

这已经不是“镜像缓存”，而是**平行 live state**。

### Phase 1 冻结决定

#### 唯一 live source
- `SESSION-STATE.md`
- `working-buffer.md`

#### 非 live / stop-write
- `memory/SESSION-STATE.md`
- `memory/working-buffer.md`

#### 保留但降权
- `handoff.md`

---

## B. Tool Boundary Audit

## 1) `tools/session-start-recovery`

### Current responsibility
- 新 session 启动时恢复状态
- 读取 continuity 文件
- 生成 recovery summary
- 有一定冲突解析逻辑

### Current read/write boundary
- **读取**：
  - `SESSION-STATE.md`
  - `memory/working-buffer.md`
  - `handoff.md`
  - `artifacts/capsules/*.json`
  - WAL / durable run-state
- **写入**：
  - `.last_session_id`
  - recovery artifacts / continuity events（间接）

### Problem type
- **P1: live working-buffer 路径错误**
- **P2: 把 capsule constraints 拉入恢复，存在辅助层抬权风险**
- **P3: 工具实现硬编码到 `~/.openclaw/workspace`，与当前仓库副本不一致**

### Why it matters
当前该工具把 `memory/working-buffer.md` 视为 live buffer；但其他链路与当前仓库根文件现实不一致。

### Suggested action
- **改接**：将 live working-buffer 统一改到根级 `working-buffer.md`
- **限制**：capsule 只能提供 auxiliary constraints，不可覆盖 state truth
- **保留**：handoff 仅用于辅助恢复摘要，不可决定 final state

### Risk level
**Critical**

---

## 2) `tools/prompt-assemble`

### Current responsibility
- 汇总 resident / active / recall 三层上下文
- 根据 budget trigger 先压缩，再检索，再拼 prompt

### Current read/write boundary
- **读取**：
  - 外部传入的 `--state`
  - 外部传入的 `--history`
  - 通过子命令调用：`context-budget-check` / `context-compress` / `context-retrieve`
- **写入**：
  - 基本无主状态写入，仅输出 JSON

### Problem type
- **P1: 仍以 history + state file 为中心，而非 materialized state**
- **P2: 其依赖链继续把 capsule / retrieval summary 注入 prompt，存在 summary 层过强风险**
- **P3: 同样硬编码 `~/.openclaw/workspace` 工具链**

### Why it matters
它本身不是 authority，但它现在是“把谁装进 prompt”的关键入口。如果上游状态源不统一，就会把冲突直接放大到模型输入。

### Suggested action
- **改接**：未来切到 `materialized_state.json` 为唯一状态输入
- **禁止**：直接把 archive distill 结果作为主 prompt 输入
- **保留**：继续作为 L1 上下文装配层，不决策 truth

### Risk level
**High**

---

## 3) `tools/context-compress`

### Current responsibility
- 压缩执行器
- 生成 compression plan
- 调用 capsule-builder
- 写 compression events / capsule refs

### Current read/write boundary
- **读取**：
  - 输入 state/history
  - `context-budget-check`
  - `capsule-builder`
- **写入**：
  - `artifacts/compression_events/*.json`
  - `compression_events.jsonl`
  - enforced 模式下写 capsule references 到 capsules log

### Problem type
- **P1: 在线压缩链会生产 summary-like capsule**
- **P2: 若无严格边界，容易被误当恢复真相**
- **P3: enforced mode 下实际写 capsules，后续 recall 可能被误提升权重**

### Why it matters
它是 summary 生产工厂。如果没有强边界，capsule 会逐步变成“伪状态数据库”。

### Suggested action
- **保留**：作为在线压缩组件
- **限制**：capsule = compressed recall artifact，不得充当 authoritative task state
- **后续改接**：压缩事件应附 raw evidence refs，而不是只保存 summary-like capsule 元数据

### Risk level
**High**

---

## 4) `tools/capsule-builder`

### Current responsibility
- wrapper，转发到 V1/V2/V3 实现
- 当前默认 V3

### Current read/write boundary
- wrapper 自身几乎不读写状态
- 实际实现写 `artifacts/capsules/*.json`

### Problem type
- **P1: capsule 概念被用于 session recovery 相关叙述，容易扩权**
- **P2: 当前 schema 是 session capsule，但文档和实践里已有继续向 continuation package 演化的倾向**

### Why it matters
如果不硬拆 schema，未来 tool output summary / child package / session capsule 很容易共用一个“万能 capsule”概念。

### Suggested action
- **收口职责**：只负责 `session_context_capsule`
- **禁止**：承载 child completion package 或 tool summary 的 authority

### Risk level
**Medium-High**

---

## 5) `tools/archive-with-distill`

### Current responsibility
- 归档时调用 distill-content
- 把 distilled 文件送去 OpenViking
- 提交 git

### Current read/write boundary
- **读取**：
  - `memory/YYYY-MM-DD.md`
  - `memory.md`
  - `tools/distill-content`
  - `scripts/openviking_archive_entry.py`
- **写入**：
  - `artifacts/distilled/*`
  - 备份 repo git commit / push

### Problem type
- **P1: 离线蒸馏链与在线 compression 名义接近**
- **P2: 若无硬限制，distilled 输出可能被人直接当 session context 输入**

### Why it matters
它本来是 archive pipeline，不应回流主执行链。

### Suggested action
- **保留**：离线归档专用
- **禁用默认回流**：distilled 输出不得直接进入 prompt-assemble 主输入
- **允许**：仅通过明确 retrieval gate 进入 recall

### Risk level
**High**

---

## 6) `tools/distill-content`

### Current responsibility
- 用 LLM 将长内容压缩为 distilled content

### Current read/write boundary
- **读取**：任意输入文件、OpenClaw config
- **写入**：输出文件（或 stdout）

### Problem type
- **P1: 产物是高压缩 summary**
- **P2: 不保留原始证据上下文结构，只保留 source_file 指针**
- **P3: 极易被误认为可以替代原始文档/证据**

### Why it matters
这类输出适合知识沉淀，不适合做运行真相或恢复 authority。

### Suggested action
- **保留**：offline distill only
- **禁用**：不得作为 recovery truth 或 prompt primary state source

### Risk level
**High**

---

## C. Summary / Capsule / Handoff Usurpation Paths

下面这些是当前最危险的“摘要层篡权路径”。

| Path | Current Pattern | Problem | Risk |
|---|---|---|---:|
| `handoff.md` → 人工/工具恢复判断 | 用 handoff 作为当前状态摘要 | handoff 只是交接摘要，不是真相 | High |
| `memory/working-buffer.md` → session-start-recovery | continuity 工具把其当 live working buffer | 与根级 `working-buffer.md` 冲突 | Critical |
| capsule → recovery constraints | 从 `artifacts/capsules/*.json` 拉 hard_constraints | recall artifact 有抬权风险 | High |
| capsule → retrieval → prompt | recall 层进入 prompt | 合法，但必须明确非 authoritative | Medium |
| distill output → archive recall | 可能被后续当“精华版真相”使用 | offline summary 不能当 runtime truth | High |
| subagent receipt `summary` 字段 | 结构化 receipt 内带 summary | summary 可辅助，但不能替代 status/evidence | Medium |

### 明确禁令

以下判断方式必须视为非法：

1. 从 `handoff.md` 判断任务已完成
2. 从 `working-buffer.md` 判断 child 已完成
3. 从 capsule 判断 gate 已通过
4. 从 distill summary 判断恢复已成功
5. 从任意 summary 文本覆盖 ledger / run-state / receipt status

---

## D. Duplicate Function / Parallel Source Audit

### 1. 平行状态源

| Source | Actual Function | Overlap With | Problem Type |
|---|---|---|---|
| `SESSION-STATE.md` | continuity bridge state | `memory/SESSION-STATE.md` | duplicate live state |
| `working-buffer.md` | working memory | `memory/working-buffer.md` | duplicate live state |
| `handoff.md` | handoff summary | `SESSION-STATE.md` / working-buffer | summary may look authoritative |
| capsule | compressed recall | state / handoff | summary overreach |
| distill outputs | archive summary | capsule / handoff / memory | offline-online mixing |

### 2. 功能重复链

| Chain | Intended Role | Overlap | Verdict |
|---|---|---|---|
| `session-start-recovery` | continuity recovery | handoff/state/buffer merge | keep, but rewire |
| `prompt-assemble` | prompt construction | uses compression + retrieval | keep, but state-driven later |
| `context-compress` + `capsule-builder` | online compression | creates durable summary artifacts | keep, but restrict authority |
| `archive-with-distill` + `distill-content` | offline archive distill | also creates summary artifacts | keep offline only |

---

## E. Priority-Ordered Action List

## P0 — Must do before any feature expansion

### 1. Freeze live state source map
- **Action**: declare only root `SESSION-STATE.md` and root `working-buffer.md` as live
- **Files impacted**:
  - `SESSION-STATE.md`
  - `working-buffer.md`
  - `memory/SESSION-STATE.md`
  - `memory/working-buffer.md`
- **Type**: stop-write / governance
- **Risk**: Critical

### 2. Repoint continuity readers from `memory/working-buffer.md` to root `working-buffer.md`
- **Action**: change `session-start-recovery`, `pre-reply-guard`, `session-state-doctor`, `handoff-create`, related continuity tools
- **Type**: rewire
- **Risk**: Critical
- **Note**: 本轮先记录，不直接大改

### 3. Mark `memory/SESSION-STATE.md` and `memory/working-buffer.md` as archive-only
- **Action**: stop-write + rename or add explicit archival marker later
- **Type**: stop-write / archive
- **Risk**: High

---

## P1 — Must do before state-driven context assembly rollout

### 4. Ban summary/handoff/capsule as authority in docs + code comments + future gates
- **Action**: add explicit rule references in Phase 2 design / guards
- **Type**: governance hardening
- **Risk**: High

### 5. Separate online compression from offline distill by contract
- **Action**: document and later enforce:
  - online = `context-compress`, `capsule-builder`, `prompt-assemble`
  - offline = `distill-content`, `archive-with-distill`
- **Type**: boundary hardening
- **Risk**: High

### 6. Introduce `materialized_state` as future唯一 prompt state入口
- **Action**: design now, implement Phase 2
- **Type**: replace path
- **Risk**: High

---

## P2 — Important but after live-state治理

### 7. Split capsule family into distinct schemas
- **Action**:
  - `session_context_capsule`
  - `tool_output_summary`
  - `child_continuation_package`
- **Type**: schema separation
- **Risk**: Medium-High

### 8. Ensure all summary-like outputs carry raw evidence refs
- **Action**: future compactor/adapter must produce raw_ref + summary
- **Type**: evidence hardening
- **Risk**: Medium-High

---

## F. Minimal Governance Plan (This Phase, No Mainline Breakage)

本轮建议只做最小治理，不直接切主逻辑：

1. 落盘 source-of-truth audit
2. 落盘 machine-readable source-of-truth map
3. 冻结唯一 live source 口径
4. 暂不改主功能实现
5. 下一步只改 continuity 工具读写路径，不碰业务主链

### Why this is the smallest safe move
因为当前仓库内不仅有状态分叉，还有工具路径硬编码到 `~/.openclaw/workspace` 的现象。贸然在本 repo 直接改功能，容易出现：

- repo 副本改了，但运行实例没改
- 文档状态与真实运行状态继续分叉
- 主链无意被打断

---

## G. Replace / Rewire / Stop-Write / Disable Checklist

| Priority | File/Tool | Current Role | Problem Type | Suggested Action | Risk |
|---|---|---|---|---|---:|
| P0 | `memory/SESSION-STATE.md` | 平行状态源 | duplicate live state | **停写 + 归档** | Critical |
| P0 | `memory/working-buffer.md` | 平行 working memory | duplicate live state | **停写 + 归档** | Critical |
| P0 | `tools/session-start-recovery` | continuity recovery | reads wrong live buffer | **改接** | Critical |
| P0 | `tools/pre-reply-guard` 等 continuity 工具 | pre-reply state checks | reads wrong live buffer | **改接** | Critical |
| P1 | `handoff.md` | handoff summary | summary may look authoritative | **降权，不作 truth** | High |
| P1 | `tools/prompt-assemble` | prompt assembly | still history/state centric | **后续改接** | High |
| P1 | `tools/context-compress` | online compression | capsule overreach risk | **保留但限制 authority** | High |
| P1 | `tools/archive-with-distill` | offline archive | may mix into online recall | **保留 offline only** | High |
| P1 | `tools/distill-content` | offline distill | summary overreach | **保留 offline only** | High |
| P2 | `tools/capsule-builder` | session capsule builder | capsule family overload | **收口职责** | Medium-High |

---

## Final Decision

### 保留为 live
- `SESSION-STATE.md`
- `working-buffer.md`

### 保留但降权
- `handoff.md`
- `artifacts/capsules/*`
- `artifacts/distilled/*`

### 停写 / 归档候选
- `memory/SESSION-STATE.md`
- `memory/working-buffer.md`

### 下一步最优动作
**不要直接大改功能。先只做 continuity reader 的路径统一和 stop-write 治理。**

也就是：

1. 统一 live working buffer 路径
2. 给 `memory/*` 同名状态文件加 archive/stop-write 口径
3. 再进入 Phase 2 的 `materialized_state + prompt-assemble` 改造
