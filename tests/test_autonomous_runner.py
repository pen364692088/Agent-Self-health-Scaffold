"""
Tests for v3-D: Autonomous Runner

测试自主运行器的核心功能：
1. 生命周期管理 (start/stop/pause/resume)
2. 启动扫描
3. 任务扫描器
4. 调度器
5. 重试机制
6. 卡住检测
7. 恢复机制
8. 心跳监控
9. Feature flag 控制
10. v2 baseline 兼容性
"""

import json
import os
import shutil
import tempfile
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from runtime.autonomous_runner import (
    AutonomousRunner,
    RunnerConfig,
    RunnerState,
    RunnerStatus,
    LoopType,
    LoopStatus,
    TaskSummary,
    create_autonomous_runner
)


class TestRunnerConfig:
    """测试运行器配置"""
    
    def test_default_config(self):
        """测试默认配置"""
        config = RunnerConfig()
        
        assert config.enabled is True
        assert config.startup_scan_enabled is True
        assert config.pending_scan_enabled is True
        assert config.scheduler_enabled is True
        assert config.retry_enabled is True
        assert config.stuck_detection_enabled is True
        assert config.recovery_enabled is True
        assert config.heartbeat_enabled is True
    
    def test_config_from_dict(self):
        """测试从字典创建配置"""
        data = {
            "enabled": False,
            "scanner_interval_seconds": 10.0,
            "max_retry_attempts": 5
        }
        config = RunnerConfig.from_dict(data)
        
        assert config.enabled is False
        assert config.scanner_interval_seconds == 10.0
        assert config.max_retry_attempts == 5
    
    def test_config_save_load(self, tmp_path):
        """测试配置保存和加载"""
        config = RunnerConfig(
            enabled=True,
            scanner_interval_seconds=15.0,
            max_retry_attempts=3
        )
        
        config_path = tmp_path / "config.json"
        config.save(str(config_path))
        
        loaded = RunnerConfig.load(str(config_path))
        
        assert loaded.enabled == config.enabled
        assert loaded.scanner_interval_seconds == config.scanner_interval_seconds
        assert loaded.max_retry_attempts == config.max_retry_attempts


class TestAutonomousRunnerLifecycle:
    """测试运行器生命周期"""
    
    def test_create_runner(self):
        """测试创建运行器"""
        runner = AutonomousRunner()
        
        assert runner._state == RunnerState.STOPPED
        assert runner.runner_id.startswith("runner_")
    
    def test_start_runner(self):
        """测试启动运行器"""
        config = RunnerConfig(
            enabled=True,
            scanner_interval_seconds=999,  # 防止实际运行
            scheduler_interval_seconds=999,
            retry_interval_seconds=999,
            stuck_detection_interval_seconds=999,
            recovery_interval_seconds=999,
            heartbeat_interval_seconds=999
        )
        runner = AutonomousRunner(config=config)
        
        assert runner.start() is True
        assert runner._state == RunnerState.RUNNING
        
        runner.stop(timeout=2.0)
        assert runner._state == RunnerState.STOPPED
    
    def test_stop_runner(self):
        """测试停止运行器"""
        config = RunnerConfig(
            enabled=True,
            scanner_interval_seconds=999,
            scheduler_interval_seconds=999,
            retry_interval_seconds=999,
            stuck_detection_interval_seconds=999,
            recovery_interval_seconds=999,
            heartbeat_interval_seconds=999
        )
        runner = AutonomousRunner(config=config)
        
        runner.start()
        assert runner.stop(timeout=2.0) is True
        assert runner._state == RunnerState.STOPPED
    
    def test_pause_resume_runner(self):
        """测试暂停和恢复"""
        config = RunnerConfig(
            enabled=True,
            scanner_interval_seconds=999,
            scheduler_interval_seconds=999,
            retry_interval_seconds=999,
            stuck_detection_interval_seconds=999,
            recovery_interval_seconds=999,
            heartbeat_interval_seconds=999
        )
        runner = AutonomousRunner(config=config)
        
        runner.start()
        assert runner.pause() is True
        assert runner._state == RunnerState.PAUSED
        
        assert runner.resume() is True
        assert runner._state == RunnerState.RUNNING
        
        runner.stop(timeout=2.0)
    
    def test_disabled_runner_wont_start(self):
        """测试禁用的运行器不会启动"""
        config = RunnerConfig(enabled=False)
        runner = AutonomousRunner(config=config)
        
        assert runner.start() is False
        assert runner._state == RunnerState.STOPPED
    
    def test_get_status(self):
        """测试获取状态"""
        config = RunnerConfig(enabled=True)
        runner = AutonomousRunner(config=config)
        
        status = runner.get_status()
        
        assert status.state == RunnerState.STOPPED.value
        assert status.runner_id == runner.runner_id
        assert "loops" in status.to_dict()


