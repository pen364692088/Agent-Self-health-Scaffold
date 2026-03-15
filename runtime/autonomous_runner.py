"""
Autonomous Runner - 自主运行器 (v3-D)

让系统从"需要人手动触发继续"变成"默认自动启用、自动持续推进"。

核心组件：
1. Service Startup Loop - 服务启动循环
2. Pending Task Scanner - 待处理任务扫描器
3. Scheduler Loop - 调度循环
4. Retry Loop - 重试循环
5. Stuck Task Detector - 卡住任务检测器
6. Restart Recovery Loop - 重启恢复循环
7. Heartbeat / Health Monitor - 心跳健康监控

约束：
- 不修改 Gate 规则
- 不修改 task_state.schema.json 核心字段
- 新增功能通过 feature flag 控制
- 与现有的 step_scheduler.py, resume_engine.py 集成
"""

import json
import os
import signal
import sys
import threading
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
from enum import Enum
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger("autonomous_runner")


class RunnerState(str, Enum):
    """运行器状态"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    ERROR = "error"


class LoopType(str, Enum):
    """循环类型"""
    STARTUP = "startup"
    SCANNER = "scanner"
    SCHEDULER = "scheduler"
    RETRY = "retry"
    STUCK_DETECTOR = "stuck_detector"
    RECOVERY = "recovery"
    HEARTBEAT = "heartbeat"


@dataclass
class LoopStatus:
    """循环状态"""
    loop_type: str
    enabled: bool = True
    running: bool = False
    last_run_at: Optional[str] = None
    last_result: Optional[str] = None
    error_count: int = 0
    last_error: Optional[str] = None
    interval_seconds: float = 5.0
    consecutive_failures: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RunnerConfig:
    """运行器配置 - 通过 feature flag 控制"""
    enabled: bool = True
    startup_scan_enabled: bool = True
    pending_scan_enabled: bool = True
    scheduler_enabled: bool = True
    retry_enabled: bool = True
    stuck_detection_enabled: bool = True
    recovery_enabled: bool = True
    heartbeat_enabled: bool = True
    
    # 间隔配置
    scanner_interval_seconds: float = 5.0
    scheduler_interval_seconds: float = 2.0
    retry_interval_seconds: float = 10.0
    stuck_detection_interval_seconds: float = 30.0
    recovery_interval_seconds: float = 15.0
    heartbeat_interval_seconds: float = 5.0
    
    # 阈值配置
    stuck_threshold_seconds: float = 300.0  # 5 分钟无进展视为卡住
    max_retry_attempts: int = 3
    retry_backoff_seconds: float = 30.0
    max_consecutive_failures: int = 5
    health_check_interval_seconds: float = 10.0
    
    # 路径配置
    tasks_base_dir: str = "artifacts/tasks"
    config_path: Optional[str] = None
    state_path: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RunnerConfig':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
    
    @classmethod
    def load(cls, config_path: str) -> 'RunnerConfig':
        """从文件加载配置"""
        path = Path(config_path)
        if path.exists():
            with open(path) as f:
                data = json.load(f)
            return cls.from_dict(data)
        return cls()
    
    def save(self, config_path: str):
        """保存配置到文件"""
        path = Path(config_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)


@dataclass
class TaskSummary:
    """任务摘要"""
    task_id: str
    status: str
    current_step: Optional[str]
    has_pending_steps: bool
    has_running_steps: bool
    has_failed_steps: bool
    stuck_detected: bool
    last_updated: Optional[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RunnerStatus:
    """运行器状态快照"""
    state: str
    runner_id: str
    started_at: Optional[str] = None
    uptime_seconds: float = 0.0
    loops: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    active_tasks: int = 0
    pending_tasks: int = 0
    stuck_tasks: int = 0
    recovered_tasks: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AutonomousRunner:
    """
    自主运行器
    
    负责管理任务的生命周期和自动推进，包括：
    - 启动时扫描未完成任务
    - 周期性扫描待处理任务
    - 调度步骤执行
    - 重试失败步骤
    - 检测卡住的任务
    - 从崩溃中恢复
    - 心跳和健康监控
    """
    
    def __init__(
        self,
        config: Optional[RunnerConfig] = None,
        task_dossier_factory: Optional[Callable] = None,
        step_scheduler_factory: Optional[Callable] = None,
        resume_engine_factory: Optional[Callable] = None,
        step_executor_factory: Optional[Callable] = None
    ):
        self.runner_id = f"runner_{uuid.uuid4().hex[:8]}"
        self.config = config or RunnerConfig()
        
        # 工厂函数 - 用于创建组件实例
        self._task_dossier_factory = task_dossier_factory
        self._step_scheduler_factory = step_scheduler_factory
        self._resume_engine_factory = resume_engine_factory
        self._step_executor_factory = step_executor_factory
        
        # 状态
        self._state = RunnerState.STOPPED
        self._started_at: Optional[datetime] = None
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        
        # 循环状态
        self._loop_statuses: Dict[str, LoopStatus] = {
            LoopType.STARTUP.value: LoopStatus(loop_type=LoopType.STARTUP.value, interval_seconds=0),
            LoopType.SCANNER.value: LoopStatus(loop_type=LoopType.SCANNER.value, interval_seconds=self.config.scanner_interval_seconds),
            LoopType.SCHEDULER.value: LoopStatus(loop_type=LoopType.SCHEDULER.value, interval_seconds=self.config.scheduler_interval_seconds),
            LoopType.RETRY.value: LoopStatus(loop_type=LoopType.RETRY.value, interval_seconds=self.config.retry_interval_seconds),
            LoopType.STUCK_DETECTOR.value: LoopStatus(loop_type=LoopType.STUCK_DETECTOR.value, interval_seconds=self.config.stuck_detection_interval_seconds),
            LoopType.RECOVERY.value: LoopStatus(loop_type=LoopType.RECOVERY.value, interval_seconds=self.config.recovery_interval_seconds),
            LoopType.HEARTBEAT.value: LoopStatus(loop_type=LoopType.HEARTBEAT.value, interval_seconds=self.config.heartbeat_interval_seconds),
        }
        
        # 线程
        self._threads: Dict[str, threading.Thread] = {}
        
        # 任务追踪
        self._active_tasks: Dict[str, TaskSummary] = {}
        self._task_recovery_counts: Dict[str, int] = {}
        
        # 统计
        self._stats = {
            "tasks_scanned": 0,
            "tasks_scheduled": 0,
            "tasks_retried": 0,
            "tasks_recovered": 0,
            "steps_executed": 0,
            "errors": 0
        }
        
        # 回调
        self._on_task_progress: Optional[Callable] = None
        self._on_error: Optional[Callable] = None
        self._on_health_issue: Optional[Callable] = None
        
        # 信号处理
        self._setup_signal_handlers()
    
    def _setup_signal_handlers(self):
        """设置信号处理器"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            self.stop()
        
        try:
            signal.signal(signal.SIGTERM, signal_handler)
            signal.signal(signal.SIGINT, signal_handler)
        except ValueError:
            # 信号处理只能在主线程设置
            pass
    
    # ==================== 生命周期管理 ====================
    
    def start(self) -> bool:
        """
        启动自主运行器
        
        Returns:
            bool: 启动是否成功
        """
        if self._state == RunnerState.RUNNING:
            logger.warning("Runner already running")
            return True
        
        if not self.config.enabled:
            logger.warning("Runner is disabled by config")
            return False
        
        logger.info(f"Starting autonomous runner: {self.runner_id}")
        self._state = RunnerState.STARTING
        self._stop_event.clear()
        self._pause_event.clear()
        
        # 启动时扫描
        if self.config.startup_scan_enabled:
            self._run_startup_scan()
        
        # 启动各个循环线程
        self._start_loops()
        
        self._state = RunnerState.RUNNING
        self._started_at = datetime.utcnow()
        logger.info(f"Autonomous runner started: {self.runner_id}")
        
        return True
    
    def stop(self, timeout: float = 30.0) -> bool:
        """
        停止自主运行器
        
        Args:
            timeout: 等待线程结束的超时时间
            
        Returns:
            bool: 是否成功停止
        """
        if self._state == RunnerState.STOPPED:
            return True
        
        logger.info(f"Stopping autonomous runner: {self.runner_id}")
        self._state = RunnerState.STOPPING
        
        # 设置停止事件
        self._stop_event.set()
        
        # 等待所有线程结束
        for name, thread in self._threads.items():
            if thread.is_alive():
                thread.join(timeout=timeout)
                if thread.is_alive():
                    logger.warning(f"Thread {name} did not stop gracefully")
        
        self._threads.clear()
        self._state = RunnerState.STOPPED
        logger.info(f"Autonomous runner stopped: {self.runner_id}")
        
        return True
    
    def pause(self) -> bool:
        """暂停运行器"""
        if self._state != RunnerState.RUNNING:
            return False
        
        self._pause_event.set()
        self._state = RunnerState.PAUSED
        logger.info(f"Runner paused: {self.runner_id}")
        return True
    
    def resume(self) -> bool:
        """恢复运行器"""
        if self._state != RunnerState.PAUSED:
            return False
        
        self._pause_event.clear()
        self._state = RunnerState.RUNNING
        logger.info(f"Runner resumed: {self.runner_id}")
        return True
    
    def get_status(self) -> RunnerStatus:
        """获取运行器状态"""
        uptime = 0.0
        if self._started_at:
            uptime = (datetime.utcnow() - self._started_at).total_seconds()
        
        return RunnerStatus(
            state=self._state.value,
            runner_id=self.runner_id,
            started_at=self._started_at.isoformat() + "Z" if self._started_at else None,
            uptime_seconds=uptime,
            loops={k: v.to_dict() for k, v in self._loop_statuses.items()},
            active_tasks=len([t for t in self._active_tasks.values() if t.status == "running"]),
            pending_tasks=len([t for t in self._active_tasks.values() if t.has_pending_steps]),
            stuck_tasks=len([t for t in self._active_tasks.values() if t.stuck_detected]),
            recovered_tasks=sum(self._task_recovery_counts.values())
        )
    
    # ==================== 循环管理 ====================
    
    def _start_loops(self):
        """启动所有循环"""
        loops_config = [
            (LoopType.SCANNER, self._scanner_loop, self.config.pending_scan_enabled),
            (LoopType.SCHEDULER, self._scheduler_loop, self.config.scheduler_enabled),
            (LoopType.RETRY, self._retry_loop, self.config.retry_enabled),
            (LoopType.STUCK_DETECTOR, self._stuck_detector_loop, self.config.stuck_detection_enabled),
            (LoopType.RECOVERY, self._recovery_loop, self.config.recovery_enabled),
            (LoopType.HEARTBEAT, self._heartbeat_loop, self.config.heartbeat_enabled),
        ]
        
        for loop_type, target, enabled in loops_config:
            if enabled:
                self._start_loop_thread(loop_type.value, target)
    
    def _start_loop_thread(self, name: str, target: Callable):
        """启动单个循环线程"""
        if name in self._threads and self._threads[name].is_alive():
            return
        
        thread = threading.Thread(
            target=target,
            name=f"{self.runner_id}_{name}",
            daemon=True
        )
        thread.start()
        self._threads[name] = thread
        logger.debug(f"Started loop thread: {name}")
    
    def _wait_for_interval(self, loop_type: LoopType, interval: float) -> bool:
        """
        等待间隔时间，可被中断
        
        Returns:
            bool: True 如果应该继续，False 如果应该停止
        """
        status = self._loop_statuses[loop_type.value]
        check_interval = min(0.5, interval / 10)
        elapsed = 0.0
        
        while elapsed < interval:
            if self._stop_event.is_set():
                return False
            
            if self._pause_event.is_set():
                # 暂停时等待
                while self._pause_event.is_set() and not self._stop_event.is_set():
                    time.sleep(check_interval)
                if self._stop_event.is_set():
                    return False
            
            time.sleep(check_interval)
            elapsed += check_interval
        
        return True
    
    def _record_loop_result(self, loop_type: LoopType, result: str, error: Optional[str] = None):
        """记录循环执行结果"""
        status = self._loop_statuses[loop_type.value]
        status.last_run_at = datetime.utcnow().isoformat() + "Z"
        status.last_result = result
        
        if error:
            status.error_count += 1
            status.last_error = error
            status.consecutive_failures += 1
            self._stats["errors"] += 1
        else:
            status.consecutive_failures = 0
    
    # ==================== 1. Service Startup Loop ====================
    
    def _run_startup_scan(self):
        """
        服务启动扫描
        
        在服务启动时执行，扫描所有未完成的任务并恢复执行。
        """
        logger.info("Running startup scan...")
        status = self._loop_statuses[LoopType.STARTUP.value]
        status.running = True
        
        try:
            tasks = self._scan_all_tasks()
            recovered = 0
            
            for task_summary in tasks:
                if task_summary.status in ("created", "running", "blocked"):
                    self._active_tasks[task_summary.task_id] = task_summary
                    
                    if task_summary.has_pending_steps or task_summary.has_running_steps:
                        logger.info(f"Found unfinished task at startup: {task_summary.task_id}")
                        recovered += 1
            
            self._record_loop_result(LoopType.STARTUP, f"recovered_{recovered}_tasks")
            logger.info(f"Startup scan complete: {recovered} tasks recovered")
            
        except Exception as e:
            error_msg = f"Startup scan failed: {e}"
            logger.error(error_msg)
            self._record_loop_result(LoopType.STARTUP, "error", error_msg)
        finally:
            status.running = False
    
    # ==================== 2. Pending Task Scanner Loop ====================
    
    def _scanner_loop(self):
        """
        待处理任务扫描循环
        
        周期性扫描任务目录，发现新的或未完成的任务。
        """
        loop_type = LoopType.SCANNER
        status = self._loop_statuses[loop_type.value]
        logger.info(f"Scanner loop started, interval: {status.interval_seconds}s")
        
        while not self._stop_event.is_set():
            status.running = True
            
            try:
                # 扫描任务
                tasks = self._scan_all_tasks()
                new_tasks = 0
                
                for task_summary in tasks:
                    if task_summary.task_id not in self._active_tasks:
                        if task_summary.status in ("created", "running", "blocked"):
                            self._active_tasks[task_summary.task_id] = task_summary
                            new_tasks += 1
                            logger.debug(f"New task discovered: {task_summary.task_id}")
                    else:
                        # 更新现有任务状态
                        self._active_tasks[task_summary.task_id] = task_summary
                
                self._stats["tasks_scanned"] += len(tasks)
                self._record_loop_result(loop_type, f"scanned_{len(tasks)}_tasks_new_{new_tasks}")
                
            except Exception as e:
                error_msg = f"Scanner loop error: {e}"
                logger.error(error_msg)
                self._record_loop_result(loop_type, "error", error_msg)
            
            finally:
                status.running = False
            
            # 等待下次扫描
            if not self._wait_for_interval(loop_type, status.interval_seconds):
                break
        
        logger.info("Scanner loop stopped")
    
    def _scan_all_tasks(self) -> List[TaskSummary]:
        """扫描所有任务目录"""
        tasks = []
        tasks_dir = Path(self.config.tasks_base_dir)
        
        if not tasks_dir.exists():
            return tasks
        
        for task_dir in tasks_dir.iterdir():
            if not task_dir.is_dir():
                continue
            
            state_file = task_dir / "task_state.json"
            if not state_file.exists():
                continue
            
            try:
                with open(state_file) as f:
                    state = json.load(f)
                
                task_summary = TaskSummary(
                    task_id=state["task_id"],
                    status=state["status"],
                    current_step=state.get("current_step"),
                    has_pending_steps=any(s["status"] == "pending" for s in state.get("steps", [])),
                    has_running_steps=any(s["status"] == "running" for s in state.get("steps", [])),
                    has_failed_steps=any(s["status"] in ("failed_retryable", "failed_blocked") for s in state.get("steps", [])),
                    stuck_detected=False,
                    last_updated=state.get("updated_at")
                )
                tasks.append(task_summary)
                
            except Exception as e:
                logger.warning(f"Failed to read task state: {task_dir.name}: {e}")
        
        return tasks
    
    # ==================== 3. Scheduler Loop ====================
    
    def _scheduler_loop(self):
        """
        调度循环
        
        负责调度待执行的步骤，通过 step_scheduler 进行准入控制。
        """
        loop_type = LoopType.SCHEDULER
        status = self._loop_statuses[loop_type.value]
        logger.info(f"Scheduler loop started, interval: {status.interval_seconds}s")
        
        while not self._stop_event.is_set():
            status.running = True
            
            try:
                scheduled = 0
                
                for task_id, task_summary in list(self._active_tasks.items()):
                    if task_summary.status != "running":
                        continue
                    
                    if not task_summary.has_pending_steps:
                        continue
                    
                    # 尝试调度下一步
                    if self._schedule_next_step(task_id, task_summary):
                        scheduled += 1
                
                self._stats["tasks_scheduled"] += scheduled
                self._record_loop_result(loop_type, f"scheduled_{scheduled}_steps")
                
            except Exception as e:
                error_msg = f"Scheduler loop error: {e}"
                logger.error(error_msg)
                self._record_loop_result(loop_type, "error", error_msg)
            
            finally:
                status.running = False
            
            if not self._wait_for_interval(loop_type, status.interval_seconds):
                break
        
        logger.info("Scheduler loop stopped")
    
    def _schedule_next_step(self, task_id: str, task_summary: TaskSummary) -> bool:
        """
        调度下一个待执行步骤
        
        Returns:
            bool: 是否成功调度
        """
        try:
            # 加载任务状态
            state = self._load_task_state(task_id)
            if not state:
                return False
            
            # 找到下一个待执行步骤
            next_step = None
            for step in state.get("steps", []):
                if step["status"] == "pending":
                    # 检查依赖
                    if self._check_dependencies_met(state, step["step_id"]):
                        next_step = step
                        break
            
            if not next_step:
                return False
            
            step_id = next_step["step_id"]
            
            # 如果有调度器，进行调度准入检查
            if self._step_scheduler_factory:
                scheduler = self._step_scheduler_factory()
                decision = scheduler.request_execution(
                    task_id=task_id,
                    step_id=step_id,
                    worker_id=self.runner_id
                )
                
                if decision.decision != "admit":
                    logger.debug(f"Step {step_id} not admitted: {decision.reason}")
                    return False
            
            # 执行步骤
            return self._execute_step(task_id, step_id)
            
        except Exception as e:
            logger.error(f"Failed to schedule step for {task_id}: {e}")
            return False
    
    def _check_dependencies_met(self, state: Dict[str, Any], step_id: str) -> bool:
        """检查步骤依赖是否满足"""
        # 从 plan_graph 加载依赖信息
        task_id = state["task_id"]
        plan_graph_path = Path(self.config.tasks_base_dir) / task_id / "plan_graph.json"
        
        if not plan_graph_path.exists():
            return True  # 没有计划图，假设无依赖
        
        try:
            with open(plan_graph_path) as f:
                plan_graph = json.load(f)
            
            dependencies = plan_graph.get("dependencies", {}).get(step_id, [])
            
            for dep_id in dependencies:
                dep_step = next((s for s in state.get("steps", []) if s["step_id"] == dep_id), None)
                if not dep_step or dep_step["status"] != "success":
                    return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Failed to check dependencies: {e}")
            return True
    
    def _execute_step(self, task_id: str, step_id: str) -> bool:
        """
        执行步骤
        
        Returns:
            bool: 是否成功启动执行
        """
        try:
            # 更新步骤状态为 running
            self._update_step_status(task_id, step_id, "running")
            
            # 如果有执行器工厂，创建执行器
            if self._step_executor_factory and self._task_dossier_factory:
                dossier = self._task_dossier_factory(task_id)
                step_packet = dossier.get_step_packet(step_id)
                
                if step_packet:
                    executor = self._step_executor_factory(dossier)
                    result = executor.execute_step(step_packet)
                    
                    # 更新步骤状态
                    self._update_step_status(
                        task_id,
                        step_id,
                        result.status,
                        result.error.get("message") if result.error else None
                    )
                    
                    self._stats["steps_executed"] += 1
                    
                    # 回调通知
                    if self._on_task_progress:
                        self._on_task_progress(task_id, step_id, result.status)
                    
                    return result.status == "success"
            
            # 没有执行器，返回成功（模拟执行）
            logger.info(f"No executor configured, marking step as executed: {task_id}/{step_id}")
            self._update_step_status(task_id, step_id, "success")
            return True
            
        except Exception as e:
            logger.error(f"Failed to execute step {task_id}/{step_id}: {e}")
            self._update_step_status(task_id, step_id, "failed_retryable", str(e))
            return False
    
    # ==================== 4. Retry Loop ====================
    
    def _retry_loop(self):
        """
        重试循环
        
        负责重试失败的步骤。
        """
        loop_type = LoopType.RETRY
        status = self._loop_statuses[loop_type.value]
        logger.info(f"Retry loop started, interval: {status.interval_seconds}s")
        
        while not self._stop_event.is_set():
            status.running = True
            
            try:
                retried = 0
                
                for task_id, task_summary in list(self._active_tasks.items()):
                    if not task_summary.has_failed_steps:
                        continue
                    
                    if self._retry_failed_steps(task_id):
                        retried += 1
                
                self._stats["tasks_retried"] += retried
                self._record_loop_result(loop_type, f"retried_{retried}_steps")
                
            except Exception as e:
                error_msg = f"Retry loop error: {e}"
                logger.error(error_msg)
                self._record_loop_result(loop_type, "error", error_msg)
            
            finally:
                status.running = False
            
            if not self._wait_for_interval(loop_type, status.interval_seconds):
                break
        
        logger.info("Retry loop stopped")
    
    def _retry_failed_steps(self, task_id: str) -> bool:
        """
        重试失败步骤
        
        Returns:
            bool: 是否有步骤被重试
        """
        try:
            state = self._load_task_state(task_id)
            if not state:
                return False
            
            retried = False
            
            for step in state.get("steps", []):
                if step["status"] == "failed_retryable":
                    step_id = step["step_id"]
                    attempts = step.get("attempts", 0)
                    
                    if attempts < self.config.max_retry_attempts:
                        logger.info(f"Retrying step: {task_id}/{step_id} (attempt {attempts + 1})")
                        
                        # 检查退避时间
                        last_completed = step.get("completed_at")
                        if last_completed:
                            last_time = datetime.fromisoformat(last_completed.replace("Z", "+00:00"))
                            elapsed = (datetime.utcnow() - last_time.replace(tzinfo=None)).total_seconds()
                            
                            if elapsed < self.config.retry_backoff_seconds:
                                continue
                        
                        # 重置状态为 pending
                        self._update_step_status(task_id, step_id, "pending")
                        retried = True
            
            return retried
            
        except Exception as e:
            logger.error(f"Failed to retry steps for {task_id}: {e}")
            return False
    
    # ==================== 5. Stuck Task Detector Loop ====================
    
    def _stuck_detector_loop(self):
        """
        卡住任务检测循环
        
        检测长时间无进展的任务。
        """
        loop_type = LoopType.STUCK_DETECTOR
        status = self._loop_statuses[loop_type.value]
        logger.info(f"Stuck detector loop started, interval: {status.interval_seconds}s")
        
        while not self._stop_event.is_set():
            status.running = True
            
            try:
                stuck_count = 0
                
                for task_id, task_summary in list(self._active_tasks.items()):
                    if self._detect_stuck_task(task_id, task_summary):
                        stuck_count += 1
                
                self._record_loop_result(loop_type, f"detected_{stuck_count}_stuck")
                
            except Exception as e:
                error_msg = f"Stuck detector loop error: {e}"
                logger.error(error_msg)
                self._record_loop_result(loop_type, "error", error_msg)
            
            finally:
                status.running = False
            
            if not self._wait_for_interval(loop_type, status.interval_seconds):
                break
        
        logger.info("Stuck detector loop stopped")
    
    def _detect_stuck_task(self, task_id: str, task_summary: TaskSummary) -> bool:
        """
        检测任务是否卡住
        
        Returns:
            bool: 是否检测到卡住
        """
        try:
            # 检查最后更新时间
            if task_summary.last_updated:
                last_time = datetime.fromisoformat(task_summary.last_updated.replace("Z", "+00:00"))
                elapsed = (datetime.utcnow() - last_time.replace(tzinfo=None)).total_seconds()
                
                if elapsed > self.config.stuck_threshold_seconds:
                    if task_summary.status == "running":
                        logger.warning(f"Stuck task detected: {task_id} (no update for {elapsed:.0f}s)")
                        
                        # 更新状态
                        self._active_tasks[task_id] = TaskSummary(
                            task_id=task_summary.task_id,
                            status=task_summary.status,
                            current_step=task_summary.current_step,
                            has_pending_steps=task_summary.has_pending_steps,
                            has_running_steps=task_summary.has_running_steps,
                            has_failed_steps=task_summary.has_failed_steps,
                            stuck_detected=True,
                            last_updated=task_summary.last_updated
                        )
                        
                        # 回调通知
                        if self._on_health_issue:
                            self._on_health_issue("stuck_task", task_id, {"elapsed_seconds": elapsed})
                        
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to detect stuck task {task_id}: {e}")
            return False
    
    # ==================== 6. Restart Recovery Loop ====================
    
    def _recovery_loop(self):
        """
        重启恢复循环
        
        负责从崩溃中恢复任务执行。
        """
        loop_type = LoopType.RECOVERY
        status = self._loop_statuses[loop_type.value]
        logger.info(f"Recovery loop started, interval: {status.interval_seconds}s")
        
        while not self._stop_event.is_set():
            status.running = True
            
            try:
                recovered = 0
                
                for task_id, task_summary in list(self._active_tasks.items()):
                    if task_summary.stuck_detected or task_summary.has_running_steps:
                        if self._recover_task(task_id):
                            recovered += 1
                
                self._stats["tasks_recovered"] += recovered
                self._record_loop_result(loop_type, f"recovered_{recovered}_tasks")
                
            except Exception as e:
                error_msg = f"Recovery loop error: {e}"
                logger.error(error_msg)
                self._record_loop_result(loop_type, "error", error_msg)
            
            finally:
                status.running = False
            
            if not self._wait_for_interval(loop_type, status.interval_seconds):
                break
        
        logger.info("Recovery loop stopped")
    
    def _recover_task(self, task_id: str) -> bool:
        """
        恢复任务执行
        
        Returns:
            bool: 是否成功恢复
        """
        try:
            # 检查恢复次数
            recovery_count = self._task_recovery_counts.get(task_id, 0)
            if recovery_count >= self.config.max_consecutive_failures:
                logger.warning(f"Task {task_id} exceeded max recovery attempts")
                return False
            
            logger.info(f"Recovering task: {task_id}")
            
            # 使用 resume_engine 恢复
            if self._resume_engine_factory and self._task_dossier_factory:
                dossier = self._task_dossier_factory(task_id)
                engine = self._resume_engine_factory(dossier)
                
                context = engine.analyze()
                
                if context.needs_recovery:
                    # 获取执行上下文
                    exec_context = engine.rebuild_context(context)
                    
                    # 执行恢复动作
                    if context.recovery_action == "continue":
                        if context.current_step_id:
                            return self._execute_step(task_id, context.current_step_id)
                    
                    elif context.recovery_action == "retry":
                        # 获取租约
                        if context.current_step_id:
                            engine.acquire_lease(context.current_step_id, self.runner_id)
                            return self._execute_step(task_id, context.current_step_id)
            
            # 记录恢复
            self._task_recovery_counts[task_id] = recovery_count + 1
            
            # 更新任务状态
            if task_id in self._active_tasks:
                old_summary = self._active_tasks[task_id]
                self._active_tasks[task_id] = TaskSummary(
                    task_id=old_summary.task_id,
                    status=old_summary.status,
                    current_step=old_summary.current_step,
                    has_pending_steps=old_summary.has_pending_steps,
                    has_running_steps=old_summary.has_running_steps,
                    has_failed_steps=old_summary.has_failed_steps,
                    stuck_detected=False,
                    last_updated=datetime.utcnow().isoformat() + "Z"
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to recover task {task_id}: {e}")
            return False
    
    # ==================== 7. Heartbeat / Health Monitor Loop ====================
    
    def _heartbeat_loop(self):
        """
        心跳健康监控循环
        
        发送心跳并监控系统健康状态。
        """
        loop_type = LoopType.HEARTBEAT
        status = self._loop_statuses[loop_type.value]
        logger.info(f"Heartbeat loop started, interval: {status.interval_seconds}s")
        
        while not self._stop_event.is_set():
            status.running = True
            
            try:
                # 发送心跳
                self._send_heartbeat()
                
                # 检查系统健康
                health_issues = self._check_health()
                
                if health_issues:
                    issue_str = ", ".join(health_issues)
                    self._record_loop_result(loop_type, f"health_issues: {issue_str}")
                    
                    if self._on_health_issue:
                        for issue in health_issues:
                            self._on_health_issue(issue, self.runner_id, {})
                else:
                    self._record_loop_result(loop_type, "healthy")
                
            except Exception as e:
                error_msg = f"Heartbeat loop error: {e}"
                logger.error(error_msg)
                self._record_loop_result(loop_type, "error", error_msg)
            
            finally:
                status.running = False
            
            if not self._wait_for_interval(loop_type, status.interval_seconds):
                break
        
        logger.info("Heartbeat loop stopped")
    
    def _send_heartbeat(self):
        """发送心跳"""
        heartbeat_file = Path(self.config.state_path or ".autonomous_runner") / "heartbeat.json"
        heartbeat_file.parent.mkdir(parents=True, exist_ok=True)
        
        heartbeat = {
            "runner_id": self.runner_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "state": self._state.value,
            "stats": self._stats.copy()
        }
        
        with open(heartbeat_file, 'w') as f:
            json.dump(heartbeat, f, indent=2)
    
    def _check_health(self) -> List[str]:
        """
        检查系统健康状态
        
        Returns:
            List[str]: 健康问题列表
        """
        issues = []
        
        # 检查循环失败次数
        for loop_type, status in self._loop_statuses.items():
            if status.consecutive_failures >= self.config.max_consecutive_failures:
                issues.append(f"loop_{loop_type}_failing")
        
        # 检查活跃任务数
        active_count = len([t for t in self._active_tasks.values() if t.status == "running"])
        if active_count > 10:  # 可配置
            issues.append(f"high_active_tasks: {active_count}")
        
        # 检查卡住任务数
        stuck_count = len([t for t in self._active_tasks.values() if t.stuck_detected])
        if stuck_count > 3:
            issues.append(f"multiple_stuck_tasks: {stuck_count}")
        
        return issues
    
    # ==================== 辅助方法 ====================
    
    def _load_task_state(self, task_id: str) -> Optional[Dict[str, Any]]:
        """加载任务状态"""
        state_file = Path(self.config.tasks_base_dir) / task_id / "task_state.json"
        
        if not state_file.exists():
            return None
        
        try:
            with open(state_file) as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load task state: {task_id}: {e}")
            return None
    
    def _update_step_status(
        self, 
        task_id: str, 
        step_id: str, 
        status: str, 
        error: Optional[str] = None
    ) -> bool:
        """
        更新步骤状态
        
        Returns:
            bool: 是否成功更新
        """
        state_file = Path(self.config.tasks_base_dir) / task_id / "task_state.json"
        
        if not state_file.exists():
            return False
        
        try:
            with open(state_file) as f:
                state = json.load(f)
            
            now = datetime.utcnow().isoformat() + "Z"
            
            for step in state.get("steps", []):
                if step["step_id"] == step_id:
                    step["status"] = status
                    step["updated_at"] = now
                    
                    if status == "running" and not step.get("started_at"):
                        step["started_at"] = now
                    
                    if status in ("success", "failed_terminal"):
                        step["completed_at"] = now
                    
                    if error:
                        step["error"] = error
                    break
            
            # 更新任务状态
            state["updated_at"] = now
            
            # 检查是否所有步骤都完成
            all_success = all(s["status"] == "success" for s in state.get("steps", []))
            if all_success:
                state["status"] = "completed"
                state["current_step"] = None
            else:
                # 更新当前步骤
                for step in state.get("steps", []):
                    if step["status"] == "pending":
                        state["current_step"] = step["step_id"]
                        break
            
            # 保存状态
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2)
            
            # 追加 ledger
            ledger_file = Path(self.config.tasks_base_dir) / task_id / "ledger.jsonl"
            event = {
                "timestamp": now,
                "action": "step_status_updated",
                "task_id": task_id,
                "data": {
                    "step_id": step_id,
                    "status": status,
                    "error": error
                }
            }
            with open(ledger_file, 'a') as f:
                f.write(json.dumps(event) + "\n")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update step status: {task_id}/{step_id}: {e}")
            return False
    
    # ==================== 回调设置 ====================
    
    def on_task_progress(self, callback: Callable):
        """设置任务进度回调"""
        self._on_task_progress = callback
    
    def on_error(self, callback: Callable):
        """设置错误回调"""
        self._on_error = callback
    
    def on_health_issue(self, callback: Callable):
        """设置健康问题回调"""
        self._on_health_issue = callback
    
    # ==================== 统计信息 ====================
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self._stats,
            "active_tasks": len(self._active_tasks),
            "stuck_tasks": len([t for t in self._active_tasks.values() if t.stuck_detected]),
            "recovery_counts": dict(self._task_recovery_counts)
        }


