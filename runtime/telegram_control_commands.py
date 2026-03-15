"""
Telegram Control Commands - Telegram 控制命令处理

处理 /status, /resume, /pause, /cancel, /mode, /approve, /reject 等命令。
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, asdict, field
from enum import Enum


class CommandType(str, Enum):
    """命令类型"""
    STATUS = "status"
    PAUSE = "pause"
    RESUME = "resume"
    CANCEL = "cancel"
    MODE = "mode"
    APPROVE = "approve"
    REJECT = "reject"
    KILL = "kill"
    HELP = "help"


@dataclass
class CommandContext:
    """命令上下文"""
    chat_id: str
    user_id: str
    message_id: str
    command: str
    args: List[str] = field(default_factory=list)
    task_id: Optional[str] = None
    approval_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CommandResult:
    """命令结果"""
    success: bool
    command: str
    message: str
    task_id: Optional[str] = None
    state_change: Optional[Dict[str, Any]] = None
    audit_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}


class AuditLog:
    """审计日志"""
    
    def __init__(self, log_path: str = ".control_audit.jsonl"):
        self.log_path = Path(log_path)
    
    def log(self, event: Dict[str, Any]) -> str:
        """记录审计事件"""
        audit_id = f"audit_{uuid.uuid4().hex[:8]}"
        event["audit_id"] = audit_id
        event["timestamp"] = datetime.utcnow().isoformat() + "Z"
        
        with open(self.log_path, 'a') as f:
            f.write(json.dumps(event) + "\n")
        
        return audit_id


class AuthorizationChecker:
    """授权检查器"""
    
    def __init__(self, authorized_users: List[str] = None, admin_users: List[str] = None):
        self.authorized_users = authorized_users or []
        self.admin_users = admin_users or []
    
    def is_authorized(self, user_id: str) -> bool:
        """检查用户是否授权"""
        if not self.authorized_users:
            return True  # 如果没有配置授权列表，默认允许
        return user_id in self.authorized_users
    
    def is_admin(self, user_id: str) -> bool:
        """检查用户是否是管理员"""
        if not self.admin_users:
            return True  # 如果没有配置管理员列表，默认允许
        return user_id in self.admin_users


class TelegramControlCommands:
    """Telegram 控制命令处理器"""
    
    def __init__(
        self,
        auto_start_controller: Any = None,
        task_registry: Any = None,
        approval_registry: Any = None,
        status_bridge: Any = None,
        audit_log_path: str = None,
        authorized_users: List[str] = None,
        admin_users: List[str] = None
    ):
        self.auto_start_controller = auto_start_controller
        self.task_registry = task_registry
        self.approval_registry = approval_registry
        self.status_bridge = status_bridge
        self.audit_log = AuditLog(audit_log_path or ".control_audit.jsonl")
        self.auth_checker = AuthorizationChecker(authorized_users, admin_users)
        
        # 注册命令处理器
        self._handlers: Dict[str, Callable] = {
            "/status": self._handle_status,
            "/s": self._handle_status,
            "/pause": self._handle_pause,
            "/stop": self._handle_pause,
            "/resume": self._handle_resume,
            "/continue": self._handle_resume,
            "/cancel": self._handle_cancel,
            "/abort": self._handle_cancel,
            "/mode": self._handle_mode,
            "/approve": self._handle_approve,
            "/yes": self._handle_approve,
            "/reject": self._handle_reject,
            "/no": self._handle_reject,
            "/kill": self._handle_kill,
            "/emergency_stop": self._handle_kill,
            "/help": self._handle_help,
        }
    
    def parse_command(self, text: str) -> CommandContext:
        """解析命令文本"""
        parts = text.strip().split()
        command = parts[0].lower() if parts else ""
        args = parts[1:] if len(parts) > 1 else []
        
        # 处理 @bot_name 后缀
        if "@" in command:
            command = command.split("@")[0]
        
        return CommandContext(
            chat_id="",
            user_id="",
            message_id="",
            command=command,
            args=args
        )
    
    def handle(self, context: CommandContext) -> CommandResult:
        """处理命令"""
        command = context.command.lower()
        
        # 检查授权
        if not self.auth_checker.is_authorized(context.user_id):
            return CommandResult(
                success=False,
                command=command,
                message="⛔ 你没有权限执行此命令"
            )
        
        # 查找处理器
        handler = self._handlers.get(command)
        if not handler:
            return CommandResult(
                success=False,
                command=command,
                message=f"❓ 未知命令: {command}\n使用 /help 查看可用命令"
            )
        
        # 执行处理器
        try:
            result = handler(context)
            
            # 记录审计
            audit_id = self.audit_log.log({
                "command": command,
                "user_id": context.user_id,
                "chat_id": context.chat_id,
                "task_id": result.task_id,
                "success": result.success,
                "state_change": result.state_change
            })
            result.audit_id = audit_id
            
            return result
        
        except Exception as e:
            return CommandResult(
                success=False,
                command=command,
                message=f"❌ 命令执行失败: {str(e)}"
            )
    
    def _handle_status(self, context: CommandContext) -> CommandResult:
        """处理 /status 命令"""
        # 获取任务 ID
        task_id = context.args[0] if context.args else context.task_id
        
        if not task_id:
            # 尝试获取用户最近的活跃任务
            if self.task_registry:
                task_id = self.task_registry.get_recent_task(context.user_id)
        
        if not task_id:
            return CommandResult(
                success=False,
                command="/status",
                message="❓ 没有找到活跃的任务\n\n请指定任务 ID: /status <task_id>"
            )
        
        # 获取状态
        if self.status_bridge:
            status = self.status_bridge.build_status_message(task_id)
            message = self.status_bridge.format_status_for_telegram(status)
        else:
            message = f"📋 任务 ID: {task_id}"
        
        return CommandResult(
            success=True,
            command="/status",
            message=message,
            task_id=task_id
        )
    
    def _handle_pause(self, context: CommandContext) -> CommandResult:
        """处理 /pause 命令"""
        task_id = context.args[0] if context.args else context.task_id
        
        if not task_id and self.task_registry:
            task_id = self.task_registry.get_recent_task(context.user_id)
        
        if not task_id:
            return CommandResult(
                success=False,
                command="/pause",
                message="❓ 没有找到要暂停的任务\n\n请指定任务 ID: /pause <task_id>"
            )
        
        # 更新任务状态
        if self.task_registry:
            self.task_registry.update_task_status(task_id, "paused")
        
        return CommandResult(
            success=True,
            command="/pause",
            message=f"⏸️ 任务已暂停\n\n任务 ID: `{task_id}`\n\n使用 /resume 恢复执行",
            task_id=task_id,
            state_change={"task_status": "paused"}
        )
    
    def _handle_resume(self, context: CommandContext) -> CommandResult:
        """处理 /resume 命令"""
        task_id = context.args[0] if context.args else context.task_id
        
        if not task_id and self.task_registry:
            task_id = self.task_registry.get_recent_task(context.user_id)
        
        if not task_id:
            return CommandResult(
                success=False,
                command="/resume",
                message="❓ 没有找到要恢复的任务\n\n请指定任务 ID: /resume <task_id>"
            )
        
        # 更新任务状态
        if self.task_registry:
            self.task_registry.update_task_status(task_id, "running")
        
        return CommandResult(
            success=True,
            command="/resume",
            message=f"▶️ 任务已恢复\n\n任务 ID: `{task_id}`\n\n使用 /status 查看进度",
            task_id=task_id,
            state_change={"task_status": "running"}
        )
    
    def _handle_cancel(self, context: CommandContext) -> CommandResult:
        """处理 /cancel 命令"""
        task_id = context.args[0] if context.args else context.task_id
        
        if not task_id and self.task_registry:
            task_id = self.task_registry.get_recent_task(context.user_id)
        
        if not task_id:
            return CommandResult(
                success=False,
                command="/cancel",
                message="❓ 没有找到要取消的任务\n\n请指定任务 ID: /cancel <task_id>"
            )
        
        # 更新任务状态
        if self.task_registry:
            self.task_registry.update_task_status(task_id, "cancelled")
        
        return CommandResult(
            success=True,
            command="/cancel",
            message=f"🚫 任务已取消\n\n任务 ID: `{task_id}`",
            task_id=task_id,
            state_change={"task_status": "cancelled"}
        )
    
    def _handle_mode(self, context: CommandContext) -> CommandResult:
        """处理 /mode 命令"""
        # 检查管理员权限
        if not self.auth_checker.is_admin(context.user_id):
            return CommandResult(
                success=False,
                command="/mode",
                message="⛔ 只有管理员可以切换模式"
            )
        
        if not context.args:
            # 显示当前模式
            if self.auto_start_controller:
                status = self.auto_start_controller.get_status()
                return CommandResult(
                    success=True,
                    command="/mode",
                    message=f"📊 当前模式: `{status['mode']}`\n\n可用模式:\n• `shadow` - 观测模式\n• `guarded-auto` - 保守自动模式\n• `full-auto` - 全自动模式\n\n使用 /mode <模式> 切换"
                )
            else:
                return CommandResult(
                    success=True,
                    command="/mode",
                    message="📊 使用 /mode <模式> 切换运行模式"
                )
        
        # 切换模式
        new_mode = context.args[0].lower()
        
        if self.auto_start_controller:
            result = self.auto_start_controller.set_mode(new_mode)
            if result["success"]:
                return CommandResult(
                    success=True,
                    command="/mode",
                    message=f"✅ 模式已切换\n\n从 `{result['old_mode']}` → `{result['new_mode']}`",
                    state_change={"mode": new_mode}
                )
            else:
                return CommandResult(
                    success=False,
                    command="/mode",
                    message=f"❌ 模式切换失败: {result['error']}"
                )
        else:
            return CommandResult(
                success=False,
                command="/mode",
                message="❌ 模式控制器未初始化"
            )
    
    def _handle_approve(self, context: CommandContext) -> CommandResult:
        """处理 /approve 命令"""
        approval_id = context.args[0] if context.args else context.approval_id
        
        if not approval_id:
            return CommandResult(
                success=False,
                command="/approve",
                message="❓ 请指定审批 ID 或回复审批消息"
            )
        
        # 解决审批
        if self.approval_registry:
            self.approval_registry.resolve_approval(approval_id, "approved")
        
        return CommandResult(
            success=True,
            command="/approve",
            message=f"✅ 已批准操作\n\n审批 ID: `{approval_id}`\n\n任务将继续执行",
            state_change={"approval_status": "approved"}
        )
    
    def _handle_reject(self, context: CommandContext) -> CommandResult:
        """处理 /reject 命令"""
        approval_id = context.args[0] if context.args else context.approval_id
        
        if not approval_id:
            return CommandResult(
                success=False,
                command="/reject",
                message="❓ 请指定审批 ID 或回复审批消息"
            )
        
        # 解决审批
        if self.approval_registry:
            self.approval_registry.resolve_approval(approval_id, "rejected")
        
        return CommandResult(
            success=True,
            command="/reject",
            message=f"❌ 已拒绝操作\n\n审批 ID: `{approval_id}`\n\n任务将暂停",
            state_change={"approval_status": "rejected"}
        )
    
    def _handle_kill(self, context: CommandContext) -> CommandResult:
        """处理 /kill 命令 - Kill Switch"""
        # 检查管理员权限
        if not self.auth_checker.is_admin(context.user_id):
            return CommandResult(
                success=False,
                command="/kill",
                message="⛔ 只有管理员可以触发 Kill Switch"
            )
        
        if self.auto_start_controller:
            result = self.auto_start_controller.enable_kill_switch()
            return CommandResult(
                success=True,
                command="/kill",
                message=f"🚨 **KILL SWITCH 已启用**\n\n所有自动推进已暂停。\n\n使用 `/kill off` 恢复。",
                state_change={"kill_switch_enabled": True}
            )
        else:
            return CommandResult(
                success=False,
                command="/kill",
                message="❌ 控制器未初始化"
            )
    
    def _handle_help(self, context: CommandContext) -> CommandResult:
        """处理 /help 命令"""
        message = """
