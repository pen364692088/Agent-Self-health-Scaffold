"""
Memory Service

统一查询服务入口，对外提供简洁的 API。

Author: Memory Kernel
Created: 2026-03-15
Version: 1.0.0
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from pathlib import Path
import json

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from contract.memory.types import (
    MemoryRecord,
    MemoryScope,
    MemoryTier,
    MemorySourceKind,
    TruthKnowledgeRetrieval,
)
from core.memory.memory_search import (
    MemorySearchEngine,
    SearchParams,
    SearchResult,
)
from core.memory.memory_scope import MemoryScopeHandler, ScopeFilter
from core.memory.memory_ranker import MemoryRanker, RankedResult


@dataclass
class ServiceConfig:
    """
    服务配置
    
    定义服务行为参数。
    """
    default_top_k: int = 10
    max_top_k: int = 100
    enable_trace: bool = False


class MemoryService:
    """
    记忆服务
    
    统一查询入口，封装搜索引擎和排序器。
    不迁移、不删旧链、不接管 truth source、不强上 LanceDB。
    """
    
    def __init__(
        self,
        records: Optional[List[MemoryRecord]] = None,
        config: Optional[ServiceConfig] = None
    ):
        """
        初始化服务
        
        Args:
            records: 记忆记录列表（可选）
            config: 服务配置
        """
        self._config = config or ServiceConfig()
        self._engine = MemorySearchEngine(records)
        self._scope_handler = MemoryScopeHandler()
        self._ranker = MemoryRanker()
    
    def load_records(self, records: List[MemoryRecord]):
        """
        加载记录
        
        Args:
            records: 记忆记录列表
        """
        self._engine.load_records(records)
    
    def load_from_json(self, path: str):
        """
        从 JSON 文件加载记录
        
        Args:
            path: JSON 文件路径
        """
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        records = []
        for item in data.get("records", []):
            record = MemoryRecord.from_dict(item)
            records.append(record)
        
        self.load_records(records)
    
    def search(
        self,
        query: str,
        scope: Optional[str] = None,
        scope_qualifier: Optional[str] = None,
        include_global: bool = True,
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 10,
        trace: bool = False
    ) -> SearchResult:
        """
        统一查询入口
        
        Args:
            query: 关键词查询
            scope: 作用域过滤 (global/projects/domains)
            scope_qualifier: 作用域限定符
            include_global: 是否包含全局记录（当 scope 非空时）
            filters: 元数据过滤
            top_k: 返回数量
            trace: 是否输出追踪信息
        
        Returns:
            SearchResult: 包含 records 和 trace_info
        """
        # 限制 top_k
        top_k = min(top_k, self._config.max_top_k)
        
        # 构建搜索参数
        params = SearchParams(
            query=query,
            scope=MemoryScope(scope.lower()) if scope else None,
            scope_qualifier=scope_qualifier,
            include_global=include_global,
            filters=filters or {},
            top_k=top_k,
            trace=trace or self._config.enable_trace
        )
        
        return self._engine.search(params)
    
    def keyword_search(
        self,
        query: str,
        top_k: int = 10
    ) -> List[MemoryRecord]:
        """
        简化版关键词搜索
        
        Args:
            query: 查询关键词
            top_k: 返回数量
        
        Returns:
            记录列表
        """
        result = self.search(query=query, top_k=top_k)
        return result.records
    
    def search_by_scope(
        self,
        scope: str,
        qualifier: Optional[str] = None,
        include_global: bool = True,
        top_k: int = 10
    ) -> List[MemoryRecord]:
        """
        按作用域搜索
        
        Args:
            scope: 作用域 (global/projects/domains)
            qualifier: 限定符
            include_global: 是否包含全局记录
            top_k: 返回数量
        
        Returns:
            记录列表
        """
        result = self.search(
            query="",
            scope=scope,
            scope_qualifier=qualifier,
            include_global=include_global,
            top_k=top_k
        )
        return result.records
    
    def search_by_layer(
        self,
        layer: str,
        query: str = "",
        top_k: int = 10
    ) -> List[MemoryRecord]:
        """
        按层级搜索
        
        Args:
            layer: 层级 (truth/knowledge/retrieval)
            query: 查询关键词
            top_k: 返回数量
        
        Returns:
            记录列表
        """
        result = self.search(
            query=query,
            filters={"tkr_layer": layer},
            top_k=top_k
        )
        return result.records
    
    def search_by_tags(
        self,
        tags: List[str],
        query: str = "",
        top_k: int = 10
    ) -> List[MemoryRecord]:
        """
        按标签搜索
        
        Args:
            tags: 必须包含的标签
            query: 查询关键词
            top_k: 返回数量
        
        Returns:
            记录列表
        """
        result = self.search(
            query=query,
            filters={"tags": tags},
            top_k=top_k
        )
        return result.records
    
    def search_by_source(
        self,
        source_kind: str,
        query: str = "",
        top_k: int = 10
    ) -> List[MemoryRecord]:
        """
        按来源类型搜索
        
        Args:
            source_kind: 来源类型
            query: 查询关键词
            top_k: 返回数量
        
        Returns:
            记录列表
        """
        result = self.search(
            query=query,
            filters={"source_kind": source_kind},
            top_k=top_k
        )
        return result.records
    
    def advanced_search(
        self,
        query: str = "",
        scope: Optional[str] = None,
        scope_qualifier: Optional[str] = None,
        tkr_layer: Optional[str] = None,
        source_kind: Optional[str] = None,
        tier: Optional[str] = None,
        tags: Optional[List[str]] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        top_k: int = 10,
        trace: bool = False
    ) -> SearchResult:
        """
        高级搜索
        
        支持所有过滤条件的组合。
        
        Args:
            query: 关键词查询
            scope: 作用域
            scope_qualifier: 作用域限定符
            tkr_layer: 层级
            source_kind: 来源类型
            tier: 层级
            tags: 标签
            date_from: 起始日期
            date_to: 结束日期
            top_k: 返回数量
            trace: 是否输出追踪信息
        
        Returns:
            SearchResult
        """
        filters: Dict[str, Any] = {}
        
        if tkr_layer:
            filters["tkr_layer"] = tkr_layer
        if source_kind:
            filters["source_kind"] = source_kind
        if tier:
            filters["tier"] = tier
        if tags:
            filters["tags"] = tags
        if date_from:
            filters["date_from"] = date_from
        if date_to:
            filters["date_to"] = date_to
        
        return self.search(
            query=query,
            scope=scope,
            scope_qualifier=scope_qualifier,
            filters=filters,
            top_k=top_k,
            trace=trace
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取记录统计信息
        
        Returns:
            统计字典
        """
        return self._engine.get_statistics()
    
    def get_scope_distribution(self) -> Dict[str, int]:
        """
        获取作用域分布
        
        Returns:
            作用域分布字典
        """
        stats = self.get_statistics()
        return stats.get("by_scope", {})
    
    def get_layer_distribution(self) -> Dict[str, int]:
        """
        获取层级分布
        
        Returns:
            层级分布字典
        """
        stats = self.get_statistics()
        return stats.get("by_tkr_layer", {})
    
    def count(self) -> int:
        """
        获取记录总数
        
        Returns:
            记录数量
        """
        return len(self._engine._records)


# 便捷函数
def create_service(
    records: Optional[List[MemoryRecord]] = None,
    config: Optional[Dict[str, Any]] = None
) -> MemoryService:
    """
    创建记忆服务实例
    
    Args:
        records: 记忆记录列表
        config: 配置字典
    
    Returns:
        MemoryService 实例
    """
    service_config = None
    if config:
        service_config = ServiceConfig(
            default_top_k=config.get("default_top_k", 10),
            max_top_k=config.get("max_top_k", 100),
            enable_trace=config.get("enable_trace", False)
        )
    
    return MemoryService(records, service_config)
