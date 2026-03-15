#!/usr/bin/env python3
"""
Tool Doctor - 工具链健康检查

检查项目工具链是否配置正确。
"""

import sys
import subprocess
from pathlib import Path


def check_python():
    """检查 Python 版本"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 10:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} (需要 >= 3.10)")
        return False


def check_git():
    """检查 Git 是否可用"""
    try:
        result = subprocess.run(
            ["git", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            print(f"✅ {result.stdout.strip()}")
            return True
        else:
            print("❌ Git 不可用")
            return False
    except Exception as e:
        print(f"❌ Git 检查失败: {e}")
        return False


def check_pytest():
    """检查 pytest 是否可用"""
    try:
        result = subprocess.run(
            ["python", "-m", "pytest", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            print(f"✅ {result.stdout.strip().split(chr(10))[0]}")
            return True
        else:
            print("❌ pytest 不可用")
            return False
    except Exception as e:
        print(f"❌ pytest 检查失败: {e}")
        return False


def check_project_structure():
    """检查项目结构"""
    required_dirs = ["src", "tests", "scripts"]
    all_exist = True
    for dir_name in required_dirs:
        if Path(dir_name).exists():
            print(f"✅ {dir_name}/")
        else:
            print(f"❌ {dir_name}/ (缺失)")
            all_exist = False
    return all_exist


def main():
    """主函数"""
    print("=" * 50)
    print("Tool Doctor - 工具链健康检查")
    print("=" * 50)
    print()

    checks = [
        ("Python 版本", check_python),
        ("Git", check_git),
        ("pytest", check_pytest),
        ("项目结构", check_project_structure),
    ]

    all_passed = True
    for name, check_func in checks:
        print(f"\n[{name}]")
        if not check_func():
            all_passed = False

    print()
    print("=" * 50)
    if all_passed:
        print("✅ 所有检查通过")
        return 0
    else:
        print("❌ 部分检查失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
