"""
Task Dossier Model - 任务总档案

每个长任务的独立目录结构管理器。
负责初始化、验证和管理任务的生命周期文件。
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict
import hashlib
import uuid


@dataclass
class TaskContract:
    """任务契约"""
    objective: str
    repository: str
    branch: str = "main"
    acceptance_criteria: List[str] = None
    
    def __post_init__(self):
        if self.acceptance_criteria is None:
            self.acceptance_criteria = []


@dataclass
class StepState:
    """步骤状态"""
    step_id: str
    status: str = "pending"  # pending, running, success, failed_retryable, failed_blocked, failed_terminal
    attempts: int = 0
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None


@dataclass
class TaskState:
    """任务状态 - 机器真相"""
    task_id: str
    version: str = "v1.0"
    status: str = "created"  # created, running, blocked, completed, failed
    created_at: str = None
    updated_at: str = None
    contract: Dict[str, Any] = None
    steps: List[Dict[str, Any]] = None
    current_step: Optional[str] = None
    blocked_on: Optional[str] = None
    artifacts_dir: str = None
    ledger_path: str = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat() + "Z"
        if self.updated_at is None:
            self.updated_at = self.created_at
        if self.steps is None:
            self.steps = []
        if self.metadata is None:
            self.metadata = {}


class TaskDossier:
    """任务档案管理器"""
    
    def __init__(self, base_dir: str, task_id: Optional[str] = None):
        self.base_dir = Path(base_dir)
        
        if task_id is None:
            # 生成新任务 ID
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            short_uuid = uuid.uuid4().hex[:8]
            self.task_id = f"task_{timestamp}_{short_uuid}"
        else:
            self.task_id = task_id
        
        self.task_dir = self.base_dir / "artifacts" / "tasks" / self.task_id
        self.state_file = self.task_dir / "task_state.json"
        self.task_md = self.task_dir / "TASK.md"
        self.plan_md = self.task_dir / "PLAN.md"
        self.plan_graph = self.task_dir / "plan_graph.json"
        self.steps_dir = self.task_dir / "steps"
        self.evidence_dir = self.task_dir / "evidence"
        self.handoff_dir = self.task_dir / "handoff"
        self.final_dir = self.task_dir / "final"
        self.ledger_file = self.task_dir / "ledger.jsonl"
    
    def initialize(self, contract: TaskContract, plan: List[Dict[str, Any]]) -> TaskState:
        """初始化任务档案"""
        
        # 创建目录结构
        self.task_dir.mkdir(parents=True, exist_ok=True)
        self.steps_dir.mkdir(exist_ok=True)
        self.evidence_dir.mkdir(exist_ok=True)
        self.handoff_dir.mkdir(exist_ok=True)
        self.final_dir.mkdir(exist_ok=True)
        
        # 创建步骤目录
        for step in plan:
            step_id = step.get("step_id", step.get("id"))
            step_dir = self.steps_dir / step_id
            step_dir.mkdir(exist_ok=True)
            evidence_step_dir = self.evidence_dir / step_id
            evidence_step_dir.mkdir(exist_ok=True)
        
        # 创建任务状态
        now = datetime.utcnow().isoformat() + "Z"
        steps_state = [
            {
                "step_id": step.get("step_id", step.get("id")),
                "status": "pending",
                "attempts": 0,
                "started_at": None,
                "completed_at": None,
                "error": None
            }
            for step in plan
        ]
        
        task_state = TaskState(
            task_id=self.task_id,
            version="v1.0",
            status="created",
            created_at=now,
            updated_at=now,
            contract=asdict(contract),
            steps=steps_state,
            current_step=plan[0].get("step_id", plan[0].get("id")) if plan else None,
            blocked_on=None,
            artifacts_dir=str(self.task_dir),
            ledger_path=str(self.ledger_file)
        )
        
        # 保存状态
        self._save_state(task_state)
        
        # 创建 TASK.md
        self._create_task_md(contract, plan)
        
        # 创建 ledger
        self._append_ledger("task_created", {"contract": asdict(contract)})
        
        # 创建计划文件
        self._save_plan(plan)
        
        return task_state
    
    def _save_state(self, state: TaskState) -> None:
        """保存任务状态"""
        state.updated_at = datetime.utcnow().isoformat() + "Z"
        with open(self.state_file, 'w') as f:
            json.dump(asdict(state), f, indent=2)
    
    def _create_task_md(self, contract: TaskContract, plan: List[Dict[str, Any]]) -> None:
        """创建人类可读的任务契约文档"""
        content = f"""# Task: {self.task_id}

## Objective
{contract.objective}

## Repository
- Path: `{contract.repository}`
- Branch: `{contract.branch}`

## Acceptance Criteria
"""
        for i, criterion in enumerate(contract.acceptance_criteria, 1):
            content += f"{i}. {criterion}\n"
        
        content += "\n## Steps\n"
        for step in plan:
            step_id = step.get("step_id", step.get("id"))
            title = step.get("title", step.get("goal", "Untitled"))
            content += f"- [{step_id}] {title}\n"
        
        content += f"""
