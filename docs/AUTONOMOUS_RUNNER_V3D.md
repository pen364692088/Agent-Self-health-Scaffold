# Autonomous Runner v3-D

## 概述

Autonomous Runner (自主运行器) 是 v3-D 的核心组件，让系统从"需要人手动触发继续"变成"默认自动启用、自动持续推进"。

## 设计原则

1. **自动化优先**: 系统默认自动运行，无需人工干预
2. **可观测性**: 所有循环状态可监控
3. **可恢复性**: 崩溃后自动恢复
4. **Feature Flag 控制**: 所有功能可独立开关
5. **v2 Baseline 兼容**: 不修改 Gate 规则和 task_state.schema.json 核心字段

## 核心组件

### 1. Service Startup Loop (启动扫描)

在服务启动时执行，扫描所有未完成的任务并恢复执行。

**触发时机**: 服务启动时一次性执行

**功能**:
- 扫描任务目录中的所有任务
- 识别未完成的任务 (status = created, running, blocked)
- 将未完成任务加入活跃任务列表

**Feature Flag**: `startup_scan_enabled` (默认: true)

### 2. Pending Task Scanner (待处理任务扫描器)

周期性扫描任务目录，发现新的或未完成的任务。

**触发时机**: 每隔 `scanner_interval_seconds` 秒执行 (默认: 5s)

**功能**:
- 发现新创建的任务
- 更新现有任务状态
- 移除已完成的任务

**Feature Flag**: `pending_scan_enabled` (默认: true)

### 3. Scheduler Loop (调度循环)

负责调度待执行的步骤，通过 `step_scheduler` 进行准入控制。

**触发时机**: 每隔 `scheduler_interval_seconds` 秒执行 (默认: 2s)

**功能**:
- 检查任务是否有待执行步骤
- 检查步骤依赖是否满足
- 通过调度器获取执行槽位和租约
- 触发步骤执行

**Feature Flag**: `scheduler_enabled` (默认: true)

**集成点**: 
- `step_scheduler.py`: 调度准入控制
- `step_executor.py`: 实际执行步骤

### 4. Retry Loop (重试循环)

负责重试失败的步骤。

**触发时机**: 每隔 `retry_interval_seconds` 秒执行 (默认: 10s)

**功能**:
- 检查失败的可重试步骤 (status = failed_retryable)
- 检查重试次数限制
- 检查退避时间
- 重置步骤状态以重新执行

**Feature Flag**: `retry_enabled` (默认: true)

**配置**:
- `max_retry_attempts`: 最大重试次数 (默认: 3)
- `retry_backoff_seconds`: 重试退避时间 (默认: 30s)

### 5. Stuck Task Detector (卡住任务检测器)

检测长时间无进展的任务。

**触发时机**: 每隔 `stuck_detection_interval_seconds` 秒执行 (默认: 30s)

**功能**:
- 检查任务最后更新时间
- 标记超过阈值的任务为"卡住"
- 触发健康问题回调

**Feature Flag**: `stuck_detection_enabled` (默认: true)

**配置**:
- `stuck_threshold_seconds`: 卡住判定阈值 (默认: 300s = 5分钟)

### 6. Restart Recovery Loop (重启恢复循环)

负责从崩溃中恢复任务执行。

**触发时机**: 每隔 `recovery_interval_seconds` 秒执行 (默认: 15s)

**功能**:
- 检测卡住的任务或有运行中步骤的任务
- 使用 `resume_engine` 分析恢复策略
- 获取步骤租约并恢复执行
- 限制恢复次数

**Feature Flag**: `recovery_enabled` (默认: true)

**集成点**:
- `resume_engine.py`: 恢复上下文分析和策略决定

### 7. Heartbeat / Health Monitor (心跳健康监控)

发送心跳并监控系统健康状态。

**触发时机**: 每隔 `heartbeat_interval_seconds` 秒执行 (默认: 5s)

**功能**:
- 写入心跳文件
- 检查循环健康状态
- 检查任务健康状态
- 触发健康问题回调

**Feature Flag**: `heartbeat_enabled` (默认: true)

## 配置

### 完整配置示例

