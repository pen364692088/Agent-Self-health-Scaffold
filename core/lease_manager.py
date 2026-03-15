"""
Lease Manager - 步骤租约管理器

提供完整的租约生命周期管理，包括：
- 租约获取（带幂等检查）
- 租约续期
- 租约释放
- 租约回收（过期后接管）
- 心跳维护
"""

import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
import hashlib
import threading
import threading


@dataclass
class LeaseState:
    """租约状态"""
    step_id: str
    owner: str
    owner_session_key: Optional[str]
    acquired_at: str
    expires_at: str
    ttl_seconds: int
    status: str  # active, expired, released, revoked
    heartbeat: Dict[str, Any]
    reclaim_count: int
    max_reclaims: int
    checksum: str


class LeaseManager:
    """租约管理器"""
    
    DEFAULT_TTL = 300  # 5 minutes
    DEFAULT_HEARTBEAT_INTERVAL_MS = 30000  # 30 seconds
    DEFAULT_MAX_MISSED = 3
    DEFAULT_MAX_RECLAIMS = 3
    
    def __init__(self, steps_dir: Path):
        self.steps_dir = steps_dir
        self._locks: Dict[str, threading.Lock] = {}
    
    def _get_lock(self, step_id: str) -> threading.Lock:
        """获取步骤锁"""
        if step_id not in self._locks:
            self._locks[step_id] = threading.Lock()
        return self._locks[step_id]
    
    def _lease_file(self, step_id: str) -> Path:
        """获取租约文件路径"""
        return self.steps_dir / step_id / "lease.json"
    
    def _calculate_checksum(self, lease_data: Dict[str, Any]) -> str:
        """计算租约校验和"""
        # 排除 checksum 字段本身
        data = {k: v for k, v in lease_data.items() if k != "checksum"}
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
    
    def acquire(
        self,
        step_id: str,
        owner: str,
        ttl_seconds: int = DEFAULT_TTL,
        session_key: Optional[str] = None
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        获取租约
        
        Returns:
            (success, lease_data or reason)
        """
        lock = self._get_lock(step_id)
        
        with lock:
            lease_file = self._lease_file(step_id)
            
            # 检查是否存在活跃租约
            if lease_file.exists():
                with open(lease_file) as f:
                    existing = json.load(f)
                
                # 验证校验和
                expected_checksum = self._calculate_checksum(existing)
                if existing.get("checksum") != expected_checksum:
                    # 校验和不匹配，可能被篡改
                    return False, {"reason": "checksum_mismatch", "existing_lease": existing}
                
                # 检查是否过期
                expires_at = datetime.fromisoformat(existing["expires_at"].replace("Z", "+00:00"))
                now = datetime.utcnow()
                
                if now < expires_at.replace(tzinfo=None):
                    # 租约仍然有效
                    if existing["owner"] == owner:
                        # 同一个 owner，幂等返回
                        return True, existing
                    else:
                        # 其他 owner 持有
                        return False, {"reason": "lease_held", "holder": existing["owner"], "expires_at": existing["expires_at"]}
                
                # 租约已过期，可以回收
                reclaim_count = existing.get("reclaim_count", 0) + 1
            else:
                reclaim_count = 0
            
            # 创建新租约
            now = datetime.utcnow()
            lease = {
                "step_id": step_id,
                "owner": owner,
                "owner_session_key": session_key,
                "acquired_at": now.isoformat() + "Z",
                "expires_at": (now + timedelta(seconds=ttl_seconds)).isoformat() + "Z",
                "ttl_seconds": ttl_seconds,
                "status": "active",
                "heartbeat": {
                    "last_heartbeat_at": now.isoformat() + "Z",
                    "heartbeat_interval_ms": self.DEFAULT_HEARTBEAT_INTERVAL_MS,
                    "missed_count": 0,
                    "max_missed": self.DEFAULT_MAX_MISSED
                },
                "reclaim_count": reclaim_count,
                "max_reclaims": self.DEFAULT_MAX_RECLAIMS
            }
            
            # 计算校验和
            lease["checksum"] = self._calculate_checksum(lease)
            
            # 保存租约
            lease_file.parent.mkdir(parents=True, exist_ok=True)
            with open(lease_file, 'w') as f:
                json.dump(lease, f, indent=2)
            
            return True, lease
    
    def renew(
        self,
        step_id: str,
        owner: str,
        extend_seconds: Optional[int] = None
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        续期租约
        """
        lock = self._get_lock(step_id)
        
        with lock:
            lease_file = self._lease_file(step_id)
            
            if not lease_file.exists():
                return False, {"reason": "no_lease"}
            
            with open(lease_file) as f:
                lease = json.load(f)
            
            # 验证所有权
            if lease["owner"] != owner:
                return False, {"reason": "not_owner", "owner": lease["owner"]}
            
            # 验证状态
            if lease["status"] != "active":
                return False, {"reason": "not_active", "status": lease["status"]}
            
            # 续期
            now = datetime.utcnow()
            extend = extend_seconds or lease["ttl_seconds"]
            lease["expires_at"] = (now + timedelta(seconds=extend)).isoformat() + "Z"
            lease["heartbeat"]["last_heartbeat_at"] = now.isoformat() + "Z"
            
            # 重新计算校验和
            lease["checksum"] = self._calculate_checksum(lease)
            
            with open(lease_file, 'w') as f:
                json.dump(lease, f, indent=2)
            
            return True, lease
    
    def release(
        self,
        step_id: str,
        owner: str,
        reason: str = "completed"
    ) -> Tuple[bool, Optional[str]]:
        """
        释放租约
        """
        lock = self._get_lock(step_id)
        
        with lock:
            lease_file = self._lease_file(step_id)
            
            if not lease_file.exists():
                return True, "no_lease_to_release"
            
            with open(lease_file) as f:
                lease = json.load(f)
            
            # 验证所有权
            if lease["owner"] != owner:
                return False, f"not_owner: current owner is {lease['owner']}"
            
            # 标记为已释放
            lease["status"] = "released"
            lease["released_at"] = datetime.utcnow().isoformat() + "Z"
            lease["release_reason"] = reason
            
            # 重新计算校验和
            lease["checksum"] = self._calculate_checksum(lease)
            
            with open(lease_file, 'w') as f:
                json.dump(lease, f, indent=2)
            
            return True, "released"
    
    def revoke(
        self,
        step_id: str,
        admin_key: str
    ) -> Tuple[bool, Optional[str]]:
        """
        撤销租约（管理员操作）
        """
        lock = self._get_lock(step_id)
        
        with lock:
            lease_file = self._lease_file(step_id)
            
            if not lease_file.exists():
                return False, "no_lease"
            
            with open(lease_file) as f:
                lease = json.load(f)
            
            lease["status"] = "revoked"
            lease["revoked_at"] = datetime.utcnow().isoformat() + "Z"
            lease["revoked_by"] = admin_key
            
            # 重新计算校验和
            lease["checksum"] = self._calculate_checksum(lease)
            
            with open(lease_file, 'w') as f:
                json.dump(lease, f, indent=2)
            
            return True, "revoked"
    
    def heartbeat(
        self,
        step_id: str,
        owner: str
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        发送心跳
        """
        lock = self._get_lock(step_id)
        
        with lock:
            lease_file = self._lease_file(step_id)
            
            if not lease_file.exists():
                return False, {"reason": "no_lease"}
            
            with open(lease_file) as f:
                lease = json.load(f)
            
            # 验证所有权
            if lease["owner"] != owner:
                return False, {"reason": "not_owner"}
            
            # 更新心跳
            now = datetime.utcnow()
            lease["heartbeat"]["last_heartbeat_at"] = now.isoformat() + "Z"
            lease["heartbeat"]["missed_count"] = 0
            
            # 重新计算校验和
            lease["checksum"] = self._calculate_checksum(lease)
            
            with open(lease_file, 'w') as f:
                json.dump(lease, f, indent=2)
            
            return True, lease
    
    def check(
        self,
        step_id: str
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        检查租约状态
        
        Returns:
            (is_valid, lease_info)
        """
        lease_file = self._lease_file(step_id)
        
        if not lease_file.exists():
            return False, {"status": "no_lease"}
        
        with open(lease_file) as f:
            lease = json.load(f)
        
        # 验证校验和
        expected_checksum = self._calculate_checksum(lease)
        if lease.get("checksum") != expected_checksum:
            return False, {**lease, "status": "checksum_invalid"}
        
        # 检查状态
        if lease["status"] != "active":
            return False, lease
        
        # 检查过期
        expires_at = datetime.fromisoformat(lease["expires_at"].replace("Z", "+00:00"))
        now = datetime.utcnow()
        
        if now >= expires_at.replace(tzinfo=None):
            return False, {**lease, "status": "expired"}
        
        # 检查心跳
        heartbeat = lease.get("heartbeat", {})
        last_heartbeat = heartbeat.get("last_heartbeat_at")
        if last_heartbeat:
            last_heartbeat_time = datetime.fromisoformat(last_heartbeat.replace("Z", "+00:00"))
            interval_ms = heartbeat.get("heartbeat_interval_ms", self.DEFAULT_HEARTBEAT_INTERVAL_MS)
            max_missed = heartbeat.get("max_missed", self.DEFAULT_MAX_MISSED)
            
            elapsed_ms = (now - last_heartbeat_time.replace(tzinfo=None)).total_seconds() * 1000
            expected_heartbeats = elapsed_ms / interval_ms
            
            if expected_heartbeats > max_missed:
                return False, {**lease, "status": "heartbeat_timeout"}
        
        return True, lease
    
    def get_status(self, step_id: str) -> Optional[Dict[str, Any]]:
        """获取租约详细状态"""
        lease_file = self._lease_file(step_id)
        
        if not lease_file.exists():
            return None
        
        with open(lease_file) as f:
            return json.load(f)


class DuplicateCompletionProtection:
    """
    重复完成保护器
    
    防止同一任务被多次标记为完成
    """
    
    def __init__(self, task_dossier):
        self.dossier = task_dossier
        self.completion_lock = threading.Lock()
    
    def is_already_completed(self) -> bool:
        """检查任务是否已经完成"""
        state = self.dossier.load_state()
        if state is None:
            return False
        
        # 检查状态是否为 completed
        if state.status == "completed":
            return True
        
        # 检查 receipt 文件是否存在
        receipt_file = self.dossier.final_dir / "receipt.json"
        if receipt_file.exists():
            return True
        
        return False
    
    def mark_completed(self, receipt: Dict[str, Any]) -> Tuple[bool, str]:
        """
        标记任务完成
        
        Returns:
            (success, message)
        """
        with self.completion_lock:
            # 检查 receipt 文件是否已存在（防止重复写入）
            receipt_file = self.dossier.final_dir / "receipt.json"
            if receipt_file.exists():
                return False, "Receipt already exists - task already marked completed"
            
            # 写入 receipt
            self.dossier.final_dir.mkdir(parents=True, exist_ok=True)
            with open(receipt_file, 'w') as f:
                json.dump(receipt, f, indent=2)
            
            # 更新状态（如果还没有）
            state = self.dossier.load_state()
            if state.status != "completed":
                state.status = "completed"
                state.updated_at = datetime.utcnow().isoformat() + "Z"
                self.dossier._save_state(state)
            
            # 追加 ledger 事件
            self.dossier._append_ledger("task_completed", {"receipt_path": str(receipt_file)})
            
            return True, "Marked as completed"
    
    def verify_completion_integrity(self) -> Tuple[bool, Dict[str, Any]]:
        """
        验证完成完整性
        
        检查：
        - receipt 存在
        - task_state 状态一致
        - ledger 有完成事件
        """
        issues = []
        
        # 检查 receipt
        receipt_file = self.dossier.final_dir / "receipt.json"
        if not receipt_file.exists():
            issues.append("receipt.json missing")
        
        # 检查 task_state
        state = self.dossier.load_state()
        if state and state.status != "completed":
            issues.append(f"task_state status is '{state.status}', expected 'completed'")
        
        # 检查 ledger
        events = self.dossier.get_ledger_events()
        completed_events = [e for e in events if e.get("action") == "task_completed"]
        if not completed_events:
            issues.append("No task_completed event in ledger")
        
        return len(issues) == 0, {"issues": issues, "events_checked": len(events)}
