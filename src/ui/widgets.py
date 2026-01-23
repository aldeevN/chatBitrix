"""
Custom styled widgets for Telegram-like UI with modern design
"""

from PyQt5.QtWidgets import QPushButton, QTextEdit, QLineEdit
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from .themes import COLORS, get_theme_colors

class TelegramButton(QPushButton):
    """Modern Telegram-style button"""
    def __init__(self, text="", icon=None, parent=None, is_dark=False):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.is_dark = is_dark
        self.update_style()
    
    def update_style(self):
        colors = get_theme_colors(self.is_dark)
        self._style = f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                padding: 8px 16px;
                color: {colors['PRIMARY']};
                font-weight: 600;
                border-radius: 8px;
                font-size: 13px;
                letter-spacing: 0.5px;
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
    """Modern Telegram-style text input"""
    def __init__(self, parent=None, is_dark=False):
        super().__init__(parent)
        self.setPlaceholderText("Message...")
        self.setMaximumHeight(100)
        self.is_dark = is_dark
        self.update_style()
    
    def update_style(self):
        colors = get_theme_colors(self.is_dark)
        self.setStyleSheet(f"""
            QTextEdit {{
                background-color: {colors['SURFACE']};
                border: 1px solid {colors['BORDER']};
                border-radius: 24px;
                padding: 10px 16px;
                font-size: 14px;
                color: {colors['ON_SURFACE']};
                selection-background-color: {colors['PRIMARY']};
                margin: 4px;
            }}
            QTextEdit:focus {{
                border: 2px solid {colors['PRIMARY']};
            }}
        """)

class TelegramSearchBar(QLineEdit):
    """Modern Telegram-style search bar"""
    def __init__(self, parent=None, is_dark=False):
        super().__init__(parent)
        self.setPlaceholderText("🔍 Search...")
        self.setMaximumHeight(40)
        self.is_dark = is_dark
        self.update_style()
    
    def update_style(self):
        colors = get_theme_colors(self.is_dark)
        self.setStyleSheet(f"""
            QLineEdit {{
                background-color: {colors['SURFACE_VARIANT']};
                border: none;
                border-radius: 20px;
                padding: 8px 16px;
                padding-left: 40px;
                font-size: 14px;
                color: {colors['ON_SURFACE']};
                margin: 8px 12px;
            }}
            QLineEdit:focus {{
                background-color: {colors['SURFACE']};
                border: 1px solid {colors['PRIMARY']};
            }}
        """)