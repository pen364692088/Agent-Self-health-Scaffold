"""
Retry Policy - Minimal Implementation

重试策略引擎。

Author: Autonomy Closure
Created: 2026-03-16
Version: 1.0.0-minimal
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import time
import random


class ErrorType(Enum):
    """错误类型"""
    TRANSIENT = "transient"      # 临时错误，可重试
    RESOURCE = "resource"        # 资源错误，可重试
    EXTERNAL = "external"        # 外部错误，可重试
    PERMANENT = "permanent"      # 永久错误，不可重试


@dataclass
class RetryConfig:
    """重试配置"""
    max_retry: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True


@dataclass
class RetryAttempt:
    """重试尝试记录"""
    attempt: int
    error_type: ErrorType
    error_message: str
    delay: float
    timestamp: datetime


@dataclass
class RetryResult:
    """重试结果"""
    success: bool
    attempts: int
    max_attempts: int
    exhausted: bool
    error_type: Optional[ErrorType]
    error_message: Optional[str]
    attempts_detail: List[RetryAttempt]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "attempts": self.attempts,
            "max_attempts": self.max_attempts,
            "exhausted": self.exhausted,
            "error_type": self.error_type.value if self.error_type else None,
            "error_message": self.error_message,
            "attempts_detail": [
                {
                    "attempt": a.attempt,
                    "error_type": a.error_type.value,
                    "error_message": a.error_message,
                    "delay": a.delay,
                    "timestamp": a.timestamp.isoformat(),
                }
                for a in self.attempts_detail
            ],
        }


class RetryPolicy:
    """
    重试策略
    
    基于 EXECUTION_RECOVERY_RETRY_ROLLBACK_POLICY.md。
    """
    
    # 默认配置
    DEFAULT_CONFIGS: Dict[ErrorType, RetryConfig] = {
        ErrorType.TRANSIENT: RetryConfig(max_retry=3, base_delay=1.0),
        ErrorType.RESOURCE: RetryConfig(max_retry=2, base_delay=5.0),
        ErrorType.EXTERNAL: RetryConfig(max_retry=2, base_delay=10.0),
        ErrorType.PERMANENT: RetryConfig(max_retry=0),
    }
    
    def __init__(self, configs: Optional[Dict[ErrorType, RetryConfig]] = None):
        """
        初始化
        
        Args:
            configs: 自定义配置
        """
        self._configs = configs or self.DEFAULT_CONFIGS
        self._history: List[RetryResult] = []
    
    def classify_error(self, error_message: str) -> ErrorType:
        """
        分类错误类型
        
        Args:
            error_message: 错误信息
        
        Returns:
            ErrorType
        """
        error_lower = error_message.lower()
        
        # 临时错误
        transient_patterns = [
            "timeout", "connection reset", "temporarily unavailable",
            "rate limit", "too many requests", "service unavailable",
        ]
        for pattern in transient_patterns:
            if pattern in error_lower:
                return ErrorType.TRANSIENT
        
        # 资源错误
        resource_patterns = [
            "out of memory", "disk full", "resource exhausted",
            "no space left", "quota exceeded",
        ]
        for pattern in resource_patterns:
            if pattern in error_lower:
                return ErrorType.RESOURCE
        
        # 外部错误
        external_patterns = [
            "external api", "third party", "upstream",
            "remote service", "network error",
        ]
        for pattern in external_patterns:
            if pattern in error_lower:
                return ErrorType.EXTERNAL
        
        # 默认永久错误
        return ErrorType.PERMANENT
    
    def calculate_delay(
        self,
        attempt: int,
        config: RetryConfig,
    ) -> float:
        """
        计算重试延迟（指数退避 + 抖动）
        
        Args:
            attempt: 当前尝试次数
            config: 重试配置
        
        Returns:
            延迟秒数
        """
        delay = config.base_delay * (config.exponential_base ** (attempt - 1))
        delay = min(delay, config.max_delay)
        
        # 添加抖动
        if config.jitter:
            delay = delay * (0.5 + random.random())
        
        return delay
    
    def should_retry(
        self,
        error_type: ErrorType,
        attempt: int,
    ) -> tuple[bool, float]:
        """
        判断是否应该重试
        
        Args:
            error_type: 错误类型
            attempt: 当前尝试次数
        
        Returns:
            (should_retry, delay)
        """
        config = self._configs.get(error_type, RetryConfig())
        
        if attempt >= config.max_retry:
            return False, 0
        
        delay = self.calculate_delay(attempt + 1, config)
        return True, delay
    
    def execute_with_retry(
        self,
        operation: callable,
        operation_name: str = "operation",
    ) -> RetryResult:
        """
        执行操作并自动重试
        
        Args:
            operation: 要执行的操作
            operation_name: 操作名称
        
        Returns:
            RetryResult
        """
        attempts_detail = []
        attempt = 0
        last_error_type = None
        last_error_message = None
        
        while True:
            attempt += 1
            
            try:
                result = operation()
                
                # 成功
                return RetryResult(
                    success=True,
                    attempts=attempt,
                    max_attempts=self._configs.get(last_error_type or ErrorType.TRANSIENT, RetryConfig()).max_retry,
                    exhausted=False,
                    error_type=None,
                    error_message=None,
                    attempts_detail=attempts_detail,
                )
            
            except Exception as e:
                error_message = str(e)
                error_type = self.classify_error(error_message)
                last_error_type = error_type
                last_error_message = error_message
                
                config = self._configs.get(error_type, RetryConfig())
                
                # 记录尝试
                attempts_detail.append(RetryAttempt(
                    attempt=attempt,
                    error_type=error_type,
                    error_message=error_message,
                    delay=0,  # Will update if retry
                    timestamp=datetime.now(timezone.utc),
                ))
                
                # 检查是否应该重试
                should_retry, delay = self.should_retry(error_type, attempt)
                
                if not should_retry:
                    # 重试耗尽
                    return RetryResult(
                        success=False,
                        attempts=attempt,
                        max_attempts=config.max_retry,
                        exhausted=True,
                        error_type=error_type,
                        error_message=error_message,
                        attempts_detail=attempts_detail,
                    )
                
                # 等待并重试
                attempts_detail[-1].delay = delay
                time.sleep(delay)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计"""
        total = len(self._history)
        if total == 0:
            return {"total": 0, "success": 0, "exhausted": 0}
        
        success = sum(1 for r in self._history if r.success)
        exhausted = sum(1 for r in self._history if r.exhausted)
        
        by_error_type = {}
        for error_type in ErrorType:
            by_error_type[error_type.value] = sum(
                1 for r in self._history
                if r.error_type == error_type
            )
        
        return {
            "total": total,
            "success": success,
            "exhausted": exhausted,
            "success_rate": success / total,
            "by_error_type": by_error_type,
        }


def create_retry_policy(configs: Optional[Dict[ErrorType, RetryConfig]] = None) -> RetryPolicy:
    """创建重试策略"""
    return RetryPolicy(configs=configs)
