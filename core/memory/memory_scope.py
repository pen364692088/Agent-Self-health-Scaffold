"""
Memory Scope Handler

处理记忆作用域过滤逻辑。

Author: Memory Kernel
Created: 2026-03-15
Version: 1.0.0
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any, Set
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from contract.memory.types import (
    MemoryRecord,
    MemoryScope,
)


@dataclass
class ScopeFilter:
    """
    作用域过滤器配置
    
    定义如何过滤记忆条目的作用域。
    """
    scope: MemoryScope
    qualifier: Optional[str] = None  # 项目名或域名
    include_global: bool = True  # 是否包含 GLOBAL 作用域


class MemoryScopeHandler:
    """
    作用域处理器
    
    处理记忆条目的作用域过滤逻辑。
    """
    
    def __init__(self):
        """初始化作用域处理器"""
        self._project_indicators = [
            "projects", "project", "openemotion", "emotiond", "openclaw-core"
        ]
        self._domain_indicators = [
            "domains", "domain", "infra", "security", "frontend", "backend"
        ]
    
    def infer_scope(self, path: str) -> tuple[MemoryScope, Optional[str]]:
        """
        从路径推断作用域
        
        Args:
            path: 文件路径
        
        Returns:
            (scope, qualifier): 作用域和限定符
        """
        path_lower = path.lower()
        
        # 检查项目特征
        for indicator in self._project_indicators:
            if indicator in path_lower:
                # 尝试提取项目名
                return MemoryScope.PROJECTS, indicator.replace("-", "_")
        
        # 检查领域特征 - 需要在路径中提取具体的领域名
        if "/domains/" in path_lower or "\\domains\\" in path_lower:
            # 尝试提取域名
            parts = path_lower.replace("\\", "/").split("/domains/")
            if len(parts) > 1:
                # 提取 domains/ 后面的第一部分作为域名
                after_domains = parts[1].split("/")[0]
                if after_domains:
                    return MemoryScope.DOMAINS, after_domains
        
        # 备用检查
        for indicator in self._domain_indicators:
            if indicator in path_lower and indicator not in ["domains", "domain"]:
                return MemoryScope.DOMAINS, indicator
        
        return MemoryScope.GLOBAL, None
    
    def matches_filter(
        self,
        record: MemoryRecord,
        scope_filter: Optional[ScopeFilter] = None
    ) -> bool:
        """
        检查记录是否匹配作用域过滤器
        
        Args:
            record: 记忆记录
            scope_filter: 作用域过滤器
        
        Returns:
            是否匹配
        """
        if scope_filter is None:
            return True
        
        # GLOBAL 记录处理
        if record.scope == MemoryScope.GLOBAL:
            return scope_filter.include_global
        
        # 匹配作用域
        if record.scope != scope_filter.scope:
            return False
        
        # 匹配限定符
        if scope_filter.qualifier is not None:
            if record.scope_qualifier != scope_filter.qualifier:
                return False
        
        return True
    
    def filter_records(
        self,
        records: List[MemoryRecord],
        scope_filter: Optional[ScopeFilter] = None
    ) -> List[MemoryRecord]:
        """
        过滤记录列表
        
        Args:
            records: 记录列表
            scope_filter: 作用域过滤器
        
        Returns:
            过滤后的记录列表
        """
        if scope_filter is None:
            return records
        
        return [r for r in records if self.matches_filter(r, scope_filter)]
    
    def create_filter(
        self,
        scope: MemoryScope,
        qualifier: Optional[str] = None,
        include_global: bool = True
    ) -> ScopeFilter:
        """
        创建作用域过滤器
        
        Args:
            scope: 目标作用域
            qualifier: 限定符
            include_global: 是否包含全局记录
        
        Returns:
            ScopeFilter 实例
        """
        return ScopeFilter(
            scope=scope,
            qualifier=qualifier,
            include_global=include_global
        )
    
    def get_scope_distribution(
        self,
        records: List[MemoryRecord]
    ) -> Dict[str, int]:
        """
        获取作用域分布统计
        
        Args:
            records: 记录列表
        
        Returns:
            作用域分布字典
        """
        distribution: Dict[str, int] = {}
        
        for record in records:
            scope_name = record.scope.value
            distribution[scope_name] = distribution.get(scope_name, 0) + 1
        
        return distribution
    
    def get_qualifier_distribution(
        self,
        records: List[MemoryRecord],
        scope: MemoryScope
    ) -> Dict[str, int]:
        """
        获取限定符分布统计
        
        Args:
            records: 记录列表
            scope: 目标作用域
        
        Returns:
            限定符分布字典
        """
        distribution: Dict[str, int] = {}
        
        for record in records:
            if record.scope == scope and record.scope_qualifier:
                qualifier = record.scope_qualifier
                distribution[qualifier] = distribution.get(qualifier, 0) + 1
        
        return distribution


def create_scope_filter(
    scope: str,
    qualifier: Optional[str] = None,
    include_global: bool = True
) -> ScopeFilter:
    """
    便捷函数：创建作用域过滤器
    
    Args:
        scope: 作用域名称 (global/projects/domains)
        qualifier: 限定符
        include_global: 是否包含全局记录
    
    Returns:
        ScopeFilter 实例
    """
    scope_enum = MemoryScope(scope.lower())
    return ScopeFilter(
        scope=scope_enum,
        qualifier=qualifier,
        include_global=include_global
    )