# ==================== 工厂函数 ====================

def create_autonomous_runner(
    config: Optional[RunnerConfig] = None,
    config_path: Optional[str] = None,
    task_dossier_factory: Optional[Callable] = None,
    step_scheduler_factory: Optional[Callable] = None,
    resume_engine_factory: Optional[Callable] = None,
    step_executor_factory: Optional[Callable] = None
) -> AutonomousRunner:
    """
    创建自主运行器
    
    Args:
        config: 配置对象
        config_path: 配置文件路径
        task_dossier_factory: 任务档案工厂函数
        step_scheduler_factory: 步骤调度器工厂函数
        resume_engine_factory: 恢复引擎工厂函数
        step_executor_factory: 步骤执行器工厂函数
        
    Returns:
        AutonomousRunner 实例
    """
    if config is None and config_path:
        config = RunnerConfig.load(config_path)
    
    return AutonomousRunner(
        config=config,
        task_dossier_factory=task_dossier_factory,
        step_scheduler_factory=step_scheduler_factory,
        resume_engine_factory=resume_engine_factory,
        step_executor_factory=step_executor_factory
    )


# ==================== CLI 入口 ====================

def main():
    """CLI 入口点"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Autonomous Runner (v3-D)")
    parser.add_argument("--config", "-c", help="Config file path")
    parser.add_argument("--tasks-dir", "-t", default="artifacts/tasks", help="Tasks directory")
    parser.add_argument("--state-dir", "-s", default=".autonomous_runner", help="State directory")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    parser.add_argument("--status", action="store_true", help="Show status and exit")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    args = parser.parse_args()
    
    config = RunnerConfig(
        tasks_base_dir=args.tasks_dir,
        state_path=args.state_dir
    )
    
    if args.config:
        config = RunnerConfig.load(args.config)
    
    runner = create_autonomous_runner(config=config)
    
    if args.status:
        status = runner.get_status()
        if args.json:
            print(json.dumps(status.to_dict(), indent=2))
        else:
            print(f"Runner: {status.runner_id}")
            print(f"State: {status.state}")
            print(f"Active tasks: {status.active_tasks}")
            print(f"Pending tasks: {status.pending_tasks}")
            print(f"Stuck tasks: {status.stuck_tasks}")
        return
    
    if args.once:
        runner._run_startup_scan()
        status = runner.get_status()
        if args.json:
            print(json.dumps(status.to_dict(), indent=2))
        else:
            print(f"Startup scan complete")
            print(f"Active tasks: {status.active_tasks}")
        return
    
    # 正常启动
    try:
        runner.start()
        logger.info(f"Autonomous runner started: {runner.runner_id}")
        logger.info("Press Ctrl+C to stop")
        
        # 等待停止信号
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    finally:
        runner.stop()


if __name__ == "__main__":
    main()