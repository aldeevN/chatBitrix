"""
Themes and colors for the UI
"""

COLORS = {
    'TELEGRAM_BLUE': '#3390ec',
    'TELEGRAM_BLUE_DARK': '#2b7bc2',
    'BACKGROUND_LIGHT': '#f1f3f4',
    'BACKGROUND_DARK': '#1e1e1e',
    'CHAT_BG_LIGHT': '#ffffff',
    'CHAT_BG_DARK': '#1a1d21',
    'SIDEBAR_BG_LIGHT': '#ffffff',
    'SIDEBAR_BG_DARK': '#1a1d21',
    'BUBBLE_ME_LIGHT': '#dbf6c6',
    'BUBBLE_ME_DARK': '#2b5278',
    'BUBBLE_THEM_LIGHT': '#ffffff',
    'BUBBLE_THEM_DARK': '#2d2d2d',
    'TEXT_LIGHT': '#000000',
    'TEXT_DARK': '#e1e3e6',
    'TEXT_SECONDARY_LIGHT': '#707579',
    'TEXT_SECONDARY_DARK': '#a5a7ab',
    'BORDER_LIGHT': '#e7e8ec',
    'BORDER_DARK': '#2f3136',
}

def apply_theme(widget, is_dark_mode=False):
    """Apply theme to widget"""
    if is_dark_mode:
        widget.setStyleSheet(f"""
            QMainWindow {{
                background-color: {COLORS['BACKGROUND_DARK']};
            }}
            QWidget#sidebar {{
                background-color: {COLORS['SIDEBAR_BG_DARK']};
                border-right: 1px solid {COLORS['BORDER_DARK']};
            }}
            QWidget#chatArea {{
                background-color: {COLORS['CHAT_BG_DARK']};
            }}
        """)
    else:
        widget.setStyleSheet(f"""
            QMainWindow {{
                background-color: {COLORS['BACKGROUND_LIGHT']};
            }}
            QWidget#sidebar {{
                background-color: {COLORS['SIDEBAR_BG_LIGHT']};
                border-right: 1px solid {COLORS['BORDER_LIGHT']};
            }}
            QWidget#chatArea {{
                background-color: {COLORS['CHAT_BG_LIGHT']};
            }}
        """)

def toggle_dark_mode(widget, current_mode):
    """Toggle dark mode"""
    new_mode = not current_mode
    apply_theme(widget, new_mode)
    return new_mode