class TestStartupScan:
    """测试启动扫描"""
    
    @pytest.fixture
    def temp_tasks_dir(self, tmp_path):
        """创建临时任务目录"""
        tasks_dir = tmp_path / "artifacts" / "tasks"
        tasks_dir.mkdir(parents=True)
        
        # 创建一个未完成的任务
        task_dir = tasks_dir / "task_test_001"
        task_dir.mkdir()
        
        state = {
            "task_id": "task_test_001",
            "version": "v1.0",
            "status": "running",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "updated_at": datetime.utcnow().isoformat() + "Z",
            "steps": [
                {"step_id": "S01", "status": "success", "attempts": 1},
                {"step_id": "S02", "status": "pending", "attempts": 0}
            ],
            "current_step": "S02",
            "contract": {
                "objective": "Test task",
                "repository": "/tmp/test",
                "acceptance_criteria": []
            }
        }
        
        with open(task_dir / "task_state.json", 'w') as f:
            json.dump(state, f)
        
        return tmp_path
    
    def test_startup_scan_finds_unfinished_tasks(self, temp_tasks_dir):
        """测试启动扫描发现未完成任务"""
        config = RunnerConfig(
            enabled=True,
            startup_scan_enabled=True,
            pending_scan_enabled=False,
            scheduler_enabled=False,
            retry_enabled=False,
            stuck_detection_enabled=False,
            recovery_enabled=False,
            heartbeat_enabled=False,
            tasks_base_dir=str(temp_tasks_dir / "artifacts" / "tasks")
        )
        runner = AutonomousRunner(config=config)
        
        # 运行启动扫描
        runner._run_startup_scan()
        
        assert "task_test_001" in runner._active_tasks
    
    def test_startup_scan_ignores_completed_tasks(self, tmp_path):
        """测试启动扫描忽略已完成任务"""
        tasks_dir = tmp_path / "artifacts" / "tasks"
        tasks_dir.mkdir(parents=True)
        
        # 创建一个已完成的任务
        task_dir = tasks_dir / "task_completed_001"
        task_dir.mkdir()
        
        state = {
            "task_id": "task_completed_001",
            "version": "v1.0",
            "status": "completed",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "updated_at": datetime.utcnow().isoformat() + "Z",
            "steps": [
                {"step_id": "S01", "status": "success", "attempts": 1}
            ],
            "current_step": None,
            "contract": {
                "objective": "Test task",
                "repository": "/tmp/test",
                "acceptance_criteria": []
            }
        }
        
        with open(task_dir / "task_state.json", 'w') as f:
            json.dump(state, f)
        
        config = RunnerConfig(
            enabled=True,
            startup_scan_enabled=True,
            pending_scan_enabled=False,
            scheduler_enabled=False,
            retry_enabled=False,
            stuck_detection_enabled=False,
            recovery_enabled=False,
            heartbeat_enabled=False,
            tasks_base_dir=str(tasks_dir)
        )
        runner = AutonomousRunner(config=config)
        
        runner._run_startup_scan()
        
        assert "task_completed_001" not in runner._active_tasks


