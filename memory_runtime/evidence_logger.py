"""
Evidence Logger - Memory Operation Evidence Chain

记录记忆操作证据链，支持审计和追溯。

Author: Memory Runtime
Created: 2026-03-17
Version: 1.0.0
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from pathlib import Path
import json
import yaml
from datetime import datetime, timezone
import hashlib


@dataclass
class EvidenceConfig:
    """
    证据配置
    """
    agent_id: str = "default"
    memory_root: Optional[Path] = None
    max_evidence_age_days: int = 30


@dataclass
class EvidenceRecord:
    """
    证据记录
    """
    evidence_id: str
    operation: str  # load/write/update/delete
    agent_id: str
    timestamp: str
    details: Dict[str, Any]
    parent_evidence_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "evidence_id": self.evidence_id,
            "operation": self.operation,
            "agent_id": self.agent_id,
            "timestamp": self.timestamp,
            "details": self.details,
            "parent_evidence_id": self.parent_evidence_id,
        }


class EvidenceLogger:
    """
    证据日志器
    
    负责：
    - 记录记忆操作
    - 构建证据链
    - 审计查询
    """
    
    def __init__(self, config: Optional[EvidenceConfig] = None, **kwargs):
        # 支持直接传参
        if config is None:
            config = EvidenceConfig(
                agent_id=kwargs.get("agent_id", "default"),
                memory_root=kwargs.get("memory_root"),
            )
        self.config = config
    
    def _get_memory_root(self) -> Path:
        """获取记忆根目录"""
        if self.config.memory_root:
            return self.config.memory_root
        
        # 默认路径
        return Path.home() / ".openclaw" / "agents" / self.config.agent_id / "memory"
    
    def _get_evidence_dir(self) -> Path:
        """获取证据目录"""
        return self._get_memory_root() / "evidence"
    
    def _ensure_evidence_dir(self) -> Path:
        """确保证据目录存在"""
        evidence_dir = self._get_evidence_dir()
        evidence_dir.mkdir(parents=True, exist_ok=True)
        return evidence_dir
    
    def _generate_evidence_id(self, operation: str, details: Dict[str, Any]) -> str:
        """生成证据 ID"""
        timestamp = datetime.now(timezone.utc).isoformat()
        content = f"{operation}:{json.dumps(details, sort_keys=True)}:{timestamp}"
        hash_part = hashlib.sha256(content.encode()).hexdigest()[:12]
        ts_short = timestamp.replace(":", "").replace("-", "").replace(".", "")[:15]
        return f"ev:{ts_short}:{hash_part}"
    
    def log(
        self,
        operation: str,
        details: Dict[str, Any],
        parent_evidence_id: Optional[str] = None,
    ) -> EvidenceRecord:
        """
        记录证据
        
        Args:
            operation: 操作类型 (load/write/update/delete)
            details: 操作详情
            parent_evidence_id: 父证据 ID
        
        Returns:
            EvidenceRecord
        """
        self._ensure_evidence_dir()
        
        # 生成证据 ID
        evidence_id = self._generate_evidence_id(operation, details)
        
        # 创建记录
        record = EvidenceRecord(
            evidence_id=evidence_id,
            operation=operation,
            agent_id=self.config.agent_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            details=details,
            parent_evidence_id=parent_evidence_id,
        )
        
        # 写入文件
        evidence_file = self._get_evidence_dir() / f"{evidence_id.replace(':', '_')}.yaml"
        
        with open(evidence_file, "w") as f:
            yaml.dump(record.to_dict(), f)
        
        return record
    
    def log_load(
        self,
        source: str,
        record_count: int,
        query: Optional[str] = None,
    ) -> EvidenceRecord:
        """
        记录加载操作
        
        Args:
            source: 来源
            record_count: 记录数
            query: 查询
        
        Returns:
            EvidenceRecord
        """
        return self.log(
            operation="load",
            details={
                "source": source,
                "record_count": record_count,
                "query": query,
            },
        )
    
    def log_write(
        self,
        target: str,
        content_hash: str,
        category: Optional[str] = None,
    ) -> EvidenceRecord:
        """
        记录写入操作
        
        Args:
            target: 目标
            content_hash: 内容哈希
            category: 分类
        
        Returns:
            EvidenceRecord
        """
        return self.log(
            operation="write",
            details={
                "target": target,
                "content_hash": content_hash,
                "category": category,
            },
        )
    
    def log_update(
        self,
        target: str,
        old_value: Optional[str],
        new_value: str,
        parent_evidence_id: Optional[str] = None,
    ) -> EvidenceRecord:
        """
        记录更新操作
        
        Args:
            target: 目标
            old_value: 旧值
            new_value: 新值
            parent_evidence_id: 父证据 ID
        
        Returns:
            EvidenceRecord
        """
        return self.log(
            operation="update",
            details={
                "target": target,
                "old_value_hash": hashlib.sha256((old_value or "").encode()).hexdigest()[:16],
                "new_value_hash": hashlib.sha256(new_value.encode()).hexdigest()[:16],
            },
            parent_evidence_id=parent_evidence_id,
        )
    
    def log_delete(
        self,
        target: str,
        reason: Optional[str] = None,
        parent_evidence_id: Optional[str] = None,
    ) -> EvidenceRecord:
        """
        记录删除操作
        
        Args:
            target: 目标
            reason: 原因
            parent_evidence_id: 父证据 ID
        
        Returns:
            EvidenceRecord
        """
        return self.log(
            operation="delete",
            details={
                "target": target,
                "reason": reason,
            },
            parent_evidence_id=parent_evidence_id,
        )
    
    def get_evidence(self, evidence_id: str) -> Optional[EvidenceRecord]:
        """
        获取证据
        
        Args:
            evidence_id: 证据 ID
        
        Returns:
            EvidenceRecord
        """
        evidence_file = self._get_evidence_dir() / f"{evidence_id.replace(':', '_')}.yaml"
        
        if not evidence_file.exists():
            return None
        
        try:
            with open(evidence_file) as f:
                data = yaml.safe_load(f)
            
            return EvidenceRecord(
                evidence_id=data["evidence_id"],
                operation=data["operation"],
                agent_id=data["agent_id"],
                timestamp=data["timestamp"],
                details=data["details"],
                parent_evidence_id=data.get("parent_evidence_id"),
            )
        except Exception:
            return None
    
    def list_evidence(
        self,
        operation: Optional[str] = None,
        limit: int = 100,
    ) -> List[EvidenceRecord]:
        """
        列出证据
        
        Args:
            operation: 操作类型过滤
            limit: 最大数量
        
        Returns:
            EvidenceRecord 列表
        """
        evidence_dir = self._get_evidence_dir()
        
        if not evidence_dir.exists():
            return []
        
        records = []
        
        for evidence_file in sorted(evidence_dir.glob("*.yaml"), reverse=True):
            try:
                with open(evidence_file) as f:
                    data = yaml.safe_load(f)
                
                if operation and data.get("operation") != operation:
                    continue
                
                records.append(EvidenceRecord(
                    evidence_id=data["evidence_id"],
                    operation=data["operation"],
                    agent_id=data["agent_id"],
                    timestamp=data["timestamp"],
                    details=data["details"],
                    parent_evidence_id=data.get("parent_evidence_id"),
                ))
                
                if len(records) >= limit:
                    break
                    
            except Exception:
                continue
        
        return records
    
    def get_evidence_chain(self, evidence_id: str) -> List[EvidenceRecord]:
        """
        获取证据链
        
        Args:
            evidence_id: 证据 ID
        
        Returns:
            EvidenceRecord 列表（从最新到最旧）
        """
        chain = []
        current_id = evidence_id
        visited = set()
        
        while current_id and current_id not in visited:
            visited.add(current_id)
            
            record = self.get_evidence(current_id)
            if not record:
                break
            
            chain.append(record)
            current_id = record.parent_evidence_id
        
        return chain
