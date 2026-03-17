"""
Retry Manager - Retry Strategy Management

重试策略管理，封装 core/execution/retry_policy.py。

Author: Execution Runtime
Created: 2026-03-17
Version: 1.0.0
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Callable, TypeVar, Generic
from pathlib import Path
import sys
import time
import random
from enum import Enum
from datetime import datetime, timezone

# 添加项目根目录到 path
sys.path.insert(0, str(Path(__file__).parent.parent))


class RetryStrategy(str, Enum):
    """重试策略"""
    FIXED = "fixed"           # 固定间隔
    LINEAR = "linear"         # 线性递增
    EXPONENTIAL = "exponential"  # 指数退避
    EXPONENTIAL_JITTER = "exponential_jitter"  # 指数退避 + 抖动


@dataclass
class RetryConfig:
    """
    重试配置
    """
    max_retries: int = 3
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_JITTER
    base_delay_ms: int = 1000  # 基础延迟（毫秒）
    max_delay_ms: int = 60000  # 最大延迟（毫秒）
    multiplier: float = 2.0    # 乘数（用于指数退避）
    retryable_errors: List[str] = field(default_factory=lambda: ["timeout", "connection", "temporary"])


@dataclass
class RetryResult(Generic[TypeVar('T')]):
    """
    重试结果
    """
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    attempts: int = 0
    total_delay_ms: int = 0
    last_attempt_at: Optional[str] = None


class RetryManager:
    """
    重试管理器
    
    负责：
    - 计算重试延迟
    - 执行重试逻辑
    - 记录重试历史
    """
    
    def __init__(self, config: Optional[RetryConfig] = None):
        self.config = config or RetryConfig()
        self._history: List[Dict[str, Any]] = []
    
    def calculate_delay(self, attempt: int) -> int:
        """
        计算重试延迟
        
        Args:
            attempt: 当前尝试次数（从 1 开始）
        
        Returns:
            延迟（毫秒）
        """
        if self.config.strategy == RetryStrategy.FIXED:
            delay = self.config.base_delay_ms
        
        elif self.config.strategy == RetryStrategy.LINEAR:
            delay = self.config.base_delay_ms * attempt
        
        elif self.config.strategy == RetryStrategy.EXPONENTIAL:
            delay = self.config.base_delay_ms * (self.config.multiplier ** (attempt - 1))
        
        elif self.config.strategy == RetryStrategy.EXPONENTIAL_JITTER:
            base_delay = self.config.base_delay_ms * (self.config.multiplier ** (attempt - 1))
            # 添加随机抖动（±25%）
            jitter = base_delay * 0.25 * (random.random() * 2 - 1)
            delay = int(base_delay + jitter)
        
        else:
            delay = self.config.base_delay_ms
        
        return min(delay, self.config.max_delay_ms)
    
    def should_retry(self, error: Optional[str]) -> bool:
        """
        判断是否应该重试
        
        Args:
            error: 错误信息
        
        Returns:
            是否应该重试
        """
        if error is None:
            return False
        
        error_lower = error.lower()
        
        for retryable in self.config.retryable_errors:
            if retryable.lower() in error_lower:
                return True
        
        return False
    
    def execute(self, fn: Callable[[], Any]) -> RetryResult:
        """
        执行带重试的操作
        
        Args:
            fn: 要执行的函数
        
        Returns:
            RetryResult
        """
        attempts = 0
        total_delay_ms = 0
        last_error = None
        
        while attempts < self.config.max_retries:
            attempts += 1
            
            try:
                result = fn()
                
                return RetryResult(
                    success=True,
                    result=result,
                    attempts=attempts,
                    total_delay_ms=total_delay_ms,
                    last_attempt_at=datetime.now(timezone.utc).isoformat(),
                )
                
            except Exception as e:
                last_error = str(e)
                
                # 记录失败
                self._history.append({
                    "attempt": attempts,
                    "error": last_error,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
                
                # 检查是否应该重试
                if not self.should_retry(last_error):
                    break
                
                # 计算延迟
                if attempts < self.config.max_retries:
                    delay = self.calculate_delay(attempts)
                    total_delay_ms += delay
                    time.sleep(delay / 1000)
        
        return RetryResult(
            success=False,
            error=last_error,
            attempts=attempts,
            total_delay_ms=total_delay_ms,
            last_attempt_at=datetime.now(timezone.utc).isoformat(),
        )
    
    async def execute_async(self, fn: Callable[[], Any]) -> RetryResult:
        """
        执行带重试的异步操作
        
        Args:
            fn: 要执行的异步函数
        
        Returns:
            RetryResult
        """
        import asyncio
        
        attempts = 0
        total_delay_ms = 0
        last_error = None
        
        while attempts < self.config.max_retries:
            attempts += 1
            
            try:
                result = await fn()
                
                return RetryResult(
                    success=True,
                    result=result,
                    attempts=attempts,
                    total_delay_ms=total_delay_ms,
                    last_attempt_at=datetime.now(timezone.utc).isoformat(),
                )
                
            except Exception as e:
                last_error = str(e)
                
                self._history.append({
                    "attempt": attempts,
                    "error": last_error,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
                
                if not self.should_retry(last_error):
                    break
                
                if attempts < self.config.max_retries:
                    delay = self.calculate_delay(attempts)
                    total_delay_ms += delay
                    await asyncio.sleep(delay / 1000)
        
        return RetryResult(
            success=False,
            error=last_error,
            attempts=attempts,
            total_delay_ms=total_delay_ms,
            last_attempt_at=datetime.now(timezone.utc).isoformat(),
        )
    
    def get_history(self) -> List[Dict[str, Any]]:
        """获取重试历史"""
        return self._history.copy()
    
    def clear_history(self):
        """清除重试历史"""
        self._history.clear()


# 便捷函数
def retry(fn: Callable[[], Any], max_retries: int = 3, **kwargs) -> RetryResult:
    """
    便捷的重试函数
    
    Args:
        fn: 要执行的函数
        max_retries: 最大重试次数
        **kwargs: 其他 RetryConfig 参数
    
    Returns:
        RetryResult
    """
    config = RetryConfig(max_retries=max_retries, **kwargs)
    manager = RetryManager(config)
    return manager.execute(fn)
