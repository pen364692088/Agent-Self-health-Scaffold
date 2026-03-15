"""
Memory Ranker

实现权威感知的排序逻辑。

Author: Memory Kernel
Created: 2026-03-15
Version: 1.0.0
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from pathlib import Path
import re

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from contract.memory.types import (
    MemoryRecord,
    MemoryScope,
    MemoryTier,
    TruthKnowledgeRetrieval,
    MemorySourceKind,
)


@dataclass
class RankingConfig:
    """
    排序配置
    
    定义排序权重和规则。
    """
    # 层级权重 (Truth > Knowledge > Retrieval)
    layer_weights: Dict[str, float] = field(default_factory=lambda: {
        TruthKnowledgeRetrieval.TRUTH.value: 3.0,
        TruthKnowledgeRetrieval.KNOWLEDGE.value: 2.0,
        TruthKnowledgeRetrieval.RETRIEVAL.value: 1.0,
    })
    
    # 作用域权重 (GLOBAL > PROJECTS > DOMAINS for authority)
    scope_weights: Dict[str, float] = field(default_factory=lambda: {
        MemoryScope.GLOBAL.value: 1.0,
        MemoryScope.PROJECTS.value: 0.8,
        MemoryScope.DOMAINS.value: 0.6,
    })
    
    # 新鲜度衰减参数
    freshness_half_life_days: float = 30.0  # 半衰期
    
    # 来源可信度权重
    source_kind_weights: Dict[str, float] = field(default_factory=lambda: {
        MemorySourceKind.DECISION_LOG.value: 2.0,
        MemorySourceKind.POLICY.value: 1.8,
        MemorySourceKind.RULE.value: 1.8,
        MemorySourceKind.TECHNICAL_NOTE.value: 1.5,
        MemorySourceKind.SESSION_LOG.value: 1.0,
        MemorySourceKind.RETRIEVAL_EVENT.value: 0.8,
        MemorySourceKind.TEMPLATE.value: 0.5,
    })
    
    # 关键词匹配权重
    keyword_title_weight: float = 3.0
    keyword_content_weight: float = 1.0
    keyword_tag_weight: float = 2.0


@dataclass
class RankedResult:
    """
    排序结果
    
    包含记录和排序分数。
    """
    record: MemoryRecord
    score: float
    score_breakdown: Dict[str, float] = field(default_factory=dict)


class MemoryRanker:
    """
    记忆排序器
    
    实现权威感知的多因素排序。
    """
    
    def __init__(self, config: Optional[RankingConfig] = None):
        """
        初始化排序器
        
        Args:
            config: 排序配置
        """
        self.config = config or RankingConfig()
    
    def compute_score(
        self,
        record: MemoryRecord,
        query: Optional[str] = None
    ) -> RankedResult:
        """
        计算记录的综合分数
        
        Args:
            record: 记忆记录
            query: 查询关键词（可选）
        
        Returns:
            RankedResult: 排序结果
        """
        breakdown: Dict[str, float] = {}
        
        # 1. 层级分数
        layer_score = self.config.layer_weights.get(
            record.tkr_layer.value, 1.0
        )
        breakdown["layer"] = layer_score
        
        # 2. 作用域权威分数
        scope_score = self.config.scope_weights.get(
            record.scope.value, 1.0
        )
        breakdown["scope"] = scope_score
        
        # 3. 新鲜度分数
        freshness_score = self._compute_freshness(record)
        breakdown["freshness"] = freshness_score
        
        # 4. 来源可信度分数
        source_score = self.config.source_kind_weights.get(
            record.source_kind.value, 1.0
        )
        breakdown["source"] = source_score
        
        # 5. 关键词匹配分数
        keyword_score = 0.0
        if query:
            keyword_score = self._compute_keyword_match(record, query)
        breakdown["keyword"] = keyword_score
        
        # 综合分数（加权平均）
        total = (
            layer_score * 0.3 +
            scope_score * 0.2 +
            freshness_score * 0.2 +
            source_score * 0.2 +
            keyword_score * 0.1
        )
        breakdown["total"] = total
        
        return RankedResult(
            record=record,
            score=total,
            score_breakdown=breakdown
        )
    
    def _compute_freshness(self, record: MemoryRecord) -> float:
        """
        计算新鲜度分数
        
        使用指数衰减模型。
        """
        # 优先使用 last_used，其次 created_at
        timestamp = record.last_used or record.created_at
        
        if timestamp is None:
            return 0.5  # 默认中等分数
        
        now = datetime.now()
        if timestamp.tzinfo:
            from datetime import timezone
            now = datetime.now(timezone.utc)
        
        age_days = (now - timestamp).total_seconds() / 86400
        half_life = self.config.freshness_half_life_days
        
        # 指数衰减: score = 2^(-age/half_life)
        freshness = 2 ** (-age_days / half_life)
        
        return max(0.0, min(1.0, freshness))
    
    def _compute_keyword_match(
        self,
        record: MemoryRecord,
        query: str
    ) -> float:
        """
        计算关键词匹配分数
        
        Args:
            record: 记忆记录
            query: 查询关键词
        
        Returns:
            匹配分数 (0.0 - 1.0)
        """
        query_lower = query.lower()
        query_terms = set(re.findall(r'\w+', query_lower))
        
        if not query_terms:
            return 0.0
        
        match_count = 0
        total_weight = 0.0
        
        # 标题匹配
        if record.title:
            title_terms = set(re.findall(r'\w+', record.title.lower()))
            title_matches = len(query_terms & title_terms)
            match_count += title_matches * self.config.keyword_title_weight
            total_weight += len(query_terms) * self.config.keyword_title_weight
        
        # 内容匹配
        if record.content:
            content_terms = set(re.findall(r'\w+', record.content.lower()))
            content_matches = len(query_terms & content_terms)
            match_count += content_matches * self.config.keyword_content_weight
            total_weight += len(query_terms) * self.config.keyword_content_weight
        
        # 标签匹配
        if record.tags:
            tag_set = set(t.lower() for t in record.tags)
            tag_matches = len(query_terms & tag_set)
            match_count += tag_matches * self.config.keyword_tag_weight
            total_weight += len(query_terms) * self.config.keyword_tag_weight
        
        if total_weight == 0:
            return 0.0
        
        return match_count / total_weight
    
    def rank_records(
        self,
        records: List[MemoryRecord],
        query: Optional[str] = None,
        top_k: int = 10
    ) -> List[RankedResult]:
        """
        对记录列表进行排序
        
        Args:
            records: 记录列表
            query: 查询关键词
            top_k: 返回数量
        
        Returns:
            排序后的结果列表
        """
        results = [
            self.compute_score(r, query)
            for r in records
        ]
        
        # 按分数降序排序
        results.sort(key=lambda x: x.score, reverse=True)
        
        # 限制返回数量
        return results[:top_k]
    
    def re_rank_by_authority(
        self,
        results: List[RankedResult],
        authority_context: Optional[str] = None
    ) -> List[RankedResult]:
        """
        根据权威上下文重排序
        
        如果提供了权威上下文（如项目名），
        提升与该上下文相关的记录。
        
        Args:
            results: 已排序的结果
            authority_context: 权威上下文
        
        Returns:
            重排序后的结果
        """
        if not authority_context:
            return results
        
        context_lower = authority_context.lower()
        
        # 对匹配权威上下文的记录加分
        for result in results:
            record = result.record
            
            # 检查作用域限定符
            if record.scope_qualifier:
                if context_lower in record.scope_qualifier.lower():
                    result.score += 0.5
                    result.score_breakdown["authority_boost"] = 0.5
            
            # 检查路径
            if record.source_file:
                if context_lower in record.source_file.lower():
                    result.score += 0.3
                    result.score_breakdown["path_boost"] = 0.3
        
        # 重新排序
        results.sort(key=lambda x: x.score, reverse=True)
        
        return results


def create_ranker(config: Optional[Dict[str, Any]] = None) -> MemoryRanker:
    """
    便捷函数：创建排序器
    
    Args:
        config: 配置字典
    
    Returns:
        MemoryRanker 实例
    """
    if config is None:
        return MemoryRanker()
    
    ranking_config = RankingConfig()
    
    if "layer_weights" in config:
        ranking_config.layer_weights.update(config["layer_weights"])
    if "scope_weights" in config:
        ranking_config.scope_weights.update(config["scope_weights"])
    if "freshness_half_life_days" in config:
        ranking_config.freshness_half_life_days = config["freshness_half_life_days"]
    
    return MemoryRanker(ranking_config)