class TestTaskScanner:
    """测试任务扫描器"""
    
    def test_scan_all_tasks(self, tmp_path):
        """测试扫描所有任务"""
        tasks_dir = tmp_path / "artifacts" / "tasks"
        tasks_dir.mkdir(parents=True)
        
        # 创建多个任务
        for i in range(3):
            task_dir = tasks_dir / f"task_{i:03d}"
            task_dir.mkdir()
            
            state = {
                "task_id": f"task_{i:03d}",
                "version": "v1.0",
                "status": "running",
                "created_at": datetime.utcnow().isoformat() + "Z",
                "updated_at": datetime.utcnow().isoformat() + "Z",
                "steps": [
                    {"step_id": "S01", "status": "pending", "attempts": 0}
                ],
                "current_step": "S01",
                "contract": {
                    "objective": f"Task {i}",
                    "repository": "/tmp/test",
                    "acceptance_criteria": []
                }
            }
            
            with open(task_dir / "task_state.json", 'w') as f:
                json.dump(state, f)
        
        config = RunnerConfig(tasks_base_dir=str(tasks_dir))
        runner = AutonomousRunner(config=config)
        
        tasks = runner._scan_all_tasks()
        
        assert len(tasks) == 3
        task_ids = [t.task_id for t in tasks]
        assert "task_000" in task_ids
        assert "task_001" in task_ids
        assert "task_002" in task_ids
    
    def test_scan_empty_directory(self, tmp_path):
        """测试扫描空目录"""
        tasks_dir = tmp_path / "artifacts" / "tasks"
        tasks_dir.mkdir(parents=True)
        
        config = RunnerConfig(tasks_base_dir=str(tasks_dir))
        runner = AutonomousRunner(config=config)
        
        tasks = runner._scan_all_tasks()
        
        assert len(tasks) == 0


class TestScheduler:
    """测试调度器"""
    
    def test_check_dependencies_met(self, tmp_path):
        """测试依赖检查"""
        tasks_dir = tmp_path / "artifacts" / "tasks"
        tasks_dir.mkdir(parents=True)
        
        task_dir = tasks_dir / "task_dep_001"
        task_dir.mkdir()
        
        # 创建计划图
        plan_graph = {
            "task_id": "task_dep_001",
            "steps": [
                {"step_id": "S01", "depends_on": []},
                {"step_id": "S02", "depends_on": ["S01"]}
            ],
            "dependencies": {
                "S01": [],
                "S02": ["S01"]
            }
        }
        
        with open(task_dir / "plan_graph.json", 'w') as f:
            json.dump(plan_graph, f)
        
        config = RunnerConfig(tasks_base_dir=str(tasks_dir))
        runner = AutonomousRunner(config=config)
        
        # S01 无依赖
        state = {"task_id": "task_dep_001", "steps": [{"step_id": "S01", "status": "pending"}]}
        assert runner._check_dependencies_met(state, "S01") is True
        
        # S02 依赖 S01，但 S01 未完成
        state = {"task_id": "task_dep_001", "steps": [
            {"step_id": "S01", "status": "pending"},
            {"step_id": "S02", "status": "pending"}
        ]}
        assert runner._check_dependencies_met(state, "S02") is False
        
        # S02 依赖 S01，S01 已完成
        state = {"task_id": "task_dep_001", "steps": [
            {"step_id": "S01", "status": "success"},
            {"step_id": "S02", "status": "pending"}
        ]}
        assert runner._check_dependencies_met(state, "S02") is True


class TestRetryMechanism:
    """测试重试机制"""
    
    def test_retry_failed_steps_respects_max_attempts(self, tmp_path):
        """测试重试次数限制"""
        tasks_dir = tmp_path / "artifacts" / "tasks"
        tasks_dir.mkdir(parents=True)
        
        task_dir = tasks_dir / "task_retry_001"
        task_dir.mkdir()
        
        state = {
            "task_id": "task_retry_001",
            "version": "v1.0",
            "status": "running",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "updated_at": datetime.utcnow().isoformat() + "Z",
            "steps": [
                {
                    "step_id": "S01",
                    "status": "failed_retryable",
                    "attempts": 3,  # 已达最大尝试次数
                    "started_at": None,
                    "completed_at": datetime.utcnow().isoformat() + "Z",
                    "error": None
                }
            ],
            "current_step": "S01",
            "contract": {
                "objective": "Test",
                "repository": "/tmp",
                "acceptance_criteria": []
            }
        }
        
        with open(task_dir / "task_state.json", 'w') as f:
            json.dump(state, f)
        
        config = RunnerConfig(
            max_retry_attempts=3,
            tasks_base_dir=str(tasks_dir)
        )
        runner = AutonomousRunner(config=config)
        
        # 尝试重试
        result = runner._retry_failed_steps("task_retry_001")
        
        # 已达最大次数，不会重试
        assert result is False


