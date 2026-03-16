"""
Slot-Lease Bridge - 槽位与租约桥接器

确保槽位和租约的一致性，实现 v2 baseline 保护规则。
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class SlotLeaseStatus:
    """槽位-租约联合状态"""
    slot_id: str
    lease_valid: bool
    slot_valid: bool
    both_valid: bool
    can_execute: bool
    reason: str


class SlotLeaseBridge:
    """槽位-租约桥接器"""
    
    def __init__(self, slot_registry, lease_manager, task_dossier=None):
        self.slot_registry = slot_registry
        self.lease_manager = lease_manager
        self.task_dossier = task_dossier
    
    def check_execution_prerequisites(
        self,
        task_id: str,
        step_id: str
    ) -> SlotLeaseStatus:
        """
        检查执行前置条件
        
        运行中的步骤必须同时持有有效槽位和有效租约
        """
        # 获取步骤的槽位
        slot_id = self.slot_registry.get_slot_for_step(task_id, step_id)
        
        if slot_id is None:
            return SlotLeaseStatus(
                slot_id="",
                lease_valid=False,
                slot_valid=False,
                both_valid=False,
                can_execute=False,
                reason="no_slot_allocated"
            )
        
        # 检查槽位状态
        slot_info = self.slot_registry.get_slot_status(slot_id)
        slot_valid = slot_info and slot_info.get("status") in ("reserved", "running")
        
        # 检查租约状态
        lease_valid = False
        if self.lease_manager:
            is_valid, lease_info = self.lease_manager.check(step_id)
            lease_valid = is_valid
        
        both_valid = slot_valid and lease_valid
        
        reason = ""
        if both_valid:
            reason = "ready_to_execute"
        elif not slot_valid:
            reason = "slot_invalid_or_stale"
        elif not lease_valid:
            reason = "lease_expired_or_missing"
        
        return SlotLeaseStatus(
            slot_id=slot_id,
            lease_valid=lease_valid,
            slot_valid=slot_valid,
            both_valid=both_valid,
            can_execute=both_valid,
            reason=reason
        )
    
    def validate_reclaim(
        self,
        task_id: str,
        step_id: str,
        slot_id: str
    ) -> Tuple[bool, str, Dict]:
        """
        验证是否可以回收
        
        关键：检查步骤状态，成功步骤禁止回收
        这是 v2 baseline 核心保护规则
        """
        result = {
            "slot_id": slot_id,
            "step_id": step_id,
            "can_reclaim": False,
            "reason": ""
        }
        
        # 获取步骤状态
        step_status = self._get_step_status(task_id, step_id)
        result["step_status"] = step_status
        
        # v2 baseline: 成功步骤禁止回收
        if step_status == "success":
            result["reason"] = "BLOCKED: step_already_success_v2_baseline_protection"
            return False, "v2_baseline_protection", result
        
        # 检查槽位是否过期
        slot_info = self.slot_registry.get_slot_status(slot_id)
        if not slot_info:
            result["reason"] = "slot_not_found"
            return False, "slot_not_found", result
        
        if slot_info.get("status") != "stale":
            result["reason"] = f"slot_not_stale: {slot_info.get('status')}"
            return False, "slot_not_stale", result
        
        # 检查租约是否过期
        lease_expired = False
        if self.lease_manager:
            is_valid, lease_info = self.lease_manager.check(step_id)
            lease_expired = not is_valid
            result["lease_expired"] = lease_expired
        
        # 两者都过期才能回收
        if lease_expired:
            result["can_reclaim"] = True
            result["reason"] = "both_stale_can_reclaim"
            return True, "can_reclaim", result
        else:
            result["reason"] = "lease_still_valid"
            return False, "lease_still_valid", result
    
    def execute_reclaim(
        self,
        task_id: str,
        step_id: str,
        slot_id: str,
        new_worker_id: str
    ) -> Tuple[bool, str, Dict]:
        """
        执行回收
        
        必须先验证，再执行
        """
        # 先验证
        can_reclaim, reason, validation = self.validate_reclaim(task_id, step_id, slot_id)
        
        if not can_reclaim:
            return False, reason, validation
        
        # 获取步骤状态
        step_status = validation.get("step_status", "unknown")
        
        # 执行槽位回收
        success, reclaim_reason, slot_info = self.slot_registry.reclaim_slot(
            slot_id=slot_id,
            new_worker_id=new_worker_id,
            step_status=step_status
        )
        
        if not success:
            return False, reclaim_reason, validation
        
        # 执行租约回收（如果需要）
        if self.lease_manager:
            # 先撤销旧租约
            self.lease_manager.revoke(step_id, "scheduler_reclaim")
            
            # 获取新租约
            lease_success, lease_info = self.lease_manager.acquire(
                step_id=step_id,
                owner=new_worker_id
            )
            
            if not lease_success:
                return False, "lease_reclaim_failed", validation
        
        result = {
            "slot_id": slot_id,
            "step_id": step_id,
            "reclaimed": True,
            "new_worker_id": new_worker_id,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        return True, "reclaimed", result
    
    def get_running_steps(self) -> List[Dict]:
        """获取所有运行中的步骤及其槽位/租约状态"""
        results = []
        
        all_slots = self.slot_registry.get_all_slots()
        
        for slot_info in all_slots:
            if slot_info.get("status") == "running" and slot_info.get("holder"):
                holder = slot_info["holder"]
                task_id = holder.get("task_id")
                step_id = holder.get("step_id")
                
                # 检查状态
                status = self.check_execution_prerequisites(task_id, step_id)
                
                results.append({
                    "slot_id": slot_info["slot_id"],
                    "task_id": task_id,
                    "step_id": step_id,
                    "worker_id": holder.get("worker_id"),
                    "slot_valid": status.slot_valid,
                    "lease_valid": status.lease_valid,
                    "both_valid": status.both_valid,
                    "started_at": slot_info.get("started_at"),
                    "last_heartbeat": slot_info.get("last_heartbeat_at")
                })
        
        return results
    
    def detect_inconsistencies(self) -> List[Dict]:
        """检测不一致状态"""
        inconsistencies = []
        
        running_steps = self.get_running_steps()
        
        for step in running_steps:
            issues = []
            
            # 槽位有效但租约无效
            if step["slot_valid"] and not step["lease_valid"]:
                issues.append("slot_valid_but_lease_invalid")
            
            # 租约有效但槽位无效
            if step["lease_valid"] and not step["slot_valid"]:
                issues.append("lease_valid_but_slot_invalid")
            
            # 两者都无效但状态是 running
            if not step["slot_valid"] and not step["lease_valid"]:
                issues.append("both_invalid_but_running")
            
            if issues:
                inconsistencies.append({
                    **step,
                    "issues": issues
                })
        
        return inconsistencies
    
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


def create_bridge(slot_registry, lease_manager, task_dossier=None) -> SlotLeaseBridge:
    """创建槽位-租约桥接器"""
    return SlotLeaseBridge(slot_registry, lease_manager, task_dossier)
