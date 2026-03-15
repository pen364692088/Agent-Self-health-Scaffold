"""
Autonomy Policy Layer 测试

测试自治策略层的核心功能:
- 默认可自治动作
- 必须阻断动作
- 需要审批动作
- 风险等级评估
- 安全停止条件
- 策略证据日志
"""

import pytest
import tempfile
import os
from pathlib import Path
from datetime import datetime

from runtime.autonomy_policy import (
    AutonomyPolicy,
    AutonomyDecision,
    ActionType,
    PolicyEvidence,
    PolicyRule,
    SafeStopCondition,
    AutonomyPolicyContext,
    create_default_policy,
    quick_decide,
)
from runtime.risk_gate import (
    RiskLevel,
    RiskAction,
    Operation,
)


class TestAutonomyPolicyBasics:
    """基础功能测试"""
    
    def test_default_policy_initialization(self):
        """测试默认策略初始化"""
        policy = AutonomyPolicy()
        
        assert policy.mode == "guarded-auto"
        assert ActionType.READ_DOCUMENT.value in policy.allowed_actions
        assert ActionType.MASS_DELETE.value in policy.forbidden_actions
        assert ActionType.LARGE_CODE_CHANGE.value in policy.approval_required_actions
    
    def test_policy_summary(self):
        """测试策略摘要"""
        policy = AutonomyPolicy()
        summary = policy.get_policy_summary()
        
        assert "mode" in summary
        assert "allowed_actions_count" in summary
        assert "forbidden_actions_count" in summary
        assert "approval_required_count" in summary
        assert summary["mode"] == "guarded-auto"
    
    def test_policy_export(self):
        """测试策略导出"""
        policy = AutonomyPolicy()
        exported = policy.export_policy()
        
        assert "mode" in exported
        assert "allowed_actions" in exported
        assert "forbidden_actions" in exported
        assert "approval_required_actions" in exported


class TestAllowedActions:
    """允许动作测试"""
    
    def test_read_document_allowed(self):
        """测试读取文档允许自动执行"""
        policy = AutonomyPolicy()
        evidence = policy.decide(ActionType.READ_DOCUMENT.value)
        
        assert evidence.decision == AutonomyDecision.ALLOW_AUTO.value
        assert evidence.risk_level == RiskLevel.LOW.value
    
    def test_run_test_allowed(self):
        """测试运行测试允许自动执行"""
        policy = AutonomyPolicy()
        evidence = policy.decide(ActionType.RUN_TEST.value)
        
        assert evidence.decision == AutonomyDecision.ALLOW_AUTO.value
    
    def test_small_code_fix_allowed(self):
        """测试小范围代码修复允许自动执行"""
        policy = AutonomyPolicy()
        evidence = policy.decide(ActionType.SMALL_CODE_FIX.value)
        
        assert evidence.decision == AutonomyDecision.ALLOW_AUTO.value
    
    def test_write_report_allowed(self):
        """测试写报告允许自动执行"""
        policy = AutonomyPolicy()
        evidence = policy.decide(ActionType.WRITE_REPORT.value)
        
        assert evidence.decision == AutonomyDecision.ALLOW_AUTO.value
    
    def test_retry_allowed(self):
        """测试重试允许自动执行"""
        policy = AutonomyPolicy()
        evidence = policy.decide(ActionType.RETRY.value)
        
        assert evidence.decision == AutonomyDecision.ALLOW_AUTO.value
    
    def test_rollback_allowed(self):
        """测试回滚允许自动执行"""
        policy = AutonomyPolicy()
        evidence = policy.decide(ActionType.ROLLBACK.value)
        
        assert evidence.decision == AutonomyDecision.ALLOW_AUTO.value


