"""
Telegram-style message bubble widget
"""

import os
import html
from typing import Dict, List
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QPainter, QPainterPath, QColor

from src.api.models import Message
from .themes import get_theme_colors

class TelegramMessageBubble(QWidget):
    """Telegram-style message bubble with proper spacing and styling"""
    
    def __init__(self, message: Message, is_dark: bool = False):
        super().__init__()
        self.message = message
        self.is_dark = is_dark
        self.colors = get_theme_colors(is_dark)
        
        self.setup_ui()
        self.apply_bubble_style()
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Bubble frame
        self.bubble_frame = QFrame()
        bubble_layout = QVBoxLayout(self.bubble_frame)
        bubble_layout.setContentsMargins(12, 8, 12, 8)
        bubble_layout.setSpacing(4)
        
        # Sender name (only for group chats and not own messages)
        if not self.message.is_own and hasattr(self.message, 'sender_name') and self.message.sender_name:
            sender_label = QLabel(self.message.sender_name)
            sender_font = QFont()
            sender_font.setPointSize(12)
            sender_font.setWeight(QFont.Medium)
            sender_label.setFont(sender_font)
            sender_label.setStyleSheet(f"""
                QLabel {{
                    color: {self.colors['PRIMARY']};
                    padding-bottom: 2px;
                }}
            """)
            bubble_layout.addWidget(sender_label)
        
        # Message text
        message_text = html.escape(self.message.text) if hasattr(html, 'escape') else self.message.text
        message_label = QLabel(message_text)
        message_label.setWordWrap(True)
        message_label.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.LinksAccessibleByMouse)
        message_font = QFont()
        message_font.setPointSize(14)
        message_label.setFont(message_font)
        message_label.setStyleSheet("""
            QLabel {
                background-color: transparent;
                line-height: 1.4;
            }
        """)
        bubble_layout.addWidget(message_label)
        
        # Files attachments
        if self.message.files:
            for file_info in self.message.files:
                file_widget = self.create_file_widget(file_info)
                bubble_layout.addWidget(file_widget)
        
        # Time and status footer
        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(0, 4, 0, 0)
        
        time_label = QLabel(self.format_message_time())
        time_font = QFont()
        time_font.setPointSize(11)
        time_label.setFont(time_font)
        time_label.setStyleSheet(f"""
            QLabel {{
                color: {'rgba(255, 255, 255, 0.6)' if self.message.is_own else self.colors['ON_SURFACE_VARIANT']};
            }}
        """)
        footer_layout.addWidget(time_label)
        
        if self.message.is_own:
            footer_layout.addStretch()
            status_label = QLabel(self.get_status_icon())
            status_label.setStyleSheet(f"""
                QLabel {{
                    color: {'#ffffff' if self.message.read else 'rgba(255, 255, 255, 0.6)'};
                    font-size: 12px;
                }}
            """)
            footer_layout.addWidget(status_label)
        
        bubble_layout.addLayout(footer_layout)
        
        layout.addWidget(self.bubble_frame)
    
    def apply_bubble_style(self):
        """Apply Telegram-style bubble appearance"""
        if self.message.is_own:
            # Outgoing message (blue)
            bg_color = self.colors['OUTGOING_BUBBLE']
            text_color = self.colors['OUTGOING_TEXT']
            border_radius = "18px 4px 18px 18px"
        else:
            # Incoming message
            bg_color = self.colors['INCOMING_BUBBLE']
            text_color = self.colors['INCOMING_TEXT']
            border_radius = "4px 18px 18px 18px"
        
        self.bubble_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border: {'1px solid ' + self.colors['BUBBLE_BORDER'] if not self.message.is_own else 'none'};
                border-radius: {border_radius};
                margin: {'2px 8px 2px 2px' if self.message.is_own else '2px 2px 2px 8px'};
            }}
            QLabel {{
                color: {text_color};
                background-color: transparent;
            }}
        """)
    
    def create_file_widget(self, file_info: Dict) -> QFrame:
        """Create file attachment widget"""
        file_widget = QFrame()
        file_widget.setStyleSheet(f"""
            QFrame {{
                background-color: {'rgba(255, 255, 255, 0.1)' if self.message.is_own else self.colors['SURFACE_VARIANT']};
                border-radius: 12px;
                border: 1px solid {'rgba(255, 255, 255, 0.2)' if self.message.is_own else self.colors['BORDER']};
                padding: 8px;
                margin-top: 8px;
            }}
        """)
        
        layout = QHBoxLayout(file_widget)
        layout.setSpacing(8)
        
        # File icon
        filename = file_info.get('name', 'file')
        ext = os.path.splitext(filename)[1].lower()
        icon = self.get_file_icon(ext)
        
        icon_label = QLabel(icon)
        icon_label.setFixedSize(32, 32)
        icon_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                qproperty-alignment: 'AlignCenter';
            }
        """)
        layout.addWidget(icon_label)
        
        # File info
        file_layout = QVBoxLayout()
        file_layout.setSpacing(2)
        
        name_label = QLabel(filename)
        name_font = QFont()
        name_font.setPointSize(13)
        name_font.setWeight(QFont.Medium)
        name_label.setFont(name_font)
        name_label.setStyleSheet("""
            QLabel {
                background-color: transparent;
            }
        """)
        file_layout.addWidget(name_label)
        
        # File size
        size = file_info.get('size', 0)
        if size > 0:
            size_str = self.format_size(size)
            size_label = QLabel(size_str)
            size_font = QFont()
            size_font.setPointSize(11)
            size_label.setFont(size_font)
            size_label.setStyleSheet(f"""
                QLabel {{
                    color: {'rgba(255, 255, 255, 0.6)' if self.message.is_own else self.colors['ON_SURFACE_VARIANT']};
                    background-color: transparent;
                }}
            """)
            file_layout.addWidget(size_label)
        
        layout.addLayout(file_layout, 1)
        
        # Download button
        if file_info.get('url') or file_info.get('download_link'):
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
        """Get appropriate emoji for file type"""
        icon_map = {
            '.pdf': '📕',
            '.doc': '📘', '.docx': '📘',
            '.xls': '📊', '.xlsx': '📊',
            '.ppt': '📑', '.pptx': '📑',
            '.jpg': '🖼️', '.jpeg': '🖼️', '.png': '🖼️', '.gif': '🖼️',
            '.zip': '📦', '.rar': '📦', '.7z': '📦', '.tar': '📦',
            '.mp3': '🎵', '.wav': '🎵', '.flac': '🎵',
            '.mp4': '🎬', '.avi': '🎬', '.mov': '🎬', '.mkv': '🎬',
            '.txt': '📄', '.md': '📄',
            '.py': '🐍', '.js': '📜', '.html': '🌐', '.css': '🎨',
        }
        return icon_map.get(ext, '📎')
    
    def format_size(self, size: int) -> str:
        """Format file size human-readable"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    def format_message_time(self) -> str:
        """Format message time like Telegram"""
        try:
            if hasattr(self.message, 'timestamp'):
                dt = datetime.fromisoformat(self.message.timestamp.replace('Z', '+00:00'))
                return dt.strftime("%H:%M")
        except:
            pass
        return "00:00"
    
    def get_status_icon(self) -> str:
        """Get message status icon (single/double check)"""
        if self.message.read:
            return "✓✓"
        return "✓"
    
    def download_file(self, file_info: Dict):
        """Handle file download"""
        print(f"Downloading: {file_info.get('name')}")
        # TODO: Implement actual file download
    
    def sizeHint(self) -> QSize:
        """Provide size hint for layout"""
        return QSize(400, 100)
    
    def minimumSizeHint(self) -> QSize:
        """Provide minimum size hint"""
        return QSize(200, 60)


# Backward compatibility
MessageBubble = TelegramMessageBubble