# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

# Local Notes (Manager)

- Telegram-facing agent.
- Prefer sub-agents over “file mailboxes” unless we intentionally share one workspace.
- Keep messages short; use checklists.
- If tool permissions block something, propose the safest workaround.
- **Proactive skill usage enabled**: invoke available skills when situation matches documented use cases, with transparency and minimal side effects. See AGENTS.md for policy.
- **edit tool caveat**: If `edit` fails with "file not found" despite correct path, use `exec` with `cat >> file << 'EOF'` or `sed -i` as fallback. Prefer absolute paths.

## High-reliability execution defaults

### Data fetching / web stats jobs
- Default to **API/filter endpoint first**; avoid full dataset archives first.
- If a file is likely large (>50MB) or unknown size, do a probe first (headers/sample endpoint).
- Set strict timeout budget per attempt; on timeout, switch strategy (don’t retry same heavy path repeatedly).
- Prefer incremental retrieval (by month/range/member) over monolithic download.
- If official source has not yet published a period, mark it `N/A (not yet published)` instead of blocking delivery.

### Long-running commands
- Use background execution only when needed.
- Avoid tight poll loops; use reasonable poll timeouts.
- Kill stale processes quickly once a better fallback is available.

### Antfarm model routing reliability
- Avoid `polling.model: default` in workflow.yml for production runs; in this environment it can resolve to disallowed provider/model combinations and stall runs with `model not allowed`.
- Prefer explicit model ids per workflow, then recreate crons:
  - `node ~/.openclaw/workspace/antfarm/dist/cli/cli.js workflow ensure-crons <workflow-id>`
- Current stable picks in this setup:
  - `feature-dev` → `nvidia-nim/qwen/qwen3.5-397b-a17b`
  - `bug-fix`, `security-audit` → `nvidia-nim/qwen/qwen3.5-397b-a17b`
- Check iFlow availability via API before adding models to OpenClaw:
  - `curl -H "Authorization: Bearer $IFLOW_API_KEY" https://apis.iflow.cn/v1/models`
- Antfarm scheduling is cron-driven (`everyMs` default 300000 with stagger); pending at start can be normal.

### Antfarm medic stall handling (resume-first)
- For stalled runs, prefer **fail + resume** path, not cancel path.
- In this setup, `workflow stop` is effectively cancel and makes runs non-resumable.
- Policy when Medic alerts:
  1) Check status/logs of target run
  2) If run is `failed`, execute `workflow resume <run-id>` first
  3) Only use `workflow stop` when explicitly abandoning the run
- Goal: preserve completed story progress and avoid full restart.

### Heartbeat reliability (local model)
- Heartbeat strict prompt should default healthy and force exact output contract:
  - healthy: `HEARTBEAT_OK`
  - unhealthy: single-line `ALERT: <reason>`
- Keep heartbeat on local Ollama (`qwen2.5:3b-instruct`) for better adherence than 1B in this setup.
- Keep main agent model cloud-based (`opencode/kimi-k2.5-free`) and separate from heartbeat model.
- If malformed heartbeat output appears again, add whitelist post-filter guard.

### Tooling notes (validated)
- qmd: install via `npm install -g @tobilu/qmd` in this environment (Bun GitHub route was unreliable here).
- Exa MCP endpoint works with `mcporter` using `--http-url` + `--tool` + `--args` JSON.
- VM cannot use host GPU directly for Ollama in current VMware setup; use host Ollama API endpoint instead.

### Output delivery
- First pass should prioritize correctness + traceable sources.
- Add source sheet/section in generated docs by default.
- If conversion tooling is limited, still deliver standard office formats through reliable minimal generation path.

### SearXNG (agent web-search backend)
- Stack path: `/home/moonlight/.openclaw/workspace/searxng-docker`
- Access URL: `http://localhost/`
- JSON search API: `http://localhost/search?q=<query>&format=json`
- Unified wrapper (preferred): `/home/moonlight/.openclaw/workspace/tools/web-search "<query>" [limit]`
- JSON wrapper mode: `/home/moonlight/.openclaw/workspace/tools/web-search --json "<query>"`
- Compatibility wrapper: `/home/moonlight/.openclaw/workspace/tools/searx-search.sh`
- Startup behavior: Docker `restart: unless-stopped` + host Docker service enabled (`systemctl is-enabled docker` => enabled)

### OpenViking (local, token-saving retrieval)
- Prefer layered retrieval before full reads:
  1) `openviking search` (find candidate URIs)
  2) `openviking abstract` (L0)
  3) `openviking overview` (L1)
  4) `openviking read` (L2, only when necessary)
- qmd is secondary for cross-checking and quote/path extraction.
- Evidence precedence: raw file/read > qmd snippet > abstract/overview.
- Local runtime in this environment:
  - server: `127.0.0.1:8000`
  - embedding backend: host Ollama via `http://192.168.79.1:11434/v1`