```json
{
  "enabled": true,
  "startup_scan_enabled": true,
  "pending_scan_enabled": true,
  "scheduler_enabled": true,
  "retry_enabled": true,
  "stuck_detection_enabled": true,
  "recovery_enabled": true,
  "heartbeat_enabled": true,
  
  "scanner_interval_seconds": 5.0,
  "scheduler_interval_seconds": 2.0,
  "retry_interval_seconds": 10.0,
  "stuck_detection_interval_seconds": 30.0,
  "recovery_interval_seconds": 15.0,
  "heartbeat_interval_seconds": 5.0,
  
  "stuck_threshold_seconds": 300.0,
  "max_retry_attempts": 3,
  "retry_backoff_seconds": 30.0,
  "max_consecutive_failures": 5,
  "health_check_interval_seconds": 10.0,
  
  "tasks_base_dir": "artifacts/tasks",
  "config_path": null,
  "state_path": ".autonomous_runner"
}
```

### 配置项说明

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `enabled` | bool | true | 全局开关 |
| `startup_scan_enabled` | bool | true | 启动扫描开关 |
| `pending_scan_enabled` | bool | true | 待处理扫描开关 |
| `scheduler_enabled` | bool | true | 调度循环开关 |
| `retry_enabled` | bool | true | 重试循环开关 |
| `stuck_detection_enabled` | bool | true | 卡住检测开关 |
| `recovery_enabled` | bool | true | 恢复循环开关 |
| `heartbeat_enabled` | bool | true | 心跳监控开关 |
| `scanner_interval_seconds` | float | 5.0 | 扫描间隔 |
| `scheduler_interval_seconds` | float | 2.0 | 调度间隔 |
| `retry_interval_seconds` | float | 10.0 | 重试间隔 |
| `stuck_detection_interval_seconds` | float | 30.0 | 卡住检测间隔 |
| `recovery_interval_seconds` | float | 15.0 | 恢复间隔 |
| `heartbeat_interval_seconds` | float | 5.0 | 心跳间隔 |
| `stuck_threshold_seconds` | float | 300.0 | 卡住判定阈值 |
| `max_retry_attempts` | int | 3 | 最大重试次数 |
| `retry_backoff_seconds` | float | 30.0 | 重试退避时间 |
| `max_consecutive_failures` | int | 5 | 最大连续失败次数 |
| `tasks_base_dir` | string | "artifacts/tasks" | 任务目录 |
| `state_path` | string | ".autonomous_runner" | 状态目录 |

## 使用方式

### Python API

```python
from runtime.autonomous_runner import AutonomousRunner, RunnerConfig

# 创建配置
config = RunnerConfig(
    enabled=True,
    tasks_base_dir="artifacts/tasks"
)

# 创建运行器
runner = AutonomousRunner(config=config)

# 启动
runner.start()

# 获取状态
status = runner.get_status()
print(f"Active tasks: {status.active_tasks}")

# 暂停
runner.pause()

# 恢复
runner.resume()

# 停止
runner.stop()
```

### 工厂函数

```python
from runtime.autonomous_runner import create_autonomous_runner

# 从配置文件创建
runner = create_autonomous_runner(
    config_path="/path/to/config.json"
)

# 带工厂函数创建
runner = create_autonomous_runner(
    task_dossier_factory=lambda task_id: TaskDossier(base_dir, task_id),
    step_scheduler_factory=lambda: StepScheduler(...),
    resume_engine_factory=lambda dossier: ResumeEngine(dossier),
    step_executor_factory=lambda dossier: StepExecutor(dossier)
)
```

### CLI

```bash
# 启动运行器
python -m runtime.autonomous_runner

# 使用配置文件
python -m runtime.autonomous_runner --config /path/to/config.json

# 指定任务目录
python -m runtime.autonomous_runner --tasks-dir artifacts/tasks

# 运行一次并退出
python -m runtime.autonomous_runner --once

# 查看状态
python -m runtime.autonomous_runner --status --json
```

## 与现有组件集成

### step_scheduler.py 集成

```python
from runtime.step_scheduler import create_scheduler
from core.worker_slot_registry import create_slot_registry

registry = create_slot_registry(total_slots=4)

def step_scheduler_factory():
    return create_scheduler(registry)

runner = AutonomousRunner(
    step_scheduler_factory=step_scheduler_factory
)
```

### resume_engine.py 集成

```python
from runtime.resume_engine import ResumeEngine
from core.task_dossier import TaskDossier

def task_dossier_factory(task_id):
    return TaskDossier(base_dir, task_id)

def resume_engine_factory(dossier):
    return ResumeEngine(dossier)

runner = AutonomousRunner(
    task_dossier_factory=task_dossier_factory,
    resume_engine_factory=resume_engine_factory
)
```

