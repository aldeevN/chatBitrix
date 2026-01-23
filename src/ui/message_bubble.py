"""
Message bubble widget for chat with modern design
"""

import os
from typing import Dict

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame
)
from PyQt5.QtCore import Qt

from api.models import Message
from .themes import get_theme_colors

class MessageBubble(QWidget):
    def __init__(self, message: Message, is_dark: bool = False):
        super().__init__()
        self.message = message
        self.is_dark = is_dark
        self.colors = get_theme_colors(is_dark)
        
        self.setup_ui()
        self.apply_style()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(4)
        
        # Sender name for group chats
        if not self.message.is_own:
            sender_label = QLabel(self.message.sender_name)
            sender_label.setStyleSheet(f"""
                QLabel {{
                    color: {self.colors['PRIMARY']};
                    font-weight: 600;
                    font-size: 12px;
                    letter-spacing: 0.3px;
                }}
            """)
            layout.addWidget(sender_label)
        
        # Message text
        text_label = QLabel(self.message.text)
        text_label.setWordWrap(True)
        text_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        text_label.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['ON_SURFACE']};
                font-size: 14px;
                line-height: 1.4;
                background-color: transparent;
            }}
        """)
        layout.addWidget(text_label)
        
        # Files attachments
        if self.message.files:
            for file_info in self.message.files:
                file_widget = self.create_file_widget(file_info)
                layout.addWidget(file_widget)
        
        # Time and status
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()
        
        time_label = QLabel(self.message.time_display)
        time_label.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['ON_SURFACE_VARIANT']};
                font-size: 11px;
            }}
        """)
        footer_layout.addWidget(time_label)
        
        if self.message.is_own:
            status_icon = "✓✓" if self.message.read else "✓"
            status_label = QLabel(status_icon)
            status_label.setStyleSheet(f"""
                QLabel {{
                    color: {self.colors['PRIMARY']};
                    font-size: 11px;
                    margin-left: 4px;
                }}
            """)
            footer_layout.addWidget(status_label)
        
        layout.addLayout(footer_layout)
    
    def create_file_widget(self, file_info: Dict) -> QFrame:
        file_widget = QFrame()
        file_widget.setStyleSheet(f"""
            QFrame {{
                background-color: {self.colors['SURFACE_VARIANT']};
                border-radius: 12px;
                border: 1px solid {self.colors['BORDER']};
                padding: 8px;
            }}
        """)
        
        layout = QHBoxLayout(file_widget)
        layout.setSpacing(8)
        
        # File icon based on type
        filename = file_info.get('name', 'file')
        ext = os.path.splitext(filename)[1].lower()
        icon = self.get_file_icon(ext)
        
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 24px;")
        icon_label.setFixedWidth(30)
        layout.addWidget(icon_label)
        
        # File info
        file_layout = QVBoxLayout()
        file_layout.setSpacing(2)
        
        name_label = QLabel(filename)
        name_label.setStyleSheet(f"""
            QLabel {{
                font-weight: 600;
                font-size: 13px;
                color: {self.colors['ON_SURFACE']};
            }}
        """)
        file_layout.addWidget(name_label)
        
        size = file_info.get('size', 0)
        size_str = self.format_size(size)
        size_label = QLabel(size_str)
        size_label.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['ON_SURFACE_VARIANT']};
                font-size: 11px;
            }}
        """)
        file_layout.addWidget(size_label)
        
        layout.addLayout(file_layout, 1)
        
        # Download button
        download_btn = QPushButton("↓")
        download_btn.setFixedSize(32, 32)
        download_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.colors['PRIMARY']};
                border: none;
                border-radius: 16px;
                color: white;
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {self.colors['PRIMARY_DARK']};
            }}
        """)
        download_btn.clicked.connect(lambda: self.download_file(file_info))
        layout.addWidget(download_btn)
        
        return file_widget
    
    def get_file_icon(self, ext: str) -> str:
        icons = {
            '.pdf': '📕',
            '.doc': '📘', '.docx': '📘',
            '.xls': '📊', '.xlsx': '📊',
            '.jpg': '🖼️', '.jpeg': '🖼️', '.png': '🖼️', '.gif': '🖼️',
            '.zip': '📦', '.rar': '📦', '.7z': '📦',
            '.mp3': '🎵', '.wav': '🎵',
            '.mp4': '🎬', '.avi': '🎬', '.mov': '🎬',
        }
        return icons.get(ext, '📎')
    
    def format_size(self, size: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    def apply_style(self):
        """Apply modern bubble style based on sender"""
        if self.message.is_own:
            self.setStyleSheet(f"""
                QWidget {{
                    background-color: {self.colors['PRIMARY']};
                    border-radius: 20px;
                    border-top-right-radius: 4px;
                    border: none;
                    padding: 8px;
                    margin: 2px;
                }}
                QLabel {{
                    color: white;
                    background-color: transparent;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QWidget {{
                    background-color: {self.colors['SURFACE']};
                    border-radius: 20px;
                    border-top-left-radius: 4px;
                    border: 1px solid {self.colors['BORDER']};
                    padding: 8px;
                    margin: 2px;
                }}
                QLabel {{
                    color: {self.colors['ON_SURFACE']};
                    background-color: transparent;
                }}
            """)
    
    def download_file(self, file_info: Dict):
        """Handle file download"""
        print(f"Downloading: {file_info.get('name')}")