📚 **可用命令**

**任务管理**
• `/status` [task_id] - 查看任务状态
• `/pause` [task_id] - 暂停任务
• `/resume` [task_id] - 恢复任务
• `/cancel` [task_id] - 取消任务

**审批**
• `/approve` [approval_id] - 批准操作
• `/reject` [approval_id] - 拒绝操作

**系统** (管理员)
• `/mode` [mode] - 查看或切换运行模式
• `/kill` - 启用 Kill Switch

**其他**
• `/help` - 显示此帮助

**运行模式**
• `shadow` - 观测模式，只记录不执行
• `guarded-auto` - 保守自动，高风险需确认
• `full-auto` - 全自动模式
"""
        return CommandResult(
            success=True,
            command="/help",
            message=message
        )
    
    def disable_kill_switch(self, context: CommandContext) -> CommandResult:
        """禁用 Kill Switch"""
        if not self.auth_checker.is_admin(context.user_id):
            return CommandResult(
                success=False,
                command="/kill",
                message="⛔ 只有管理员可以重置 Kill Switch"
            )
        
        if self.auto_start_controller:
            result = self.auto_start_controller.disable_kill_switch()
            return CommandResult(
                success=True,
                command="/kill",
                message=f"✅ Kill Switch 已禁用\n\n自动推进已恢复。",
                state_change={"kill_switch_enabled": False}
            )
        else:
            return CommandResult(
                success=False,
                command="/kill",
                message="❌ 控制器未初始化"
            )


# 便捷函数
def handle_command(
    command: str,
    user_id: str,
    chat_id: str,
    args: List[str] = None,
    task_id: str = None
) -> CommandResult:
    """便捷函数：处理命令"""
    controller = TelegramControlCommands()
    context = CommandContext(
        chat_id=chat_id,
        user_id=user_id,
        message_id="",
        command=command,
        args=args or [],
        task_id=task_id
    )
    return controller.handle(context)
