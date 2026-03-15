"""
Memory Contract - Type Definitions

Memory Kernel 统一类型定义。
所有记忆相关组件必须遵守此契约。

Author: Memory Kernel
Created: 2026-03-15
Version: 1.0.0
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pathlib import Path


class MemoryScope(str, Enum):
    """
    记忆作用域
    
    定义记忆条目的适用范围，用于冲突检测和检索过滤。
    """
    GLOBAL = "global"  # 全局通用
    PROJECTS = "projects"  # 项目专用（需配合 project_name）
    DOMAINS = "domains"  # 领域专用（需配合 domain_name）
    
    @classmethod
    def from_path(cls, path: str) -> tuple["MemoryScope", Optional[str]]:
        """
        从文件路径推断作用域
        
        Returns:
            (scope, qualifier): 作用域和限定符（项目名或域名）
        """
        path_lower = path.lower()
        
        # 项目路径特征
        project_indicators = [
            "/projects/",
            "/project/",
            "openemotion",
            "emotiond",
            "openclaw-core",
        ]
        for indicator in project_indicators:
            if indicator in path_lower:
                # 提取项目名
                parts = path_lower.split(indicator.replace("/", ""))
                if len(parts) > 1:
                    # 尝试提取项目名
                    project_name = indicator.replace("/", "").replace("-", "_")
                    return cls.PROJECTS, project_name
        
        # 领域路径特征
        domain_indicators = [
            "/domains/",
            "/domain/",
            "infra",
            "security",
            "frontend",
            "backend",
        ]
        for indicator in domain_indicators:
            if indicator in path_lower:
                return cls.DOMAINS, indicator
        
        return cls.GLOBAL, None


class MemorySourceKind(str, Enum):
    """
    记忆来源类型
    
    定义记忆条目的来源，用于可信度评估和检索优先级。
    """
    # 会话日志类
    SESSION_LOG = "session_log"  # 会话日志
    DECISION_LOG = "decision_log"  # 决策日志
    TECHNICAL_NOTE = "technical_note"  # 技术笔记
    
    # 规则策略类
    RULE = "rule"  # 规则
    POLICY = "policy"  # 策略
    PREFERENCE = "preference"  # 偏好
    
    # 状态事实类
    STATE = "state"  # 状态
    CONFIG = "config"  # 配置
    METRICS = "metrics"  # 统计
    
    # 事件日志类
    RETRIEVAL_EVENT = "retrieval_event"  # 检索事件
    DRIFT_EVENT = "drift_event"  # 漂移事件
    EVOLUTION_EVENT = "evolution_event"  # 进化事件
    
    # 模板定义类
    TEMPLATE = "template"  # 模板
    SCHEMA = "schema"  # Schema
    
    @classmethod
    def from_file_pattern(cls, filename: str) -> "MemorySourceKind":
        """
        从文件名推断来源类型
        """
        filename_lower = filename.lower()
        
        # 模板和 schema
        if "template" in filename_lower:
            return cls.TEMPLATE
        if "schema" in filename_lower:
            return cls.SCHEMA
        
        # 状态文件
        if filename_lower in ["session-state.md", "working-buffer.md"]:
            return cls.STATE
        if filename_lower.endswith(".state.json") or ".state." in filename_lower:
            return cls.STATE
        
        # 配置文件
        if "config" in filename_lower:
            return cls.CONFIG
        
        # 统计文件
        if "stats" in filename_lower or "metrics" in filename_lower:
            return cls.METRICS
        
        # 事件日志
        if "events" in filename_lower or filename_lower.endswith(".log"):
            return cls.RETRIEVAL_EVENT
        if "drift" in filename_lower:
            return cls.DRIFT_EVENT
        if "evolution" in filename_lower:
            return cls.EVOLUTION_EVENT
        
        # 策略文档
        if "policy" in filename_lower:
            return cls.POLICY
        
        # 决策日志
        if "decision" in filename_lower:
            return cls.DECISION_LOG
        
        # 技术笔记（按日期命名的文件）
        import re
        if re.match(r"\d{4}-\d{2}-\d{2}", filename_lower):
            if "fix" in filename_lower or "debug" in filename_lower:
                return cls.TECHNICAL_NOTE
            return cls.SESSION_LOG
        
        # 默认
        return cls.SESSION_LOG


class MemoryTier(str, Enum):
    """
    记忆分层
    
    基于使用频率和价值的热度分层。
    """
    HOT = "hot"  # 高频使用，高价值
    WARM = "warm"  # 中等使用
    COLD = "cold"  # 低频或待清理
    ARCHIVED = "archived"  # 已归档


class MemoryStatus(str, Enum):
    """
    记忆状态
    
    定义记忆条目的生命周期状态。
    """
    ACTIVE = "active"  # 正常使用
    DEPRECATED = "deprecated"  # 已弃用
    SUPERSEDED = "superseded"  # 已被替换
    PENDING_REVIEW = "pending_review"  # 待审核
    DELETED = "deleted"  # 已删除


class MemoryContentType(str, Enum):
    """
    记忆内容类型
    
    对应 ENTRY_TEMPLATE.md 中的 type 字段。
    """
    RULE = "RULE"  # 规则
    FACT = "FACT"  # 事实
    PREFERENCE = "PREFERENCE"  # 偏好
    REFLECTION = "REFLECTION"  # 反思


class TruthKnowledgeRetrieval(str, Enum):
    """
    Truth/Knowledge/Retrieval 三层分类
    
    用于记忆条目的高层分类。
    """
    TRUTH = "truth"  # 确定性事实层
    KNOWLEDGE = "knowledge"  # 知识规则层
    RETRIEVAL = "retrieval"  # 检索召回层


@dataclass
class MemorySource:
    """
    记忆来源信息
    
    记录记忆条目的来源会话和证据。
    """
    session: str  # 来源会话日期 (YYYY-MM-DD)
    evidence: str  # 证据描述
    task_id: Optional[str] = None  # 关联任务 ID
    commit: Optional[str] = None  # 关联 commit hash


@dataclass
class MemoryRecord:
    """
    记忆条目记录
    
    Memory Kernel 的核心数据结构，表示一条完整的记忆。
    """
    # 标识
    id: str  # 唯一标识 (mem_YYYYMMDD_XXX 格式)
    
    # 分类（必填字段）
    scope: MemoryScope  # 作用域
    source_kind: MemorySourceKind  # 来源类型
    content_type: MemoryContentType  # 内容类型
    tkr_layer: TruthKnowledgeRetrieval  # Truth/Knowledge/Retrieval 层
    
    # 内容（必填字段）
    title: str  # 标题
    content: str  # 正文内容
    source_file: str  # 来源文件路径
    
    # 可选字段（有默认值）
    scope_qualifier: Optional[str] = None  # 作用域限定符（项目名或域名）
    tags: List[str] = field(default_factory=list)  # 标签
    sources: List[MemorySource] = field(default_factory=list)  # 来源信息列表
    
    # 元数据
    tier: MemoryTier = MemoryTier.WARM  # 分层
    status: MemoryStatus = MemoryStatus.ACTIVE  # 状态
    
    created_at: datetime = field(default_factory=datetime.now)  # 创建时间
    last_used: Optional[datetime] = None  # 最后使用时间
    use_count: int = 0  # 使用次数
    correction_count: int = 0  # 纠正次数
    
    confidence: float = 0.5  # 置信度 [0.0, 1.0]
    importance: float = 0.5  # 重要性 [0.0, 1.0]
    pinned: bool = False  # 是否手动标记高价值
    
    conflict_penalty: float = 0.0  # 冲突惩罚
    superseded_by: Optional[str] = None  # 替换者 ID
    
    # 扩展
    metadata: Dict[str, Any] = field(default_factory=dict)  # 扩展元数据
    
    def calculate_score(self) -> float:
        """
        计算记忆条目的评分
        
        基于 EVENT_SCHEMA.md 中定义的评分模型。
        """
        import math
        
        # 计算天数差
        days_ago = 0
        if self.last_used:
            delta = datetime.now() - self.last_used
            days_ago = delta.days
        elif self.created_at:
            delta = datetime.now() - self.created_at
            days_ago = delta.days
        
        # recency boost (半衰期 14 天)
        half_life = 14
        recency = math.exp(-days_ago / half_life)
        
        # 评分公式
        score = (
            2.0 * math.log(self.use_count + 1) +
            1.5 * recency +
            3.0 * min(max(self.importance, 0), 1) -
            2.0 * max(self.conflict_penalty, 0)
        )
        
        return round(score, 2)
    
    def determine_tier(self) -> MemoryTier:
        """
        基于评分确定分层
        """
        if self.pinned:
            return MemoryTier.HOT
        
        score = self.calculate_score()
        
        if score >= 7:
            return MemoryTier.HOT
        elif score >= 3:
            return MemoryTier.WARM
        else:
            return MemoryTier.COLD
    
    def to_entry_template_format(self) -> str:
        """
        转换为 ENTRY_TEMPLATE.md 格式的 YAML 头
        """
        lines = [
            "---",
            f"id: {self.id}",
            f"type: {self.content_type.value}",
            f"scope: {self.scope.value}",
        ]
        
        if self.scope_qualifier:
            lines[2] = f"scope: {self.scope.value}/{self.scope_qualifier}"
        
        lines.extend([
            f"tier: {self.tier.value.upper()}",
            f"created_at: {self.created_at.strftime('%Y-%m-%d')}",
            f"last_used: {self.last_used.strftime('%Y-%m-%d') if self.last_used else 'N/A'}",
            f"use_count: {self.use_count}",
            f"correction_count: {self.correction_count}",
            f"confidence: {self.confidence:.2f}",
            f"importance: {self.importance:.2f}",
            f"pinned: {str(self.pinned).lower()}",
            f"conflict_penalty: {self.conflict_penalty:.2f}",
            "sources:",
        ])
        
        for source in self.sources:
            lines.append(f"  - session: {source.session}")
            lines.append(f"    evidence: \"{source.evidence}\"")
            if source.task_id:
                lines.append(f"    task_id: \"{source.task_id}\"")
        
        lines.append("---")
        lines.append("")
        lines.append(self.content)
        
        return "\n".join(lines)


@dataclass
class MemoryQuery:
    """
    记忆查询
    
    用于检索记忆条目的查询结构。
    """
    query: str  # 查询文本
    scope: Optional[MemoryScope] = None  # 限定作用域
    scope_qualifier: Optional[str] = None  # 作用域限定符
    source_kind: Optional[MemorySourceKind] = None  # 限定来源类型
    content_type: Optional[MemoryContentType] = None  # 限定内容类型
    tkr_layer: Optional[TruthKnowledgeRetrieval] = None  # 限定 TKR 层
    tier: Optional[MemoryTier] = None  # 限定分层
    tags: Optional[List[str]] = None  # 限定标签
    min_confidence: float = 0.0  # 最低置信度
    limit: int = 10  # 返回数量限制
