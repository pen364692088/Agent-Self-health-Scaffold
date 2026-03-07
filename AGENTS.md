# AGENTS.md

## 最高优先级：会话连续性协议 (MANDATORY) ⭐⭐⭐⭐⭐

### Purpose
防止新 session/thread 导致工作上下文丢失。

### Core Rules

1. **Chat context is temporary cache only, not source of truth.**
   - 聊天上下文只是临时缓存，不是真相来源
   - 真相必须持久化到状态文件

2. **Source of truth for ongoing work must be persisted in:**
   - `SESSION-STATE.md` - 当前总目标、阶段、分支、blocker、下一步
   - `working-buffer.md` - 当前工作焦点、假设、待验证点
   - `handoff.md` - 交接摘要（长会话或任务交接时）

3. **Before sending a reply that changes anything important:**
   - 任务状态变化 → 更新 SESSION-STATE.md
   - 工作焦点变化 → 更新 working-buffer.md
   - 会话可能结束 → 写 handoff.md
   - **Rule: Persist first, reply second.**

4. **On every new session start, read before doing substantive work:**
   - SESSION-STATE.md
   - working-buffer.md
   - latest handoff.md (if present)

5. **If these files are missing, stale, or contradictory:**
   - 明确报告状态不确定
   - 从 repo/logs 重建状态后再继续

6. **Never rely on prior chat history alone for continuity.**

7. **Context threshold behavior:**
   | Context | Behavior |
   |---------|----------|
   | < 60% | 按事件写状态 |
   | 60-80% | 每条实质性回复前检查并必要时写 |
   | > 80% | 强制 handoff + 压缩前强制落盘 |

---

## 子代理编排唯一正式规则

### 唯一正式入口
所有子代理相关操作默认只通过以下入口进行：

- `subtask-orchestrate run "<task>" -m <model>`
- `subtask-orchestrate status`
- `subtask-orchestrate resume`

### 禁止直接走的底层路径
除非明确处于调试/修复场景，否则主 agent 不应直接调用：

- `spawn-with-callback`
- `subagent-inbox`
- `subagent-completion-handler`
- `sessions_spawn` 作为普通子任务主链路
- `sessions_send` 作为关键完成回执主链路
- `check-subagent-mailbox`（已废弃）

### 正式主链路
当前正式子代理完成链路：

1. `subtask-orchestrate` 先执行 inbox preflight
2. `subagent-inbox` 检查并处理未消费 receipt
3. 如有未处理 receipt，优先处理，不创建新子任务
4. 仅在没有待处理 receipt 时，才允许 spawn 新子任务
5. 关键完成回执只认 `subagent-inbox`

---

## 日常工作默认顺序

当任务涉及 workflow 推进、子任务状态、继续执行、或用户询问"现在怎么样了"时，默认顺序是：

1. `subtask-orchestrate status`
2. 如需要，`subtask-orchestrate resume`
3. 仅在确认无待处理 receipt、无进行中冲突任务后，才 `subtask-orchestrate run`

简化原则：
- 先收敛状态，再创建新工作
- 先处理 receipt，再决定回复用户
- 先走包装器，再考虑底层工具

---

## cc-godmode 边界

### 允许升级到 cc-godmode 的场景
- 架构设计或重大重构
- 多方案取舍，需要选全局最优
- 跨模块冲突或规则本身失效
- 重复出现、无法解释的系统漂移
- 故障复盘与治理审计

### 不应升级到 cc-godmode 的场景
以下属于系统层或普通 agent 层职责，不应升级：

- inbox 检查
- receipt 处理
- 常规 workflow 推进
- 普通重试
- 常规子任务创建
- 日常工具调用顺序控制

规则：
> 能规则化的，不交给 cc-godmode。
> 能测试化的，不交给记忆。
> 能自动化的，不交给提示词。

---

## 会话归档规则

当用户明确说"归档 / 会话归档 / wrap up / session wrap up"时，必须运行：

```bash
~/.openclaw/workspace/tools/session-archive
```

该归档流程应统一完成：
- 更新每日日志
- 更新 bootstrap 摘要
- 运行索引/归档入口
- 执行顶层备份仓库提交/推送

不要手动拆开执行归档步骤，除非在调试归档工具本身。

---

## Bootstrap 与记忆读取规则

### 会话启动时默认只加载
- `SOUL.md`
- `USER.md`
- `IDENTITY.md`
- `memory/YYYY-MM-DD.md`（若存在）

### 新 Session 启动时必须执行 (强制) ⭐⭐⭐⭐⭐
1. 读取 `SESSION-STATE.md`
2. 读取 `working-buffer.md`
3. 如存在 `handoff.md`，读取最新版本
4. 比较恢复状态与当前 repo/task 状态
5. 如有冲突，以文件/repo 为准，报告不确定

### 需要历史信息时
先做最小检索，再取最小片段，不整文件灌入。

---

## 文件编辑规则

### `.openclaw` 下的文件
当目标路径在 `.openclaw` 下时：
- 优先使用 `exec` + heredoc / shell 命令
- 使用 `safe-write` / `safe-replace` 工具
- 避免 `edit` 工具直接文本替换

### 共享规则文件
对 `AGENTS.md / TOOLS.md / USER.md / memory.md` 这类文件：
- 优先保持结构清晰、短小、低冲突
- 不要把调试 runbook 写进 bootstrap 文件
- 不要在多个文件里重复规定同一条正式主链路

---

## 运行时行为准则

- 优先选择最简单、最稳定、最可审计的方案
- 若用户前提不稳，直接指出并给替代方案
- 在已有正式包装器存在时，不绕过包装器
- 不把"模型记住规则"当成关键可靠性来源
- 回答用户前，先确认系统状态是否已经一致

---

## 子代理完成自动推进 (强制) ⭐⭐⭐⭐⭐

**触发条件**: 收到以 `✅ Subagent` 开头的消息

**必须立即执行**:
```bash
~/.openclaw/workspace/tools/handle-subagent-complete --json
```

**根据返回的 action 执行**:
| action | 执行 |
|--------|------|
| `spawn_next` | 对每个 pending 执行 sessions_spawn，不回复用户 |
| `notify_user` | 发送 message 给用户 |
| `wait` | 不回复，等待下一个子代理 |

**禁止行为**:
- ❌ 跳过运行 handle-subagent-complete
- ❌ 在 should_silence=true 时回复用户
- ❌ 忽略 pending_spawns > 0 的情况

---

## 回复前状态落盘 (强制) ⭐⭐⭐⭐⭐

**Before any substantive reply, verify whether state persistence is required.**

### 触发落盘的变化类型
- 任务状态变化
- 当前目标变化
- 分支/仓库状态变化
- 架构决策变化
- 执行策略变化
- 下一步/blocker 变化
- 交接准备

### 落盘动作
1. 更新 `SESSION-STATE.md`:
   - current objective
   - current phase
   - current branch / workspace
   - latest verified status
   - next actions
   - blockers

2. 更新 `working-buffer.md`:
   - active local focus
   - temporary hypotheses
   - immediate reasoning context

3. 如果 session 长 / context 高 / 用户可能离开:
   - 写或刷新 `handoff.md`

**Rule: Persist first, reply second.**