- If OpenViking is unavailable, use qmd first (if indexed), then `grep/glob/read`, and mark degraded mode.

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

Add whatever helps you do your job. This is your cheat sheet.

<!-- antfarm:workflows -->
# Antfarm Workflows

Antfarm CLI (always use full path to avoid PATH issues):
`node ~/.openclaw/workspace/antfarm/dist/cli/cli.js`

Commands:
- Install: `node ~/.openclaw/workspace/antfarm/dist/cli/cli.js workflow install <name>`
- Run: `node ~/.openclaw/workspace/antfarm/dist/cli/cli.js workflow run <workflow-id> "<task>"`
- Status: `node ~/.openclaw/workspace/antfarm/dist/cli/cli.js workflow status "<task title>"`
- Logs: `node ~/.openclaw/workspace/antfarm/dist/cli/cli.js logs`

Workflows are self-advancing via per-agent cron jobs. No manual orchestration needed.
<!-- /antfarm:workflows -->

<!-- EMOTIOND_RUNTIME_BEGIN -->
```json
{
  "target_id": "telegram:8420019401",
  "channel": "telegram",
  "from": "telegram:8420019401",
  "conversation_id": "telegram:8420019401",
  "message_id": "6449",
  "ts": 1772734742000,
  "dt_seconds": 300,
  "request_id_base": "telegram:6449",
  "pre_decision": {
    "action": "boundary",
    "decision_id": 419
  },
  "allowed_subtypes_infer": [
    "care",
    "apology",
    "ignored",
    "rejection",
    "betrayal",
    "neutral",
    "uncertain"
  ]
}
```
<!-- EMOTIOND_RUNTIME_END -->

### write tool anti-error rule (path escapes workspace)
- In this environment, `write` only supports paths under workspace root (`/home/moonlight/.openclaw/workspace`).
- For external repo paths (e.g., `~/Project/...`), **do not use `write`**.
- Use `exec` with heredoc instead:
  - `cat > /absolute/path/file << 'EOF' ... EOF`
- Preflight before write/edit to external paths:
  1) `pwd` + absolute target path
  2) `test -d "$(dirname <path>)"`
  3) then write via `exec`
- This prevents non-critical tool-error notifications in chat.

## Session Memory System (三层存储架构)

**位置**: `~/.openclaw/workspace/.session-index/`

### 架构设计 (per Memory.txt)

| 层 | 用途 | 工具 | 内容 |
|---|------|------|------|
| A. 原始层 | 冷存档/可审计 | JSONL 文件 | 原始 session logs |
| B. 结构化层 | 精确查询/过滤 | SQLite + FTS5 | events 表 + high_signal 表 |
| C. 语义层 | 高信号语义召回 | OpenViking | 摘要/决策/错误修复 |

### 工具

**session-indexer** - 解析 JSONL 到 SQLite
```bash
~/.openclaw/workspace/tools/session-indexer --days 7   # 索引最近 7 天
~/.openclaw/workspace/tools/session-indexer --all      # 索引所有
~/.openclaw/workspace/tools/session-indexer --stats    # 查看统计
```

**session-query** - 统一检索接口
```bash
~/.openclaw/workspace/tools/session-query "关键词" --limit 10
~/.openclaw/workspace/tools/session-query "MVP" --type message
~/.openclaw/workspace/tools/session-query "decision" --signal decision
~/.openclaw/workspace/tools/session-query "preference" --signal user_preference
~/.openclaw/workspace/tools/session-query "cc-godmode" --semantic  # 含语义搜索
```

### 检索流程

1. **结构化过滤**: 按 session_id / 时间 / tool_name / event_type 精确定位
2. **全文搜索**: FTS5 对 content_preview 进行匹配
3. **语义检索**: OpenViking 高信号内容语义召回
4. **回源回放**: 根据 source_path + source_line 回到原始 JSONL

### 高信号提取类型

| signal_type | 描述 | 数量 |
|-------------|------|------|
| decision | 工具调用决策 | ~2900 |
| key_conclusion | 关键结论 | ~100 |
| user_preference | 用户偏好 | ~80 |

### 数据库 Schema

```sql
-- events 表
session_id, event_id, event_type, ts, role, tool_name, status, 
error_sig, content_preview, file_refs, source_path, source_line

-- high_signal 表  
session_id, event_id, signal_type, summary, keywords, source_path, source_line

-- events_fts (FTS5)
session_id, event_type, tool_name, content_preview
```

### 维护

- 索引后 SQLite 数据库约 5-10MB（vs JSONL 139MB）
- 增量索引：只处理 last_indexed_ts 之后的事件
- 定期运行 `--days 7` 保持索引更新
- 原始 JSONL 不变，可随时重建索引

