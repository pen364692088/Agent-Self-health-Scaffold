"""
Memory Contract - Policy Definitions

Memory Kernel 策略定义。
定义记忆生命周期管理和冲突解决策略。

Author: Memory Kernel
Created: 2026-03-15
Version: 1.0.0
"""

from dataclasses import dataclass, field
from datetime import timedelta
from enum import Enum
from typing import Optional, List, Callable, Any


class RetentionAction(str, Enum):
    """
    保留策略动作
    """
    KEEP = "keep"  # 保留
    ARCHIVE = "archive"  # 归档
    DELETE = "delete"  # 删除
    REVIEW = "review"  # 人工审核


class ConflictStrategy(str, Enum):
    """
    冲突解决策略
    """
    NEWEST_WINS = "newest_wins"  # 最新的胜出
    HIGHEST_CONFIDENCE = "highest_confidence"  # 最高置信度胜出
    HIGHEST_IMPORTANCE = "highest_importance"  # 最高重要性胜出
    MOST_USED = "most_used"  # 最常使用的胜出
    SCOPE_PRIORITY = "scope_priority"  # 作用域优先级（global > projects > domains）
    MANUAL = "manual"  # 人工解决
    MERGE = "merge"  # 合并


class ConflictSeverity(str, Enum):
    """
    冲突严重程度
    """
    LOW = "low"  # 轻微冲突，可自动解决
    MEDIUM = "medium"  # 中等冲突，需记录
    HIGH = "high"  # 严重冲突，需人工介入
    CRITICAL = "critical"  # 关键冲突，必须人工解决


@dataclass
class RetentionRule:
    """
    保留规则
    
    定义在什么条件下执行什么动作。
    """
    name: str  # 规则名称
    condition: Callable[[Any], bool]  # 条件函数
    action: RetentionAction  # 执行动作
    priority: int = 0  # 优先级（越高越先执行）
    description: str = ""  # 规则描述


@dataclass
class RetentionPolicy:
    """
    保留策略
    
    定义记忆条目的生命周期管理规则。
    基于 MAINTENANCE.md 中的维护流程设计。
    """
    # 时间阈值
    hot_max_age: timedelta = field(default_factory=lambda: timedelta(days=90))  # HOT 最长保留
    warm_max_age: timedelta = field(default_factory=lambda: timedelta(days=180))  # WARM 最长保留
    cold_max_age: timedelta = field(default_factory=lambda: timedelta(days=365))  # COLD 最长保留
    
    # 使用阈值
    hot_min_use_count: int = 5  # HOT 最低使用次数
    warm_min_use_count: int = 2  # WARM 最低使用次数
    
    # 分数阈值
    hot_min_score: float = 7.0  # HOT 最低分数
    warm_min_score: float = 3.0  # WARM 最低分数
    
    # 纠正阈值
    max_correction_count: int = 10  # 最大纠正次数（超过则降级或删除）
    
    # 冲突惩罚阈值
    max_conflict_penalty: float = 5.0  # 最大冲突惩罚
    
    # 热启动配置（参考 MAINTENANCE.md v1.2.7）
    warmup_days: int = 7  # 热启动天数
    baseline_min_days: int = 7  # 基线最小天数
    
    # 漂移检测配置（参考 MAINTENANCE.md v1.2.6）
    bucket_a_ratio_threshold: float = 0.70  # A 桶占比阈值
    expected_ratio_threshold: float = 0.50  # expected 占比阈值
    
    # 绝对下限保护（参考 MAINTENANCE.md v1.2.7）
    bucket_a_abs_min: float = 0.10  # A 桶绝对下限
    expected_abs_min: float = 0.50  # expected 绝对下限
    
    def evaluate_retention(self, record: Any) -> RetentionAction:
        """
        评估记忆条目的保留动作
        
        Args:
            record: MemoryRecord 实例
            
        Returns:
            RetentionAction: 建议的动作
        """
        from datetime import datetime
        
        # 计算年龄
        age = datetime.now() - record.created_at
        age_days = age.days
        
        # 检查纠正次数
        if record.correction_count > self.max_correction_count:
            return RetentionAction.REVIEW
        
        # 检查冲突惩罚
        if record.conflict_penalty > self.max_conflict_penalty:
            return RetentionAction.REVIEW
        
        # 根据分层评估
        if record.tier.value == "hot":
            if age_days > self.hot_max_age.days and record.use_count < self.hot_min_use_count:
                return RetentionAction.ARCHIVE
            return RetentionAction.KEEP
        
        elif record.tier.value == "warm":
            if age_days > self.warm_max_age.days and record.use_count < self.warm_min_use_count:
                return RetentionAction.ARCHIVE
            return RetentionAction.KEEP
        
        elif record.tier.value == "cold":
            if age_days > self.cold_max_age.days:
                return RetentionAction.DELETE
            return RetentionAction.ARCHIVE
        
        elif record.tier.value == "archived":
            return RetentionAction.KEEP
        
        return RetentionAction.KEEP
    
    def should_trigger_baseline_reset(self, old_config_hash: str, new_config_hash: str) -> bool:
        """
        判断是否应该触发基线重置
        
        参考 MAINTENANCE.md v1.2.8 "baseline 来源审计"
        """
        return old_config_hash != new_config_hash
    
    def is_warmup_period(self, baseline_days: int) -> bool:
        """
        判断是否在热启动期
        
        参考 MAINTENANCE.md v1.2.7
        """
        return baseline_days < self.warmup_days


