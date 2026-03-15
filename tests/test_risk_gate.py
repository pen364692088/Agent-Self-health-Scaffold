"""
Test Risk Gate

测试风险门禁
"""

import pytest
from runtime.risk_gate import (
    RiskGate,
    RiskPatternMatcher,
    CriticalFileChecker,
    RiskLevel,
    RiskAction,
    Operation,
    assess_risk,
    is_safe_operation
)


class TestRiskPatternMatcher:
    """测试风险模式匹配器"""
    
    def test_match_critical_patterns(self):
        """测试严重风险模式"""
        matcher = RiskPatternMatcher()
        
        # 删除根目录
        matches = matcher.match("rm -rf /")
        assert any(p["severity"] == "critical" for p in matches)
        
        # dd 写磁盘
        matches = matcher.match("dd if=/dev/zero of=/dev/sda")
        assert any(p["severity"] == "critical" for p in matches)
    
    def test_match_high_risk_patterns(self):
        """测试高风险模式"""
        matcher = RiskPatternMatcher()
        
        # 强制删除
        matches = matcher.match("rm -rf ./temp")
        assert any(p["severity"] == "high" for p in matches)
        
        # 强制推送
        matches = matcher.match("git push --force")
        assert any(p["severity"] == "high" for p in matches)
        
        # 删除表
        matches = matcher.match("DROP TABLE users")
        assert any(p["severity"] == "high" for p in matches)
    
    def test_match_medium_risk_patterns(self):
        """测试中等风险模式"""
        matcher = RiskPatternMatcher()
        
        # 删除文件
        matches = matcher.match("rm file.txt")
        assert any(p["severity"] == "medium" for p in matches)
        
        # 推送代码
        matches = matcher.match("git push origin main")
        assert any(p["severity"] == "medium" for p in matches)
    
    def test_no_match(self):
        """测试无匹配"""
        matcher = RiskPatternMatcher()
        
        matches = matcher.match("ls -la")
        assert len(matches) == 0
        
        matches = matcher.match("echo 'hello'")
        assert len(matches) == 0


class TestCriticalFileChecker:
    """测试关键文件检查器"""
    
    def test_is_critical_file(self):
        """测试关键文件检测"""
        checker = CriticalFileChecker()
        
        assert checker.is_critical(".env") is True
        assert checker.is_critical("id_rsa") is True
        assert checker.is_critical("credentials.json") is True
        assert checker.is_critical("config.yaml") is False
        assert checker.is_critical("README.md") is False
    
    def test_is_critical_directory(self):
        """测试关键目录检测"""
        checker = CriticalFileChecker()
        
        assert checker.is_critical("/etc/passwd") is True
        assert checker.is_critical("~/.ssh/id_rsa") is True
        assert checker.is_critical("/home/user/project/file.py") is True
        assert checker.is_critical("/tmp/test") is False
    
    def test_affects_critical_files(self):
        """测试影响关键文件"""
        checker = CriticalFileChecker()
        
        assert checker.affects_critical_files([".env", "config.yaml"]) is True
        assert checker.affects_critical_files(["README.md", "main.py"]) is False


class TestRiskGate:
    """测试风险门禁"""
    
    def test_assess_low_risk(self):
        """测试低风险评估"""
        gate = RiskGate()
        
        operation = Operation(
            type="shell_command",
            description="List files",
            command="ls -la"
        )
        
        assessment = gate.assess(operation, {"mode": "guarded-auto"})
        
        assert assessment.risk_level == RiskLevel.LOW.value
        assert assessment.action["type"] == RiskAction.EXECUTE.value
    
    def test_assess_high_risk(self):
        """测试高风险评估"""
        gate = RiskGate()
        
        operation = Operation(
            type="shell_command",
            description="Delete directory",
            command="rm -rf ./temp"
        )
        
        assessment = gate.assess(operation, {"mode": "guarded-auto"})
        
        assert assessment.risk_level == RiskLevel.HIGH.value
        assert assessment.action["type"] == RiskAction.PAUSE_FOR_APPROVAL.value
    
    def test_assess_critical_risk(self):
        """测试严重风险评估"""
        gate = RiskGate()
        
        operation = Operation(
            type="shell_command",
            description="Delete root",
            command="rm -rf /"
        )
        
        assessment = gate.assess(operation, {"mode": "guarded-auto"})
        
        assert assessment.risk_level == RiskLevel.CRITICAL.value
        assert assessment.action["type"] == RiskAction.BLOCK.value
    
    def test_mode_affects_action(self):
        """测试模式影响动作"""
        gate = RiskGate()
        
        operation = Operation(
            type="shell_command",
            description="Force delete",
            command="rm -rf ./temp"
        )
        
        # guarded-auto: 暂停
        assessment = gate.assess(operation, {"mode": "guarded-auto"})
        assert assessment.action["type"] == RiskAction.PAUSE_FOR_APPROVAL.value
        
        # full-auto: 执行
        assessment = gate.assess(operation, {"mode": "full-auto"})
        assert assessment.action["type"] == RiskAction.EXECUTE.value
        
        # shadow: 暂停
        assessment = gate.assess(operation, {"mode": "shadow"})
        assert assessment.action["type"] == RiskAction.PAUSE_FOR_APPROVAL.value
    
    def test_critical_file_check(self):
        """测试关键文件检查"""
        gate = RiskGate()
        
        operation = Operation(
            type="file_operation",
            description="Read .env file",
            target_path=".env"
        )
        
        assessment = gate.assess(operation, {"mode": "guarded-auto"})
        
        assert assessment.risk_level == RiskLevel.HIGH.value
    
    def test_is_safe_to_auto_execute(self):
        """测试是否可以安全自动执行"""
        gate = RiskGate()
        
        # 安全操作
        safe_op = Operation(type="shell_command", description="List files", command="ls")
        assert gate.is_safe_to_auto_execute(safe_op, "guarded-auto") is True
        
        # 危险操作
        dangerous_op = Operation(type="shell_command", description="Delete", command="rm -rf /")
        assert gate.is_safe_to_auto_execute(dangerous_op, "guarded-auto") is False


class TestConvenienceFunctions:
    """测试便捷函数"""
    
    def test_assess_risk(self):
        """测试 assess_risk 便捷函数"""
        operation = Operation(
            type="shell_command",
            description="Test",
            command="ls"
        )
        
        assessment = assess_risk(operation, {"mode": "guarded-auto"})
        
        assert assessment.risk_level == RiskLevel.LOW.value
    
    def test_is_safe_operation(self):
        """测试 is_safe_operation 便捷函数"""
        assert is_safe_operation("ls -la", "guarded-auto") is True
        assert is_safe_operation("rm -rf /", "guarded-auto") is False
