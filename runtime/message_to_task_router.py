"""
Message-to-Task Router - 消息到任务路由器

判断消息属于：普通聊天、新任务、继续已有任务、控制命令。
"""

import json
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict, field


@dataclass
class RouteDecision:
    """路由决策"""
    type: str  # chat, new_task, continue_task, control, approval
    confidence: float = 1.0
    task_id: Optional[str] = None
    command: Optional[str] = None
    objective: Optional[str] = None
    reason: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}


class TaskClassifier:
    """任务分类器"""
    
    # 明确的任务触发词
    TASK_KEYWORDS = [
        "帮我", "请", "创建", "生成", "实现", "修复",
        "整理", "分析", "重构", "删除", "修改",
        "写一个", "做个", "完成", "处理", "执行",
        "build", "create", "fix", "implement", "refactor",
        "generate", "analyze", "delete", "modify"
    ]
    
    # 排除词（普通聊天）
    CHAT_KEYWORDS = [
        "你好", "谢谢", "再见", "怎么样", "是什么",
        "可以吗", "吗", "呢", "hello", "hi", "thanks"
    ]
    
    # 控制命令
    CONTROL_COMMANDS = [
        "status", "pause", "resume", "cancel", "mode",
        "approve", "reject", "kill", "help"
    ]
    
    def classify(self, text: str, context: Dict[str, Any]) -> RouteDecision:
        """
        分类消息
        
        Args:
            text: 消息文本
            context: 消息上下文（包含 is_reply, reply_to_task 等）
            
        Returns:
            RouteDecision 路由决策
        """
        text = text.strip()
        
        # 1. 检查是否控制命令
        if text.startswith("/"):
            command = self._extract_command(text)
            return RouteDecision(
                type="control",
                confidence=1.0,
                command=command,
                reason="Bot command detected"
            )
        
        # 2. 检查是否审批响应
        if context.get("is_reply") and context.get("is_pending_approval"):
            task_id = context.get("reply_task_id")
            approval_text = text.lower().strip()
            if approval_text in ["/approve", "/yes", "yes", "确认", "同意", "批准"]:
                return RouteDecision(
                    type="approval",
                    confidence=1.0,
                    task_id=task_id,
                    command="approve",
                    reason="Approval response detected"
                )
            elif approval_text in ["/reject", "/no", "no", "拒绝", "取消"]:
                return RouteDecision(
                    type="approval",
                    confidence=1.0,
                    task_id=task_id,
                    command="reject",
                    reason="Rejection response detected"
                )
        
        # 3. 检查是否继续已有任务
        if context.get("is_reply") and context.get("reply_is_task"):
            return RouteDecision(
                type="continue_task",
                confidence=0.9,
                task_id=context.get("reply_task_id"),
                reason="Reply to task message"
            )
        
        # 4. 检查显式继续模式
        continue_patterns = [
            r"继续", r"continue",
            r"接着", r"接着做",
            r"继续做", r"go on"
        ]
        for pattern in continue_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                recent_task = context.get("recent_task_id")
                if recent_task:
                    return RouteDecision(
                        type="continue_task",
                        confidence=0.85,
                        task_id=recent_task,
                        reason="Explicit continue command"
                    )
        
        # 5. 任务关键词匹配
        task_score = sum(1 for kw in self.TASK_KEYWORDS if kw.lower() in text.lower())
        chat_score = sum(1 for kw in self.CHAT_KEYWORDS if kw.lower() in text.lower())
        
        # 6. 长文本更可能是任务
        length_bonus = 1 if len(text) > 200 else 0
        
        total_task_score = task_score + length_bonus
        
        if total_task_score > chat_score and total_task_score > 0:
            confidence = min(0.5 + (total_task_score * 0.1), 0.9)
            return RouteDecision(
                type="new_task",
                confidence=confidence,
                objective=text,
                reason=f"Task keywords matched (score: {total_task_score})"
            )
        
        # 7. 检查文本长度
        if len(text) > 500:
            return RouteDecision(
                type="new_task",
                confidence=0.6,
                objective=text,
                reason="Long text, possibly a task"
            )
        
        # 8. 默认为普通聊天
        return RouteDecision(
            type="chat",
            confidence=0.8,
            reason="No task indicators found"
        )
    
    def _extract_command(self, text: str) -> str:
        """提取命令"""
        # 提取第一个命令词
        parts = text.strip().split()
        if parts:
            command = parts[0].lower()
            # 移除 @bot_name 后缀
            if "@" in command:
                command = command.split("@")[0]
            return command
        return text.strip().lower()