---
Added: 2026-03-02 19:20 CST

## Subagent Orchestrator 调用约定 (2026-03-03)

**问题**: 长任务描述（换行/中文）导致 shell 命令行解析错误 → SIGTERM

**解决方案**:
1. 任务细节写入 SESSION-STATE.md
2. `subtask-orchestrate run` 只传简短摘要（单行，无换行）
3. 子代理从 SESSION-STATE.md 读取详细上下文

**示例**:
```bash
# ❌ 错误 - 换行导致问题
subtask-orchestrate run "Task line 1
line 2
line 3" -m <model>

# ✅ 正确 - 简短摘要 + 详细文件
# 先写 SESSION-STATE.md
# 然后：
subtask-orchestrate run "Memory Retrieval Hardening v1.2 - see SESSION-STATE.md" -m <model>
```

---

## Subagent Orchestrator (可靠回调系统) - 2026-03-03

**位置**: `~/.openclaw/workspace/tools/orchestrator/`

### 问题背景
Main agent 等待 subagent 回调/announce 时，回调可能丢失/延迟，导致主任务卡住。

### 解决方案
升级为 **Join/Poll 驱动 + 可选回执 + 兜底邮箱** 架构：
- 主 agent 主动轮询完成状态
- subagent 落盘回执文件
- 持久化支持重启恢复

### 核心组件

| 文件 | 用途 |
|------|------|
| `orchestrator.py` | 状态机 + join/poll 逻辑 |
| `subagent_receipt.py` | 回执生成/处理 |
| `orchestrator-cli` | CLI 工具 |

### 使用方式

**Main Agent**:
```python
from orchestrator import Orchestrator
orch = Orchestrator()
task_id = orch.spawn_subtask(run_id, session_key, "description")
orch.join_all(timeout=300)  # 主动等待，不依赖回调
```

**Subagent**:
```python
from subagent_receipt import subtask_done
# 完成时
subtask_done(task_id, run_id, summary="Done", output_paths=[...])
```

### CLI 命令
```bash
# 状态查看
~/.openclaw/workspace/tools/orchestrator/orchestrator-cli status -v

# 等待完成
~/.openclaw/workspace/tools/orchestrator/orchestrator-cli join -t 300

# 发送回执
~/.openclaw/workspace/tools/orchestrator/orchestrator-cli receipt <task_id> <run_id> -s "summary"
```

### 文件路径
- 持久化状态: `tools/orchestrator/pending_subtasks.json`
- 邮箱回执: `reports/subtasks/<task_id>.done.json`
- 运行报告: `tools/orchestrator/run_report_*.json`

### 测试
```bash
python3 ~/.openclaw/workspace/tools/orchestrator/test_minimal.py
```

---
Added: 2026-03-03 00:55 CST

### write/edit tool 路径限制 (2026-03-03)

**问题**: `write` 和 `edit` 工具只支持 workspace 内路径（`/home/moonlight/.openclaw/workspace`）

**解决方案**: 对于外部路径，使用 `exec` + heredoc

```bash
# 写入新文件
cat > /外部路径/文件名 << 'EOF'
内容

### write/edit tool 路径限制 (2026-03-03)

**问题**: write 和 edit 工具只支持 workspace 内路径

**解决方案**: 对于外部路径，使用 exec + heredoc

写入新文件:
  cat > /外部路径/文件名 << EOF ... EOF

追加内容:
  cat >> /外部路径/文件名 << EOF ... EOF

编辑（替换）:
  sed -i 's/old/new/g' /外部路径/文件名

**外部路径示例**:
- ~/.openviking-data-local-ollama/ - 向量数据库
- ~/Project/ - 项目目录
- /tmp/ - 临时目录

---
Added: 2026-03-03 02:49 CST

## 写入规则 (2026-03-03)

**`.openclaw` 文件夹内的文件修改**:
- ❌ 不要用 `edit`/`write` 工具（会失败）
- ✅ 用 `exec` + `cat > file << 'EOF'` 或 `cat >> file << 'EOF'`

**示例**:
```bash
# 覆盖
cat > ~/.openclaw/workspace/SESSION-STATE.md << 'EOF'
内容...

## 写入规则 (2026-03-03)

**.openclaw 文件夹内的文件修改**:
- 不要用 edit/write 工具（会失败）
- 用 exec + cat heredoc 方式

**示例**:
  覆盖: cat > file << 'EOF' ... EOF
  追加: cat >> file << 'EOF' ... EOF

**原因**: workspace 外路径限制

---
Added: 2026-03-03 15:42 CST

---

## OpenViking 配置修复 (2026-03-04)

### 问题
systemd 服务没有使用正确的配置文件，导致 embedding 请求发往错误端口。