### step_executor.py 集成

```python
from runtime.step_executor import StepExecutor

def step_executor_factory(dossier):
    return StepExecutor(dossier, worker_id="autonomous_runner")

runner = AutonomousRunner(
    task_dossier_factory=task_dossier_factory,
    step_executor_factory=step_executor_factory
)
```

## 回调机制

### 任务进度回调

```python
def on_progress(task_id, step_id, status):
    print(f"Task {task_id}, Step {step_id}: {status}")

runner.on_task_progress(on_progress)
```

### 健康问题回调

```python
def on_health_issue(issue_type, target, details):
    print(f"Health issue: {issue_type} on {target}")
    if issue_type == "stuck_task":
        # 处理卡住的任务
        pass

runner.on_health_issue(on_health_issue)
```

### 错误回调

```python
def on_error(error):
    print(f"Error: {error}")

runner.on_error(on_error)
```

## 验收标准

### 1. 启动后无需人工发"继续"

✅ 启动扫描 (`_run_startup_scan`) 自动发现未完成任务
✅ 调度循环 (`_scheduler_loop`) 自动推进步骤执行

### 2. 有未完成任务时会自动推进

✅ 扫描器 (`_scanner_loop`) 发现新任务
✅ 调度器 (`_scheduler_loop`) 调度执行
✅ 重试循环 (`_retry_loop`) 处理失败步骤

### 3. Crash 后重启可恢复运行循环

✅ 启动扫描恢复未完成任务
✅ 恢复循环 (`_recovery_loop`) 使用 `resume_engine` 恢复
✅ 心跳文件记录运行状态

## v2 Baseline 兼容性

- ✅ 不修改 Gate 规则 (`docs/GATE_RULES.md`)
- ✅ 不修改 task_state.schema.json 核心字段
- ✅ 所有新功能通过 Feature Flag 控制
- ✅ 与现有 `step_scheduler.py` 集成
- ✅ 与现有 `resume_engine.py` 集成
- ✅ 与现有 `step_executor.py` 集成

## 监控和调试

### 状态检查

```python
status = runner.get_status()
# {
#   "state": "running",
#   "runner_id": "runner_xxxxx",
#   "started_at": "2026-03-15T10:00:00Z",
#   "uptime_seconds": 3600,
#   "loops": {...},
#   "active_tasks": 5,
#   "pending_tasks": 2,
#   "stuck_tasks": 0,
#   "recovered_tasks": 3
# }
```

### 统计信息

```python
stats = runner.get_stats()
# {
#   "tasks_scanned": 100,
#   "tasks_scheduled": 50,
#   "tasks_retried": 5,
#   "tasks_recovered": 3,
#   "steps_executed": 150,
#   "errors": 2,
#   "active_tasks": 5,
#   "stuck_tasks": 0,
#   "recovery_counts": {"task_001": 1, "task_002": 2}
# }
```

### 心跳文件

位置: `.autonomous_runner/heartbeat.json`

```json
{
  "runner_id": "runner_xxxxx",
  "timestamp": "2026-03-15T10:05:00Z",
  "state": "running",
  "stats": {
    "tasks_scanned": 100,
    "tasks_scheduled": 50,
    ...
  }
}
```

## 故障排除

### 任务不推进

1. 检查运行器状态: `runner.get_status()`
2. 检查循环状态: `status.loops["scheduler"]`
3. 检查任务状态: `runner._active_tasks`
4. 检查 Feature Flags: `config.scheduler_enabled`

### 任务被标记为卡住

1. 检查 `stuck_threshold_seconds` 配置
2. 检查任务最后更新时间
3. 检查恢复循环是否运行
4. 查看 `_on_health_issue` 回调

### 重试不工作

1. 检查 `retry_enabled` 配置
2. 检查 `max_retry_attempts` 限制
3. 检查 `retry_backoff_seconds` 退避时间
4. 查看步骤状态是否为 `failed_retryable`

## 测试

运行测试:

```bash
pytest tests/test_autonomous_runner.py -v
```

测试覆盖:
- 生命周期管理 (start/stop/pause/resume)
- 启动扫描
- 任务扫描器
- 调度器
- 重试机制
- 卡住检测
- 恢复机制
- 心跳监控
- Feature Flag 控制
- v2 baseline 兼容性

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v3-D | 2026-03-15 | 初始实现，7 个核心循环 |
