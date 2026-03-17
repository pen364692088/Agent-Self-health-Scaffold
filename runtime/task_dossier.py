"""
Task Dossier - 最小兼容层

从现有 task_state.json 组装 runner 所需上下文。
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class TaskDossier:
    """
    Task Dossier - 任务档案
    
    从现有任务目录结构组装执行上下文。
    """
    
    def __init__(self, task_id: str, tasks_base_dir: str = "artifacts/tasks"):
        self.task_id = task_id
        self.tasks_base_dir = Path(tasks_base_dir)
        self.task_dir = self.tasks_base_dir / task_id
        
        # 核心路径
        self.state_file = self.task_dir / "task_state.json"
        self.steps_dir = self.task_dir / "steps"
        self.evidence_dir = self.task_dir / "evidence"
        self.ledger_file = self.task_dir / "ledger.jsonl"
        
        # 确保目录存在
        self.steps_dir.mkdir(parents=True, exist_ok=True)
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        
        # 加载任务状态
        self._state: Optional[Dict] = None
    
    @property
    def state(self) -> Dict:
        """延迟加载任务状态"""
        if self._state is None:
            if self.state_file.exists():
                with open(self.state_file) as f:
                    self._state = json.load(f)
            else:
                self._state = {}
        return self._state
    
    def get_step_packet(self, step_id: str) -> Optional[Dict[str, Any]]:
        """
        获取步骤执行包
        
        Args:
            step_id: 步骤 ID
            
        Returns:
            step_packet 字典，或 None
        """
        steps = self.state.get("steps", {})
        
        # 支持 dict 和 list 两种格式
        if isinstance(steps, dict):
            step_data = steps.get(step_id)
        elif isinstance(steps, list):
            step_data = next((s for s in steps if s.get("step_id") == step_id), None)
        else:
            return None
        
        if not step_data:
            return None
        
        # 组装 step_packet
        step_packet = {
            "step_id": step_id,
            "task_id": self.task_id,
            "title": step_data.get("step_name", step_data.get("title", step_id)),
            "goal": step_data.get("goal", step_data.get("description", "")),
            "status": step_data.get("status", "pending"),
            "depends_on": step_data.get("depends_on", []),
            "step_type": step_data.get("step_type", "execute_shell"),
            "execution_type": step_data.get("execution_type", step_data.get("step_type", "manual")),
            "execution": {
                "command": step_data.get("command"),
                "cwd": step_data.get("cwd"),
                "env": step_data.get("env", {}),
                "timeout_seconds": step_data.get("timeout_seconds", 300),
            },
            "command": step_data.get("command"),
            "script": step_data.get("script"),
            "inputs": step_data.get("inputs", {}),
            "expected_outputs": step_data.get("expected_outputs", []),
            "evidence_path": str(self.evidence_dir / step_id),
            "result_path": str(self.steps_dir / step_id / "result.json"),
        }
        
        return step_packet
    
    def get_all_steps(self) -> List[Dict[str, Any]]:
        """获取所有步骤"""
        steps = self.state.get("steps", {})
        
        if isinstance(steps, dict):
            return list(steps.values())
        elif isinstance(steps, list):
            return steps
        else:
            return []
    
    def get_pending_steps(self) -> List[str]:
        """获取待执行步骤 ID 列表"""
        return [
            s.get("step_id") for s in self.get_all_steps()
            if s.get("status") == "pending"
        ]
    
    def get_running_steps(self) -> List[str]:
        """获取运行中步骤 ID 列表"""
        return [
            s.get("step_id") for s in self.get_all_steps()
            if s.get("status") == "running"
        ]
    
    def update_step_status(self, step_id: str, status: str, **kwargs) -> bool:
        """
        更新步骤状态
        
        Args:
            step_id: 步骤 ID
            status: 新状态
            **kwargs: 其他更新字段
            
        Returns:
            是否成功
        """
        if not self.state_file.exists():
            return False
        
        try:
            with open(self.state_file) as f:
                state = json.load(f)
            
            steps = state.get("steps", {})
            
            # 更新步骤
            if isinstance(steps, dict):
                if step_id in steps:
                    steps[step_id]["status"] = status
                    steps[step_id].update(kwargs)
            elif isinstance(steps, list):
                for step in steps:
                    if step.get("step_id") == step_id:
                        step["status"] = status
                        step.update(kwargs)
                        break
            
            # 更新时间戳
            state["updated_at"] = self._now()
            
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
            
            # 清除缓存
            self._state = None
            
            return True
        except Exception:
            return False
    
    def append_ledger(self, entry: Dict[str, Any]) -> bool:
        """
        追加 ledger 条目
        
        Args:
            entry: ledger 条目
            
        Returns:
            是否成功
        """
        try:
            entry["timestamp"] = self._now()
            with open(self.ledger_file, 'a') as f:
                f.write(json.dumps(entry) + "\n")
            return True
        except Exception:
            return False
    
    @staticmethod
    def _now() -> str:
        """当前时间 ISO 格式"""
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"


def create_dossier_factory(tasks_base_dir: str = "artifacts/tasks"):
    """
    创建 dossier 工厂函数
    
    Args:
        tasks_base_dir: 任务基础目录
        
    Returns:
        工厂函数
    """
    def factory(task_id: str) -> TaskDossier:
        return TaskDossier(task_id, tasks_base_dir)
    
    return factory
