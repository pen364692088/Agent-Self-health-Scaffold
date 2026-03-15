"""
Test Telegram Ingress Adapter

测试 Telegram 入口适配器
"""

import pytest
import json
from datetime import datetime

from adapters.telegram_ingress import (
    TelegramIngressAdapter,
    MessageEvent,
    IdempotencyStore,
    create_message_event,
    normalize_telegram_update
)


class TestTelegramIngressAdapter:
    """测试 TelegramIngressAdapter"""
    
    def test_normalize_basic_message(self):
        """测试基本消息标准化"""
        adapter = TelegramIngressAdapter()
        
        update = {
            "update_id": 12345,
            "message": {
                "message_id": 67890,
                "from": {
                    "id": 8420019401,
                    "username": "test_user"
                },
                "chat": {
                    "id": 8420019401,
                    "type": "private"
                },
                "text": "Hello, bot!"
            }
        }
        
        event = adapter.normalize(update)
        
        assert event is not None
        assert event.event_type == "telegram_message"
        assert event.source.chat_id == "8420019401"
        assert event.source.user_id == "8420019401"
        assert event.source.username == "test_user"
        assert event.source.message_id == "67890"
        assert event.source.update_id == "12345"
        assert event.content.text == "Hello, bot!"
        assert event.context.is_private_chat is True
        assert event.context.is_group_chat is False
    
    def test_normalize_command_message(self):
        """测试命令消息标准化"""
        adapter = TelegramIngressAdapter()
        
        update = {
            "update_id": 12346,
            "message": {
                "message_id": 67891,
                "from": {"id": 12345},
                "chat": {"id": 12345, "type": "private"},
                "text": "/status task_123",
                "entities": [
                    {"type": "bot_command", "offset": 0, "length": 7}
                ]
            }
        }
        
        event = adapter.normalize(update)
        
        assert event is not None
        assert event.context.has_command is True
        assert event.context.command == "/status"
    
    def test_normalize_reply_message(self):
        """测试回复消息标准化"""
        adapter = TelegramIngressAdapter()
        
        update = {
            "update_id": 12347,
            "message": {
                "message_id": 67892,
                "from": {"id": 12345},
                "chat": {"id": 12345, "type": "private"},
                "text": "Continue",
                "reply_to_message": {
                    "message_id": 67890
                }
            }
        }
        
        event = adapter.normalize(update)
        
        assert event is not None
        assert event.context.is_reply is True
        assert event.source.reply_to_message_id == "67890"
    
    def test_normalize_group_message(self):
        """测试群组消息标准化"""
        adapter = TelegramIngressAdapter()
        
        update = {
            "update_id": 12348,
            "message": {
                "message_id": 67893,
                "from": {"id": 12345},
                "chat": {"id": -1001234567890, "type": "supergroup"},
                "text": "Group message"
            }
        }
        
        event = adapter.normalize(update)
        
        assert event is not None
        assert event.context.is_private_chat is False
        assert event.context.is_group_chat is True
    
    def test_normalize_with_attachment(self):
        """测试带附件的消息标准化"""
        adapter = TelegramIngressAdapter()
        
        update = {
            "update_id": 12349,
            "message": {
                "message_id": 67894,
                "from": {"id": 12345},
                "chat": {"id": 12345, "type": "private"},
                "text": "Here's a document",
                "document": {
                    "file_id": "abc123",
                    "file_name": "test.pdf",
                    "mime_type": "application/pdf"
                }
            }
        }
        
        event = adapter.normalize(update)
        
        assert event is not None
        assert len(event.content.attachments) == 1
        assert event.content.attachments[0].type == "document"
        assert event.content.attachments[0].file_id == "abc123"
    
    def test_normalize_invalid_update(self):
        """测试无效 update"""
        adapter = TelegramIngressAdapter()
        
        # 空 update
        event = adapter.normalize({})
        assert event is None
        
        # 缺少 message
        event = adapter.normalize({"update_id": 123})
        assert event is None
    
    def test_idempotency_key(self):
        """测试幂等键生成"""
        event = create_message_event(
            chat_id="8420019401",
            user_id="8420019401",
            text="Test",
            message_id="123",
            update_id="456"
        )
        
        key = event.idempotency_key()
        assert key == "telegram:8420019401:123:456"


class TestIdempotencyStore:
    """测试幂等存储"""
    
    def test_check_not_processed(self, tmp_path):
        """测试未处理消息检查"""
        store = IdempotencyStore(str(tmp_path / "idempotency.json"))
        
        state = store.check("telegram:123:456:789")
        
        assert state["status"] == "not_processed"
        assert state["task_id"] is None
        assert state["result_sent"] is False
    
    def test_mark_processed(self, tmp_path):
        """测试标记已处理"""
        store = IdempotencyStore(str(tmp_path / "idempotency.json"))
        
        store.mark_processed("telegram:123:456:789", task_id="task_001", result_sent=True)
        
        state = store.check("telegram:123:456:789")
        assert state["status"] == "processed"
        assert state["task_id"] == "task_001"
        assert state["result_sent"] is True
    
    def test_persistence(self, tmp_path):
        """测试持久化"""
        store_path = str(tmp_path / "idempotency.json")
        
        # 第一次写入
        store1 = IdempotencyStore(store_path)
        store1.mark_processed("telegram:123:456:789")
        
        # 新实例读取
        store2 = IdempotencyStore(store_path)
        state = store2.check("telegram:123:456:789")
        
        assert state["status"] == "processed"


class TestShouldProcess:
    """测试是否应该处理"""
    
    def test_should_process_new_message(self):
        """测试新消息应该处理"""
        adapter = TelegramIngressAdapter()
        event = create_message_event(
            chat_id="123",
            user_id="456",
            text="Test",
            message_id="1",
            update_id="1"
        )
        
        should_process, reason, state = adapter.should_process(event)
        
        assert should_process is True
        assert reason == "new_message"
    
    def test_should_skip_processed_message(self, tmp_path):
        """测试已处理消息应该跳过"""
        adapter = TelegramIngressAdapter(
            idempotency_store_path=str(tmp_path / "idempotency.json")
        )
        event = create_message_event(
            chat_id="123",
            user_id="456",
            text="Test",
            message_id="1",
            update_id="1"
        )
        
        # 标记为已处理
        adapter.mark_processed(event, task_id="task_001", result_sent=True)
        
        # 再次检查
        should_process, reason, state = adapter.should_process(event)
        
        assert should_process is False
        assert reason == "already_processed_and_sent"


class TestCreateMessageEvent:
    """测试便捷创建 MessageEvent"""
    
    def test_create_basic_event(self):
        """测试创建基本事件"""
        event = create_message_event(
            chat_id="123",
            user_id="456",
            text="Hello"
        )
        
        assert event.source.chat_id == "123"
        assert event.source.user_id == "456"
        assert event.content.text == "Hello"
        assert event.context.is_private_chat is True
    
    def test_create_with_command(self):
        """测试创建命令事件"""
        event = create_message_event(
            chat_id="123",
            user_id="456",
            text="/status"
        )
        
        assert event.context.has_command is True
        assert event.context.command == "/status"
    
    def test_create_reply_event(self):
        """测试创建回复事件"""
        event = create_message_event(
            chat_id="123",
            user_id="456",
            text="Continue",
            is_reply=True
        )
        
        assert event.context.is_reply is True
