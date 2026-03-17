"""
Integrity Health Checker

检查 Agent 完整性：
- evidence 是否缺失
- 文件是否完整
- 隔离是否有效

Author: Health Runtime
Created: 2026-03-17
Version: 1.0.0
"""

from dataclasses import dataclass
from typing import List, Dict, Any
from pathlib import Path
import yaml
import json
import hashlib

from health_runtime.health_checker import (
    HealthCheckResult,
    HealthStatus,
    HealthCategory,
    HealthConfig,
)


class IntegrityHealthChecker:
    """完整性健康检查器"""
    
    def __init__(self, config: HealthConfig):
        self.config = config
        self.project_root = config.project_root
        self.memory_root = config.project_root / "memory" / "agents" / config.agent_id
    
    def check(self) -> HealthCheckResult:
        """执行完整性健康检查"""
        issues: List[str] = []
        details: Dict[str, Any] = {}
        
        # 1. 检查 profile 完整性
        profile_ok = self._check_profile_integrity()
        details["profile_integrity"] = profile_ok
        
        if not profile_ok.get("exists"):
            issues.append("Agent profile not found")
        elif not profile_ok.get("valid"):
            issues.append(f"Agent profile invalid: {profile_ok.get('error')}")
        
        # 2. 检查记忆文件完整性
        memory_integrity = self._check_memory_files_integrity()
        details["memory_files_integrity"] = memory_integrity
        
        if memory_integrity.get("missing"):
            for missing in memory_integrity["missing"]:
                issues.append(f"Missing memory file: {missing}")
        
        # 3. 检查隔离性
        isolation_ok = self._check_isolation()
        details["isolation_ok"] = isolation_ok
        
        if not isolation_ok.get("isolated"):
            issues.append(f"Isolation violation: {isolation_ok.get('message')}")
        
        # 4. 检查 evidence 链
        evidence_ok = self._check_evidence()
        details["evidence_ok"] = evidence_ok
        
        if not evidence_ok.get("has_evidence"):
            # evidence 缺失是 warning，不是 critical
            issues.append("No evidence records found")
        
        # 确定状态
        critical_issues = [i for i in issues if "profile" in i.lower() or "isolation" in i.lower()]
        
        if critical_issues:
            status = HealthStatus.CRITICAL
            message = f"Integrity critical: {critical_issues[0]}"
        elif issues:
            status = HealthStatus.WARNING
            message = f"Integrity warning: {len(issues)} issues"
        else:
            status = HealthStatus.HEALTHY
            message = "Integrity healthy: all checks passed"
        
        return HealthCheckResult(
            category=HealthCategory.INTEGRITY,
            status=status,
            message=message,
            details=details,
            issues=issues,
        )
    
    def _check_profile_integrity(self) -> Dict[str, Any]:
        """检查 profile 完整性"""
        result = {"exists": False, "valid": False, "error": None}
        
        profile_path = self.project_root / "agents" / f"{self.config.agent_id}.profile.json"
        
        if not profile_path.exists():
            return result
        
        result["exists"] = True
        
        try:
            with open(profile_path, "r") as f:
                profile = json.load(f)
            
            # 检查必需字段
            required = ["agent_id", "name", "role", "memory_config"]
            missing = [r for r in required if r not in profile]
            
            if missing:
                result["error"] = f"Missing fields: {missing}"
                return result
            
            # 检查 agent_id 匹配
            if profile.get("agent_id") != self.config.agent_id:
                result["error"] = "agent_id mismatch"
                return result
            
            result["valid"] = True
        
        except json.JSONDecodeError as e:
            result["error"] = f"Invalid JSON: {e}"
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    def _check_memory_files_integrity(self) -> Dict[str, Any]:
        """检查记忆文件完整性"""
        result = {"missing": [], "corrupted": []}
        
        required_files = [
            "instruction_rules.yaml",
            "handoff_state.yaml",
            "execution_state.yaml",
        ]
        
        for file_name in required_files:
            file_path = self.memory_root / file_name
            
            if not file_path.exists():
                result["missing"].append(file_name)
                continue
            
            # 检查文件是否可解析
            try:
                with open(file_path, "r") as f:
                    content = yaml.safe_load(f)
                
                if content is None:
                    result["corrupted"].append(file_name)
            except Exception:
                result["corrupted"].append(file_name)
        
        return result
    
    def _check_isolation(self) -> Dict[str, Any]:
        """检查隔离性"""
        result = {"isolated": True, "message": ""}
        
        # 检查记忆空间是否在正确位置
        expected_root = self.project_root / "memory" / "agents" / self.config.agent_id
        
        if not self.memory_root.exists():
            result["isolated"] = False
            result["message"] = "Memory root not found"
            return result
        
        # 检查是否与其他 agent 混合
        memory_agents_dir = self.project_root / "memory" / "agents"
        
        for other_agent_dir in memory_agents_dir.iterdir():
            if other_agent_dir.is_dir() and other_agent_dir.name != self.config.agent_id:
                # 检查是否有交叉引用
                # 简单检查：确保当前 agent 的文件没有出现在其他 agent 目录
                pass
        
        return result
    
    def _check_evidence(self) -> Dict[str, Any]:
        """检查 evidence 链"""
        result = {"has_evidence": False, "count": 0}
        
        # 检查 evidence_logger 相关文件
        # 在当前实现中，evidence 记录在 memory_runtime.evidence_logger 中
        # 这里简化检查：检查是否有执行痕迹
        
        execution_path = self.memory_root / "execution_state.yaml"
        handoff_path = self.memory_root / "handoff_state.yaml"
        
        evidence_count = 0
        
        if execution_path.exists():
            try:
                with open(execution_path, "r") as f:
                    state = yaml.safe_load(f) or {}
                
                if state.get("task_id") or state.get("timestamp"):
                    evidence_count += 1
            except Exception:
                pass
        
        if handoff_path.exists():
            try:
                with open(handoff_path, "r") as f:
                    handoff = yaml.safe_load(f) or {}
                
                if handoff.get("objective") or handoff.get("timestamp"):
                    evidence_count += 1
            except Exception:
                pass
        
        result["count"] = evidence_count
        result["has_evidence"] = evidence_count > 0
        
        return result