## Status
- Created: {datetime.utcnow().isoformat()}Z
- Status: created

## Files
- State: `task_state.json`
- Ledger: `ledger.jsonl`
- Steps: `steps/`
- Evidence: `evidence/`
- Handoff: `handoff/`
"""
        with open(self.task_md, 'w') as f:
            f.write(content)
    
    def _save_plan(self, plan: List[Dict[str, Any]]) -> None:
        """保存执行计划"""
        # PLAN.md
        content = "# Execution Plan\n\n"
        for step in plan:
            step_id = step.get("step_id", step.get("id"))
            content += f"## {step_id}: {step.get('title', step.get('goal', 'Untitled'))}\n\n"
            content += f"**Goal**: {step.get('goal', 'N/A')}\n\n"
            if step.get('description'):
                content += f"{step.get('description')}\n\n"
            if step.get('depends_on'):
                content += f"**Depends on**: {', '.join(step['depends_on'])}\n\n"
        
        with open(self.plan_md, 'w') as f:
            f.write(content)
        
        # plan_graph.json
        graph = {
            "task_id": self.task_id,
            "steps": plan,
            "dependencies": self._build_dependency_graph(plan)
        }
        with open(self.plan_graph, 'w') as f:
            json.dump(graph, f, indent=2)
    
    def _build_dependency_graph(self, plan: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """构建依赖图"""
        graph = {}
        for step in plan:
            step_id = step.get("step_id", step.get("id"))
            deps = step.get("depends_on", [])
            graph[step_id] = deps
        return graph
    
    def _append_ledger(self, action: str, data: Dict[str, Any]) -> None:
        """追加账本事件"""
        event = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "action": action,
            "task_id": self.task_id,
            "data": data
        }
        with open(self.ledger_file, 'a') as f:
            f.write(json.dumps(event) + "\n")
    
    def load_state(self) -> Optional[TaskState]:
        """加载任务状态"""
        if not self.state_file.exists():
            return None
        
        with open(self.state_file) as f:
            data = json.load(f)
        
        return TaskState(**data)
    
    def update_step(self, step_id: str, status: str, error: Optional[str] = None) -> TaskState:
        """更新步骤状态"""
        state = self.load_state()
        if state is None:
            raise ValueError(f"Task state not found: {self.task_id}")
        
        now = datetime.utcnow().isoformat() + "Z"
        
        for step in state.steps:
            if step["step_id"] == step_id:
                old_status = step["status"]
                step["status"] = status
                
                if status == "running" and step["started_at"] is None:
                    step["started_at"] = now
                
                if status in ("success", "failed_blocked", "failed_terminal"):
                    step["completed_at"] = now
                
                if error:
                    step["error"] = error
                
                if status != old_status:
                    step["attempts"] += 1
                
                break
        
        # 更新当前步骤
        if status == "success":
            state.current_step = self._get_next_step(state, step_id)
            if state.current_step is None:
                state.status = "completed"
        
        state.updated_at = now
        
        # 追加账本
        self._append_ledger("step_updated", {
            "step_id": step_id,
            "status": status,
            "error": error
        })
        
        self._save_state(state)
        return state
    
    def _get_next_step(self, state: TaskState, current_step_id: str) -> Optional[str]:
        """获取下一个步骤"""
        current_found = False
        for step in state.steps:
            if current_found:
                if step["status"] == "pending":
                    return step["step_id"]
            if step["step_id"] == current_step_id:
                current_found = True
        return None
    
    def get_step_packet(self, step_id: str) -> Optional[Dict[str, Any]]:
        """获取步骤执行包"""
        packet_file = self.steps_dir / step_id / "step_packet.json"
        if packet_file.exists():
            with open(packet_file) as f:
                return json.load(f)
        return None
    
    def save_step_packet(self, step_id: str, packet: Dict[str, Any]) -> None:
        """保存步骤执行包"""
        packet_file = self.steps_dir / step_id / "step_packet.json"
        with open(packet_file, 'w') as f:
            json.dump(packet, f, indent=2)
    
    def save_step_result(self, step_id: str, result: Dict[str, Any]) -> None:
        """保存步骤结果"""
        result_file = self.steps_dir / step_id / "result.json"
        with open(result_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        # 更新任务状态
        self.update_step(step_id, result["status"], result.get("error", {}).get("message") if result.get("error") else None)
    
    def save_handoff(self, step_id: str, content: str) -> None:
        """保存交接文档"""
        handoff_file = self.handoff_dir / f"{step_id}.md"
        with open(handoff_file, 'w') as f:
            f.write(content)
    
    def get_ledger_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取账本事件"""
        if not self.ledger_file.exists():
            return []
        
        events = []
        with open(self.ledger_file) as f:
            for line in f:
                if line.strip():
                    events.append(json.loads(line))
        
        return events[-limit:]
    
    @staticmethod
    def generate_checksum(data: Dict[str, Any]) -> str:
        """生成校验和"""
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
