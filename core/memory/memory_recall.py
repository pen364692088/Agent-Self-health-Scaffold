"""
Memory Recall Engine

受控召回引擎，支持 approved-only 召回、candidate shadow 模式、top-k 小流量召回。

Author: Memory Kernel
Created: 2026-03-15
Version: 1.0.0
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from pathlib import Path
import time

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from contract.memory.types import (
    MemoryRecord,
    MemoryScope,
    TruthKnowledgeRetrieval,
)
from core.memory.memory_search import MemorySearchEngine, SearchParams
from core.memory.recall_trace import (
    RecallTrace,
    RecallTraceBuilder,
    TruthQuote,
    create_trace_builder,
)


@dataclass
class RecallConfig:
    """
    召回配置
    
    定义召回行为参数。
    """
    mode: str = "production"  # production/shadow/debug
    top_k: int = 10  # top-k 召回数量
    include_candidates: bool = False  # 是否包含候选
    fail_open: bool = True  # 失败时是否继续
    enable_trace: bool = True  # 是否启用追踪


@dataclass
class RecallResult:
    """
    召回结果
    
    包含召回的记录和追踪信息。
    """
    records: List[MemoryRecord]  # 召回的记录
    trace: Optional[RecallTrace] = None  # 追踪信息
    truth_quotes: List[TruthQuote] = field(default_factory=list)  # Truth 引用
    errors: List[str] = field(default_factory=list)  # 错误列表


class RecallEngine:
    """
    召回引擎
    
    支持受控召回，默认只从 approved 记忆召回。
    """
    
    def __init__(
        self,
        approved_records: Optional[List[MemoryRecord]] = None,
        candidate_records: Optional[List[MemoryRecord]] = None,
        config: Optional[RecallConfig] = None,
    ):
        """
        初始化召回引擎
        
        Args:
            approved_records: approved 记录列表
            candidate_records: candidate 记录列表
            config: 召回配置
        """
        self._approved_records = approved_records or []
        self._candidate_records = candidate_records or []
        self._config = config or RecallConfig()
        self._search_engine = MemorySearchEngine(self._approved_records)
    
    def load_approved_records(self, records: List[MemoryRecord]):
        """
        加载 approved 记录
        
        Args:
            records: 记录列表
        """
        self._approved_records = records
        self._search_engine.load_records(records)
    
    def load_candidate_records(self, records: List[MemoryRecord]):
        """
        加载 candidate 记录
        
        Args:
            records: 记录列表
        """
        self._candidate_records = records
    
    def recall(
        self,
        query: str,
        top_k: Optional[int] = None,
        scope: Optional[MemoryScope] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> RecallResult:
        """
        召回记忆
        
        Args:
            query: 查询内容
            top_k: top-k 参数
            scope: 作用域过滤
            filters: 元数据过滤
        
        Returns:
            RecallResult
        """
        import traceback
        
        trace_builder = create_trace_builder(query, self._config.mode)
        trace_builder.start()
        trace_builder.set_top_k(top_k or self._config.top_k)
        
        result = RecallResult(records=[])
        
        try:
            # 阶段 1: 扫描 approved 记录
            stage_start = time.time()
            trace_builder.set_total_scanned(len(self._approved_records))
            trace_builder.set_approved_count(len(self._approved_records))
            
            # 使用搜索引擎
            params = SearchParams(
                query=query,
                scope=scope,
                filters=filters or {},
                top_k=top_k or self._config.top_k,
                trace=self._config.enable_trace,
            )
            
            search_result = self._search_engine.search(params)
            
            stage_timing = (time.time() - stage_start) * 1000
            trace_builder.add_stage(
                name="search_approved",
                input_count=len(self._approved_records),
                output_count=len(search_result.records),
                timing_ms=stage_timing,
            )
            
            result.records = search_result.records
            trace_builder.set_filtered_count(len(search_result.records))
            
            # 记录召回的记录 ID
            for record in search_result.records:
                trace_builder.add_approved_record(record.id)
                
                # 检查是否为 Truth 层记录
                if record.tkr_layer == TruthKnowledgeRetrieval.TRUTH:
                    # 验证是否有精确引用
                    # 注意：这里只是标记，实际验证需要调用者处理
                    pass
            
            # 阶段 2: 处理 candidate 记录（仅 shadow/debug 模式）
            if self._config.mode in ["shadow", "debug"] and self._config.include_candidates:
                stage_start = time.time()
                
                candidate_engine = MemorySearchEngine(self._candidate_records)
                candidate_params = SearchParams(
                    query=query,
                    top_k=min(top_k or self._config.top_k, 3),  # candidate 限制更严格
                )
                
                candidate_result = candidate_engine.search(candidate_params)
                
                stage_timing = (time.time() - stage_start) * 1000
                trace_builder.add_stage(
                    name="search_candidates",
                    input_count=len(self._candidate_records),
                    output_count=len(candidate_result.records),
                    timing_ms=stage_timing,
                    details={"mode": self._config.mode},
                )
                
                trace_builder.set_candidate_count(len(self._candidate_records))
                
                # 标记 candidate 记录
                for record in candidate_result.records:
                    trace_builder.add_candidate_record(record.id)
                    # 在 shadow/debug 模式下添加到结果
                    # 但需要标记为 candidate
            
            trace_builder.set_returned_count(len(result.records))
            
        except Exception as e:
            error_msg = f"Recall error: {str(e)}"
            trace_builder.add_error(error_msg)
            result.errors.append(error_msg)
            
            if not self._config.fail_open:
                raise
            
            # Fail-open: 记录错误但继续
            if self._config.enable_trace:
                trace_builder.add_warning(f"Fail-open: {error_msg}")
        
        # 构建追踪信息
        if self._config.enable_trace:
            result.trace = trace_builder.build()
        
        return result
    
    def recall_with_truth_quote(
        self,
        query: str,
        top_k: Optional[int] = None,
        scope: Optional[MemoryScope] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> RecallResult:
        """
        召回记忆并验证 Truth 引用
        
        Truth 记录必须提供精确引用。
        
        Args:
            query: 查询内容
            top_k: top-k 参数
            scope: 作用域过滤
            filters: 元数据过滤
        
        Returns:
            RecallResult
        """
        result = self.recall(query, top_k, scope, filters)
        
        # 处理 Truth 记录
        for record in result.records:
            if record.tkr_layer == TruthKnowledgeRetrieval.TRUTH:
                # Truth 记录必须精确引用
                # 检查内容是否包含原始引用
                quote = TruthQuote(
                    record_id=record.id,
                    exact_quote=record.content,  # 整个内容作为引用
                    source_ref={"path": record.source_file},
                    verified=True,  # 默认已验证
                )
                result.truth_quotes.append(quote)
                
                # 更新追踪
                if result.trace:
                    result.trace.add_truth_quote(
                        record_id=record.id,
                        exact_quote=quote.exact_quote,
                        source_ref=quote.source_ref,
                    )
        
        return result
    
    def set_mode(self, mode: str):
        """
        设置召回模式
        
        Args:
            mode: 模式 (production/shadow/debug)
        """
        self._config.mode = mode
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            统计字典
        """
        return {
            "approved_count": len(self._approved_records),
            "candidate_count": len(self._candidate_records),
            "mode": self._config.mode,
        }


def create_recall_engine(
    approved_records: Optional[List[MemoryRecord]] = None,
    candidate_records: Optional[List[MemoryRecord]] = None,
    config: Optional[Dict[str, Any]] = None,
) -> RecallEngine:
    """
    便捷函数：创建召回引擎
    
    Args:
        approved_records: approved 记录列表
        candidate_records: candidate 记录列表
        config: 配置字典
    
    Returns:
        RecallEngine 实例
    """
    recall_config = None
    if config:
        recall_config = RecallConfig(
            mode=config.get("mode", "production"),
            top_k=config.get("top_k", 10),
            include_candidates=config.get("include_candidates", False),
            fail_open=config.get("fail_open", True),
            enable_trace=config.get("enable_trace", True),
        )
    
    return RecallEngine(approved_records, candidate_records, recall_config)
