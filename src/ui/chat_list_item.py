"""
Chat list item widget for sidebar with modern design
"""

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QMouseEvent

from api.models import Group, User, Customer
from .themes import get_theme_colors

class ChatListItem(QWidget):
    clicked = pyqtSignal(int)
    
    def __init__(self, group: Group, current_user: User, customers: list, is_dark=False):
        super().__init__()
        self.group_id = group.id
        self.group = group
        self.is_dark = is_dark
        self.colors = get_theme_colors(is_dark)
        
        self.setup_ui(group, current_user, customers)
        self.apply_style()
    
    def setup_ui(self, group: Group, current_user: User, customers: list):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)
        
        # Avatar with initial
        avatar_label = QLabel()
        avatar_label.setFixedSize(48, 48)
        avatar_label.setStyleSheet(f"""
            QLabel {{
                background-color: {self.colors['PRIMARY']};
                border-radius: 24px;
                font-size: 18px;
                font-weight: bold;
                color: white;
                qproperty-alignment: 'AlignCenter';
            }}
        """)
        
        # Get first letter of chat title
        title = group.display_title(current_user, customers)
        if title:
            letter = title[0].upper()
        else:
            letter = "?"
        avatar_label.setText(letter)
        layout.addWidget(avatar_label)
        
        # Chat info section
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        
        # Title with unread count
        title_text = title
        if group.unread_count > 0:
            title_text = f"({group.unread_count}) {title_text}"
        
        title_label = QLabel(title_text)
        title_label.setStyleSheet(f"""
            QLabel {{
                font-weight: 600;
                font-size: 14px;
                color: {self.colors['ON_SURFACE']};
            }}
        """)
        info_layout.addWidget(title_label)
        
        # Last message preview
        preview_text = ""
        if group.last_message:
            preview_text = group.last_message
        if group.last_message_time:
            preview_text += f" • {group.last_message_time}"
        
        preview_label = QLabel(preview_text[:50] + ("..." if len(preview_text) > 50 else ""))
        preview_label.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['ON_SURFACE_VARIANT']};
                font-size: 13px;
            }}
        """)
        info_layout.addWidget(preview_label)
        
        layout.addLayout(info_layout, 1)
        
        # Time
        if group.date:
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(group.date.replace('Z', '+00:00'))
                time_str = dt.strftime("%H:%M")
                time_label = QLabel(time_str)
                time_label.setStyleSheet(f"""
                    QLabel {{
                        color: {self.colors['ON_SURFACE_VARIANT']};
                        font-size: 12px;
                    }}
                """)
                layout.addWidget(time_label)
            except:
                pass
    
    def apply_style(self):
        hover_bg = self.colors['SURFACE_VARIANT']
        self.setStyleSheet(f"""
            QWidget {{
                background-color: transparent;
                border: none;
                border-radius: 12px;
            }}
            QWidget:hover {{
                background-color: {hover_bg};
            }}
        """)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.group_id)
            event.accept()
    
    def enterEvent(self, event):
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {self.colors['SURFACE_VARIANT']};
                border: none;
                border-radius: 12px;
            }}
        """)
    
    def leaveEvent(self, event):
        self.apply_style()