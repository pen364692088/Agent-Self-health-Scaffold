#!/usr/bin/env python3
"""
Gate C: Preflight Validator
执行 tool_doctor 健康检查
"""

import sys
import subprocess
import json
import yaml
from pathlib import Path
from typing import Tuple, Dict, List


def load_gates_config() -> Dict:
    """加载 Gate 配置"""
    config_path = Path("policy/gates.yaml")
    if not config_path.exists():
        return {}
    with open(config_path) as f:
        return yaml.safe_load(f)


def run_tool_doctor(sandbox_path: Path) -> Tuple[int, str, str]:
    """运行 tool_doctor"""
    tool_doctor_path = sandbox_path / "scripts" / "tool_doctor.py"
    
    # 检查脚本是否存在
    if not tool_doctor_path.exists():
        return -1, "", f"tool_doctor.py not found at {tool_doctor_path}"
    
    try:
        result = subprocess.run(
            ["python", "scripts/tool_doctor.py"],
            cwd=sandbox_path,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Timeout"
    except Exception as e:
        return -1, "", str(e)


def validate(sandbox_path: Path) -> Tuple[str, List[str], Dict]:
    """
    验证 Gate C
    
    Returns:
        (verdict, violations, evidence)
    """
    # 运行 tool_doctor
    returncode, stdout, stderr = run_tool_doctor(sandbox_path)
    
    evidence = {
        "returncode": returncode,
        "stdout": stdout,
        "stderr": stderr,
        "tool_doctor_path": str(sandbox_path / "scripts" / "tool_doctor.py")
    }
    
    violations = []
    
    # 检查脚本是否存在
    if returncode == -1 and "not found" in stderr:
        violations.append(f"tool_doctor.py 不存在: {stderr}")
        return "FAIL", violations, evidence
    
    # 检查返回码
    if returncode != 0:
        violations.append(f"tool_doctor 返回非零: {returncode}")
        violations.append(f"输出: {stdout}")
    
    if violations:
        return "FAIL", violations, evidence
    else:
        return "PASS", [], evidence


def main():
    """CLI 入口"""
    if len(sys.argv) < 2:
        print("Usage: gate_c_preflight.py <sandbox_path>")
        sys.exit(1)
    
    sandbox_path = Path(sys.argv[1])
    
    verdict, violations, evidence = validate(sandbox_path)
    
    result = {
        "gate": "gate_c",
        "verdict": verdict,
        "violations": violations,
        "evidence": evidence
    }
    
    print(json.dumps(result, indent=2))
    sys.exit(0 if verdict == "PASS" else 1)


if __name__ == "__main__":
    main()
