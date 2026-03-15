"""
Telegram Ingress Adapter - Telegram 入口适配器

接收 Telegram update，标准化为 MessageEvent，进行去重处理。
"""

import json
import hashlib
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict, field
import re


@dataclass
class TelegramSource:
    """Telegram 消息来源"""
    platform: str = "telegram"
    chat_id: str = ""
    user_id: str = ""
    username: Optional[str] = None
    message_id: str = ""
    thread_id: Optional[str] = None
    reply_to_message_id: Optional[str] = None
    update_id: str = ""


@dataclass
class TelegramEntity:
    """Telegram 消息实体"""
    type: str
    offset: int
    length: int


@dataclass
class TelegramAttachment:
    """Telegram 附件"""
    type: str
    file_id: str
    file_name: Optional[str] = None
    mime_type: Optional[str] = None
    file_size: Optional[int] = None


@dataclass
class TelegramContent:
    """Telegram 消息内容"""
    text: str = ""
    entities: List[TelegramEntity] = field(default_factory=list)
    attachments: List[TelegramAttachment] = field(default_factory=list)


@dataclass
class TelegramContext:
    """Telegram 消息上下文"""
    is_private_chat: bool = True
    is_group_chat: bool = False
    is_reply: bool = False
    has_command: bool = False
    command: Optional[str] = None


@dataclass
class MessageEvent:
    """标准化消息事件"""
    event_id: str
    event_type: str = "telegram_message"
    timestamp: str = ""
    source: TelegramSource = None
    content: TelegramContent = None
    context: TelegramContext = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.timestamp is None or self.timestamp == "":
            self.timestamp = datetime.utcnow().isoformat() + "Z"
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "source": asdict(self.source) if self.source else {},
            "content": asdict(self.content) if self.content else {},
            "context": asdict(self.context) if self.context else {},
            "metadata": self.metadata
        }
        return result
    
    def idempotency_key(self) -> str:
        """生成幂等键"""
        return f"telegram:{self.source.chat_id}:{self.source.message_id}:{self.source.update_id}"


class IdempotencyStore:
    """幂等状态存储"""
    
    def __init__(self, store_path: str = ".idempotency_store.json"):
        self.store_path = Path(store_path)
        self._store = self._load_store()
    
    def _load_store(self) -> Dict[str, Any]:
        if self.store_path.exists():
            try:
                with open(self.store_path, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}
    
    def _save_store(self):
        with open(self.store_path, 'w') as f:
            json.dump(self._store, f, indent=2)
    
    def check(self, key: str) -> Dict[str, Any]:
        """检查幂等状态"""
        return self._store.get(key, {
            "status": "not_processed",
            "task_id": None,
            "processed_at": None,
            "result_sent": False
        })
    
    def mark_processed(self, key: str, task_id: str = None, result_sent: bool = False):
        """标记为已处理"""
        self._store[key] = {
            "status": "processed",
            "task_id": task_id,
            "processed_at": datetime.utcnow().isoformat() + "Z",
            "result_sent": result_sent
        }
        self._save_store()
    
    def mark_result_sent(self, key: str):
        """标记结果已发送"""
        if key in self._store:
            self._store[key]["result_sent"] = True
            self._save_store()


