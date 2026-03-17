"""
Memory Health Checker

检查 Agent 记忆链健康状态：
- 记忆是否加载
- 规则是否解析
- 文件是否存在

Author: Health Runtime
Created: 2026-03-17
Version: 1.0.0
"""

from dataclasses import dataclass
from typing import List, Dict, Any
from pathlib import Path
import yaml

from health_runtime.health_checker import (
    HealthCheckResult,
    HealthStatus,
    HealthCategory,
    HealthConfig,
)


class MemoryHealthChecker:
    """记忆健康检查器"""
    
    def __init__(self, config: HealthConfig):
        self.config = config
        self.memory_root = config.project_root / "memory" / "agents" / config.agent_id
    
    def check(self) -> HealthCheckResult:
        """执行记忆健康检查"""
        issues: List[str] = []
        details: Dict[str, Any] = {}
        
        # 1. 检查记忆空间是否存在
        if not self.memory_root.exists():
            issues.append("Memory root directory not found")
            return HealthCheckResult(
                category=HealthCategory.MEMORY,
                status=HealthStatus.CRITICAL,
                message="Memory space not initialized",
                details={"memory_root": str(self.memory_root)},
                issues=issues,
            )
        
        details["memory_root"] = str(self.memory_root)
        
        # 2. 检查 instruction_rules.yaml
        instruction_rules_path = self.memory_root / "instruction_rules.yaml"
        rules_loaded = False
        rules_valid = False
        
        if instruction_rules_path.exists():
            try:
                with open(instruction_rules_path, "r") as f:
                    rules = yaml.safe_load(f)
                
                if rules:
                    rules_loaded = True
                    # 验证必要字段
                    if rules.get("agent_id") == self.config.agent_id:
                        rules_valid = True
                        details["rules_count"] = len(rules.get("workflow_rules", []))
                    else:
                        issues.append("instruction_rules agent_id mismatch")
            except Exception as e:
                issues.append(f"Failed to parse instruction_rules: {e}")
        else:
            issues.append("instruction_rules.yaml not found")
        
        details["instruction_rules_loaded"] = rules_loaded
        details["instruction_rules_valid"] = rules_valid
        
        # 3. 检查 handoff_state.yaml
        handoff_path = self.memory_root / "handoff_state.yaml"
        handoff_loaded = handoff_path.exists()
        
        if not handoff_loaded:
            issues.append("handoff_state.yaml not found")
        
        details["handoff_loaded"] = handoff_loaded
        
        # 4. 检查 execution_state.yaml
        execution_path = self.memory_root / "execution_state.yaml"
        execution_loaded = execution_path.exists()
        
        if not execution_loaded:
            issues.append("execution_state.yaml not found")
        
        details["execution_state_loaded"] = execution_loaded
        
        # 5. 检查 long_term 目录
        long_term_path = self.memory_root / "long_term"
        long_term_exists = long_term_path.exists()
        
        if not long_term_exists:
            issues.append("long_term directory not found")
        
        details["long_term_exists"] = long_term_exists
        
        # 确定状态
        if not rules_loaded or not rules_valid:
            status = HealthStatus.CRITICAL
            message = "Memory critical: rules not loaded or invalid"
        elif len(issues) > 1:
            status = HealthStatus.WARNING
            message = "Memory warning: some files missing"
        elif issues:
            status = HealthStatus.WARNING
            message = f"Memory warning: {issues[0]}"
        else:
            status = HealthStatus.HEALTHY
            message = "Memory healthy: all files present and loaded"
        
        return HealthCheckResult(
            category=HealthCategory.MEMORY,
            status=status,
            message=message,
            details=details,
            issues=issues,
        )