class TaskRegistry:
    """任务注册表 - 用于关联消息和任务"""
    
    def __init__(self, registry_path: str = ".task_registry.json"):
        self.registry_path = Path(registry_path)
        self._registry = self._load_registry()
    
    def _load_registry(self) -> Dict[str, Any]:
        if self.registry_path.exists():
            try:
                with open(self.registry_path, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {"tasks": {}, "user_tasks": {}}
        return {"tasks": {}, "user_tasks": {}}
    
    def _save_registry(self):
        with open(self.registry_path, 'w') as f:
            json.dump(self._registry, f, indent=2)
    
    def register_task(self, task_id: str, chat_id: str, user_id: str, message_id: str, objective: str):
        """注册新任务"""
        self._registry["tasks"][task_id] = {
            "chat_id": chat_id,
            "user_id": user_id,
            "message_id": message_id,
            "objective": objective,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "status": "created"
        }
        
        # 用户任务索引
        if user_id not in self._registry["user_tasks"]:
            self._registry["user_tasks"][user_id] = []
        self._registry["user_tasks"][user_id].append(task_id)
        
        self._save_registry()
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务信息"""
        return self._registry["tasks"].get(task_id)
    
    def get_recent_task(self, user_id: str) -> Optional[str]:
        """获取用户最近的活跃任务"""
        user_tasks = self._registry["user_tasks"].get(user_id, [])
        for task_id in reversed(user_tasks):
            task = self._registry["tasks"].get(task_id)
            if task and task.get("status") in ["created", "running", "blocked"]:
                return task_id
        return None
    
    def get_task_by_message(self, message_id: str, chat_id: str) -> Optional[str]:
        """通过消息 ID 获取任务"""
        for task_id, task in self._registry["tasks"].items():
            if task.get("message_id") == message_id and task.get("chat_id") == chat_id:
                return task_id
        return None
    
    def update_task_status(self, task_id: str, status: str):
        """更新任务状态"""
        if task_id in self._registry["tasks"]:
            self._registry["tasks"][task_id]["status"] = status
            self._registry["tasks"][task_id]["updated_at"] = datetime.utcnow().isoformat() + "Z"
            self._save_registry()


class ApprovalRegistry:
    """审批注册表"""
    
    def __init__(self, registry_path: str = ".approval_registry.json"):
        self.registry_path = Path(registry_path)
        self._registry = self._load_registry()
    
    def _load_registry(self) -> Dict[str, Any]:
        if self.registry_path.exists():
            try:
                with open(self.registry_path, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {"pending": {}}
        return {"pending": {}}
    
    def _save_registry(self):
        with open(self.registry_path, 'w') as f:
            json.dump(self._registry, f, indent=2)
    
    def create_approval(self, task_id: str, step_id: str, operation: Dict[str, Any], chat_id: str, message_id: str) -> str:
        """创建审批请求"""
        approval_id = f"approval_{uuid.uuid4().hex[:8]}"
        self._registry["pending"][approval_id] = {
            "task_id": task_id,
            "step_id": step_id,
            "operation": operation,
            "chat_id": chat_id,
            "message_id": message_id,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "status": "pending"
        }
        self._save_registry()
        return approval_id
    
    def get_pending_approval(self, message_id: str) -> Optional[Dict[str, Any]]:
        """获取消息关联的待审批"""
        for approval_id, approval in self._registry["pending"].items():
            if approval.get("message_id") == message_id and approval.get("status") == "pending":
                return {"approval_id": approval_id, **approval}
        return None
    
    def resolve_approval(self, approval_id: str, decision: str):
        """解决审批"""
        if approval_id in self._registry["pending"]:
            self._registry["pending"][approval_id]["status"] = decision
            self._registry["pending"][approval_id]["resolved_at"] = datetime.utcnow().isoformat() + "Z"
            self._save_registry()


class MessageToTaskRouter:
    """消息到任务路由器"""
    
    def __init__(
        self,
        task_registry_path: str = None,
        approval_registry_path: str = None
    ):
        self.classifier = TaskClassifier()
        self.task_registry = TaskRegistry(task_registry_path or ".task_registry.json")
        self.approval_registry = ApprovalRegistry(approval_registry_path or ".approval_registry.json")
    
    def route(self, event: Dict[str, Any]) -> RouteDecision:
        """
        路由消息
        
        Args:
            event: MessageEvent 字典
            
        Returns:
            RouteDecision 路由决策
        """
        # 提取信息
        text = event.get("content", {}).get("text", "")
        source = event.get("source", {})
        context = event.get("context", {})
        
        user_id = source.get("user_id", "")
        chat_id = source.get("chat_id", "")
        message_id = source.get("message_id", "")
        reply_to_message_id = source.get("reply_to_message_id")
        
        # 构建路由上下文
        route_context = {
            "is_reply": context.get("is_reply", False),
            "is_pending_approval": False,
            "reply_is_task": False,
            "reply_task_id": None,
            "recent_task_id": None
        }
        
        # 检查回复是否关联待审批
        if reply_to_message_id:
            pending_approval = self.approval_registry.get_pending_approval(reply_to_message_id)
            if pending_approval:
                route_context["is_pending_approval"] = True
                route_context["reply_task_id"] = pending_approval.get("task_id")
            
            # 检查回复是否关联任务
            task_id = self.task_registry.get_task_by_message(reply_to_message_id, chat_id)
            if task_id:
                route_context["reply_is_task"] = True
                route_context["reply_task_id"] = task_id
        
        # 获取用户最近任务
        recent_task = self.task_registry.get_recent_task(user_id)
        route_context["recent_task_id"] = recent_task
        
        # 分类
        decision = self.classifier.classify(text, route_context)
        
        # 添加元数据
        decision.metadata.update({
            "user_id": user_id,
            "chat_id": chat_id,
            "message_id": message_id,
            "classification_context": route_context
        })
        
        return decision
    
    def register_task(
        self,
        task_id: str,
        chat_id: str,
        user_id: str,
        message_id: str,
        objective: str
    ):
        """注册新任务"""
        self.task_registry.register_task(task_id, chat_id, user_id, message_id, objective)
    
    def create_approval(
        self,
        task_id: str,
        step_id: str,
        operation: Dict[str, Any],
        chat_id: str,
        message_id: str
    ) -> str:
        """创建审批请求"""
        return self.approval_registry.create_approval(task_id, step_id, operation, chat_id, message_id)
    
    def resolve_approval(self, approval_id: str, decision: str):
        """解决审批"""
        self.approval_registry.resolve_approval(approval_id, decision)


# 便捷函数
def route_message(event: Dict[str, Any]) -> RouteDecision:
    """便捷函数：路由消息"""
    router = MessageToTaskRouter()
    return router.route(event)
