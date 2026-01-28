"""
UI module for Telegram-like Bitrix24 Chat
"""

from src.ui.main_window import TelegramChatWindow
from src.ui.widgets import TelegramButton, TelegramInput, TelegramSearchBar
from src.ui.chat_list_item import ChatListItem
from src.ui.message_bubble import MessageBubble
from src.ui.themes import COLORS, apply_theme, toggle_dark_mode

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