### 修复
1. **配置文件位置**: `~/.openviking/ov.conf`
   - embedding 端点: `http://192.168.79.1:11434/v1` (宿主机 Ollama)
   - 模型: `mxbai-embed-large`

2. **systemd 服务**: `~/.config/systemd/user/openviking.service`
   - 已添加 `--config /home/moonlight/.openviking/ov.conf`

3. **管理命令**:
   ```bash
   # 查看状态
   systemctl --user status openviking.service
   
   # 重启服务
   systemctl --user restart openviking.service
   
   # 查看日志
   journalctl --user -u openviking.service -f
   ```

4. **添加记忆**:
   ```bash
   curl -X POST "http://127.0.0.1:8000/api/v1/resources" \
     -H "Content-Type: application/json" \
     -d '{"path": "/path/to/file.md", "target": "viking://resources/user/memory/", "wait": true}'
   ```

5. **搜索记忆**:
   ```bash
   openviking find "query" -u viking://resources/user/memory/
   ```

### 注意事项
- 文档长度不能超过 embedding 模型上下文限制
- 如果 embedding 失败，创建精简版摘要

---

## Callback Handler v2.0 (2026-03-04)

### 问题
旧版 callback-handler 依赖 SESSION-STATE.md 的 YAML 块，但文件经常被覆写成任务报告，导致工作流状态丢失，后续步骤无法触发。

### 修复
1. **独立工作流文件**: `WORKFLOW_STATE.json`
2. **健壮的 from_dict**: 使用 `data.get()` 避免 KeyError
3. **清晰的 API**: `--create`, `--activate`, `--status`, `--clear`

### 使用方式

**创建串行工作流**:
```bash
callback-handler --create '{
  "steps": [
    {"id": "phase1", "task": "安全修复", "model": "qianfan-code-latest"},
    {"id": "phase2", "task": "评测通路", "model": "qianfan-code-latest"},
    {"id": "phase3", "task": "配置验证", "model": "qianfan-code-latest"}
  ],
  "notify_on_done": "✅ 全部完成",
  "workflow_type": "serial"
}'
```

**激活步骤** (spawn 后调用):
```bash
callback-handler --activate phase1 <run_id>
```

**回调处理**:
```bash
callback-handler <run_id>
# → {"action": "spawn_next", "next_step": {...}, "should_silence": true}
```

### 文件
- 工具: `tools/callback-handler`
- 状态: `WORKFLOW_STATE.json`
- Orchestrator: `tools/orchestrator/orchestrator.py`

---
Added: 2026-03-04 11:15 CST

---

## WORKFLOW_STATE.json 结构规范 (2026-03-05)

### 问题
callback-handler 使用 `steps: [...]` 扁平结构，但手动创建的 WORKFLOW_STATE.json 使用了 `batches: [{steps: [...]}]` 嵌套结构，导致 callback-handler 无法找到 run_id，返回 `run_id_not_found`。

### 修复
统一使用扁平结构：

```json
{
  "active": true,
  "workflow_type": "serial",
  "steps": [
    {"id": "step1", "run_id": "xxx", "status": "done"},
    {"id": "step2", "run_id": "yyy", "status": "running"}
  ],
  "notify_on_done": "✅ 完成消息"
}
```

### 根因分析
1. callback-handler 假设扁平结构：`state.get('steps', [])`
2. 手动创建使用了嵌套结构：`state.get('batches', [{steps: []}])`
3. 结构不匹配 → 找不到 step → 无法自动推进

### 正确的工作流创建方式
```bash
callback-handler --create '{"steps":[{"id":"A","task":"..."}],"notify_on_done":"完成"}'
```

---
Added: 2026-03-05 08:30 CST

---

## 子代理完成自动推进修复 (2026-03-05)

### 问题
收到 `✅ Subagent main finished` 消息后，主代理没有自动推进工作流，需要用户说"继续"。

### 根因
1. 没有运行 `callback-handler` / `subagent-completion-handler`
2. 直接手动更新 `WORKFLOW_STATE.json`
3. AGENTS.md 引用了错误的文件 (`SESSION-STATE.md` 而非 `WORKFLOW_STATE.json`)

### 修复
1. 创建 `tools/subagent-completion-handler` - 统一的子代理完成处理入口
2. 更新 `AGENTS.md` - 正确的文件引用和处理流程
3. 更新 `SOUL.md` - 强制执行规则

### 正确流程
```
收到: "✅ Subagent main finished..."
步骤1: 提取 run_id
步骤2: subagent-completion-handler <run_id>
步骤3: 解析 {"action": "...", "should_silence": ...}
步骤4: 执行动作（spawn_next / notify_user / ignore）
```

### 工具
- `~/.openclaw/workspace/tools/subagent-completion-handler <run_id>`
- `~/.openclaw/workspace/tools/callback-handler --status`

---
Added: 2026-03-05 09:50 CST
