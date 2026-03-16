"""
Resume Engine - 恢复推进引擎

负责在中断后从持久化状态恢复执行。
不依赖模型记忆，只依赖机器可读状态。
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ResumeContext:
    """恢复上下文"""
    task_id: str
    task_state: Dict[str, Any]
    current_step_id: Optional[str]
    current_step_status: str
    last_ledger_events: List[Dict[str, Any]]
    previous_evidence: Dict[str, Any]
    lease_valid: bool
    needs_recovery: bool
    recovery_action: str  # continue, retry, skip, abort


class ResumeEngine:
    """恢复推进引擎"""
    
    def __init__(self, task_dossier):
        self.dossier = task_dossier
    
    def analyze(self) -> ResumeContext:
        """分析当前任务状态，决定恢复策略"""
        
        # 1. 加载任务状态
        task_state = self.dossier.load_state()
        if task_state is None:
            raise ValueError(f"Task state not found: {self.dossier.task_id}")
        
        state_dict = self._state_to_dict(task_state)
        
        # 2. 读取最近的账本事件
        ledger_events = self.dossier.get_ledger_events(limit=20)
        
        # 3. 找到当前步骤
        current_step_id, current_step_status = self._find_current_step(state_dict)
        
        # 4. 检查租约有效性
        lease_valid = self._check_lease_validity(current_step_id)
        
        # 5. 收集前序证据
        previous_evidence = self._collect_previous_evidence(current_step_id)
        
        # 6. 决定恢复动作
        recovery_action = self._determine_recovery_action(
            state_dict, 
            current_step_id, 
            current_step_status,
            lease_valid
        )
        
        needs_recovery = recovery_action in ("continue", "retry")
        
        return ResumeContext(
            task_id=self.dossier.task_id,
            task_state=state_dict,
            current_step_id=current_step_id,
            current_step_status=current_step_status,
            last_ledger_events=ledger_events,
            previous_evidence=previous_evidence,
            lease_valid=lease_valid,
            needs_recovery=needs_recovery,
            recovery_action=recovery_action
        )
    
    def _state_to_dict(self, state) -> Dict[str, Any]:
        """转换状态为字典"""
        from dataclasses import asdict
        return asdict(state)
    
    def _find_current_step(self, state: Dict[str, Any]) -> Tuple[Optional[str], str]:
        """找到当前步骤及其状态"""
        # 首先检查 current_step 字段
        if state.get("current_step"):
            step_id = state["current_step"]
            for step in state.get("steps", []):
                if step["step_id"] == step_id:
                    return step_id, step["status"]
        
        # 如果没有 current_step，找第一个未完成的步骤
        for step in state.get("steps", []):
            if step["status"] not in ("success", "failed_terminal"):
                return step["step_id"], step["status"]
        
        # 所有步骤都完成了
        return None, "completed"
    
    def _check_lease_validity(self, step_id: Optional[str]) -> bool:
        """检查步骤租约是否有效"""
        if step_id is None:
            return False
        
        lease_file = self.dossier.steps_dir / step_id / "lease.json"
        if not lease_file.exists():
            return True  # 没有租约文件，允许执行
        
        with open(lease_file) as f:
            lease = json.load(f)
        
        # 检查租约是否过期
        expires_at = datetime.fromisoformat(lease["expires_at"].replace("Z", "+00:00"))
        now = datetime.utcnow()
        
        if now > expires_at.replace(tzinfo=None):
            return False  # 租约已过期
        
        # 检查心跳
        heartbeat = lease.get("heartbeat", {})
        last_heartbeat = heartbeat.get("last_heartbeat_at")
        if last_heartbeat:
            last_heartbeat_time = datetime.fromisoformat(last_heartbeat.replace("Z", "+00:00"))
            interval_ms = heartbeat.get("heartbeat_interval_ms", 30000)
            max_missed = heartbeat.get("max_missed", 3)
            
            expected_heartbeats = (now - last_heartbeat_time.replace(tzinfo=None)).total_seconds() * 1000 / interval_ms
            if expected_heartbeats > max_missed:
                return False
        
        return True
    
    def _collect_previous_evidence(self, current_step_id: Optional[str]) -> Dict[str, Any]:
        """收集前序步骤的证据"""
        evidence = {}
        
        if current_step_id is None:
            return evidence
        
        # 获取任务状态
        task_state = self.dossier.load_state()
        if task_state is None:
            return evidence
        
        # 找到当前步骤之前的所有成功步骤
        current_found = False
        for step in task_state.steps:
            if step["step_id"] == current_step_id:
                current_found = True
                break
            
            if step["status"] == "success":
                step_evidence = self._load_step_evidence(step["step_id"])
                evidence[step["step_id"]] = step_evidence
        
        return evidence
    
    def _load_step_evidence(self, step_id: str) -> Dict[str, Any]:
        """加载步骤证据"""
        evidence_dir = self.dossier.evidence_dir / step_id
        evidence = {}
        
        if evidence_dir.exists():
            for file_path in evidence_dir.iterdir():
                if file_path.is_file():
                    try:
                        with open(file_path) as f:
                            if file_path.suffix == ".json":
                                evidence[file_path.name] = json.load(f)
                            else:
                                evidence[file_path.name] = f.read()
                    except Exception:
                        evidence[file_path.name] = f"<binary or unreadable: {file_path.name}>"
        
        # 加载 handoff
        handoff_file = self.dossier.handoff_dir / f"{step_id}.md"
        if handoff_file.exists():
            with open(handoff_file) as f:
                evidence["handoff.md"] = f.read()
        
        # 加载 result
        result_file = self.dossier.steps_dir / step_id / "result.json"
        if result_file.exists():
            with open(result_file) as f:
                evidence["result.json"] = json.load(f)
        
        return evidence
    
    def _determine_recovery_action(
        self, 
        state: Dict[str, Any], 
        step_id: Optional[str], 
        step_status: str,
        lease_valid: bool
    ) -> str:
        """决定恢复动作"""
        
        # 任务已完成
        if state["status"] == "completed":
            return "abort"  # 任务已完成，无需恢复
        
        # 任务失败
        if state["status"] == "failed":
            return "abort"  # 任务失败，需要人工干预
        
        # 没有当前步骤
        if step_id is None:
            return "abort"  # 无法确定恢复点
        
        # 步骤状态判断
        if step_status == "pending":
            return "continue"  # 步骤未开始，直接执行
        
        if step_status == "running":
            if lease_valid:
                # 租约有效，但有可能是自己之前的租约
                # 检查是否需要继续执行
                return "continue"  # 继续执行当前步骤
            else:
                return "retry"  # 租约过期，可以接管重试
        
        if step_status == "failed_retryable":
            return "retry"  # 可重试的失败
        
        if step_status == "failed_blocked":
            return "abort"  # 被阻塞，需要人工干预
        
        if step_status == "failed_terminal":
            return "abort"  # 终端失败，任务失败
        
        if step_status == "success":
            return "continue"  # 步骤成功，继续下一步
        
        return "abort"  # 未知状态，保守处理
    
    def rebuild_context(self, context: ResumeContext) -> Dict[str, Any]:
        """重建执行上下文，供执行器使用"""
        
        if context.current_step_id is None:
            return {}
        
        # 加载步骤包
        step_packet = self.dossier.get_step_packet(context.current_step_id)
        if step_packet is None:
            raise ValueError(f"Step packet not found: {context.current_step_id}")
        
        # 构建执行上下文
        execution_context = {
            "task_id": context.task_id,
            "step_id": context.current_step_id,
            "step_packet": step_packet,
            "task_state": context.task_state,
            "previous_evidence": context.previous_evidence,
            "recovery_action": context.recovery_action,
            "artifacts_dir": str(self.dossier.task_dir)
        }
        
        return execution_context
    
    def acquire_lease(self, step_id: str, owner: str, ttl_seconds: int = 300) -> Dict[str, Any]:
        """获取步骤租约"""
        now = datetime.utcnow()
        
        lease = {
            "step_id": step_id,
            "owner": owner,
            "acquired_at": now.isoformat() + "Z",
            "expires_at": (now.replace(microsecond=0) + __import__('datetime').timedelta(seconds=ttl_seconds)).isoformat() + "Z",
            "ttl_seconds": ttl_seconds,
            "status": "active",
            "heartbeat": {
                "last_heartbeat_at": now.isoformat() + "Z",
                "heartbeat_interval_ms": 30000,
                "missed_count": 0,
                "max_missed": 3
            },
            "reclaim_count": 0,
            "max_reclaims": 3
        }
        
        # 保存租约
        lease_file = self.dossier.steps_dir / step_id / "lease.json"
        with open(lease_file, 'w') as f:
            json.dump(lease, f, indent=2)
        
        return lease
    
    def release_lease(self, step_id: str, owner: str, reason: str = "completed") -> bool:
        """释放步骤租约"""
        lease_file = self.dossier.steps_dir / step_id / "lease.json"
        
        if not lease_file.exists():
            return True
        
        with open(lease_file) as f:
            lease = json.load(f)
        
        # 验证所有权
        if lease.get("owner") != owner:
            return False
        
        lease["status"] = "released"
        lease["released_at"] = datetime.utcnow().isoformat() + "Z"
        lease["release_reason"] = reason
        
        with open(lease_file, 'w') as f:
            json.dump(lease, f, indent=2)
        
        return True
    
    def heartbeat(self, step_id: str, owner: str) -> bool:
        """发送心跳"""
        lease_file = self.dossier.steps_dir / step_id / "lease.json"
        
        if not lease_file.exists():
            return False
        
        with open(lease_file) as f:
            lease = json.load(f)
        
        # 验证所有权
        if lease.get("owner") != owner:
            return False
        
        # 更新心跳
        lease["heartbeat"]["last_heartbeat_at"] = datetime.utcnow().isoformat() + "Z"
        lease["heartbeat"]["missed_count"] = 0
        
        with open(lease_file, 'w') as f:
            json.dump(lease, f, indent=2)
        
        return True
