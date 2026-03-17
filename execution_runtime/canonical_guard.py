"""
Canonical Guard - Canonical Source Verification

仓库/路径/状态源验证，封装 core/canonical_adapter.py。

Author: Execution Runtime
Created: 2026-03-17
Version: 1.0.0
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from pathlib import Path
import sys
import yaml

# 添加项目根目录到 path
sys.path.insert(0, str(Path(__file__).parent.parent))


@dataclass
class CanonicalConfig:
    """
    Canonical Guard 配置
    """
    canonical_repo: Optional[Path] = None
    allowed_paths: List[Path] = field(default_factory=list)
    config_file: Optional[Path] = None


@dataclass
class CanonicalResult:
    """
    Canonical 检查结果
    """
    allowed: bool
    current_path: Path
    canonical_repo: Optional[Path] = None
    reason: Optional[str] = None
    relative_path: Optional[Path] = None


class CanonicalGuard:
    """
    Canonical 守卫
    
    负责：
    - 验证当前路径是否在 canonical repo 内
    - 验证写入路径是否在允许范围内
    - 防止写入非授权位置
    """
    
    def __init__(self, config: Optional[CanonicalConfig] = None):
        self.config = config or CanonicalConfig()
        self._load_config()
    
    def _load_config(self):
        """加载配置"""
        if self.config.config_file:
            self._load_from_file(self.config.config_file)
        elif self.config.canonical_repo is None:
            # 尝试从默认配置加载
            default_config = Path(__file__).parent.parent / "config" / "canonical_repos.yaml"
            if default_config.exists():
                self._load_from_file(default_config)
    
    def _load_from_file(self, config_file: Path):
        """从文件加载配置"""
        try:
            with open(config_file) as f:
                data = yaml.safe_load(f) or {}
            
            # 假设配置格式
            repos = data.get("repos", [])
            if repos:
                self.config.canonical_repo = Path(repos[0].get("path", "."))
                
        except Exception:
            pass
    
    def check_path(self, path: Path) -> CanonicalResult:
        """
        检查路径是否在 canonical 范围内
        
        Args:
            path: 要检查的路径
        
        Returns:
            CanonicalResult
        """
        path = path.resolve()
        
        # 如果没有配置 canonical_repo，允许所有
        if self.config.canonical_repo is None:
            return CanonicalResult(
                allowed=True,
                current_path=path,
                reason="No canonical repo configured",
            )
        
        canonical = self.config.canonical_repo.resolve()
        
        # 检查是否在 canonical repo 内
        if path.is_relative_to(canonical):
            return CanonicalResult(
                allowed=True,
                current_path=path,
                canonical_repo=canonical,
                relative_path=path.relative_to(canonical),
            )
        
        # 检查是否在允许的路径列表中
        for allowed in self.config.allowed_paths:
            if path.is_relative_to(allowed.resolve()):
                return CanonicalResult(
                    allowed=True,
                    current_path=path,
                    canonical_repo=allowed,
                    relative_path=path.relative_to(allowed.resolve()),
                )
        
        return CanonicalResult(
            allowed=False,
            current_path=path,
            canonical_repo=canonical,
            reason=f"Path outside canonical repo: {canonical}",
        )
    
    def check_current_path(self) -> CanonicalResult:
        """检查当前工作目录"""
        return self.check_path(Path.cwd())
    
    def check_write_path(self, target: Path) -> CanonicalResult:
        """检查写入路径"""
        return self.check_path(target)
    
    def get_canonical_root(self) -> Optional[Path]:
        """获取 canonical 根目录"""
        return self.config.canonical_repo
    
    def is_canonical(self, path: Path) -> bool:
        """检查是否在 canonical 内"""
        result = self.check_path(path)
        return result.allowed
    
    def enforce(self, path: Path) -> Path:
        """
        强制返回 canonical 路径
        
        如果路径不在 canonical 内，返回 canonical 根
        
        Args:
            path: 原始路径
        
        Returns:
            canonical 路径或根目录
        """
        result = self.check_path(path)
        
        if result.allowed:
            return path
        
        # 返回 canonical 根
        return self.config.canonical_repo or Path.cwd()


# 便捷函数
def check_canonical(path: Path, canonical_repo: Optional[Path] = None) -> CanonicalResult:
    """
    便捷的 canonical 检查函数
    
    Args:
        path: 要检查的路径
        canonical_repo: canonical 仓库路径
    
    Returns:
        CanonicalResult
    """
    config = CanonicalConfig(canonical_repo=canonical_repo)
    guard = CanonicalGuard(config)
    return guard.check_path(path)