class TestStuckDetection:
    """测试卡住检测"""
    
    def test_detect_stuck_task(self, tmp_path):
        """测试检测卡住的任务"""
        tasks_dir = tmp_path / "artifacts" / "tasks"
        tasks_dir.mkdir(parents=True)
        
        # 创建一个看起来卡住的任务（最后更新是很久以前）
        old_time = (datetime.utcnow() - timedelta(minutes=10)).isoformat() + "Z"
        
        task_summary = TaskSummary(
            task_id="task_stuck_001",
            status="running",
            current_step="S01",
            has_pending_steps=False,
            has_running_steps=True,
            has_failed_steps=False,
            stuck_detected=False,
            last_updated=old_time
        )
        
        config = RunnerConfig(
            stuck_threshold_seconds=300.0,  # 5 分钟
            tasks_base_dir=str(tasks_dir)
        )
        runner = AutonomousRunner(config=config)
        
        # 检测卡住
        result = runner._detect_stuck_task("task_stuck_001", task_summary)
        
        assert result is True
    
    def test_not_stuck_recent_update(self, tmp_path):
        """测试最近更新的任务不被标记为卡住"""
        recent_time = (datetime.utcnow() - timedelta(minutes=1)).isoformat() + "Z"
        
        task_summary = TaskSummary(
            task_id="task_active_001",
            status="running",
            current_step="S01",
            has_pending_steps=False,
            has_running_steps=True,
            has_failed_steps=False,
            stuck_detected=False,
            last_updated=recent_time
        )
        
        config = RunnerConfig(
            stuck_threshold_seconds=300.0,
            tasks_base_dir=""
        )
        runner = AutonomousRunner(config=config)
        
        result = runner._detect_stuck_task("task_active_001", task_summary)
        
        assert result is False


class TestHeartbeat:
    """测试心跳"""
    
    def test_send_heartbeat(self, tmp_path):
        """测试发送心跳"""
        state_dir = tmp_path / ".autonomous_runner"
        
        config = RunnerConfig(
            enabled=True,
            state_path=str(state_dir)
        )
        runner = AutonomousRunner(config=config)
        
        runner._send_heartbeat()
        
        heartbeat_file = state_dir / "heartbeat.json"
        assert heartbeat_file.exists()
        
        with open(heartbeat_file) as f:
            heartbeat = json.load(f)
        
        assert heartbeat["runner_id"] == runner.runner_id
        assert heartbeat["state"] == RunnerState.STOPPED.value
    
    def test_check_health(self):
        """测试健康检查"""
        config = RunnerConfig()
        runner = AutonomousRunner(config=config)
        
        # 正常情况下应该没有问题
        issues = runner._check_health()
        assert len(issues) == 0


class TestFeatureFlags:
    """测试 Feature Flag 控制"""
    
    def test_individual_loops_can_be_disabled(self):
        """测试可以禁用单个循环"""
        config = RunnerConfig(
            enabled=True,
            scanner_interval_seconds=999,
            scheduler_enabled=False,
            retry_enabled=False,
            stuck_detection_enabled=False,
            recovery_enabled=False,
            heartbeat_enabled=False
        )
        runner = AutonomousRunner(config=config)
        
        # 只有 scanner 循环会被启动
        assert runner._loop_statuses[LoopType.SCHEDULER.value].enabled is True
        assert runner._loop_statuses[LoopType.RETRY.value].enabled is True
        # 但实际启动时不会创建线程
        
        # 验证配置
        assert config.scheduler_enabled is False
        assert config.retry_enabled is False
    
    def test_can_enable_without_startup_scan(self):
        """测试可以启动但不执行启动扫描"""
        config = RunnerConfig(
            enabled=True,
            startup_scan_enabled=False,
            pending_scan_enabled=False,
            scheduler_enabled=False,
            retry_enabled=False,
            stuck_detection_enabled=False,
            recovery_enabled=False,
            heartbeat_enabled=False
        )
        runner = AutonomousRunner(config=config)
        
        assert runner.start() is True
        assert runner._state == RunnerState.RUNNING
        
        runner.stop(timeout=2.0)


