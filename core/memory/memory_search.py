"""
Memory Search Engine

统一搜索引擎，支持关键词、元数据、作用域过滤。

Author: Memory Kernel
Created: 2026-03-15
Version: 1.0.0
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path
import re

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from contract.memory.types import (
    MemoryRecord,
    MemoryScope,
    MemoryTier,
    MemorySourceKind,
    TruthKnowledgeRetrieval,
)
from core.memory.memory_scope import MemoryScopeHandler, ScopeFilter
from core.memory.memory_ranker import MemoryRanker, RankedResult


@dataclass
class SearchParams:
    """
    搜索参数
    
    定义搜索请求的所有参数。
    """
    query: str = ""
    scope: Optional[MemoryScope] = None
    scope_qualifier: Optional[str] = None
    include_global: bool = True
    filters: Dict[str, Any] = field(default_factory=dict)
    top_k: int = 10
    trace: bool = False


@dataclass
class TraceInfo:
    """
    追踪信息
    
    记录搜索过程的详细信息。
    """
    total_records_scanned: int = 0
    keyword_filtered: int = 0
    scope_filtered: int = 0
    metadata_filtered: int = 0
    final_count: int = 0
    timing_ms: float = 0.0
    stages: List[Dict[str, Any]] = field(default_factory=list)
    
    def add_stage(self, name: str, count: int, timing_ms: float):
        """添加阶段信息"""
        self.stages.append({
            "name": name,
            "count": count,
            "timing_ms": timing_ms
        })


@dataclass
class SearchResult:
    """
    搜索结果
    
    包含记录、统计和追踪信息。
    """
    records: List[MemoryRecord]
    ranked_results: List[RankedResult]
    total_count: int
    trace_info: Optional[TraceInfo] = None


class MemorySearchEngine:
    """
    记忆搜索引擎
    
    支持关键词搜索、元数据过滤、作用域过滤和权威感知排序。
    """
    
    def __init__(
        self,
        records: Optional[List[MemoryRecord]] = None
    ):
        """
        初始化搜索引擎
        
        Args:
            records: 记忆记录列表（可选）
        """
        self._records: List[MemoryRecord] = records or []
        self._scope_handler = MemoryScopeHandler()
        self._ranker = MemoryRanker()
    
    def load_records(self, records: List[MemoryRecord]):
        """
        加载记录
        
        Args:
            records: 记忆记录列表
        """
        self._records = records
    
    def search(self, params: SearchParams) -> SearchResult:
        """
        执行搜索
        
        Args:
            params: 搜索参数
        
        Returns:
            SearchResult: 搜索结果
        """
        import time
        start_time = time.time()
        
        trace = TraceInfo() if params.trace else None
        
        # 阶段 1: 扫描全部记录
        candidates = self._records.copy()
        if trace:
            trace.total_records_scanned = len(candidates)
            trace.add_stage("scan", len(candidates), 0)
        
        # 阶段 2: 关键词过滤
        if params.query:
            candidates = self._filter_by_keyword(candidates, params.query)
            if trace:
                trace.keyword_filtered = len(candidates)
                trace.add_stage("keyword_filter", len(candidates), 0)
        
        # 阶段 3: 作用域过滤
        if params.scope:
            scope_filter = ScopeFilter(
                scope=params.scope,
                qualifier=params.scope_qualifier,
                include_global=params.include_global
            )
            candidates = self._scope_handler.filter_records(candidates, scope_filter)
            if trace:
                trace.scope_filtered = len(candidates)
                trace.add_stage("scope_filter", len(candidates), 0)
        
        # 阶段 4: 元数据过滤
        if params.filters:
            candidates = self._filter_by_metadata(candidates, params.filters)
            if trace:
                trace.metadata_filtered = len(candidates)
                trace.add_stage("metadata_filter", len(candidates), 0)
        
        # 阶段 5: 排序
        ranked_results = self._ranker.rank_records(
            candidates,
            query=params.query,
            top_k=params.top_k
        )
        
        # 提取记录
        final_records = [r.record for r in ranked_results]
        
        # 完成追踪
        elapsed_ms = (time.time() - start_time) * 1000
        
        if trace:
            trace.final_count = len(final_records)
            trace.timing_ms = elapsed_ms
            trace.add_stage("ranking", len(ranked_results), elapsed_ms)
        
        return SearchResult(
            records=final_records,
            ranked_results=ranked_results,
            total_count=len(candidates),
            trace_info=trace
        )
    
    def _filter_by_keyword(
        self,
        records: List[MemoryRecord],
        query: str
    ) -> List[MemoryRecord]:
        """
        关键词过滤
        
        Args:
            records: 记录列表
            query: 查询关键词
        
        Returns:
            过滤后的记录
        """
        query_lower = query.lower()
        query_terms = set(re.findall(r'\w+', query_lower))
        
        if not query_terms:
            return records
        
        def matches(record: MemoryRecord) -> bool:
            # 检查标题
            if record.title:
                title_terms = set(re.findall(r'\w+', record.title.lower()))
                if query_terms & title_terms:
                    return True
            
            # 检查内容
            if record.content:
                content_terms = set(re.findall(r'\w+', record.content.lower()))
                if query_terms & content_terms:
                    return True
            
            # 检查标签
            if record.tags:
                tag_set = set(t.lower() for t in record.tags)
                if query_terms & tag_set:
                    return True
            
            return False
        
        return [r for r in records if matches(r)]
    
    def _filter_by_metadata(
        self,
        records: List[MemoryRecord],
        filters: Dict[str, Any]
    ) -> List[MemoryRecord]:
        """
        元数据过滤
        
        Args:
            records: 记录列表
            filters: 过滤条件
        
        Returns:
            过滤后的记录
        """
        candidates = records
        
        # 作用域过滤
        if "scope" in filters:
            scope_value = filters["scope"]
            if isinstance(scope_value, str):
                scope = MemoryScope(scope_value.lower())
            else:
                scope = scope_value
            candidates = [r for r in candidates if r.scope == scope]
        
        # 层级过滤
        if "tkr_layer" in filters:
            layer_value = filters["tkr_layer"]
            if isinstance(layer_value, str):
                layer = TruthKnowledgeRetrieval(layer_value.lower())
            else:
                layer = layer_value
            candidates = [r for r in candidates if r.tkr_layer == layer]
        
        # 来源类型过滤
        if "source_kind" in filters:
            kind_value = filters["source_kind"]
            if isinstance(kind_value, str):
                kind = MemorySourceKind(kind_value.lower())
            else:
                kind = kind_value
            candidates = [r for r in candidates if r.source_kind == kind]
        
        # 层级过滤
        if "tier" in filters:
            tier_value = filters["tier"]
            if isinstance(tier_value, str):
                tier = MemoryTier(tier_value.lower())
            else:
                tier = tier_value
            candidates = [r for r in candidates if r.tier == tier]
        
        # 标签过滤
        if "tags" in filters:
            required_tags = set(filters["tags"])
            candidates = [
                r for r in candidates
                if required_tags.issubset(set(r.tags or []))
            ]
        
        # 日期范围过滤
        if "date_from" in filters:
            date_from = filters["date_from"]
            if isinstance(date_from, str):
                date_from = datetime.fromisoformat(date_from.replace("Z", "+00:00"))
            candidates = [
                r for r in candidates
                if r.created_at and r.created_at >= date_from
            ]
        
        if "date_to" in filters:
            date_to = filters["date_to"]
            if isinstance(date_to, str):
                date_to = datetime.fromisoformat(date_to.replace("Z", "+00:00"))
            candidates = [
                r for r in candidates
                if r.created_at and r.created_at <= date_to
            ]
        
        return candidates
    
    def keyword_search(
        self,
        query: str,
        top_k: int = 10
    ) -> SearchResult:
        """
        简化版关键词搜索
        
        Args:
            query: 查询关键词
            top_k: 返回数量
        
        Returns:
            SearchResult
        """
        params = SearchParams(query=query, top_k=top_k)
        return self.search(params)
    
    def scope_search(
        self,
        scope: MemoryScope,
        qualifier: Optional[str] = None,
        include_global: bool = True,
        top_k: int = 10
    ) -> SearchResult:
        """
        按作用域搜索
        
        Args:
            scope: 作用域
            qualifier: 限定符
            include_global: 是否包含全局记录
            top_k: 返回数量
        
        Returns:
            SearchResult
        """
        params = SearchParams(
            scope=scope,
            scope_qualifier=qualifier,
            include_global=include_global,
            top_k=top_k
        )
        return self.search(params)
    
    def filtered_search(
        self,
        query: str,
        filters: Dict[str, Any],
        top_k: int = 10
    ) -> SearchResult:
        """
        带元数据过滤的搜索
        
        Args:
            query: 查询关键词
            filters: 过滤条件
            top_k: 返回数量
        
        Returns:
            SearchResult
        """
        params = SearchParams(query=query, filters=filters, top_k=top_k)
        return self.search(params)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取记录统计信息
        
        Returns:
            统计字典
        """
        if not self._records:
            return {"total": 0}
        
        stats = {
            "total": len(self._records),
            "by_scope": {},
            "by_tkr_layer": {},
            "by_source_kind": {},
            "by_tier": {},
        }
        
        for record in self._records:
            # 作用域分布
            scope_name = record.scope.value
            stats["by_scope"][scope_name] = stats["by_scope"].get(scope_name, 0) + 1
            
            # 层级分布
            layer_name = record.tkr_layer.value
            stats["by_tkr_layer"][layer_name] = stats["by_tkr_layer"].get(layer_name, 0) + 1
            
            # 来源类型分布
            kind_name = record.source_kind.value
            stats["by_source_kind"][kind_name] = stats["by_source_kind"].get(kind_name, 0) + 1
            
            # 层级分布
            tier_name = record.tier.value
            stats["by_tier"][tier_name] = stats["by_tier"].get(tier_name, 0) + 1
        
        return stats


def create_search_engine(records: Optional[List[MemoryRecord]] = None) -> MemorySearchEngine:
    """
    便捷函数：创建搜索引擎
    
    Args:
        records: 记忆记录列表
    
    Returns:
        MemorySearchEngine 实例
    """
    return MemorySearchEngine(records)
