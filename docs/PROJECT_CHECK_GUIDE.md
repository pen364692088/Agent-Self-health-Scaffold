# Project Check Pipeline

**目标**: 标准化项目检查流程，避免长对话卡死。

## 核心原则

1. **主会话只做 orchestration** - 不读原始长日志，不承担深分析
2. **一个 session 只做一个 phase** - 做完就退出
3. **worker 只交付 artifact** - status.json + summary.md + raw.log
4. **进度查询只读状态文件** - 不打到执行 worker

## 快速开始

```bash
# 1. 创建检查
project-check init /path/to/repo

# 2. 启动第一个 phase
project-check spawn <check_id>

# 3. 查看状态
project-check status <check_id>

# 4. 查看下一步
project-check next <check_id>
```

## 5 个标准 Phase

| Phase | 名称 | 入口命令 | 超时 |
|-------|------|---------|------|
| A | Repo Snapshot | `pytest -q tests/mvp11 tests/testbot` | 60s |
| B | Fast Tests | `pytest -q tests/mvp11 tests/testbot` | 300s |
| C | Testbot E2E | `python scripts/run_testbot_scenarios.py --subset pr` | 600s |
| D | Hard Gate | `python scripts/mvp11_hard_gate_eval.py` | 300s |
| E | Final Aggregation | 汇总所有 phase | 60s |

## 目录结构

```
artifacts/project_check/<check_id>/
  manifest.json
  phase_a_repo/
    status.json
    summary.md
    raw.log
  phase_b_tests/
    ...
  final/
    FINAL_CHECK_STATUS.json
    FINAL_CHECK_REPORT.md
    one_liner.txt
```

## status.json 结构

```json
{
  "phase": "phase_b_tests",
  "state": "done",
  "ok": true,
  "started_at": "2026-03-06T03:10:00Z",
  "finished_at": "2026-03-06T03:16:00Z",
  "metrics": {
    "tests_passed": 678,
    "tests_failed": 0
  },
  "next_action": "phase_c_testbot"
}
```

## 6 条硬规则

1. 同一 session 禁止跨 phase
2. 任何 phase 完成后必须退出 session
3. 进度查询只读取 status.json
4. raw log 只落盘，不回灌聊天
5. 失败后只做定点复盘
6. 总检查必须先有 manifest

## 工具位置

- `tools/project-check` - 主入口
- `tools/project-check-phase` - Phase worker
- `schemas/project_check_manifest.v1.schema.json` - Manifest schema
- `schemas/phase_status.v1.schema.json` - Status schema

## 错误处理

- 任一 phase 失败 → 停止后续 phase
- 创建单独的 `failure-analysis` 任务
- 不让原任务继续膨胀

---

## 自动推进系统 (P1)

`project-check-advance` 提供与现有 `callback-handler` 兼容的自动推进能力。

### 工作原理

1. 读取 `WORKFLOW_STATE.json`（兼容格式）
2. 检查所有 phase 的 `status.json`
3. 更新工作流状态
4. 返回下一步动作

### 使用方式

```bash
# 初始化工作流状态
project-check-advance <check_id> --init

# 检查并推进
project-check-advance <check_id>

# 自动 spawn 下一 phase
project-check-advance <check_id> --auto-spawn

# JSON 输出（用于程序调用）
project-check-advance <check_id> --json
```

### 返回格式

```json
{
  "action": "spawn_next" | "notify_user",
  "phase_id": "phase_b_tests",
  "should_silence": true | false,
  "check_id": "check_xxx",
  "ok": true
}
```

### 与 callback-handler 集成

`project-check-advance` 返回的 JSON 格式与 `callback-handler` 兼容：

- `action: spawn_next` + `should_silence: true` → 自动 spawn，不通知用户
- `action: notify_user` + `should_silence: false` → 发送完成通知

### 典型流程

```bash
# 1. 初始化检查
project-check init /path/to/repo
# 输出: check_20260306_xxx

# 2. 初始化工作流状态
project-check-advance check_20260306_xxx --init

# 3. 自动推进（循环直到完成）
while project-check-advance check_20260306_xxx --auto-spawn --json | jq -e '.action == "spawn_next"'; do
  echo "Phase spawned, waiting..."
  sleep 5
done

# 4. 获取最终报告
cat artifacts/project_check/check_20260306_xxx/final/one_liner.txt
```

### Cron 集成

可以在 `.openclaw/cron/jobs.json` 中配置定期检查：

```json
{
  "id": "project-check-daily",
  "schedule": "0 2 * * *",
  "command": "project-check init /path/to/repo && project-check-advance <check_id> --auto-spawn"
}
```
