"""
Slot Registry - 最小 Stub 实现

为 autonomous_runner 提供 slot 管理接口。
当前实现：单 slot，无实际调度控制。
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import uuid


@dataclass
class SlotInfo:
    """Slot 信息"""
    slot_id: str
    worker_id: Optional[str] = None
    task_id: Optional[str] = None
    status: str = "available"  # available, reserved, active, stale
    reserved_at: Optional[str] = None
    last_heartbeat: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "slot_id": self.slot_id,
            "worker_id": self.worker_id,
            "task_id": self.task_id,
            "status": self.status,
            "reserved_at": self.reserved_at,
            "last_heartbeat": self.last_heartbeat,
        }


class SlotRegistry:
    """
    Slot Registry - 最小实现
    
    当前配置：单 slot，无并发控制。
    未来可扩展为多 slot + 公平调度。
    """
    
    def __init__(self, max_slots: int = 1):
        self.max_slots = max_slots
        self.slots: Dict[str, SlotInfo] = {}
        
        # 初始化 slots
        for i in range(max_slots):
            slot_id = f"slot_{i:03d}"
            self.slots[slot_id] = SlotInfo(slot_id=slot_id)
    
    def get_available_slots(self) -> List[str]:
        """获取可用 slot 列表"""
        return [
            slot_id for slot_id, slot in self.slots.items()
            if slot.status == "available"
        ]
    
    def reserve_slot(
        self, 
        task_id: str, 
        worker_id: str,
        step_id: str = None,
        session_key: str = None
    ) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """
        预留 slot
        
        Returns:
            (success, slot_id, slot_info)
        """
        for slot_id, slot in self.slots.items():
            if slot.status == "available":
                slot.status = "reserved"
                slot.worker_id = worker_id
                slot.task_id = task_id
                slot.reserved_at = datetime.utcnow().isoformat() + "Z"
                return True, slot_id, slot.to_dict()
        
        return False, None, None
    
    def start_slot(self, slot_id: str, worker_id: str) -> bool:
        """启动 slot"""
        if slot_id not in self.slots:
            return False
        
        slot = self.slots[slot_id]
        if slot.worker_id != worker_id:
            return False
        
        slot.status = "active"
        slot.last_heartbeat = datetime.utcnow().isoformat() + "Z"
        return True
    
    def heartbeat(self, slot_id: str, worker_id: str) -> bool:
        """更新心跳"""
        if slot_id not in self.slots:
            return False
        
        slot = self.slots[slot_id]
        if slot.worker_id != worker_id:
            return False
        
        slot.last_heartbeat = datetime.utcnow().isoformat() + "Z"
        return True
    
    def release_slot(
        self, 
        slot_id: str, 
        worker_id: str, 
        reason: str = "completed"
    ) -> Tuple[bool, str]:
        """
        释放 slot
        
        Returns:
            (success, reason)
        """
        if slot_id not in self.slots:
            return False, "slot_not_found"
        
        slot = self.slots[slot_id]
        if slot.worker_id != worker_id:
            return False, "worker_mismatch"
        
        # 重置 slot
        self.slots[slot_id] = SlotInfo(slot_id=slot_id)
        return True, reason
    
    def check_stale_slots(self, stale_threshold_seconds: float = 300.0) -> List[str]:
        """检查过期 slot"""
        stale_slots = []
        now = datetime.utcnow()
        
        for slot_id, slot in self.slots.items():
            if slot.status == "active" and slot.last_heartbeat:
                last = datetime.fromisoformat(slot.last_heartbeat.rstrip("Z"))
                if (now - last).total_seconds() > stale_threshold_seconds:
                    slot.status = "stale"
                    stale_slots.append(slot_id)
        
        return stale_slots
    
    def get_slot_status(self, slot_id: str) -> Optional[Dict]:
        """获取 slot 状态"""
        if slot_id not in self.slots:
            return None
        return self.slots[slot_id].to_dict()
