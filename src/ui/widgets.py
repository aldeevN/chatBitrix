"""
Telegram-styled custom widgets
"""

from PyQt5.QtWidgets import QPushButton, QTextEdit, QLineEdit, QFrame
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QPainter, QPainterPath, QColor

from .themes import get_theme_colors

class TelegramButton(QPushButton):
    """Telegram-style button with rounded corners"""
    
    def __init__(self, text="", icon=None, parent=None, is_dark=False):
        super().__init__(text, parent)
        self.is_dark = is_dark
        self.setCursor(Qt.PointingHandCursor)
        self.update_style()
    
    def update_style(self):
        colors = get_theme_colors(self.is_dark)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors['PRIMARY']};
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                color: {colors['ON_PRIMARY']};
                font-weight: 600;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {colors['PRIMARY_DARK']};
            }}
            QPushButton:pressed {{
                background-color: {colors['PRIMARY_DARK']};
                padding-top: 9px;
                padding-bottom: 7px;
            }}
            QPushButton:disabled {{
                background-color: {colors['BORDER']};
                color: {colors['ON_SURFACE_VARIANT']};
            }}
        """)

class TelegramInput(QLineEdit):
    """Telegram-style text input"""
    
    def __init__(self, parent=None, is_dark=False):
        super().__init__(parent)
        self.is_dark = is_dark
        self.update_style()
    
    def update_style(self):
        colors = get_theme_colors(self.is_dark)
        self.setStyleSheet(f"""
            QLineEdit {{
                background-color: {colors['SURFACE_VARIANT']};
                border: 1px solid {colors['BORDER']};
                border-radius: 20px;
                padding: 10px 16px;
                font-size: 14px;
                color: {colors['ON_SURFACE']};
                selection-background-color: {colors['PRIMARY']};
                selection-color: {colors['ON_PRIMARY']};
            }}
            QLineEdit:focus {{
                border: 2px solid {colors['PRIMARY']};
                background-color: {colors['SURFACE']};
            }}
            QLineEdit::placeholder {{
                color: {colors['ON_SURFACE_VARIANT']};
            }}
        """)

class TelegramSearchBar(TelegramInput):
    """Telegram-style search bar with icon"""
    
    def __init__(self, parent=None, is_dark=False):
        super().__init__(parent, is_dark)
        self.setPlaceholderText("Search...")
    
    def update_style(self):
        colors = get_theme_colors(self.is_dark)
        self.setStyleSheet(f"""
            QLineEdit {{
                background-color: {colors['SURFACE_VARIANT']};
                border: none;
                border-radius: 20px;
                padding: 10px 16px 10px 40px;
                font-size: 14px;
                color: {colors['ON_SURFACE']};
                selection-background-color: {colors['PRIMARY']};
                selection-color: {colors['ON_PRIMARY']};
            }}
            QLineEdit:focus {{
                background-color: {colors['SURFACE']};
                border: 1px solid {colors['PRIMARY']};
            }}
            QLineEdit::placeholder {{
                color: {colors['ON_SURFACE_VARIANT']};
                font-style: italic;
            }}
        """)

class TelegramFrame(QFrame):
    """Telegram-style frame with rounded corners"""
    
    def __init__(self, parent=None, is_dark=False):
        super().__init__(parent)
        self.is_dark = is_dark
        self.update_style()
    
    def update_style(self):
        colors = get_theme_colors(self.is_dark)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {colors['SURFACE']};
                border: 1px solid {colors['BORDER']};
                border-radius: 12px;
            }}
        """)