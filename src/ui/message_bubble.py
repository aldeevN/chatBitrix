"""
Message bubble widget for chat
"""

import os
from typing import Dict

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame
)
from PyQt5.QtCore import Qt

from api.models import Message
from .themes import COLORS

class MessageBubble(QWidget):
    def __init__(self, message: Message, is_dark: bool = False):
        super().__init__()
        self.message = message
        self.is_dark = is_dark
        
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
                    color: {COLORS['TELEGRAM_BLUE']};
                    font-weight: 500;
                    font-size: 13px;
                }}
            """)
            layout.addWidget(sender_label)
        
        # Message text
        text_label = QLabel(self.message.text)
        text_label.setWordWrap(True)
        text_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
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
                color: {COLORS['TEXT_SECONDARY_LIGHT']};
                font-size: 12px;
            }}
        """)
        footer_layout.addWidget(time_label)
        
        if self.message.is_own:
            status_icon = "✓✓" if self.message.read else "✓"
            status_label = QLabel(status_icon)
            status_label.setStyleSheet(f"""
                QLabel {{
                    color: {COLORS['TELEGRAM_BLUE']};
                    font-size: 12px;
                }}
            """)
            footer_layout.addWidget(status_label)
        
        layout.addLayout(footer_layout)
    
    def create_file_widget(self, file_info: Dict) -> QFrame:
        file_widget = QFrame()
        file_widget.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.3);
                border-radius: 8px;
                padding: 8px;
            }
        """)
        
        layout = QHBoxLayout(file_widget)
        
        # File icon based on type
        filename = file_info.get('name', 'file')
        ext = os.path.splitext(filename)[1].lower()
        icon = self.get_file_icon(ext)
        
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 20px;")
        layout.addWidget(icon_label)
        
        # File info
        file_layout = QVBoxLayout()
        
        name_label = QLabel(filename)
        name_label.setStyleSheet("font-weight: 500;")
        file_layout.addWidget(name_label)
        
        size = file_info.get('size', 0)
        size_str = self.format_size(size)
        size_label = QLabel(size_str)
        size_label.setStyleSheet(f"color: {COLORS['TEXT_SECONDARY_LIGHT']}; font-size: 12px;")
        file_layout.addWidget(size_label)
        
        layout.addLayout(file_layout, 1)
        
        # Download button
        download_btn = QPushButton("↓")
        download_btn.setFixedSize(30, 30)
        download_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(51, 144, 236, 0.1);
                border: none;
                border-radius: 15px;
                color: {COLORS['TELEGRAM_BLUE']};
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: rgba(51, 144, 236, 0.2);
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
        if self.message.is_own:
            if self.is_dark:
                self.setStyleSheet(f"""
                    QWidget {{
                        background-color: {COLORS['BUBBLE_ME_DARK']};
                        border-radius: 18px;
                        border-top-right-radius: 4px;
                        border: none;
                        padding: 8px;
                    }}
                    QLabel {{
                        color: {COLORS['TEXT_DARK']};
                        background-color: transparent;
                    }}
                """)
            else:
                self.setStyleSheet(f"""
                    QWidget {{
                        background-color: {COLORS['BUBBLE_ME_LIGHT']};
                        border-radius: 18px;
                        border-top-right-radius: 4px;
                        border: none;
                        padding: 8px;
                    }}
                    QLabel {{
                        color: {COLORS['TEXT_LIGHT']};
                        background-color: transparent;
                    }}
                """)
        else:
            if self.is_dark:
                self.setStyleSheet(f"""
                    QWidget {{
                        background-color: {COLORS['BUBBLE_THEM_DARK']};
                        border-radius: 18px;
                        border-top-left-radius: 4px;
                        border: 1px solid {COLORS['BORDER_DARK']};
                        padding: 8px;
                    }}
                    QLabel {{
                        color: {COLORS['TEXT_DARK']};
                        background-color: transparent;
                    }}
                """)
            else:
                self.setStyleSheet(f"""
                    QWidget {{
                        background-color: {COLORS['BUBBLE_THEM_LIGHT']};
                        border-radius: 18px;
                        border-top-left-radius: 4px;
                        border: 1px solid {COLORS['BORDER_LIGHT']};
                        padding: 8px;
                    }}
                    QLabel {{
                        color: {COLORS['TEXT_LIGHT']};
                        background-color: transparent;
                    }}
                """)
    
    def download_file(self, file_info: Dict):
        """Handle file download"""
        print(f"Downloading: {file_info.get('name')}")
        # TODO: Implement actual file download