class TelegramIngressAdapter:
    """Telegram 入口适配器"""
    
    def __init__(self, idempotency_store_path: str = None):
        self.idempotency_store = IdempotencyStore(
            idempotency_store_path or ".idempotency_store.json"
        )
    
    def normalize(self, telegram_update: Dict[str, Any]) -> Optional[MessageEvent]:
        """
        将 Telegram update 标准化为 MessageEvent
        
        Args:
            telegram_update: 原始 Telegram update 对象
            
        Returns:
            标准化的 MessageEvent，如果无效则返回 None
        """
        # 提取 message
        message = telegram_update.get("message")
        if not message:
            message = telegram_update.get("edited_message")
            if not message:
                message = telegram_update.get("channel_post")
                if not message:
                    return None
        
        # 提取基本字段
        update_id = str(telegram_update.get("update_id", ""))
        message_id = str(message.get("message_id", ""))
        
        # 提取 chat 信息
        chat = message.get("chat", {})
        chat_id = str(chat.get("id", ""))
        chat_type = chat.get("type", "private")
        
        # 提取 user 信息
        user = message.get("from", {})
        user_id = str(user.get("id", ""))
        username = user.get("username")
        
        # 提取文本
        text = message.get("text", "")
        if not text:
            # 处理 caption
            text = message.get("caption", "")
        
        # 提取 reply_to
        reply_to_message_id = None
        if message.get("reply_to_message"):
            reply_to_message_id = str(message["reply_to_message"].get("message_id", ""))
        
        # 提取 thread_id
        thread_id = None
        if message.get("message_thread_id"):
            thread_id = str(message["message_thread_id"])
        
        # 构建 source
        source = TelegramSource(
            platform="telegram",
            chat_id=chat_id,
            user_id=user_id,
            username=username,
            message_id=message_id,
            thread_id=thread_id,
            reply_to_message_id=reply_to_message_id,
            update_id=update_id
        )
        
        # 提取 entities
        entities = []
        for entity in message.get("entities", []):
            entities.append(TelegramEntity(
                type=entity.get("type", ""),
                offset=entity.get("offset", 0),
                length=entity.get("length", 0)
            ))
        
        # 提取附件
        attachments = []
        attachment_types = ["photo", "document", "audio", "video", "voice", "sticker", "animation"]
        for att_type in attachment_types:
            att_data = message.get(att_type)
            if att_data:
                if att_type == "photo":
                    # photo 是数组，取最大尺寸
                    att_data = att_data[-1] if att_data else None
                
                if att_data:
                    attachments.append(TelegramAttachment(
                        type=att_type,
                        file_id=att_data.get("file_id", ""),
                        file_name=att_data.get("file_name"),
                        mime_type=att_data.get("mime_type"),
                        file_size=att_data.get("file_size")
                    ))
        
        # 构建 content
        content = TelegramContent(
            text=text,
            entities=entities,
            attachments=attachments
        )
        
        # 构建上下文
        has_command = any(e.type == "bot_command" for e in entities)
        command = None
        if has_command:
            for entity in entities:
                if entity.type == "bot_command":
                    command = text[entity.offset:entity.offset + entity.length]
                    break
        
        context = TelegramContext(
            is_private_chat=(chat_type == "private"),
            is_group_chat=(chat_type in ["group", "supergroup"]),
            is_reply=(reply_to_message_id is not None),
            has_command=has_command,
            command=command
        )
        
        # 构建 MessageEvent
        event = MessageEvent(
            event_id=str(uuid.uuid4()),
            event_type="telegram_message",
            timestamp=datetime.utcnow().isoformat() + "Z",
            source=source,
            content=content,
            context=context,
            metadata={
                "chat_type": chat_type,
                "raw_update_id": update_id
            }
        )
        
        return event
    
    def check_idempotency(self, event: MessageEvent) -> Dict[str, Any]:
        """
        检查消息的幂等状态
        
        Args:
            event: 标准化的 MessageEvent
            
        Returns:
            幂等状态字典
        """
        key = event.idempotency_key()
        return self.idempotency_store.check(key)
    
    def mark_processed(self, event: MessageEvent, task_id: str = None, result_sent: bool = False):
        """
        标记消息为已处理
        
        Args:
            event: 标准化的 MessageEvent
            task_id: 关联的任务 ID
            result_sent: 结果是否已发送
        """
        key = event.idempotency_key()
        self.idempotency_store.mark_processed(key, task_id, result_sent)
    
    def mark_result_sent(self, event: MessageEvent):
        """标记消息的结果已发送"""
        key = event.idempotency_key()
        self.idempotency_store.mark_result_sent(key)
    
    def should_process(self, event: MessageEvent) -> tuple:
        """
        判断是否应该处理该消息
        
        Returns:
            (should_process: bool, reason: str, idempotency_state: dict)
        """
        idempotency_state = self.check_idempotency(event)
        
        if idempotency_state["status"] == "processed":
            if idempotency_state["result_sent"]:
                return False, "already_processed_and_sent", idempotency_state
            else:
                return False, "already_processed_pending_result", idempotency_state
        
        return True, "new_message", idempotency_state
    
    def process_update(self, telegram_update: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理 Telegram update 的完整流程
        
        Args:
            telegram_update: 原始 Telegram update 对象
            
        Returns:
            处理结果，包含 event 和 idempotency 状态
        """
        # 1. 标准化
        event = self.normalize(telegram_update)
        if event is None:
            return {
                "status": "invalid_update",
                "event": None,
                "reason": "No valid message in update"
            }
        
        # 2. 幂等检查
        should_process, reason, idempotency_state = self.should_process(event)
        
        return {
            "status": "should_process" if should_process else "skipped",
            "event": event,
            "reason": reason,
            "idempotency_state": idempotency_state,
            "idempotency_key": event.idempotency_key()
        }


# 便捷函数
def normalize_telegram_update(update: Dict[str, Any]) -> Optional[MessageEvent]:
    """便捷函数：标准化 Telegram update"""
    adapter = TelegramIngressAdapter()
    return adapter.normalize(update)


def create_message_event(
    chat_id: str,
    user_id: str,
    text: str,
    message_id: str = "1",
    update_id: str = "1",
    **kwargs
) -> MessageEvent:
    """便捷函数：创建 MessageEvent（用于测试）"""
    source = TelegramSource(
        platform="telegram",
        chat_id=chat_id,
        user_id=user_id,
        message_id=message_id,
        update_id=update_id
    )
    
    content = TelegramContent(text=text)
    
    context = TelegramContext(
        is_private_chat=kwargs.get("is_private_chat", True),
        is_group_chat=kwargs.get("is_group_chat", False),
        is_reply=kwargs.get("is_reply", False),
        has_command=text.startswith("/"),
        command=text.split()[0] if text.startswith("/") else None
    )
    
    return MessageEvent(
        event_id=str(uuid.uuid4()),
        source=source,
        content=content,
        context=context,
        metadata=kwargs.get("metadata", {})
    )