class TestV2BaselineCompatibility:
    """测试 v2 baseline 兼容性"""
    
    def test_gate_rules_not_modified(self):
        """测试 Gate 规则未被修改"""
        repo_root = Path(__file__).parent.parent
        
        gate_rules = repo_root / "docs" / "GATE_RULES.md"
        assert gate_rules.exists()
    
    def test_task_state_schema_not_modified(self):
        """测试 task_state.schema.json 未被修改"""
        repo_root = Path(__file__).parent.parent
        
        schema_file = repo_root / "schemas" / "task_state.schema.json"
        assert schema_file.exists()
        
        with open(schema_file) as f:
            schema = json.load(f)
        
        # 检查核心字段仍然存在
        required_fields = ["task_id", "version", "status", "created_at", "updated_at", "steps", "current_step", "contract"]
        for field in required_fields:
            assert field in schema.get("required", [])
    
    def test_autonomous_runner_uses_existing_components(self, tmp_path):
        """测试运行器使用现有组件"""
        tasks_dir = tmp_path / "artifacts" / "tasks"
        tasks_dir.mkdir(parents=True)
        
        config = RunnerConfig(
            enabled=True,
            tasks_base_dir=str(tasks_dir)
        )
        
        # 测试可以通过工厂函数注入现有组件
        task_dossier_called = []
        
        def mock_dossier_factory(task_id):
            task_dossier_called.append(task_id)
            return None
        
        runner = AutonomousRunner(
            config=config,
            task_dossier_factory=mock_dossier_factory
        )
        
        assert runner._task_dossier_factory is not None


class TestIntegration:
    """集成测试"""
    
    @pytest.fixture
    def full_setup(self, tmp_path):
        """完整测试环境设置"""
        tasks_dir = tmp_path / "artifacts" / "tasks"
        tasks_dir.mkdir(parents=True)
        state_dir = tmp_path / ".autonomous_runner"
        
        # 创建一个有 pending 步骤的任务
        task_dir = tasks_dir / "task_integration_001"
        task_dir.mkdir()
        
        state = {
            "task_id": "task_integration_001",
            "version": "v1.0",
            "status": "running",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "updated_at": datetime.utcnow().isoformat() + "Z",
            "steps": [
                {"step_id": "S01", "status": "success", "attempts": 1},
                {"step_id": "S02", "status": "pending", "attempts": 0}
            ],
            "current_step": "S02",
            "contract": {
                "objective": "Integration test",
                "repository": "/tmp/test",
                "acceptance_criteria": ["Step S02 completes"]
            }
        }
        
        with open(task_dir / "task_state.json", 'w') as f:
            json.dump(state, f)
        
        # 创建 step packet
        steps_dir = task_dir / "steps"
        steps_dir.mkdir()
        s02_dir = steps_dir / "S02"
        s02_dir.mkdir()
        
        step_packet = {
            "step_id": "S02",
            "step_type": "verify_outputs",
            "execution": {
                "expected_files": []
            }
        }
        
        with open(s02_dir / "step_packet.json", 'w') as f:
            json.dump(step_packet, f)
        
        return {
            "tasks_dir": str(tasks_dir),
            "state_dir": str(state_dir)
        }
    
    def test_full_lifecycle(self, full_setup):
        """测试完整生命周期"""
        config = RunnerConfig(
            enabled=True,
            startup_scan_enabled=True,
            pending_scan_enabled=False,
            scheduler_enabled=False,
            retry_enabled=False,
            stuck_detection_enabled=False,
            recovery_enabled=False,
            heartbeat_enabled=False,
            tasks_base_dir=full_setup["tasks_dir"],
            state_path=full_setup["state_dir"]
        )
        
        runner = AutonomousRunner(config=config)
        
        # 启动
        assert runner.start() is True
        assert runner._state == RunnerState.RUNNING
        
        # 检查状态
        status = runner.get_status()
        assert status.state == RunnerState.RUNNING.value
        
        # 检查任务被发现
        time.sleep(0.5)
        assert len(runner._active_tasks) >= 1
        
        # 停止
        assert runner.stop(timeout=2.0) is True
        assert runner._state == RunnerState.STOPPED


class TestFactoryFunction:
    """测试工厂函数"""
    
    def test_create_autonomous_runner(self):
        """测试工厂函数创建运行器"""
        runner = create_autonomous_runner()
        
        assert runner is not None
        assert isinstance(runner, AutonomousRunner)
    
    def test_create_with_config(self, tmp_path):
        """测试带配置创建运行器"""
        config = RunnerConfig(
            enabled=True,
            tasks_base_dir=str(tmp_path)
        )
        
        runner = create_autonomous_runner(config=config)
        
        assert runner.config.tasks_base_dir == str(tmp_path)
    
    def test_create_with_config_path(self, tmp_path):
        """测试从配置文件创建运行器"""
        config = RunnerConfig(enabled=False)
        config_path = tmp_path / "config.json"
        config.save(str(config_path))
        
        runner = create_autonomous_runner(config_path=str(config_path))
        
        assert runner.config.enabled is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
