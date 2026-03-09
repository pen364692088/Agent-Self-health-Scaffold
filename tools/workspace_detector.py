"""
Workspace Detector - Reusable workspace path detection for CI compatibility.

Usage:
    from workspace_detector import detect_workspace
    WORKSPACE = detect_workspace()
"""

import os
from pathlib import Path

def detect_workspace() -> Path:
    """Detect workspace path from environment or script location."""
    # 1. 环境变量优先
    env_workspace = os.environ.get("OPENCLAW_WORKSPACE")
    if env_workspace:
        return Path(env_workspace)
    
    # 2. 从调用脚本位置推断 (caller is in tools/ -> workspace is parent)
    import inspect
    try:
        frame = inspect.currentframe()
        while frame:
            filename = frame.f_code.co_filename
            if filename and not filename.startswith('<'):
                caller_path = Path(filename).resolve()
                # Check if caller is in tools/ directory
                possible_workspace = caller_path.parent.parent
                if (possible_workspace / "tools").exists():
                    return possible_workspace
            frame = frame.f_back
    except:
        pass
    
    # 3. 当前工作目录
    cwd = Path.cwd()
    if (cwd / "tools").exists():
        return cwd
    
    # 4. 默认路径 (本地开发环境)
    default = Path("/home/moonlight/.openclaw/workspace")
    if default.exists():
        return default
    
    # 5. 最后回退: 使用当前目录
    return cwd
