"""
Test Telegram Control Commands

测试 Telegram 控制命令
"""

import pytest
from runtime.telegram_control_commands import (
    TelegramControlCommands,
    CommandContext,
    CommandResult,
    CommandType
)


class MockAutoStartController:
    """模拟自动启动控制器"""
    
    def __init__(self):
        self.mode = "guarded-auto"
        self.kill_switch = False
    
    def get_status(self):
        return {
            "mode": self.mode,
            "main_flow_enabled": True,
            "kill_switch_enabled": self.kill_switch
        }
    
    def set_mode(self, mode):
        if mode not in ["shadow", "guarded-auto", "full-auto"]:
            return {"success": False, "error": f"Invalid mode: {mode}"}
        old = self.mode
        self.mode = mode
        return {"success": True, "old_mode": old, "new_mode": mode}
    
    def enable_kill_switch(self):
        self.kill_switch = True
        return {"success": True, "kill_switch_enabled": True}
    
    def disable_kill_switch(self):
        self.kill_switch = False
        return {"success": True, "kill_switch_enabled": False}


class MockTaskRegistry:
    """模拟任务注册表"""
    
    def __init__(self):
        self.tasks = {}
    
    def get_recent_task(self, user_id):
        for task_id, task in reversed(list(self.tasks.items())):
            if task.get("user_id") == user_id and task.get("status") in ["created", "running"]:
                return task_id
        return None
    
    def update_task_status(self, task_id, status):
        if task_id in self.tasks:
            self.tasks[task_id]["status"] = status


class MockApprovalRegistry:
    """模拟审批注册表"""
    
    def __init__(self):
        self.approvals = {}
    
    def resolve_approval(self, approval_id, decision):
        if approval_id in self.approvals:
            self.approvals[approval_id]["status"] = decision


class MockStatusBridge:
    """模拟状态桥"""
    
    def build_status_message(self, task_id):
        from runtime.telegram_status_bridge import TaskStatus
        return TaskStatus(task_id=task_id, status="running", progress="1/4")
    
    def format_status_for_telegram(self, status):
        return f"📋 任务状态\n\n🆔 任务 ID: `{status.task_id}`\n📊 状态: {status.status}"


class TestTelegramControlCommands:
    """测试控制命令处理器"""
    
    @pytest.fixture
    def controller(self):
        return TelegramControlCommands(
            auto_start_controller=MockAutoStartController(),
            task_registry=MockTaskRegistry(),
            approval_registry=MockApprovalRegistry(),
            status_bridge=MockStatusBridge()
        )
    
    def test_handle_status_no_task(self, controller):
        """测试 /status 无任务"""
        context = CommandContext(
            chat_id="123",
            user_id="456",
            message_id="789",
            command="/status"
        )
        
        result = controller.handle(context)
        
        assert result.success is False
        assert "没有找到" in result.message
    
    def test_handle_status_with_task(self, controller):
        """测试 /status 有任务"""
        controller.task_registry.tasks["task_001"] = {
            "user_id": "456",
            "status": "running"
        }
        
        context = CommandContext(
            chat_id="123",
            user_id="456",
            message_id="789",
            command="/status",
            task_id="task_001"
        )
        
        result = controller.handle(context)
        
        assert result.success is True
        assert "task_001" in result.message
    
    def test_handle_pause(self, controller):
        """测试 /pause"""
        controller.task_registry.tasks["task_001"] = {
            "user_id": "456",
            "status": "running"
        }
        
        context = CommandContext(
            chat_id="123",
            user_id="456",
            message_id="789",
            command="/pause",
            task_id="task_001"
        )
        
        result = controller.handle(context)
        
        assert result.success is True
        assert "暂停" in result.message
        assert controller.task_registry.tasks["task_001"]["status"] == "paused"
    
    def test_handle_resume(self, controller):
        """测试 /resume"""
        controller.task_registry.tasks["task_001"] = {
            "user_id": "456",
            "status": "paused"
        }
        
        context = CommandContext(
            chat_id="123",
            user_id="456",
            message_id="789",
            command="/resume",
            task_id="task_001"
        )
        
        result = controller.handle(context)
        
        assert result.success is True
        assert "恢复" in result.message
        assert controller.task_registry.tasks["task_001"]["status"] == "running"
    
    def test_handle_cancel(self, controller):
        """测试 /cancel"""
        controller.task_registry.tasks["task_001"] = {
            "user_id": "456",
            "status": "running"
        }
        
        context = CommandContext(
            chat_id="123",
            user_id="456",
            message_id="789",
            command="/cancel",
            task_id="task_001"
        )
        
        result = controller.handle(context)
        
        assert result.success is True
        assert "取消" in result.message
        assert controller.task_registry.tasks["task_001"]["status"] == "cancelled"
    
    def test_handle_mode_view(self, controller):
        """测试 /mode 查看模式"""
        context = CommandContext(
            chat_id="123",
            user_id="456",
            message_id="789",
            command="/mode"
        )
        
        result = controller.handle(context)
        
        assert result.success is True
        assert "guarded-auto" in result.message
    
    def test_handle_mode_change(self, controller):
        """测试 /mode 切换模式"""
        context = CommandContext(
            chat_id="123",
            user_id="456",
            message_id="789",
            command="/mode",
            args=["shadow"]
        )
        
        result = controller.handle(context)
        
        assert result.success is True
        assert "shadow" in result.message
    
    def test_handle_approve(self, controller):
        """测试 /approve"""
        controller.approval_registry.approvals["approval_001"] = {"status": "pending"}
        
        context = CommandContext(
            chat_id="123",
            user_id="456",
            message_id="789",
            command="/approve",
            approval_id="approval_001"
        )
        
        result = controller.handle(context)
        
        assert result.success is True
        assert "批准" in result.message
    
    def test_handle_reject(self, controller):
        """测试 /reject"""
        controller.approval_registry.approvals["approval_001"] = {"status": "pending"}
        
        context = CommandContext(
            chat_id="123",
            user_id="456",
            message_id="789",
            command="/reject",
            approval_id="approval_001"
        )
        
        result = controller.handle(context)
        
        assert result.success is True
        assert "拒绝" in result.message
    
    def test_handle_kill(self, controller):
        """测试 /kill"""
        context = CommandContext(
            chat_id="123",
            user_id="456",
            message_id="789",
            command="/kill"
        )
        
        result = controller.handle(context)
        
        assert result.success is True
        assert "KILL SWITCH" in result.message
        assert controller.auto_start_controller.kill_switch is True
    
    def test_handle_help(self, controller):
        """测试 /help"""
        context = CommandContext(
            chat_id="123",
            user_id="456",
            message_id="789",
            command="/help"
        )
        
        result = controller.handle(context)
        
        assert result.success is True
        assert "/status" in result.message
        assert "/pause" in result.message
    
    def test_unknown_command(self, controller):
        """测试未知命令"""
        context = CommandContext(
            chat_id="123",
            user_id="456",
            message_id="789",
            command="/unknown"
        )
        
        result = controller.handle(context)
        
        assert result.success is False
        assert "未知命令" in result.message
    
    def test_parse_command(self, controller):
        """测试命令解析"""
        context = controller.parse_command("/status task_001")
        
        assert context.command == "/status"
        assert context.args == ["task_001"]
        
        context = controller.parse_command("/mode@mybot shadow")
        assert context.command == "/mode"
        assert context.args == ["shadow"]
