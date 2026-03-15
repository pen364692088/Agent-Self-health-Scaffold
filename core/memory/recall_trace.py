"""
Recall Trace

召回追踪信息，记录召回过程的详细信息。

Author: Memory Kernel
Created: 2026-03-15
Version: 1.0.0
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class TraceStage:
    """
    追踪阶段
    
    记录召回过程的单个阶段。
    """
    name: str  # 阶段名称
    input_count: int  # 输入数量
    output_count: int  # 输出数量
    timing_ms: float  # 耗时（毫秒）
    details: Dict[str, Any] = field(default_factory=dict)  # 详细信息


@dataclass
class RecallTrace:
    """
    召回追踪
    
    记录召回过程的完整追踪信息。
    """
    # 基本信息
    query: str  # 查询内容
    mode: str  # 召回模式 (production/shadow/debug)
    
    # 统计信息
    total_scanned: int = 0  # 扫描总数
    approved_count: int = 0  # approved 记录数
    candidate_count: int = 0  # candidate 记录数
    filtered_count: int = 0  # 过滤后数量
    top_k: int = 10  # top-k 参数
    returned_count: int = 0  # 返回数量
    
    # 时间信息
    timing_ms: float = 0.0  # 总耗时（毫秒）
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # 错误信息
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    # 阶段信息
    stages: List[TraceStage] = field(default_factory=list)
    
    # 召回结果
    approved_records: List[str] = field(default_factory=list)  # approved 记录 ID
    candidate_records: List[str] = field(default_factory=list)  # candidate 记录 ID
    
    # Truth 引用
    truth_quotes: List[Dict[str, Any]] = field(default_factory=list)
    
    def add_stage(
        self,
        name: str,
        input_count: int,
        output_count: int,
        timing_ms: float,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        添加阶段
        
        Args:
            name: 阶段名称
            input_count: 输入数量
            output_count: 输出数量
            timing_ms: 耗时
            details: 详细信息
        """
        stage = TraceStage(
            name=name,
            input_count=input_count,
            output_count=output_count,
            timing_ms=timing_ms,
            details=details or {},
        )
        self.stages.append(stage)
    
    def add_error(self, error: str):
        """添加错误"""
        self.errors.append(error)
    
    def add_warning(self, warning: str):
        """添加警告"""
        self.warnings.append(warning)
    
    def add_approved_record(self, record_id: str):
        """添加 approved 记录"""
        self.approved_records.append(record_id)
    
    def add_candidate_record(self, record_id: str):
        """添加 candidate 记录"""
        self.candidate_records.append(record_id)
    
    def add_truth_quote(
        self,
        record_id: str,
        exact_quote: str,
        source_ref: Dict[str, Any],
    ):
        """
        添加 Truth 引用
        
        Args:
            record_id: 记录 ID
            exact_quote: 精确引用
            source_ref: 来源引用
        """
        self.truth_quotes.append({
            "record_id": record_id,
            "exact_quote": exact_quote,
            "source_ref": source_ref,
        })
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "query": self.query,
            "mode": self.mode,
            "total_scanned": self.total_scanned,
            "approved_count": self.approved_count,
            "candidate_count": self.candidate_count,
            "filtered_count": self.filtered_count,
            "top_k": self.top_k,
            "returned_count": self.returned_count,
            "timing_ms": self.timing_ms,
            "timestamp": self.timestamp.isoformat(),
            "errors": self.errors,
            "warnings": self.warnings,
            "stages": [
                {
                    "name": s.name,
                    "input_count": s.input_count,
                    "output_count": s.output_count,
                    "timing_ms": s.timing_ms,
                    "details": s.details,
                }
                for s in self.stages
            ],
            "approved_records": self.approved_records,
            "candidate_records": self.candidate_records,
            "truth_quotes": self.truth_quotes,
        }
    
    def is_success(self) -> bool:
        """是否成功"""
        return len(self.errors) == 0
    
    def has_candidates(self) -> bool:
        """是否有候选记录"""
        return len(self.candidate_records) > 0
    
    def has_truth_quotes(self) -> bool:
        """是否有 Truth 引用"""
        return len(self.truth_quotes) > 0


@dataclass
class TruthQuote:
    """
    Truth 精确引用
    
    Truth 层记录必须使用精确引用，不允许摘要或改写。
    """
    record_id: str  # 记录 ID
    exact_quote: str  # 精确引用原文
    source_ref: Dict[str, Any]  # 来源引用
    verified: bool = False  # 是否已验证
    
    def verify(self, original_content: str) -> bool:
        """
        验证引用是否精确
        
        Args:
            original_content: 原始内容
        
        Returns:
            是否精确匹配
        """
        # 检查精确引用是否在原文中
        if self.exact_quote in original_content:
            self.verified = True
            return True
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "record_id": self.record_id,
            "exact_quote": self.exact_quote,
            "source_ref": self.source_ref,
            "verified": self.verified,
        }


class RecallTraceBuilder:
    """
    召回追踪构建器
    
    便于构建 RecallTrace 对象。
    """
    
    def __init__(self, query: str, mode: str = "production"):
        """
        初始化构建器
        
        Args:
            query: 查询内容
            mode: 召回模式
        """
        self._trace = RecallTrace(query=query, mode=mode)
        self._start_time: Optional[float] = None
    
    def start(self):
        """开始计时"""
        import time
        self._start_time = time.time()
    
    def stop(self):
        """停止计时"""
        import time
        if self._start_time:
            self._trace.timing_ms = (time.time() - self._start_time) * 1000
    
    def set_total_scanned(self, count: int):
        """设置扫描总数"""
        self._trace.total_scanned = count
    
    def set_approved_count(self, count: int):
        """设置 approved 数量"""
        self._trace.approved_count = count
    
    def set_candidate_count(self, count: int):
        """设置 candidate 数量"""
        self._trace.candidate_count = count
    
    def set_filtered_count(self, count: int):
        """设置过滤后数量"""
        self._trace.filtered_count = count
    
    def set_top_k(self, k: int):
        """设置 top-k"""
        self._trace.top_k = k
    
    def set_returned_count(self, count: int):
        """设置返回数量"""
        self._trace.returned_count = count
    
    def add_stage(
        self,
        name: str,
        input_count: int,
        output_count: int,
        timing_ms: float,
        details: Optional[Dict[str, Any]] = None,
    ):
        """添加阶段"""
        self._trace.add_stage(name, input_count, output_count, timing_ms, details)
    
    def add_error(self, error: str):
        """添加错误"""
        self._trace.add_error(error)
    
    def add_warning(self, warning: str):
        """添加警告"""
        self._trace.add_warning(warning)
    
    def add_approved_record(self, record_id: str):
        """添加 approved 记录"""
        self._trace.add_approved_record(record_id)
    
    def add_candidate_record(self, record_id: str):
        """添加 candidate 记录"""
        self._trace.add_candidate_record(record_id)
    
    def add_truth_quote(
        self,
        record_id: str,
        exact_quote: str,
        source_ref: Dict[str, Any],
    ):
        """添加 Truth 引用"""
        self._trace.add_truth_quote(record_id, exact_quote, source_ref)
    
    def build(self) -> RecallTrace:
        """构建追踪对象"""
        self.stop()
        return self._trace


def create_trace_builder(query: str, mode: str = "production") -> RecallTraceBuilder:
    """
    便捷函数：创建追踪构建器
    
    Args:
        query: 查询内容
        mode: 召回模式
    
    Returns:
        RecallTraceBuilder 实例
    """
    return RecallTraceBuilder(query=query, mode=mode)