@dataclass
class ConflictRecord:
    """
    冲突记录
    
    记录记忆条目之间的冲突信息。
    """
    id: str  # 冲突 ID
    records: List[str]  # 冲突的记忆条目 ID 列表
    field: str  # 冲突的字段
    values: List[Any]  # 冲突的值
    severity: ConflictSeverity  # 严重程度
    strategy: ConflictStrategy  # 解决策略
    resolution: Optional[str] = None  # 解决结果
    resolved_at: Optional[str] = None  # 解决时间
    evidence: str = ""  # 冲突证据


@dataclass
class ConflictResolutionPolicy:
    """
    冲突解决策略
    
    定义如何处理记忆条目之间的冲突。
    """
    # 默认策略
    default_strategy: ConflictStrategy = ConflictStrategy.NEWEST_WINS
    
    # 按字段定制策略
    field_strategies: dict = field(default_factory=lambda: {
        "content": ConflictStrategy.MERGE,  # 内容冲突尝试合并
        "confidence": ConflictStrategy.HIGHEST_CONFIDENCE,
        "importance": ConflictStrategy.HIGHEST_IMPORTANCE,
        "scope": ConflictStrategy.SCOPE_PRIORITY,
    })
    
    # 按作用域优先级
    scope_priority: dict = field(default_factory=lambda: {
        "global": 3,
        "projects": 2,
        "domains": 1,
    })
    
    # 自动解决阈值
    auto_resolve_threshold: ConflictSeverity = ConflictSeverity.MEDIUM  # 此级别以下自动解决
    
    # 审核队列
    review_queue: List[ConflictRecord] = field(default_factory=list)
    
    def resolve(self, conflict: ConflictRecord, records: List[Any]) -> str:
        """
        解决冲突
        
        Args:
            conflict: 冲突记录
            records: 冲突的记忆条目列表
            
        Returns:
            str: 胜出者 ID 或合并结果
        """
        strategy = conflict.strategy
        
        if strategy == ConflictStrategy.NEWEST_WINS:
            return self._resolve_by_newest(records)
        
        elif strategy == ConflictStrategy.HIGHEST_CONFIDENCE:
            return self._resolve_by_confidence(records)
        
        elif strategy == ConflictStrategy.HIGHEST_IMPORTANCE:
            return self._resolve_by_importance(records)
        
        elif strategy == ConflictStrategy.MOST_USED:
            return self._resolve_by_use_count(records)
        
        elif strategy == ConflictStrategy.SCOPE_PRIORITY:
            return self._resolve_by_scope(records)
        
        elif strategy == ConflictStrategy.MANUAL:
            return self._resolve_manually(conflict)
        
        elif strategy == ConflictStrategy.MERGE:
            return self._resolve_by_merge(records, conflict.field)
        
        return records[0].id  # 默认返回第一个
    
    def _resolve_by_newest(self, records: List[Any]) -> str:
        """最新的胜出"""
        sorted_records = sorted(records, key=lambda r: r.created_at, reverse=True)
        return sorted_records[0].id
    
    def _resolve_by_confidence(self, records: List[Any]) -> str:
        """最高置信度胜出"""
        sorted_records = sorted(records, key=lambda r: r.confidence, reverse=True)
        return sorted_records[0].id
    
    def _resolve_by_importance(self, records: List[Any]) -> str:
        """最高重要性胜出"""
        sorted_records = sorted(records, key=lambda r: r.importance, reverse=True)
        return sorted_records[0].id
    
    def _resolve_by_use_count(self, records: List[Any]) -> str:
        """最常使用的胜出"""
        sorted_records = sorted(records, key=lambda r: r.use_count, reverse=True)
        return sorted_records[0].id
    
    def _resolve_by_scope(self, records: List[Any]) -> str:
        """作用域优先级"""
        def scope_score(record):
            scope = record.scope.value if hasattr(record.scope, 'value') else str(record.scope)
            return self.scope_priority.get(scope, 0)
        
        sorted_records = sorted(records, key=scope_score, reverse=True)
        return sorted_records[0].id
    
    def _resolve_manually(self, conflict: ConflictRecord) -> str:
        """人工解决 - 加入审核队列"""
        self.review_queue.append(conflict)
        return f"PENDING_REVIEW:{conflict.id}"
    
    def _resolve_by_merge(self, records: List[Any], field: str) -> str:
        """合并策略"""
        if field == "content":
            # 内容合并：拼接所有内容
            merged_content = "\n\n---\n\n".join([
                f"[{r.id}] {r.content}" 
                for r in records
            ])
            return f"MERGED:{merged_content[:200]}..."
        
        return records[0].id
    
    def detect_conflict(self, records: List[Any], field: str) -> Optional[ConflictRecord]:
        """
        检测冲突
        
        Args:
            records: 待检测的记忆条目列表
            field: 检测的字段
            
        Returns:
            ConflictRecord 或 None
        """
        if len(records) < 2:
            return None
        
        # 获取值
        values = []
        for r in records:
            value = getattr(r, field, None)
            values.append(value)
        
        # 检查是否冲突
        unique_values = set(str(v) for v in values if v is not None)
        if len(unique_values) <= 1:
            return None  # 无冲突
        
        # 确定策略
        strategy = self.field_strategies.get(field, self.default_strategy)
        
        # 确定严重程度
        severity = self._determine_severity(field, values)
        
        return ConflictRecord(
            id=f"conflict_{field}_{records[0].id}",
            records=[r.id for r in records],
            field=field,
            values=values,
            severity=severity,
            strategy=strategy,
            evidence=f"Field '{field}' has conflicting values: {unique_values}"
        )
    
    def _determine_severity(self, field: str, values: List[Any]) -> ConflictSeverity:
        """
        确定冲突严重程度
        """
        # 关键字段冲突更严重
        critical_fields = ["scope", "status", "content_type"]
        if field in critical_fields:
            return ConflictSeverity.HIGH
        
        # 重要字段冲突中等
        important_fields = ["confidence", "importance", "tier"]
        if field in important_fields:
            return ConflictSeverity.MEDIUM
        
        # 其他字段冲突轻微
        return ConflictSeverity.LOW
    
    def get_review_queue_size(self) -> int:
        """获取审核队列大小"""
        return len(self.review_queue)
    
    def clear_reviewed(self, conflict_ids: List[str]) -> int:
        """清除已审核的冲突"""
        before = len(self.review_queue)
        self.review_queue = [
            c for c in self.review_queue 
            if c.id not in conflict_ids
        ]
        return before - len(self.review_queue)


