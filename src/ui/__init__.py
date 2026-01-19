"""
UI module for Telegram-like Bitrix24 Chat
"""

from .main_window import TelegramChatWindow
from .widgets import TelegramButton, TelegramInput, TelegramSearchBar
from .chat_list_item import ChatListItem
from .message_bubble import MessageBubble
from .themes import COLORS, apply_theme, toggle_dark_mode

__all__ = [
    'TelegramChatWindow',
    'TelegramButton',
    'TelegramInput',
    'TelegramSearchBar',
    'ChatListItem',
    'MessageBubble',
    'COLORS',
    'apply_theme',
    'toggle_dark_mode'
]