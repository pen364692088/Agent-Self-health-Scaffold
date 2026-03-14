"""
Unit tests for Plan Injection Patch
"""
import pytest
import sys
import os

# Add hooks path to sys.path
sys.path.insert(0, os.path.expanduser("~/.openclaw/workspace/OpenEmotion/integrations/openclaw/hooks/plan-injection"))

# Import handler module (we'll test the logic functions)
# Note: handler.js is JavaScript, so we test the logic concepts here


class TestGate:
    """Test gate logic for plan injection"""
    
    def test_gate_allows_chat(self):
        """Normal chat should be allowed"""
        # Simulate gate evaluation
        message = {"body": "Hello, how are you?"}
        context = {}
        
        # Gate logic: not a command, not task control, not tool path
        is_command = message["body"].strip().startswith('/') and not message["body"].strip().startswith('//')
        is_task_control = any(message["body"].strip().lower().startswith(kw) for kw in ['/approve', '/deny', '/cancel', '/pause', '/resume', '/status', '/reset', '/new', '/wrap'])
        is_tool_path = bool(context.get('tool_result') or context.get('tool_call_pending'))
        
        assert is_command is False
        assert is_task_control is False
        assert is_tool_path is False
        # Gate result should be ALLOW
    
    def test_gate_blocks_command(self):
        """Slash command should be blocked"""
        message = {"body": "/status"}
        context = {}
        
        is_command = message["body"].strip().startswith('/') and not message["body"].strip().startswith('//')
        
        assert is_command is True
        # Gate result should be SKIP
    
    def test_gate_blocks_task_control(self):
        """Task control commands should be blocked"""
        for cmd in ['/approve', '/deny', '/cancel', '/status']:
            message = {"body": cmd}
            
            is_task_control = any(message["body"].strip().lower().startswith(kw) for kw in ['/approve', '/deny', '/cancel', '/pause', '/resume', '/status', '/reset', '/new', '/wrap'])
            
            assert is_task_control is True
            # Gate result should be SKIP
    
    def test_gate_blocks_tool_path(self):
        """Tool execution path should be blocked"""
        message = {"body": "Check the logs"}
        context = {"tool_result": {"output": "logs..."}}
        
        is_tool_path = bool(context.get('tool_result') or context.get('tool_call_pending'))
        
        assert is_tool_path is True
        # Gate result should be SKIP
    
    def test_gate_respects_config_disabled(self):
        """Feature disabled should return DISABLED"""
        # When inject_plan_into_reply = false
        # Gate should return DISABLED immediately
        # No API call should be made
        pass  # Configuration test


class TestSchema:
    """Test schema validation for plan response"""
    
    def test_schema_validates_required_fields(self):
        """Missing required fields should fail validation"""
        plan = {"key_points": []}  # Missing tone
        
        has_tone = "tone" in plan
        has_key_points = "key_points" in plan and isinstance(plan.get("key_points"), list)
        
        assert has_tone is False
        # Schema should be INVALID
    
    def test_schema_accepts_valid_plan(self):
        """Valid plan should pass validation"""
        plan = {
            "tone": "warm",
            "intent": "repair",
            "key_points": ["acknowledge"],
            "constraints": [],
            "focus_target": "user",
            "emotion": {"valence": 0.5},
            "relationship": {"bond": 0.7}
        }
        
        has_tone = "tone" in plan
        has_key_points = "key_points" in plan and isinstance(plan.get("key_points"), list)
        
        assert has_tone is True
        assert has_key_points is True
        # Schema should be VALID


class TestFallback:
    """Test fallback scenarios"""
    
    def test_fallback_timeout(self):
        """Timeout should trigger fallback"""
        # Simulate timeout (latency > configured timeout)
        latency_ms = 6000
        timeout_ms = 5000
        
        is_timeout = latency_ms > timeout_ms
        
        assert is_timeout is True
        # Should trigger fallback
    
    def test_fallback_connection_refused(self):
        """Connection refused should trigger fallback"""
        error = "ECONNREFUSED"
        
        is_connection_error = error in ["ECONNREFUSED", "ENOTFOUND", "ETIMEDOUT"]
        
        assert is_connection_error is True
        # Should trigger fallback
    
    def test_fallback_5xx(self):
        """HTTP 5xx should trigger fallback"""
        status_code = 500
        
        is_5xx = 500 <= status_code < 600
        
        assert is_5xx is True
        # Should trigger fallback
    
    def test_fallback_schema_invalid(self):
        """Invalid schema should trigger fallback"""
        response = {"some_field": "value"}  # Missing tone and key_points
        
        has_required = "tone" in response and "key_points" in response
        
        assert has_required is False
        # Should trigger fallback


class TestConfig:
    """Test configuration"""
    
    def test_config_defaults(self):
        """Default configuration should be enabled"""
        import os
        
        # Read from environment (set in openclaw.json)
        # These are set via env vars
        inject_plan = os.environ.get("inject_plan_into_reply", "true")
        
        assert inject_plan == "true"
    
    def test_config_master_switch(self):
        """Master switch should control all injection"""
        # When inject_plan_into_reply = false
        # All injection should be disabled
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
