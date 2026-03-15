"""
Telegram Ingress Adapters

Telegram 消息入口适配器，将 Telegram update 标准化为统一 MessageEvent。
"""

from .telegram_ingress import (
    TelegramIngressAdapter,
    MessageEvent,
    TelegramSource,
    TelegramContent,
    TelegramContext,
    IdempotencyStore,
    normalize_telegram_update,
    create_message_event
)

__all__ = [
    "TelegramIngressAdapter",
    "MessageEvent",
    "TelegramSource",
    "TelegramContent",
    "TelegramContext",
    "IdempotencyStore",
    "normalize_telegram_update",
    "create_message_event"
]
