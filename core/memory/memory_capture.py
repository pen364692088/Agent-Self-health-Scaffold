"""
Memory Capture Engine

自动捕获新记忆，写入 candidate store，不直接进入 authority knowledge。

Author: Memory Kernel
Created: 2026-03-15
Version: 1.0.0
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Set
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import re

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from contract.memory.types import (
    MemoryRecord,
    MemoryScope,
    MemoryTier,
    MemorySourceKind,
    MemoryContentType,
    TruthKnowledgeRetrieval,
)


@dataclass
class CaptureReason:
    """
    捕获原因
    
    记录为什么捕获这条记忆。
    """
    reason: str  # 原因描述
    category: str  # 分类：auto/manual/suggestion
    triggered_by: Optional[str] = None  # 触发者（如用户、系统）


@dataclass
class SourceRef:
    """
    来源引用
    
    记录记忆的来源信息。
    """
    path: str  # 文件路径
    line_start: Optional[int] = None  # 起始行
    line_end: Optional[int] = None  # 结束行
    context: Optional[str] = None  # 上下文
    session_id: Optional[str] = None  # 会话 ID
    timestamp: Optional[datetime] = None  # 时间戳


@dataclass
class CaptureMetadata:
    """
    捕获元数据
    
    每条捕获必须包含的元数据。
    """
    capture_reason: CaptureReason
    source_ref: SourceRef
    scope: MemoryScope
    importance: float  # [0.0, 1.0]
    confidence: float  # [0.0, 1.0]
    authority_level: str  # low/medium/high
    
    # 可选字段
    scope_qualifier: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    content_type: MemoryContentType = MemoryContentType.FACT


@dataclass
class CandidateRecord:
    """
    候选记录
    
    待审核的记忆候选。
    """
    id: str  # 候选 ID
    title: str  # 标题
    content: str  # 内容
    metadata: CaptureMetadata  # 元数据
    content_hash: str  # 内容哈希（用于去重）
    
    # 状态
    status: str = "pending"  # pending/approved/rejected/promoted
    
    # 时间戳
    captured_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    reviewed_at: Optional[datetime] = None
    promoted_at: Optional[datetime] = None
    
    # 审核信息
    reviewed_by: Optional[str] = None
    review_notes: Optional[str] = None
    
    # 提升信息
    promoted_to_id: Optional[str] = None  # 提升后的正式记忆 ID
    target_tkr_layer: Optional[TruthKnowledgeRetrieval] = None
    
    # 扩展
    extra: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "metadata": {
                "capture_reason": {
                    "reason": self.metadata.capture_reason.reason,
                    "category": self.metadata.capture_reason.category,
                    "triggered_by": self.metadata.capture_reason.triggered_by,
                },
                "source_ref": {
                    "path": self.metadata.source_ref.path,
                    "line_start": self.metadata.source_ref.line_start,
                    "line_end": self.metadata.source_ref.line_end,
                    "context": self.metadata.source_ref.context,
                    "session_id": self.metadata.source_ref.session_id,
                    "timestamp": self.metadata.source_ref.timestamp.isoformat() if self.metadata.source_ref.timestamp else None,
                },
                "scope": self.metadata.scope.value,
                "scope_qualifier": self.metadata.scope_qualifier,
                "importance": self.metadata.importance,
                "confidence": self.metadata.confidence,
                "authority_level": self.metadata.authority_level,
                "tags": self.metadata.tags,
                "content_type": self.metadata.content_type.value,
            },
            "content_hash": self.content_hash,
            "status": self.status,
            "captured_at": self.captured_at.isoformat(),
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "promoted_at": self.promoted_at.isoformat() if self.promoted_at else None,
            "reviewed_by": self.reviewed_by,
            "review_notes": self.review_notes,
            "promoted_to_id": self.promoted_to_id,
            "target_tkr_layer": self.target_tkr_layer.value if self.target_tkr_layer else None,
            "extra": self.extra,
        }


@dataclass
class CaptureWhitelist:
    """
    捕获白名单
    
    定义允许捕获的来源和内容类型。
    """
    allowed_sources: Set[MemorySourceKind] = field(default_factory=lambda: {
        MemorySourceKind.SESSION_LOG,
        MemorySourceKind.DECISION_LOG,
        MemorySourceKind.TECHNICAL_NOTE,
    })
    allowed_content_types: Set[MemoryContentType] = field(default_factory=lambda: {
        MemoryContentType.RULE,
        MemoryContentType.FACT,
        MemoryContentType.PREFERENCE,
    })
    min_confidence: float = 0.5
    min_importance: float = 0.3
    
    def is_source_allowed(self, source: MemorySourceKind) -> bool:
        """检查来源是否允许"""
        return source in self.allowed_sources
    
    def is_content_type_allowed(self, content_type: MemoryContentType) -> bool:
        """检查内容类型是否允许"""
        return content_type in self.allowed_content_types
    
    def meets_thresholds(self, confidence: float, importance: float) -> bool:
        """检查是否满足阈值"""
        return confidence >= self.min_confidence and importance >= self.min_importance


class CaptureEngine:
    """
    捕获引擎
    
    负责捕获新记忆，写入 candidate store。
    """
    
    def __init__(
        self,
        whitelist: Optional[CaptureWhitelist] = None,
        noise_threshold_chars: int = 10,
        dedup_similarity_threshold: float = 0.9,
    ):
        """
        初始化捕获引擎
        
        Args:
            whitelist: 捕获白名单
            noise_threshold_chars: 噪音过滤阈值（最小字符数）
            dedup_similarity_threshold: 去重相似度阈值
        """
        self.whitelist = whitelist or CaptureWhitelist()
        self.noise_threshold_chars = noise_threshold_chars
        self.dedup_similarity_threshold = dedup_similarity_threshold
        self._candidate_store: Dict[str, CandidateRecord] = {}
        self._content_hashes: Set[str] = set()
    
    def compute_content_hash(self, content: str) -> str:
        """
        计算内容哈希
        
        Args:
            content: 内容
        
        Returns:
            SHA256 哈希值
        """
        normalized = content.strip().lower()
        return hashlib.sha256(normalized.encode()).hexdigest()[:16]
    
    def is_noise(self, content: str) -> bool:
        """
        检查是否为噪音
        
        Args:
            content: 内容
        
        Returns:
            是否为噪音
        """
        # 空内容
        if not content or not content.strip():
            return True
        
        # 过短
        if len(content.strip()) < self.noise_threshold_chars:
            return True
        
        # 纯空白字符
        if not re.search(r'\w', content):
            return True
        
        return False
    
    def is_duplicate(self, content_hash: str) -> bool:
        """
        检查是否重复
        
        Args:
            content_hash: 内容哈希
        
        Returns:
            是否重复
        """
        return content_hash in self._content_hashes
    
    def validate_metadata(self, metadata: CaptureMetadata) -> List[str]:
        """
        验证元数据
        
        Args:
            metadata: 捕获元数据
        
        Returns:
            验证错误列表
        """
        errors = []
        
        # 检查必填字段
        if not metadata.capture_reason or not metadata.capture_reason.reason:
            errors.append("Missing capture_reason")
        
        if not metadata.source_ref or not metadata.source_ref.path:
            errors.append("Missing source_ref.path")
        
        # 检查数值范围
        if not 0.0 <= metadata.importance <= 1.0:
            errors.append(f"importance out of range: {metadata.importance}")
        
        if not 0.0 <= metadata.confidence <= 1.0:
            errors.append(f"confidence out of range: {metadata.confidence}")
        
        # 检查白名单阈值
        if not self.whitelist.meets_thresholds(metadata.confidence, metadata.importance):
            errors.append(f"Below thresholds: confidence={metadata.confidence}, importance={metadata.importance}")
        
        return errors
    
    def capture(
        self,
        title: str,
        content: str,
        metadata: CaptureMetadata,
    ) -> Optional[CandidateRecord]:
        """
        捕获记忆
        
        Args:
            title: 标题
            content: 内容
            metadata: 捕获元数据
        
        Returns:
            候选记录（如果成功）
        """
        # 1. 噪音过滤
        if self.is_noise(content):
            return None
        
        # 2. 验证元数据
        errors = self.validate_metadata(metadata)
        if errors:
            return None
        
        # 3. 计算内容哈希
        content_hash = self.compute_content_hash(content)
        
        # 4. 去重检查
        if self.is_duplicate(content_hash):
            return None
        
        # 5. 创建候选记录
        candidate_id = f"cand_{datetime.now().strftime('%Y%m%d%H%M%S')}_{content_hash[:8]}"
        
        candidate = CandidateRecord(
            id=candidate_id,
            title=title,
            content=content,
            metadata=metadata,
            content_hash=content_hash,
        )
        
        # 6. 存储候选
        self._candidate_store[candidate_id] = candidate
        self._content_hashes.add(content_hash)
        
        return candidate
    
    def get_candidate(self, candidate_id: str) -> Optional[CandidateRecord]:
        """
        获取候选记录
        
        Args:
            candidate_id: 候选 ID
        
        Returns:
            候选记录
        """
        return self._candidate_store.get(candidate_id)
    
    def list_candidates(
        self,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[CandidateRecord]:
        """
        列出候选记录
        
        Args:
            status: 状态过滤
            limit: 返回数量
        
        Returns:
            候选记录列表
        """
        candidates = list(self._candidate_store.values())
        
        if status:
            candidates = [c for c in candidates if c.status == status]
        
        # 按捕获时间倒序
        candidates.sort(key=lambda x: x.captured_at, reverse=True)
        
        return candidates[:limit]
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            统计字典
        """
        candidates = list(self._candidate_store.values())
        
        status_counts = {}
        for c in candidates:
            status_counts[c.status] = status_counts.get(c.status, 0) + 1
        
        return {
            "total": len(candidates),
            "by_status": status_counts,
            "unique_hashes": len(self._content_hashes),
        }


def create_capture_engine(
    whitelist_config: Optional[Dict[str, Any]] = None,
) -> CaptureEngine:
    """
    便捷函数：创建捕获引擎
    
    Args:
        whitelist_config: 白名单配置
    
    Returns:
        CaptureEngine 实例
    """
    if whitelist_config is None:
        return CaptureEngine()
    
    whitelist = CaptureWhitelist()
    
    if "min_confidence" in whitelist_config:
        whitelist.min_confidence = whitelist_config["min_confidence"]
    if "min_importance" in whitelist_config:
        whitelist.min_importance = whitelist_config["min_importance"]
    
    return CaptureEngine(whitelist=whitelist)