class TestForbiddenActions:
    """禁止动作测试"""
    
    def test_mass_delete_blocked(self):
        """测试大规模删除被阻断"""
        policy = AutonomyPolicy()
        evidence = policy.decide(ActionType.MASS_DELETE.value)
        
        assert evidence.decision == AutonomyDecision.BLOCK.value
        assert evidence.risk_level == RiskLevel.CRITICAL.value
        assert "forbidden:mass_delete" in evidence.matched_rules
    
    def test_modify_gate_rules_blocked(self):
        """测试修改 Gate 规则被阻断"""
        policy = AutonomyPolicy()
        evidence = policy.decide(ActionType.MODIFY_GATE_RULES.value)
        
        assert evidence.decision == AutonomyDecision.BLOCK.value
    
    def test_destroy_baseline_blocked(self):
        """测试破坏基线被阻断"""
        policy = AutonomyPolicy()
        evidence = policy.decide(ActionType.DESTROY_BASELINE.value)
        
        assert evidence.decision == AutonomyDecision.BLOCK.value
    
    def test_credential_operation_blocked(self):
        """测试敏感凭据操作被阻断"""
        policy = AutonomyPolicy()
        evidence = policy.decide(ActionType.CREDENTIAL_OPERATION.value)
        
        assert evidence.decision == AutonomyDecision.BLOCK.value
    
    def test_payment_operation_blocked(self):
        """测试支付操作被阻断"""
        policy = AutonomyPolicy()
        evidence = policy.decide(ActionType.PAYMENT_OPERATION.value)
        
        assert evidence.decision == AutonomyDecision.BLOCK.value


class TestApprovalRequiredActions:
    """需要审批动作测试"""
    
    def test_large_code_change_requires_approval(self):
        """测试大范围代码修改需要审批"""
        policy = AutonomyPolicy()
        evidence = policy.decide(ActionType.LARGE_CODE_CHANGE.value)
        
        assert evidence.decision == AutonomyDecision.REQUIRE_APPROVAL.value
        assert "approval_required:large_code_change" in evidence.matched_rules
    
    def test_external_api_call_requires_approval(self):
        """测试外部 API 调用需要审批"""
        policy = AutonomyPolicy()
        evidence = policy.decide(ActionType.EXTERNAL_API_CALL.value)
        
        assert evidence.decision == AutonomyDecision.REQUIRE_APPROVAL.value
    
    def test_deploy_operation_requires_approval(self):
        """测试部署操作需要审批"""
        policy = AutonomyPolicy()
        evidence = policy.decide(ActionType.DEPLOY_OPERATION.value)
        
        assert evidence.decision == AutonomyDecision.REQUIRE_APPROVAL.value


class TestRiskAssessment:
    """风险评估集成测试"""
    
    def test_low_risk_operation_allowed(self):
        """测试低风险操作允许执行"""
        policy = AutonomyPolicy()
        operation = Operation(
            type="shell_command",
            description="echo hello",
            command="echo hello"
        )
        
        evidence = policy.decide(ActionType.RUN_TEST.value, operation)
        assert evidence.decision == AutonomyDecision.ALLOW_AUTO.value
    
    def test_critical_risk_command_blocks_allowed_action(self):
        """测试关键风险命令阻断允许的动作"""
        policy = AutonomyPolicy()
        operation = Operation(
            type="shell_command",
            description="Dangerous operation",
            command="rm -rf /"
        )
        
        # 即使是允许的动作，如果风险等级是 CRITICAL 也会被阻断
        evidence = policy.decide(ActionType.RUN_TEST.value, operation)
        assert evidence.decision == AutonomyDecision.BLOCK.value
    
    def test_high_risk_operation_with_allowed_action(self):
        """测试高风险操作与允许动作"""
        policy = AutonomyPolicy()
        operation = Operation(
            type="shell_command",
            description="Force delete",
            command="rm -rf ./some_dir"
        )
        
        evidence = policy.decide(ActionType.SMALL_CODE_FIX.value, operation)
        # 高风险 + 允许动作 = 需要审批
        assert evidence.decision == AutonomyDecision.REQUIRE_APPROVAL.value


class TestSafeStopConditions:
    """安全停止条件测试"""
    
    def test_consecutive_blocks_triggers_safe_stop(self):
        """测试连续阻断触发安全停止"""
        policy = AutonomyPolicy()
        policy._max_consecutive_blocks = 2
        
        # 连续触发阻断 (超过阈值)
        for _ in range(3):
            policy.decide(ActionType.MASS_DELETE.value)
        
        # 检查安全停止被触发 (在第3次调用开始时检测到连续阻断>=阈值)
        assert policy._safe_stop_triggered == "consecutive_blocks_exceeded"
    
    def test_safe_stop_blocks_all_operations(self):
        """测试安全停止后阻断所有操作"""
        policy = AutonomyPolicy()
        # 直接设置安全停止状态
        policy._consecutive_blocks = 10  # 超过阈值
        
        # 下一次 decide 会触发 safe_stop
        evidence = policy.decide(ActionType.READ_DOCUMENT.value)
        assert evidence.decision == AutonomyDecision.SAFE_STOP.value
    
    def test_clear_safe_stop(self):
        """测试清除安全停止状态"""
        policy = AutonomyPolicy()
        policy._safe_stop_triggered = "test"
        policy._consecutive_blocks = 5
        
        policy.clear_safe_stop()
        
        assert policy._safe_stop_triggered is None
        assert policy._consecutive_blocks == 0


