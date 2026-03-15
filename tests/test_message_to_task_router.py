"""
Test Message-to-Task Router

测试消息到任务路由器
"""

import pytest
from runtime.message_to_task_router import (
    MessageToTaskRouter,
    TaskClassifier,
    RouteDecision,
    TaskRegistry,
    ApprovalRegistry
)


class TestTaskClassifier:
    """测试任务分类器"""
    
    def test_classify_control_command(self):
        """测试控制命令分类"""
        classifier = TaskClassifier()
        
        decision = classifier.classify("/status", {})
        assert decision.type == "control"
        assert decision.command == "/status"
        
        decision = classifier.classify("/pause task_123", {})
        assert decision.type == "control"
        assert decision.command == "/pause"
    
    def test_classify_approval_response(self):
        """测试审批响应分类"""
        classifier = TaskClassifier()
        
        # 文本确认（非命令形式）
        decision = classifier.classify("yes", {
            "is_reply": True,
            "is_pending_approval": True,
            "reply_task_id": "task_123"
        })
        assert decision.type == "approval"
        assert decision.command == "approve"
        
        # 文本拒绝（非命令形式）
        decision = classifier.classify("no", {
            "is_reply": True,
            "is_pending_approval": True,
            "reply_task_id": "task_123"
        })
        assert decision.type == "approval"
        assert decision.command == "reject"
        
        # /approve 作为命令会被分类为 control（优先级更高）
        decision = classifier.classify("/approve", {})
        assert decision.type == "control"
    
    def test_classify_continue_task(self):
        """测试继续任务分类"""
        classifier = TaskClassifier()
        
        # 回复任务消息
        decision = classifier.classify("继续", {
            "is_reply": True,
            "reply_is_task": True,
            "reply_task_id": "task_123"
        })
        assert decision.type == "continue_task"
        assert decision.task_id == "task_123"
    
    def test_classify_new_task(self):
        """测试新任务分类"""
        classifier = TaskClassifier()
        
        # 包含任务关键词
        decision = classifier.classify("帮我整理 docs 目录", {})
        assert decision.type == "new_task"
        assert decision.confidence >= 0.5
        
        # 长文本
        decision = classifier.classify("这是一个很长的任务描述" * 50, {})
        assert decision.type == "new_task"
    
    def test_classify_chat(self):
        """测试普通聊天分类"""
        classifier = TaskClassifier()
        
        decision = classifier.classify("你好", {})
        assert decision.type == "chat"
        
        decision = classifier.classify("今天天气怎么样", {})
        assert decision.type == "chat"
    
    def test_extract_command(self):
        """测试命令提取"""
        classifier = TaskClassifier()
        
        assert classifier._extract_command("/status") == "/status"
        assert classifier._extract_command("/status@mybot") == "/status"
        assert classifier._extract_command("/MODE guarded-auto") == "/mode"


class TestTaskRegistry:
    """测试任务注册表"""
    
    def test_register_task(self, tmp_path):
        """测试注册任务"""
        registry = TaskRegistry(str(tmp_path / "tasks.json"))
        
        registry.register_task(
            task_id="task_001",
            chat_id="123",
            user_id="456",
            message_id="789",
            objective="Test task"
        )
        
        task = registry.get_task("task_001")
        assert task is not None
        assert task["chat_id"] == "123"
        assert task["objective"] == "Test task"
    
    def test_get_recent_task(self, tmp_path):
        """测试获取最近任务"""
        registry = TaskRegistry(str(tmp_path / "tasks.json"))
        
        registry.register_task("task_001", "123", "456", "1", "Task 1")
        registry.register_task("task_002", "123", "456", "2", "Task 2")
        registry.update_task_status("task_001", "completed")
        
        recent = registry.get_recent_task("456")
        assert recent == "task_002"
    
    def test_get_task_by_message(self, tmp_path):
        """测试通过消息获取任务"""
        registry = TaskRegistry(str(tmp_path / "tasks.json"))
        
        registry.register_task("task_001", "123", "456", "msg_123", "Test")
        
        task_id = registry.get_task_by_message("msg_123", "123")
        assert task_id == "task_001"
        
        # 不同 chat_id
        task_id = registry.get_task_by_message("msg_123", "999")
        assert task_id is None


class TestApprovalRegistry:
    """测试审批注册表"""
    
    def test_create_approval(self, tmp_path):
        """测试创建审批"""
        registry = ApprovalRegistry(str(tmp_path / "approvals.json"))
        
        approval_id = registry.create_approval(
            task_id="task_001",
            step_id="S01",
            operation={"type": "shell_command", "command": "rm -rf /tmp/test"},
            chat_id="123",
            message_id="456"
        )
        
        assert approval_id.startswith("approval_")
    
    def test_get_pending_approval(self, tmp_path):
        """测试获取待审批"""
        registry = ApprovalRegistry(str(tmp_path / "approvals.json"))
        
        approval_id = registry.create_approval(
            task_id="task_001",
            step_id="S01",
            operation={},
            chat_id="123",
            message_id="456"
        )
        
        pending = registry.get_pending_approval("456")
        assert pending is not None
        assert pending["task_id"] == "task_001"
    
    def test_resolve_approval(self, tmp_path):
        """测试解决审批"""
        registry = ApprovalRegistry(str(tmp_path / "approvals.json"))
        
        approval_id = registry.create_approval(
            task_id="task_001",
            step_id="S01",
            operation={},
            chat_id="123",
            message_id="456"
        )
        
        registry.resolve_approval(approval_id, "approved")
        
        pending = registry.get_pending_approval("456")
        assert pending is None  # 已解决


class TestMessageToTaskRouter:
    """测试消息到任务路由器"""
    
    def test_route_control_command(self):
        """测试路由控制命令"""
        router = MessageToTaskRouter()
        
        event = {
            "event_id": "test_001",
            "content": {"text": "/status"},
            "source": {
                "chat_id": "123",
                "user_id": "456",
                "message_id": "789"
            },
            "context": {
                "is_reply": False,
                "has_command": True
            }
        }
        
        decision = router.route(event)
        assert decision.type == "control"
        assert decision.command == "/status"
    
    def test_route_new_task(self):
        """测试路由新任务"""
        router = MessageToTaskRouter()
        
        event = {
            "event_id": "test_002",
            "content": {"text": "帮我整理 docs 目录"},
            "source": {
                "chat_id": "123",
                "user_id": "456",
                "message_id": "789"
            },
            "context": {
                "is_reply": False,
                "has_command": False
            }
        }
        
        decision = router.route(event)
        assert decision.type == "new_task"
    
    def test_route_chat(self):
        """测试路由普通聊天"""
        router = MessageToTaskRouter()
        
        event = {
            "event_id": "test_003",
            "content": {"text": "你好"},
            "source": {
                "chat_id": "123",
                "user_id": "456",
                "message_id": "789"
            },
            "context": {
                "is_reply": False,
                "has_command": False
            }
        }
        
        decision = router.route(event)
        assert decision.type == "chat"
