#!/usr/bin/env python3
"""
Gate A: Contract Validator
验证变更是否符合契约、不碰禁区
"""

import sys
import yaml
from pathlib import Path
from typing import List, Dict, Tuple


def load_gates_config() -> Dict:
    """加载 Gate 配置"""
    config_path = Path("policy/gates.yaml")
    if not config_path.exists():
        return {}
    with open(config_path) as f:
        return yaml.safe_load(f)


def check_forbidden_patterns(changed_files: List[str], forbidden_patterns: List[str]) -> List[str]:
    """检查是否触及禁区"""
    violations = []
    for file in changed_files:
        for pattern in forbidden_patterns:
            if pattern in file:
                violations.append(f"{file} 触及禁区: {pattern}")
    return violations


def check_change_size(lines_changed: int, files_changed: int, max_lines: int, max_files: int) -> List[str]:
    """检查变更大小"""
    violations = []
    if lines_changed > max_lines:
        violations.append(f"变更行数 {lines_changed} 超过限制 {max_lines}")
    if files_changed > max_files:
        violations.append(f"变更文件数 {files_changed} 超过限制 {max_files}")
    return violations


def validate(changed_files: List[str], lines_changed: int, files_changed: int) -> Tuple[str, List[str], Dict]:
    """
    验证 Gate A
    
    Returns:
        (verdict, violations, evidence)
    """
    config = load_gates_config()
    gate_config = next((g for g in config.get("gates", []) if g["id"] == "gate_a"), {})
    
    forbidden_patterns = gate_config.get("forbidden_patterns", [])
    max_lines = gate_config.get("max_lines_changed", 100)
    max_files = gate_config.get("max_files_changed", 10)
    
    violations = []
    
    # 检查禁区
    pattern_violations = check_forbidden_patterns(changed_files, forbidden_patterns)
    violations.extend(pattern_violations)
    
    # 检查变更大小
    size_violations = check_change_size(lines_changed, files_changed, max_lines, max_files)
    violations.extend(size_violations)
    
    evidence = {
        "changed_files": changed_files,
        "lines_changed": lines_changed,
        "files_changed": files_changed,
        "forbidden_patterns_checked": forbidden_patterns,
        "violations": violations
    }
    
    if violations:
        return "FAIL", violations, evidence
    else:
        return "PASS", [], evidence


def main():
    """CLI 入口"""
    if len(sys.argv) < 4:
        print("Usage: gate_a_contract.py <changed_files_json> <lines_changed> <files_changed>")
        sys.exit(1)
    
    import json
    changed_files = json.loads(sys.argv[1])
    lines_changed = int(sys.argv[2])
    files_changed = int(sys.argv[3])
    
    verdict, violations, evidence = validate(changed_files, lines_changed, files_changed)
    
    result = {
        "gate": "gate_a",
        "verdict": verdict,
        "violations": violations,
        "evidence": evidence
    }
    
    print(json.dumps(result, indent=2))
    sys.exit(0 if verdict == "PASS" else 1)


if __name__ == "__main__":
    main()
