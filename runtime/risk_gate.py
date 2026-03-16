"""
Risk Gate - 风险门禁

评估操作风险等级，决定是否自动执行。
"""

import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict, field
from enum import Enum


class RiskLevel(str, Enum):
    """风险等级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskAction(str, Enum):
    """风险动作"""
    EXECUTE = "execute"
    EXECUTE_WITH_WARNING = "execute_with_warning"
    PAUSE_FOR_APPROVAL = "pause_for_approval"
    BLOCK = "block"


@dataclass
class Operation:
    """操作描述"""
    type: str  # shell_command, file_operation, git_operation, api_call, other
    description: str
    command: Optional[str] = None
    target_path: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RiskAssessment:
    """风险评估结果"""
    decision_id: str
    timestamp: str
    operation: Dict[str, Any]
    risk_level: str
    reason: str
    matched_patterns: List[Dict[str, Any]] = field(default_factory=list)
    action: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class RiskPatternMatcher:
    """风险模式匹配器"""
    
    CRITICAL_PATTERNS = [
        (r"rm\s+-rf\s+/", "Deleting root directory"),
        (r"rm\s+-rf\s+~", "Deleting home directory"),
        (r"dd\s+if=.*of=/dev/", "Disk write operation"),
        (r"mkfs", "Format filesystem"),
        (r">\s*/dev/sd[a-z]", "Direct disk write"),
        (r"chmod\s+(-R\s+)?777", "Insecure permissions"),
        (r"DROP\s+DATABASE", "Drop database"),
        (r"TRUNCATE\s+TABLE", "Truncate table"),
    ]
    
    HIGH_RISK_PATTERNS = [
        (r"rm\s+-rf", "Force delete recursively"),
        (r"git\s+push\s+--force", "Force push to git"),
        (r"git\s+reset\s+--hard", "Hard reset git"),
        (r"DROP\s+TABLE", "Drop table"),
        (r"DELETE\s+FROM", "Delete from table"),
        (r"TRUNCATE", "Truncate"),
        (r"chmod\s+777", "Insecure permissions"),
        (r":(){ :|:& };:", "Fork bomb"),
        (r"sudo\s+rm", "Sudo delete"),
        (r">\s*/dev/null\s+2>&1", "Suppress all output"),
    ]
    
    MEDIUM_RISK_PATTERNS = [
        (r"rm\s+", "Delete files"),
        (r"mv\s+", "Move files"),
        (r"cp\s+", "Copy files"),
        (r"git\s+push", "Push to git"),
        (r"npm\s+publish", "Publish to npm"),
        (r"pip\s+install\s+--user", "Install pip packages"),
        (r"curl\s+.*\|\s*bash", "Execute remote script"),
        (r"wget\s+.*\|\s*bash", "Execute remote script"),
    ]
    
    def match(self, text: str) -> List[Dict[str, Any]]:
        """匹配风险模式"""
        matches = []
        
        for pattern, description in self.CRITICAL_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                matches.append({
                    "pattern": pattern,
                    "description": description,
                    "severity": "critical"
                })
        
        for pattern, description in self.HIGH_RISK_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                matches.append({
                    "pattern": pattern,
                    "description": description,
                    "severity": "high"
                })
        
        for pattern, description in self.MEDIUM_RISK_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                matches.append({
                    "pattern": pattern,
                    "description": description,
                    "severity": "medium"
                })
        
        return matches


class CriticalFileChecker:
    """关键文件检查器"""
    
    CRITICAL_FILES = [
        ".env",
        "id_rsa",
        "id_ed25519",
        ".pem",
        ".key",
        "credentials.json",
        "secrets.json",
        ".htpasswd",
        "shadow",
        "passwd",
    ]
    
    CRITICAL_DIRECTORIES = [
        "/etc",
        "/root",
        "/home",
        "~/.ssh",
        "~/.gnupg",
    ]
    
    def is_critical(self, path: str) -> bool:
        """检查是否是关键文件"""
        path_lower = path.lower()
        
        for critical_file in self.CRITICAL_FILES:
            if critical_file in path_lower:
                return True
        
        for critical_dir in self.CRITICAL_DIRECTORIES:
            if critical_dir in path:
                return True
        
        return False
    
    def affects_critical_files(self, paths: List[str]) -> bool:
        """检查是否影响关键文件"""
        return any(self.is_critical(p) for p in paths)


class RiskGate:
    """风险门禁"""
    
    def __init__(
        self,
        audit_log_path: str = None,
        approval_registry: Any = None
    ):
        self.pattern_matcher = RiskPatternMatcher()
        self.critical_file_checker = CriticalFileChecker()
        self.approval_registry = approval_registry
        self.audit_log_path = Path(audit_log_path) if audit_log_path else None
    
    def assess(self, operation: Operation, context: Optional[Dict[str, Any]] = None) -> RiskAssessment:
        """
        评估操作风险
        
        Args:
            operation: 操作描述
            context: 上下文（包含 mode, task_id, step_id 等）
            
        Returns:
            RiskAssessment 风险评估结果
        """
        decision_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat() + "Z"
        context = context or {}
        
        # 1. 模式匹配
        text_to_check = operation.command or operation.description
        matched_patterns = self.pattern_matcher.match(text_to_check)
        
        # 2. 关键文件检查
        if operation.target_path:
            if self.critical_file_checker.is_critical(operation.target_path):
                matched_patterns.append({
                    "pattern": "critical_file",
                    "description": f"Operation affects critical file: {operation.target_path}",
                    "severity": "high"
                })
        
        # 3. 确定风险等级
        risk_level = RiskLevel.LOW.value
        reason = "No risk patterns matched"
        
        if matched_patterns:
            severities = [p["severity"] for p in matched_patterns]
            if "critical" in severities:
                risk_level = RiskLevel.CRITICAL.value
                reason = "Critical risk pattern matched"
            elif "high" in severities:
                risk_level = RiskLevel.HIGH.value
                reason = "High risk pattern matched"
            elif "medium" in severities:
                risk_level = RiskLevel.MEDIUM.value
                reason = "Medium risk pattern matched"
        
        # 4. 根据模式和风险等级确定动作
        mode = context.get("mode", "guarded-auto")
        
        action = self._determine_action(risk_level, mode, operation)
        
        assessment = RiskAssessment(
            decision_id=decision_id,
            timestamp=timestamp,
            operation={
                "type": operation.type,
                "description": operation.description,
                "command": operation.command,
                "target_path": operation.target_path
            },
            risk_level=risk_level,
            reason=reason,
            matched_patterns=matched_patterns,
            action=action,
            context=context
        )
        
        # 5. 记录审计日志
        self._log_assessment(assessment)
        
        return assessment
    
    def _determine_action(self, risk_level: str, mode: str, operation: Operation) -> Dict[str, Any]:
        """确定动作"""
        # 动作矩阵
        # | Risk Level | shadow       | guarded-auto      | full-auto          |
        # |------------|--------------|-------------------|--------------------|
        # | low        | execute      | execute           | execute            |
        # | medium     | execute      | execute + warning | execute            |
        # | high       | pause        | pause + approval  | execute            |
        # | critical   | block        | block             | block + 2FA        |
        
        if risk_level == RiskLevel.LOW.value:
            return {
                "type": RiskAction.EXECUTE.value,
                "message": "Low risk operation, proceeding automatically"
            }
        
        elif risk_level == RiskLevel.MEDIUM.value:
            if mode == "shadow":
                return {
                    "type": RiskAction.EXECUTE.value,
                    "message": "Medium risk, but shadow mode allows"
                }
            elif mode == "guarded-auto":
                return {
                    "type": RiskAction.EXECUTE_WITH_WARNING.value,
                    "message": f"⚠️ Medium risk operation: {operation.description}\nProceeding with caution."
                }
            else:  # full-auto
                return {
                    "type": RiskAction.EXECUTE.value,
                    "message": "Medium risk, full-auto mode allows"
                }
        
        elif risk_level == RiskLevel.HIGH.value:
            if mode == "shadow":
                return {
                    "type": RiskAction.PAUSE_FOR_APPROVAL.value,
                    "message": "High risk, shadow mode requires observation"
                }
            elif mode == "guarded-auto":
                approval_id = self._create_approval_request(operation) if self.approval_registry else None
                return {
                    "type": RiskAction.PAUSE_FOR_APPROVAL.value,
                    "message": f"🚨 High risk operation detected:\n{operation.description}\n\nPlease confirm to proceed.",
                    "approval_id": approval_id
                }
            else:  # full-auto
                return {
                    "type": RiskAction.EXECUTE.value,
                    "message": "High risk, full-auto mode allows"
                }
        
        else:  # CRITICAL
            if mode == "full-auto":
                return {
                    "type": RiskAction.BLOCK.value,
                    "message": "🚫 Critical risk operation blocked even in full-auto mode.\nThis operation requires manual verification."
                }
            else:
                return {
                    "type": RiskAction.BLOCK.value,
                    "message": "🚫 Critical risk operation blocked.\nThis operation is too dangerous to execute automatically."
                }
    
    def _create_approval_request(self, operation: Operation) -> Optional[str]:
        """创建审批请求"""
        if self.approval_registry:
            return self.approval_registry.create_approval(
                task_id=operation.details.get("task_id"),
                step_id=operation.details.get("step_id"),
                operation=operation.to_dict() if hasattr(operation, 'to_dict') else {
                    "type": operation.type,
                    "description": operation.description
                },
                chat_id=operation.details.get("chat_id"),
                message_id=operation.details.get("message_id")
            )
        return None
    
    def _log_assessment(self, assessment: RiskAssessment):
        """记录审计日志"""
        if self.audit_log_path:
            with open(self.audit_log_path, 'a') as f:
                f.write(assessment.to_dict().__str__() + "\n")
    
    def is_safe_to_auto_execute(self, operation: Operation, mode: str) -> bool:
        """快速检查是否可以安全自动执行"""
        assessment = self.assess(operation, {"mode": mode})
        return assessment.action["type"] in [RiskAction.EXECUTE.value, RiskAction.EXECUTE_WITH_WARNING.value]


# 便捷函数
def assess_risk(operation: Operation, context: Optional[Dict[str, Any]] = None) -> RiskAssessment:
    """便捷函数：评估风险"""
    gate = RiskGate()
    return gate.assess(operation, context)


def is_safe_operation(command: str, mode: str = "guarded-auto") -> bool:
    """便捷函数：检查命令是否安全"""
    operation = Operation(
        type="shell_command",
        description=command,
        command=command
    )
    gate = RiskGate()
    assessment = gate.assess(operation, {"mode": mode})
    return assessment.risk_level in [RiskLevel.LOW.value, RiskLevel.MEDIUM.value]
