"""
Custom styled widgets for Telegram-like UI
"""

from PyQt5.QtWidgets import QPushButton, QTextEdit, QLineEdit
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from .themes import COLORS

class TelegramButton(QPushButton):
    """Telegram-style button"""
    def __init__(self, text="", icon=None, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self._style = f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                padding: 8px 12px;
                color: {COLORS['TELEGRAM_BLUE']};
                font-weight: 500;
                border-radius: 8px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: rgba(51, 144, 236, 0.1);
            }}
            QPushButton:pressed {{
                background-color: rgba(51, 144, 236, 0.2);
            }}
        """
        self.setStyleSheet(self._style)

class TelegramInput(QTextEdit):
    """Telegram-style text input"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("Message...")
        self.setMaximumHeight(120)
        self.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLORS['CHAT_BG_LIGHT']};
                border: 2px solid {COLORS['BORDER_LIGHT']};
                border-radius: 20px;
                padding: 10px 15px;
                font-size: 14px;
                selection-background-color: {COLORS['TELEGRAM_BLUE']};
                margin: 4px;
            }}
            QTextEdit:focus {{
                border: 2px solid {COLORS['TELEGRAM_BLUE']};
            }}
        """)

class TelegramSearchBar(QLineEdit):
    """Telegram-style search bar"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("🔍 Search...")
        self.setMaximumHeight(40)
        self.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLORS['BACKGROUND_LIGHT']};
                border: none;
                border-radius: 20px;
                padding: 8px 15px;
                padding-left: 35px;
                font-size: 14px;
                color: {COLORS['TEXT_LIGHT']};
                margin: 8px 12px;
            }}
            QLineEdit:focus {{
                background-color: {COLORS['CHAT_BG_LIGHT']};
                border: 1px solid {COLORS['TELEGRAM_BLUE']};
            }}
        """)