class TestPolicyModes:
    """策略模式测试"""
    
    def test_shadow_mode(self):
        """测试影子模式"""
        policy = AutonomyPolicy()
        policy.mode = "shadow"
        
        # 未知动作在影子模式下允许执行（记录）
        evidence = policy.decide("unknown_action")
        assert evidence.decision == AutonomyDecision.ALLOW_WITH_LOG.value
    
    def test_guarded_auto_mode(self):
        """测试守护自动模式"""
        policy = AutonomyPolicy()
        policy.mode = "guarded-auto"
        
        # 未知动作在守护模式下需要审批
        evidence = policy.decide("unknown_action")
        assert evidence.decision == AutonomyDecision.REQUIRE_APPROVAL.value
    
    def test_full_auto_mode(self):
        """测试完全自动模式"""
        policy = AutonomyPolicy()
        policy.mode = "full-auto"
        
        # 未知动作在完全自动模式下允许执行
        evidence = policy.decide("unknown_action")
        assert evidence.decision == AutonomyDecision.ALLOW_AUTO.value
    
    def test_forbidden_action_blocks_in_all_modes(self):
        """测试禁止动作在所有模式下都被阻断"""
        for mode in ["shadow", "guarded-auto", "full-auto"]:
            policy = AutonomyPolicy()
            policy.mode = mode
            
            evidence = policy.decide(ActionType.MASS_DELETE.value)
            assert evidence.decision == AutonomyDecision.BLOCK.value, f"Mode: {mode}"


class TestPolicyEvidenceLog:
    """策略证据日志测试"""
    
    def test_evidence_recorded(self):
        """测试证据被记录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "evidence.jsonl")
            policy = AutonomyPolicy(evidence_log_path=log_path)
            
            policy.decide(ActionType.READ_DOCUMENT.value)
            
            assert len(policy.evidence_log) == 1
            
            # 检查文件写入
            with open(log_path, 'r') as f:
                content = f.read()
                assert "read_document" in content
    
    def test_evidence_contains_matched_rules(self):
        """测试证据包含匹配规则"""
        policy = AutonomyPolicy()
        
        evidence = policy.decide(ActionType.MASS_DELETE.value)
        
        assert len(evidence.matched_rules) > 0
        assert any("forbidden" in rule for rule in evidence.matched_rules)
    
    def test_evidence_to_dict(self):
        """测试证据序列化"""
        policy = AutonomyPolicy()
        evidence = policy.decide(ActionType.READ_DOCUMENT.value)
        
        evidence_dict = evidence.to_dict()
        
        assert "evidence_id" in evidence_dict
        assert "timestamp" in evidence_dict
        assert "action_type" in evidence_dict
        assert "decision" in evidence_dict


class TestPolicyConfiguration:
    """策略配置测试"""
    
    def test_load_config(self):
        """测试加载配置"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "policy.yaml")
            with open(config_path, 'w') as f:
                f.write("""
mode: "full-auto"
allowed_actions:
  - custom_action
forbidden_actions:
  - dangerous_action
""")
            
            policy = AutonomyPolicy(config_path=config_path)
            
            assert policy.mode == "full-auto"
            assert "custom_action" in policy.allowed_actions
            assert "dangerous_action" in policy.forbidden_actions
    
    def test_policy_override(self):
        """测试策略覆盖"""
        policy = AutonomyPolicy()
        
        override = {
            "add_allowed": ["new_allowed_action"],
            "add_forbidden": ["new_forbidden_action"],
            "mode": "shadow"
        }
        policy._apply_override(override)
        
        assert "new_allowed_action" in policy.allowed_actions
        assert "new_forbidden_action" in policy.forbidden_actions
        assert policy.mode == "shadow"


