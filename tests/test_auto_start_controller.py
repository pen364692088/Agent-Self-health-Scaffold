"""
Test Auto Start Controller

测试自动启动控制器
"""

import pytest
from runtime.auto_start_controller import (
    AutoStartController,
    FeatureFlags,
    AutoStartDecision,
    DecisionType,
    RunMode
)


class TestFeatureFlags:
    """测试 Feature Flags"""
    
    def test_default_flags(self):
        """测试默认 flags"""
        flags = FeatureFlags()
        
        assert flags.is_main_flow_enabled() is True
        assert flags.get_mode() == "guarded-auto"
        assert flags.is_kill_switch_enabled() is False
    
    def test_get_flag(self):
        """测试获取 flag"""
        flags = FeatureFlags()
        
        assert flags.get("telegram.high_risk_requires_approval") is True
        assert flags.get("nonexistent_flag", "default") == "default"
    
    def test_set_mode(self):
        """测试设置模式"""
        flags = FeatureFlags()
        
        flags.set_mode("shadow")
        assert flags.get_mode() == "shadow"
        
        flags.set_mode("guarded-auto")
        assert flags.get_mode() == "guarded-auto"
        
        with pytest.raises(ValueError):
            flags.set_mode("invalid_mode")


class TestAutoStartController:
    """测试自动启动控制器"""
    
    def test_decide_kill_switch_enabled(self):
        """测试 Kill Switch 启用时的决策"""
        controller = AutoStartController()
        controller.feature_flags.set("telegram.kill_switch_enabled", True)
        
        event = {"event_id": "test_001"}
        route_decision = {"type": "new_task"}
        
        decision = controller.decide(event, route_decision)
        
        assert decision.decision_type == DecisionType.SAFE_MODE.value
        assert "Kill switch" in decision.reason
    
    def test_decide_main_flow_disabled(self):
        """测试主流程禁用时的决策"""
        controller = AutoStartController()
        controller.feature_flags.set("telegram.main_flow_enabled", False)
        
        event = {"event_id": "test_002"}
        route_decision = {"type": "new_task"}
        
        decision = controller.decide(event, route_decision)
        
        assert decision.decision_type == DecisionType.MANUAL_MODE.value
    
    def test_decide_control_command(self):
        """测试控制命令决策"""
        controller = AutoStartController()
        
        event = {"event_id": "test_003"}
        route_decision = {"type": "control", "command": "/status"}
        
        decision = controller.decide(event, route_decision)
        
        assert decision.decision_type == DecisionType.CONTROL.value
        assert decision.action["type"] == "control_routing"
    
    def test_decide_chat_message(self):
        """测试普通聊天决策"""
        controller = AutoStartController()
        
        event = {"event_id": "test_004"}
        route_decision = {"type": "chat"}
        
        decision = controller.decide(event, route_decision)
        
        assert decision.decision_type == DecisionType.DIRECT_REPLY.value
    
    def test_decide_new_task_shadow_mode(self):
        """测试 shadow 模式下的新任务决策"""
        controller = AutoStartController()
        controller.feature_flags.set_mode("shadow")
        
        event = {"event_id": "test_005"}
        route_decision = {"type": "new_task", "objective": "Test task"}
        
        decision = controller.decide(event, route_decision)
        
        assert decision.decision_type == DecisionType.CREATE_TASK.value
        assert decision.action["type"] == "observe_only"
    
    def test_decide_new_task_guarded_auto(self):
        """测试 guarded-auto 模式下的新任务决策"""
        controller = AutoStartController()
        controller.feature_flags.set_mode("guarded-auto")
        
        event = {"event_id": "test_006"}
        route_decision = {"type": "new_task", "objective": "Test task"}
        
        # 低风险
        decision = controller.decide(event, route_decision, {"risk_level": "low"})
        assert decision.action["type"] == "auto_proceed"
        assert decision.action["requires_approval"] is False
        
        # 高风险
        decision = controller.decide(event, route_decision, {"risk_level": "high"})
        assert decision.action["type"] == "pause_for_approval"
        assert decision.action["requires_approval"] is True
    
    def test_decide_new_task_full_auto(self):
        """测试 full-auto 模式下的新任务决策"""
        controller = AutoStartController()
        controller.feature_flags.set_mode("full-auto")
        
        event = {"event_id": "test_007"}
        route_decision = {"type": "new_task", "objective": "Test task"}
        
        decision = controller.decide(event, route_decision, {"risk_level": "high"})
        
        assert decision.action["type"] == "auto_proceed"
        assert decision.action["requires_approval"] is False
    
    def test_set_mode(self):
        """测试切换模式"""
        controller = AutoStartController()
        
        result = controller.set_mode("shadow")
        assert result["success"] is True
        assert result["new_mode"] == "shadow"
        
        result = controller.set_mode("invalid")
        assert result["success"] is False
    
    def test_enable_kill_switch(self):
        """测试启用 Kill Switch"""
        controller = AutoStartController()
        
        result = controller.enable_kill_switch()
        
        assert result["success"] is True
        assert controller.feature_flags.is_kill_switch_enabled() is True
    
    def test_get_status(self):
        """测试获取状态"""
        controller = AutoStartController()
        
        status = controller.get_status()
        
        assert "mode" in status
        assert "main_flow_enabled" in status
        assert "kill_switch_enabled" in status
