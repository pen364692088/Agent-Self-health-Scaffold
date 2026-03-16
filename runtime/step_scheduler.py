"""
Step Scheduler - 步骤调度器

在步骤执行前进行调度准入控制。
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import uuid


@dataclass
class SchedulerDecision:
    """调度决策"""
    decision: str  # admit, reject, queue
    reason: str
    task_id: str
    step_id: str
    worker_id: str
    allocated_slot: Optional[Dict] = None
    allocated_lease: Optional[Dict] = None
    queue_position: Optional[int] = None
    estimated_wait_seconds: Optional[int] = None
    conflict_info: Optional[Dict] = None
    timestamp: str = ""
    scheduler_id: str = ""
    
    def to_dict(self) -> Dict:
        return {k: v for k, v in asdict(self).items() if v is not None}


class StepScheduler:
    """步骤调度器"""
    
    def __init__(
        self,
        slot_registry,
        lease_manager=None,
        task_dossier=None,
        scheduler_id: Optional[str] = None
    ):
        self.slot_registry = slot_registry
        self.lease_manager = lease_manager
        self.task_dossier = task_dossier
        self.scheduler_id = scheduler_id or f"scheduler_{uuid.uuid4().hex[:8]}"
        self.decision_history: List[SchedulerDecision] = []
    
    def request_execution(
        self,
        task_id: str,
        step_id: str,
        worker_id: str,
        session_key: Optional[str] = None
    ) -> SchedulerDecision:
        """
        请求执行步骤
        
        执行调度准入检查:
        1. 检查槽位可用性
        2. 检查租约可用性
        3. 检查步骤状态
        4. 返回决策
        """
        now = datetime.utcnow()
        
        # 1. 检查步骤状态（是否已成功）
        if self.task_dossier:
            state = self.task_dossier.load_state()
            if state:
                for step in state.steps:
                    if step["step_id"] == step_id:
                        if step["status"] == "success":
                            # v2 baseline: 成功步骤不得重跑
                            decision = SchedulerDecision(
                                decision="reject",
                                reason="step_already_success",
                                task_id=task_id,
                                step_id=step_id,
                                worker_id=worker_id,
                                conflict_info={
                                    "conflict_type": "step_contention",
                                    "resolution": "rejected_v2_baseline"
                                },
                                timestamp=now.isoformat() + "Z",
                                scheduler_id=self.scheduler_id
                            )
                            self.decision_history.append(decision)
                            return decision
        
        # 2. 检查槽位可用性
        available_slots = self.slot_registry.get_available_slots()
        
        if not available_slots:
            # 没有可用槽位
            decision = SchedulerDecision(
                decision="reject",
                reason="no_available_slots",
                task_id=task_id,
                step_id=step_id,
                worker_id=worker_id,
                timestamp=now.isoformat() + "Z",
                scheduler_id=self.scheduler_id
            )
            self.decision_history.append(decision)
            return decision
        
        # 3. 预留槽位
        success, slot_id, slot_info = self.slot_registry.reserve_slot(
            task_id=task_id,
            step_id=step_id,
            worker_id=worker_id,
            session_key=session_key
        )
        
        if not success:
            decision = SchedulerDecision(
                decision="reject",
                reason="slot_reservation_failed",
                task_id=task_id,
                step_id=step_id,
                worker_id=worker_id,
                timestamp=now.isoformat() + "Z",
                scheduler_id=self.scheduler_id
            )
            self.decision_history.append(decision)
            return decision
        
        # 4. 获取租约（如果有 lease_manager）
        lease_info = None
        if self.lease_manager:
            lease_success, lease_result = self.lease_manager.acquire(
                step_id=step_id,
                owner=worker_id
            )
            
            if not lease_success:
                # 租约获取失败，释放槽位
                self.slot_registry.release_slot(slot_id, worker_id, "lease_failed")
                
                decision = SchedulerDecision(
                    decision="reject",
                    reason="lease_acquisition_failed",
                    task_id=task_id,
                    step_id=step_id,
                    worker_id=worker_id,
                    conflict_info={
                        "conflict_type": "lease_contention",
                        "resolution": "rejected"
                    },
                    timestamp=now.isoformat() + "Z",
                    scheduler_id=self.scheduler_id
                )
                self.decision_history.append(decision)
                return decision
            
            lease_info = lease_result
        
        # 5. 准予执行
        decision = SchedulerDecision(
            decision="admit",
            reason="slot_and_lease_acquired",
            task_id=task_id,
            step_id=step_id,
            worker_id=worker_id,
            allocated_slot={
                "slot_id": slot_id,
                "allocated_at": now.isoformat() + "Z"
            },
            allocated_lease=lease_info,
            timestamp=now.isoformat() + "Z",
            scheduler_id=self.scheduler_id
        )
        
        self.decision_history.append(decision)
        return decision
    
    def start_execution(
        self,
        slot_id: str,
        worker_id: str
    ) -> Tuple[bool, str]:
        """启动执行"""
        return self.slot_registry.start_slot(slot_id, worker_id)
    
    def send_heartbeat(
        self,
        slot_id: str,
        worker_id: str
    ) -> Tuple[bool, str]:
        """发送心跳"""
        return self.slot_registry.heartbeat(slot_id, worker_id)
    
    def complete_execution(
        self,
        task_id: str,
        step_id: str,
        worker_id: str,
        slot_id: str
    ) -> Tuple[bool, str]:
        """完成执行，释放资源"""
        # 释放槽位
        success, reason = self.slot_registry.release_slot(slot_id, worker_id, "completed")
        
        # 释放租约（如果有）
        if self.lease_manager:
            self.lease_manager.release(step_id, worker_id, "completed")
        
        return success, reason
    
    def check_and_reclaim_stale(self) -> List[Dict]:
        """检查并回收过期资源"""
        results = []
        
        # 检查过期槽位
        stale_slots = self.slot_registry.check_stale_slots()
        
        for slot_id in stale_slots:
            # 获取槽位信息
            slot_info = self.slot_registry.get_slot_status(slot_id)
            
            if slot_info and slot_info.get("holder"):
                holder = slot_info["holder"]
                task_id = holder.get("task_id")
                step_id = holder.get("step_id")
                
                # 检查步骤状态
                step_status = self._get_step_status(task_id, step_id)
                
                # 尝试回收
                can_reclaim, reason = self.slot_registry.can_reclaim_slot(slot_id, step_status)
                
                results.append({
                    "slot_id": slot_id,
                    "task_id": task_id,
                    "step_id": step_id,
                    "step_status": step_status,
                    "can_reclaim": can_reclaim,
                    "reason": reason
                })
        
        return results
    
    def _get_step_status(self, task_id: str, step_id: str) -> str:
        """获取步骤状态"""
        if not self.task_dossier:
            return "unknown"
        
        state = self.task_dossier.load_state()
        if not state:
            return "unknown"
        
        for step in state.steps:
            if step["step_id"] == step_id:
                return step["status"]
        
        return "unknown"
    
    def get_decision_history(self, limit: int = 100) -> List[Dict]:
        """获取决策历史"""
        return [d.to_dict() for d in self.decision_history[-limit:]]


def create_scheduler(
    slot_registry,
    lease_manager=None,
    task_dossier=None
) -> StepScheduler:
    """创建调度器"""
    return StepScheduler(slot_registry, lease_manager, task_dossier)
