"""
Worker Slot Registry - Worker 槽位注册与占用管理

管理可用 worker 槽位，支持分配、释放、心跳和回收。
"""

import json
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict, field
import uuid


@dataclass
class SlotHolder:
    """槽位持有者"""
    task_id: str
    step_id: str
    worker_id: str
    session_key: Optional[str] = None


@dataclass
class WorkerSlot:
    """Worker 槽位"""
    slot_id: str
    status: str  # free, reserved, running, stale
    holder: Optional[SlotHolder] = None
    reserved_at: Optional[str] = None
    started_at: Optional[str] = None
    last_heartbeat_at: Optional[str] = None
    timeout_seconds: int = 300
    heartbeat_interval_seconds: int = 30
    max_missed_heartbeats: int = 3
    created_at: str = ""
    updated_at: str = ""
    allocation_history: List[Dict] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        if self.holder is None:
            data['holder'] = None
        return data


class WorkerSlotRegistry:
    """Worker 槽位注册器"""
    
    def __init__(self, total_slots: int = 4, storage_path: Optional[Path] = None):
        self.total_slots = total_slots
        self.storage_path = storage_path
        self.slots: Dict[str, WorkerSlot] = {}
        self._lock = threading.Lock()
        
        # 初始化槽位
        for i in range(total_slots):
            slot_id = f"slot_{i:03d}"
            self.slots[slot_id] = WorkerSlot(
                slot_id=slot_id,
                status="free",
                created_at=datetime.utcnow().isoformat() + "Z",
                updated_at=datetime.utcnow().isoformat() + "Z"
            )
    
    def get_available_slots(self) -> List[str]:
        """获取可用槽位列表"""
        with self._lock:
            return [s.slot_id for s in self.slots.values() if s.status == "free"]
    
    def get_slot_status(self, slot_id: str) -> Optional[Dict]:
        """获取槽位状态"""
        slot = self.slots.get(slot_id)
        return slot.to_dict() if slot else None
    
    def reserve_slot(
        self,
        task_id: str,
        step_id: str,
        worker_id: str,
        session_key: Optional[str] = None
    ) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """
        预留槽位
        
        Returns:
            (success, slot_id, slot_info)
        """
        with self._lock:
            # 找一个空闲槽位
            free_slot = None
            for slot in self.slots.values():
                if slot.status == "free":
                    free_slot = slot
                    break
            
            if free_slot is None:
                return False, None, {"reason": "no_free_slots"}
            
            # 预留
            now = datetime.utcnow()
            free_slot.status = "reserved"
            free_slot.holder = SlotHolder(
                task_id=task_id,
                step_id=step_id,
                worker_id=worker_id,
                session_key=session_key
            )
            free_slot.reserved_at = now.isoformat() + "Z"
            free_slot.updated_at = now.isoformat() + "Z"
            
            self._persist_slot(free_slot)
            
            return True, free_slot.slot_id, free_slot.to_dict()
    
    def start_slot(self, slot_id: str, worker_id: str) -> Tuple[bool, str]:
        """启动槽位执行"""
        with self._lock:
            slot = self.slots.get(slot_id)
            
            if slot is None:
                return False, "slot_not_found"
            
            if slot.status not in ("reserved", "running"):
                return False, f"invalid_status: {slot.status}"
            
            if slot.holder and slot.holder.worker_id != worker_id:
                return False, "not_owner"
            
            now = datetime.utcnow()
            slot.status = "running"
            slot.started_at = now.isoformat() + "Z"
            slot.last_heartbeat_at = now.isoformat() + "Z"
            slot.updated_at = now.isoformat() + "Z"
            
            self._persist_slot(slot)
            
            return True, "started"
    
    def heartbeat(self, slot_id: str, worker_id: str) -> Tuple[bool, str]:
        """发送心跳"""
        with self._lock:
            slot = self.slots.get(slot_id)
            
            if slot is None:
                return False, "slot_not_found"
            
            if slot.holder and slot.holder.worker_id != worker_id:
                return False, "not_owner"
            
            now = datetime.utcnow()
            slot.last_heartbeat_at = now.isoformat() + "Z"
            slot.updated_at = now.isoformat() + "Z"
            
            # 如果是 stale，恢复为 running
            if slot.status == "stale":
                slot.status = "running"
            
            self._persist_slot(slot)
            
            return True, "heartbeat_recorded"
    
    def release_slot(self, slot_id: str, worker_id: str, reason: str = "completed") -> Tuple[bool, str]:
        """释放槽位"""
        with self._lock:
            slot = self.slots.get(slot_id)
            
            if slot is None:
                return False, "slot_not_found"
            
            if slot.holder and slot.holder.worker_id != worker_id:
                return False, "not_owner"
            
            # 记录历史
            if slot.holder:
                slot.allocation_history.append({
                    "holder": asdict(slot.holder),
                    "reserved_at": slot.reserved_at,
                    "released_at": datetime.utcnow().isoformat() + "Z",
                    "reason": reason
                })
            
            # 重置
            now = datetime.utcnow()
            slot.status = "free"
            slot.holder = None
            slot.reserved_at = None
            slot.started_at = None
            slot.last_heartbeat_at = None
            slot.updated_at = now.isoformat() + "Z"
            
            self._persist_slot(slot)
            
            return True, "released"
    
    def check_stale_slots(self) -> List[str]:
        """检查过期槽位"""
        stale_slots = []
        now = datetime.utcnow()
        
        with self._lock:
            for slot in self.slots.values():
                if slot.status == "running" and slot.last_heartbeat_at:
                    last_heartbeat = datetime.fromisoformat(
                        slot.last_heartbeat_at.replace("Z", "+00:00")
                    ).replace(tzinfo=None)
                    
                    elapsed = (now - last_heartbeat).total_seconds()
                    expected_interval = slot.heartbeat_interval_seconds * (slot.max_missed_heartbeats + 1)
                    
                    if elapsed > expected_interval:
                        slot.status = "stale"
                        slot.updated_at = now.isoformat() + "Z"
                        stale_slots.append(slot.slot_id)
                        self._persist_slot(slot)
        
        return stale_slots
    
    def can_reclaim_slot(self, slot_id: str, step_status: str) -> Tuple[bool, str]:
        """
        检查是否可以回收槽位
        
        重要：如果 step_status == "success"，禁止回收
        这是 v2 baseline 保护规则
        """
        slot = self.slots.get(slot_id)
        
        if slot is None:
            return False, "slot_not_found"
        
        # v2 baseline: 成功步骤不得重跑
        if step_status == "success":
            return False, "step_already_success_v2_baseline_protection"
        
        if slot.status != "stale":
            return False, "slot_not_stale"
        
        return True, "can_reclaim"
    
    def reclaim_slot(
        self,
        slot_id: str,
        new_worker_id: str,
        step_status: str
    ) -> Tuple[bool, str, Optional[Dict]]:
        """
        回收过期槽位
        
        必须检查 step_status，success 步骤禁止回收
        """
        with self._lock:
            # 先检查是否可以回收
            can_reclaim, reason = self.can_reclaim_slot(slot_id, step_status)
            
            if not can_reclaim:
                return False, reason, None
            
            slot = self.slots[slot_id]
            
            # 记录历史
            if slot.holder:
                slot.allocation_history.append({
                    "holder": asdict(slot.holder),
                    "reserved_at": slot.reserved_at,
                    "released_at": datetime.utcnow().isoformat() + "Z",
                    "reason": "reclaimed"
                })
            
            # 重置
            now = datetime.utcnow()
            slot.status = "free"
            slot.holder = None
            slot.reserved_at = None
            slot.started_at = None
            slot.last_heartbeat_at = None
            slot.updated_at = now.isoformat() + "Z"
            
            self._persist_slot(slot)
            
            return True, "reclaimed", slot.to_dict()
    
    def get_slot_for_step(self, task_id: str, step_id: str) -> Optional[str]:
        """获取执行指定步骤的槽位"""
        with self._lock:
            for slot in self.slots.values():
                if slot.holder:
                    if slot.holder.task_id == task_id and slot.holder.step_id == step_id:
                        return slot.slot_id
            return None
    
    def get_all_slots(self) -> List[Dict]:
        """获取所有槽位状态"""
        with self._lock:
            return [s.to_dict() for s in self.slots.values()]
    
    def _persist_slot(self, slot: WorkerSlot) -> None:
        """持久化槽位状态"""
        if self.storage_path:
            slot_file = self.storage_path / f"{slot.slot_id}.json"
            slot_file.parent.mkdir(parents=True, exist_ok=True)
            with open(slot_file, 'w') as f:
                json.dump(slot.to_dict(), f, indent=2)


def create_slot_registry(total_slots: int = 4, storage_path: Optional[Path] = None) -> WorkerSlotRegistry:
    """创建槽位注册器"""
    return WorkerSlotRegistry(total_slots, storage_path)
