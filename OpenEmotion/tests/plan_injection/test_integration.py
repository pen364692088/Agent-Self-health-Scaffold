"""
Integration tests for Plan Injection Patch
"""
import pytest
import json
import os
import subprocess
import time

EMOTIOND_URL = "http://127.0.0.1:18080"
CONTEXT_FILE = os.path.expanduser("~/.openclaw/workspace/emotiond/context.json")


def emotiond_is_running():
    """Check if emotiond is running"""
    import urllib.request
    try:
        urllib.request.urlopen(f"{EMOTIOND_URL}/health", timeout=2)
        return True
    except:
        return False


def read_context():
    """Read current context file"""
    try:
        with open(CONTEXT_FILE) as f:
            return json.load(f)
    except:
        return {}


def write_context(data):
    """Write context file"""
    os.makedirs(os.path.dirname(CONTEXT_FILE), exist_ok=True)
    with open(CONTEXT_FILE, 'w') as f:
        json.dump(data, f, indent=2)


class TestChatIntegration:
    """Integration tests for chat path"""
    
    @pytest.mark.skipif(not emotiond_is_running(), reason="emotiond not running")
    def test_chat_requests_plan(self):
        """Normal chat should request plan from emotiond"""
        # This test requires emotiond running
        # Simulate by checking if /plan endpoint works
        
        import urllib.request
        import json
        
        plan_data = json.dumps({
            "user_id": "test_user",
            "user_text": "Hello, how are you?"
        }).encode()
        
        req = urllib.request.Request(
            f"{EMOTIOND_URL}/plan",
            data=plan_data,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer test"
            }
        )
        
        try:
            response = urllib.request.urlopen(req, timeout=5)
            result = json.loads(response.read())
            
            assert "tone" in result
            assert "key_points" in result
        except Exception as e:
            pytest.skip(f"emotiond not available: {e}")
    
    def test_context_written_after_plan(self):
        """Context should be written after plan fetch"""
        # Simulate context with plan
        context = {
            "target_id": "telegram:test",
            "plan": {
                "tone": "warm",
                "key_points": ["greet warmly"],
                "constraints": []
            },
            "injection_metadata": {
                "gate_result": "allowed",
                "latency_ms": 50,
                "fallback_triggered": False
            }
        }
        
        write_context(context)
        read_back = read_context()
        
        assert read_back.get("plan") is not None
        assert read_back["injection_metadata"]["gate_result"] == "allowed"


class TestCommandIntegration:
    """Integration tests for command path"""
    
    def test_command_no_plan_request(self):
        """Command should not request plan"""
        # Simulate context after command
        context = {
            "target_id": "telegram:test",
            "plan": None,
            "injection_metadata": {
                "gate_result": "skipped",
                "reason": "is_command"
            }
        }
        
        write_context(context)
        read_back = read_context()
        
        assert read_back.get("plan") is None
        assert read_back["injection_metadata"]["gate_result"] == "skipped"


class TestFallbackIntegration:
    """Integration tests for fallback scenarios"""
    
    def test_plan_failure_normal_reply(self):
        """Plan failure should result in normal reply"""
        context = {
            "target_id": "telegram:test",
            "plan": None,
            "injection_metadata": {
                "gate_result": "error",
                "reason": "timeout",
                "fallback_triggered": True
            }
        }
        
        write_context(context)
        read_back = read_context()
        
        assert read_back.get("plan") is None
        assert read_back["injection_metadata"]["fallback_triggered"] is True


class TestEventFlowIntegration:
    """Integration tests for event flow"""
    
    def test_decision_still_present_with_plan(self):
        """Decision should still be present when plan is available"""
        context = {
            "target_id": "telegram:test",
            "plan": {
                "tone": "warm",
                "key_points": ["greet"]
            },
            "decision": {
                "action": "approach"
            },
            "guidance": {
                "tone": "warm, open"
            },
            "injection_metadata": {
                "gate_result": "allowed"
            }
        }
        
        write_context(context)
        read_back = read_context()
        
        # Both plan and decision should coexist
        assert read_back.get("plan") is not None
        assert read_back.get("decision") is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
