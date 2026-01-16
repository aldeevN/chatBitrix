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
        self._style = """
            QPushButton {
                background-color: transparent;
                border: none;
                padding: 8px;
                color: #3390ec;
                font-weight: 500;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: rgba(51, 144, 236, 0.1);
            }
            QPushButton:pressed {
                background-color: rgba(51, 144, 236, 0.2);
            }
        """
        self.setStyleSheet(self._style)

class TelegramInput(QTextEdit):
    """Telegram-style text input"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("Message...")
        self.setMaximumHeight(120)
        self.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: 1px solid #e7e8ec;
                border-radius: 20px;
                padding: 10px 15px;
                font-size: 14px;
                selection-background-color: #3390ec;
            }
            QTextEdit:focus {
                border: 1px solid #3390ec;
            }
        """)

class TelegramSearchBar(QLineEdit):
    """Telegram-style search bar"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("Search...")
        self.setStyleSheet("""
            QLineEdit {
                background-color: #f1f3f4;
                border: none;
                border-radius: 20px;
                padding: 10px 15px;
                padding-left: 35px;
                font-size: 14px;
            }
            QLineEdit:focus {
                background-color: white;
                border: 1px solid #3390ec;
            }
        """)