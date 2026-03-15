#!/usr/bin/env python3
"""
Gate B: E2E Validator
执行并验证 E2E 测试
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


def run_e2e_test(test_command: str, timeout: int, sandbox_path: Path) -> Tuple[int, str, str]:
    """运行 E2E 测试"""
    try:
        result = subprocess.run(
            test_command.split(),
            cwd=sandbox_path,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Timeout"
    except Exception as e:
        return -1, "", str(e)


def check_success_markers(stdout: str, markers: List[str]) -> Tuple[bool, List[str]]:
    """检查成功标记"""
    found_markers = []
    missing_markers = []
    
    for marker in markers:
        if marker in stdout:
            found_markers.append(marker)
        else:
            missing_markers.append(marker)
    
    return len(missing_markers) == 0, missing_markers


def validate(sandbox_path: Path) -> Tuple[str, List[str], Dict]:
    """
    验证 Gate B
    
    Returns:
        (verdict, violations, evidence)
    """
    config = load_gates_config()
    gate_config = next((g for g in config.get("gates", []) if g["id"] == "gate_b"), {})
    
    test_command = gate_config.get("test_command", "python tests/test_self_healing_e2e.py")
    timeout = gate_config.get("timeout_seconds", 180)
    success_markers = gate_config.get("success_markers", [])
    
    # 运行测试
    returncode, stdout, stderr = run_e2e_test(test_command, timeout, sandbox_path)
    
    evidence = {
        "returncode": returncode,
        "stdout": stdout[-5000:] if len(stdout) > 5000 else stdout,  # 截断
        "stderr": stderr[-2000:] if len(stderr) > 2000 else stderr,
        "test_command": test_command,
        "timeout": timeout
    }
    
    violations = []
    
    # 检查返回码
    if returncode != 0:
        violations.append(f"测试返回非零: {returncode}")
    
    # 检查成功标记
    if success_markers:
        all_found, missing = check_success_markers(stdout, success_markers)
        if not all_found:
            violations.append(f"缺失成功标记: {missing}")
    
    if violations:
        return "FAIL", violations, evidence
    else:
        return "PASS", [], evidence


def main():
    """CLI 入口"""
    if len(sys.argv) < 2:
        print("Usage: gate_b_e2e.py <sandbox_path>")
        sys.exit(1)
    
    sandbox_path = Path(sys.argv[1])
    
    verdict, violations, evidence = validate(sandbox_path)
    
    result = {
        "gate": "gate_b",
        "verdict": verdict,
        "violations": violations,
        "evidence": evidence
    }
    
    print(json.dumps(result, indent=2))
    sys.exit(0 if verdict == "PASS" else 1)


if __name__ == "__main__":
    main()
