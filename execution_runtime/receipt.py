"""
Receipt Manager - Execution Receipt and Audit

执行凭证与审计。

Author: Execution Runtime
Created: 2026-03-17
Version: 1.0.0
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from pathlib import Path
import sys
import json
import yaml
import hashlib
from datetime import datetime, timezone

# 添加项目根目录到 path
sys.path.insert(0, str(Path(__file__).parent.parent))


@dataclass
class ReceiptConfig:
    """
    Receipt 配置
    """
    agent_id: str = "default"
    receipt_dir: Optional[Path] = None
    max_receipts: int = 1000
    retention_days: int = 30


@dataclass
class ExecutionReceipt:
    """
    执行凭证
    """
    receipt_id: str
    task_id: str
    agent_id: str
    success: bool
    steps_completed: int
    steps_failed: int
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_seconds: Optional[float] = None
    output: Optional[str] = None
    error: Optional[str] = None
    evidence_ids: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "receipt_id": self.receipt_id,
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "success": self.success,
            "steps_completed": self.steps_completed,
            "steps_failed": self.steps_failed,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration_seconds": self.duration_seconds,
            "output": self.output,
            "error": self.error,
            "evidence_ids": self.evidence_ids,
            "metadata": self.metadata,
        }


class ReceiptManager:
    """
    凭证管理器
    
    负责：
    - 创建执行凭证
    - 存储凭证
    - 查询凭证
    - 审计追踪
    """
    
    def __init__(self, config: Optional[ReceiptConfig] = None):
        self.config = config or ReceiptConfig()
    
    def _get_receipt_dir(self) -> Path:
        """获取凭证目录"""
        if self.config.receipt_dir:
            return self.config.receipt_dir
        
        # 默认路径
        return Path.home() / ".openclaw" / "agents" / self.config.agent_id / "receipts"
    
    def _ensure_receipt_dir(self) -> Path:
        """确保凭证目录存在"""
        receipt_dir = self._get_receipt_dir()
        receipt_dir.mkdir(parents=True, exist_ok=True)
        return receipt_dir
    
    def _generate_receipt_id(self, task_id: str) -> str:
        """生成凭证 ID"""
        timestamp = datetime.now(timezone.utc)
        ts_short = timestamp.strftime("%Y%m%d%H%M%S")
        hash_input = f"{task_id}:{timestamp.isoformat()}"
        hash_part = hashlib.sha256(hash_input.encode()).hexdigest()[:8]
        return f"rcpt:{ts_short}:{hash_part}"
    
    def create_receipt(
        self,
        task_result: Any,
        evidence_ids: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ExecutionReceipt:
        """
        创建凭证
        
        Args:
            task_result: 任务结果
            evidence_ids: 关联的证据 ID
            metadata: 元数据
        
        Returns:
            ExecutionReceipt
        """
        receipt_id = self._generate_receipt_id(task_result.task_id)
        
        receipt = ExecutionReceipt(
            receipt_id=receipt_id,
            task_id=task_result.task_id,
            agent_id=self.config.agent_id,
            success=task_result.success,
            steps_completed=task_result.steps_completed,
            steps_failed=task_result.steps_failed,
            started_at=task_result.started_at,
            completed_at=task_result.completed_at,
            output=task_result.output,
            error=task_result.error,
            evidence_ids=evidence_ids or [],
            metadata=metadata or {},
        )
        
        # 计算时长
        if receipt.started_at and receipt.completed_at:
            start = datetime.fromisoformat(receipt.started_at)
            end = datetime.fromisoformat(receipt.completed_at)
            receipt.duration_seconds = (end - start).total_seconds()
        
        # 存储
        self._save_receipt(receipt)
        
        return receipt
    
    def _save_receipt(self, receipt: ExecutionReceipt) -> bool:
        """存储凭证"""
        try:
            receipt_dir = self._ensure_receipt_dir()
            receipt_file = receipt_dir / f"{receipt.receipt_id.replace(':', '_')}.yaml"
            
            with open(receipt_file, "w") as f:
                yaml.dump(receipt.to_dict(), f)
            
            return True
            
        except Exception:
            return False
    
    def get_receipt(self, receipt_id: str) -> Optional[ExecutionReceipt]:
        """
        获取凭证
        
        Args:
            receipt_id: 凭证 ID
        
        Returns:
            ExecutionReceipt
        """
        receipt_dir = self._get_receipt_dir()
        receipt_file = receipt_dir / f"{receipt_id.replace(':', '_')}.yaml"
        
        if not receipt_file.exists():
            return None
        
        try:
            with open(receipt_file) as f:
                data = yaml.safe_load(f)
            
            return ExecutionReceipt(
                receipt_id=data["receipt_id"],
                task_id=data["task_id"],
                agent_id=data["agent_id"],
                success=data["success"],
                steps_completed=data["steps_completed"],
                steps_failed=data["steps_failed"],
                started_at=data.get("started_at"),
                completed_at=data.get("completed_at"),
                duration_seconds=data.get("duration_seconds"),
                output=data.get("output"),
                error=data.get("error"),
                evidence_ids=data.get("evidence_ids", []),
                metadata=data.get("metadata", {}),
            )
            
        except Exception:
            return None
    
    def get_receipts_by_task(self, task_id: str) -> List[ExecutionReceipt]:
        """
        按任务 ID 获取凭证
        
        Args:
            task_id: 任务 ID
        
        Returns:
            ExecutionReceipt 列表
        """
        receipt_dir = self._get_receipt_dir()
        
        if not receipt_dir.exists():
            return []
        
        receipts = []
        
        for receipt_file in sorted(receipt_dir.glob("*.yaml"), reverse=True):
            try:
                with open(receipt_file) as f:
                    data = yaml.safe_load(f)
                
                if data.get("task_id") == task_id:
                    receipts.append(ExecutionReceipt(
                        receipt_id=data["receipt_id"],
                        task_id=data["task_id"],
                        agent_id=data["agent_id"],
                        success=data["success"],
                        steps_completed=data["steps_completed"],
                        steps_failed=data["steps_failed"],
                        started_at=data.get("started_at"),
                        completed_at=data.get("completed_at"),
                        duration_seconds=data.get("duration_seconds"),
                        output=data.get("output"),
                        error=data.get("error"),
                        evidence_ids=data.get("evidence_ids", []),
                        metadata=data.get("metadata", {}),
                    ))
                    
            except Exception:
                continue
        
        return receipts
    
    def list_recent_receipts(self, limit: int = 100) -> List[ExecutionReceipt]:
        """
        列出最近的凭证
        
        Args:
            limit: 最大数量
        
        Returns:
            ExecutionReceipt 列表
        """
        receipt_dir = self._get_receipt_dir()
        
        if not receipt_dir.exists():
            return []
        
        receipts = []
        
        for receipt_file in sorted(receipt_dir.glob("*.yaml"), reverse=True)[:limit]:
            try:
                with open(receipt_file) as f:
                    data = yaml.safe_load(f)
                
                receipts.append(ExecutionReceipt(
                    receipt_id=data["receipt_id"],
                    task_id=data["task_id"],
                    agent_id=data["agent_id"],
                    success=data["success"],
                    steps_completed=data["steps_completed"],
                    steps_failed=data["steps_failed"],
                    started_at=data.get("started_at"),
                    completed_at=data.get("completed_at"),
                    duration_seconds=data.get("duration_seconds"),
                    output=data.get("output"),
                    error=data.get("error"),
                    evidence_ids=data.get("evidence_ids", []),
                    metadata=data.get("metadata", {}),
                ))
                
            except Exception:
                continue
        
        return receipts
    
    def get_audit_trail(self, task_id: str) -> Dict[str, Any]:
        """
        获取审计追踪
        
        Args:
            task_id: 任务 ID
        
        Returns:
            审计追踪字典
        """
        receipts = self.get_receipts_by_task(task_id)
        
        return {
            "task_id": task_id,
            "total_receipts": len(receipts),
            "receipts": [r.to_dict() for r in receipts],
        }