class TestPolicyContextManager:
    """策略上下文管理器测试"""
    
    def test_temporary_override(self):
        """测试临时覆盖"""
        policy = AutonomyPolicy()
        original_mode = policy.mode
        
        with AutonomyPolicyContext(policy, {"mode": "full-auto"}):
            assert policy.mode == "full-auto"
        
        assert policy.mode == original_mode
    
    def test_context_restores_on_exception(self):
        """测试异常时恢复状态"""
        policy = AutonomyPolicy()
        original_mode = policy.mode
        
        try:
            with AutonomyPolicyContext(policy, {"mode": "full-auto"}):
                raise ValueError("Test exception")
        except ValueError:
            pass
        
        assert policy.mode == original_mode


class TestDynamicPolicyModification:
    """动态策略修改测试"""
    
    def test_add_allowed_action(self):
        """测试添加允许动作"""
        policy = AutonomyPolicy()
        
        policy.add_allowed_action("new_allowed_action")
        
        assert "new_allowed_action" in policy.allowed_actions
        assert "new_allowed_action" not in policy.forbidden_actions
        assert "new_allowed_action" not in policy.approval_required_actions
    
    def test_add_forbidden_action(self):
        """测试添加禁止动作"""
        policy = AutonomyPolicy()
        
        policy.add_forbidden_action("new_forbidden_action")
        
        assert "new_forbidden_action" in policy.forbidden_actions
        assert "new_forbidden_action" not in policy.allowed_actions
    
    def test_add_approval_required_action(self):
        """测试添加需要审批动作"""
        policy = AutonomyPolicy()
        
        policy.add_approval_required_action("new_approval_action")
        
        assert "new_approval_action" in policy.approval_required_actions
        assert "new_approval_action" not in policy.allowed_actions


class TestConvenienceFunctions:
    """便捷函数测试"""
    
    def test_create_default_policy(self):
        """测试创建默认策略"""
        policy = create_default_policy()
        
        assert isinstance(policy, AutonomyPolicy)
        assert policy.mode == "guarded-auto"
    
    def test_quick_decide_allowed(self):
        """测试快速决策 - 允许"""
        decision = quick_decide(ActionType.READ_DOCUMENT.value)
        
        assert decision == AutonomyDecision.ALLOW_AUTO
    
    def test_quick_decide_forbidden(self):
        """测试快速决策 - 禁止"""
        decision = quick_decide(ActionType.MASS_DELETE.value)
        
        assert decision == AutonomyDecision.BLOCK
    
    def test_quick_decide_with_mode(self):
        """测试快速决策 - 指定模式"""
        decision = quick_decide("unknown_action", mode="shadow")
        
        assert decision == AutonomyDecision.ALLOW_WITH_LOG


class TestIntegrationWithRiskGate:
    """与 RiskGate 集成测试"""
    
    def test_uses_risk_gate_for_assessment(self):
        """测试使用 RiskGate 进行评估"""
        policy = AutonomyPolicy()
        operation = Operation(
            type="shell_command",
            description="Run tests",
            command="pytest tests/"
        )
        
        evidence = policy.decide(ActionType.RUN_TEST.value, operation)
        
        assert "risk_assessment:" in evidence.matched_rules[0]
    
    def test_risk_gate_integration_for_high_risk(self):
        """测试 RiskGate 集成 - 高风险"""
        policy = AutonomyPolicy()
        operation = Operation(
            type="shell_command",
            description="Force push",
            command="git push --force"
        )
        
        evidence = policy.decide(ActionType.RUN_TEST.value, operation)
        
        # 高风险命令需要审批
        assert evidence.decision == AutonomyDecision.REQUIRE_APPROVAL.value


class TestEdgeCases:
    """边缘情况测试"""
    
    def test_empty_action_type(self):
        """测试空动作类型"""
        policy = AutonomyPolicy()
        
        evidence = policy.decide("")
        
        # 未知动作，使用默认策略
        assert evidence.decision in [
            AutonomyDecision.ALLOW_WITH_LOG.value,
            AutonomyDecision.REQUIRE_APPROVAL.value,
            AutonomyDecision.ALLOW_AUTO.value
        ]
    
    def test_none_operation(self):
        """测试无操作描述"""
        policy = AutonomyPolicy()
        
        evidence = policy.decide(ActionType.READ_DOCUMENT.value, None)
        
        assert evidence.decision == AutonomyDecision.ALLOW_AUTO.value
    
    def test_is_allowed_auto_convenience(self):
        """测试 is_allowed_auto 便捷方法"""
        policy = AutonomyPolicy()
        
        assert policy.is_allowed_auto(ActionType.READ_DOCUMENT.value)
        assert not policy.is_allowed_auto(ActionType.MASS_DELETE.value)


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
