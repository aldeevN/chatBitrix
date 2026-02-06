"""
UI module for Telegram-like Bitrix24 Chat
"""

# Try to import Telegram-specific components
try:
    from src.ui.main_window import TelegramChatWindow
    from src.ui.widgets import TelegramButton, TelegramInput, TelegramSearchBar, TelegramFrame
    from src.ui.chat_list_item import ChatListItem, TelegramChatListItem
    from src.ui.message_bubble import MessageBubble, TelegramMessageBubble
    from src.ui.themes import (
        COLORS, COLORS_LIGHT, COLORS_DARK,
        TELEGRAM_LIGHT, TELEGRAM_DARK,
        get_theme_colors, apply_theme, apply_telegram_theme, toggle_dark_mode
    )
    
    # New message dialog if available
    try:
        from src.ui.new_message_dialog import NewMessageDialog
        HAS_NEW_MESSAGE_DIALOG = True
    except ImportError:
        NewMessageDialog = None
        HAS_NEW_MESSAGE_DIALOG = False
        
except ImportError as e:
    print(f"Warning: Could not import some UI components: {e}")
    # Fall back to minimal imports
    from src.ui.main_window import TelegramChatWindow
    from src.ui.widgets import TelegramButton, TelegramInput, TelegramSearchBar
    from src.ui.chat_list_item import ChatListItem
    from src.ui.message_bubble import MessageBubble
    from src.ui.themes import COLORS, apply_theme, toggle_dark_mode
    
    # Set defaults for missing imports
    TelegramFrame = None
    TelegramChatListItem = None
    TelegramMessageBubble = None
    NewMessageDialog = None
    HAS_NEW_MESSAGE_DIALOG = False
    TELEGRAM_LIGHT = COLORS
    TELEGRAM_DARK = COLORS
    COLORS_LIGHT = COLORS
    COLORS_DARK = COLORS
    apply_telegram_theme = apply_theme
    get_theme_colors = lambda is_dark: COLORS_DARK if is_dark else COLORS_LIGHT

__all__ = [
    # Main window
    'TelegramChatWindow',
    
    # Widgets
    'TelegramButton',
    'TelegramInput',
    'TelegramSearchBar',
    'TelegramFrame',
    
    # Chat components
    'ChatListItem',
    'TelegramChatListItem',
    'MessageBubble',
    'TelegramMessageBubble',
    
    # Dialog
    'NewMessageDialog',
    'HAS_NEW_MESSAGE_DIALOG',
    
    # Themes
    'COLORS',
    'COLORS_LIGHT',
    'COLORS_DARK',
    'TELEGRAM_LIGHT',
    'TELEGRAM_DARK',
    'get_theme_colors',
    'apply_theme',
    'apply_telegram_theme',
    'toggle_dark_mode'
]