@dataclass
class MemoryPolicyBundle:
    """
    策略包
    
    包含保留策略和冲突解决策略的完整配置。
    """
    retention: RetentionPolicy = field(default_factory=RetentionPolicy)
    conflict_resolution: ConflictResolutionPolicy = field(default_factory=ConflictResolutionPolicy)
    
    # 配置哈希（参考 MAINTENANCE.md v1.2.4）
    config_hash: str = ""
    version: str = "1.0.0"
    
    def calculate_config_hash(self) -> str:
        """
        计算配置哈希
        
        只包含有效配置，不包含时间戳、文件路径等。
        参考 MAINTENANCE.md v1.2.4 config_hash 计算规则。
        """
        import hashlib
        import json
        
        payload = {
            "retention": {
                "hot_max_age_days": self.retention.hot_max_age.days,
                "warm_max_age_days": self.retention.warm_max_age.days,
                "cold_max_age_days": self.retention.cold_max_age.days,
                "hot_min_use_count": self.retention.hot_min_use_count,
                "warm_min_use_count": self.retention.warm_min_use_count,
                "hot_min_score": self.retention.hot_min_score,
                "warm_min_score": self.retention.warm_min_score,
            },
            "conflict": {
                "default_strategy": self.conflict_resolution.default_strategy.value,
            },
            "version": self.version,
        }
        
        hash_value = hashlib.md5(
            json.dumps(payload, sort_keys=True).encode()
        ).hexdigest()[:8]
        
        self.config_hash = hash_value
        return hash_value
