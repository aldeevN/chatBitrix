"""
Chat list item widget for sidebar
"""

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QMouseEvent

from api.models import Group, User, Customer
from .themes import COLORS

class ChatListItem(QWidget):
    clicked = pyqtSignal(int)
    
    def __init__(self, group: Group, current_user: User, customers: list[Customer]):
        super().__init__()
        self.group_id = group.id
        self.group = group
        
        self.setup_ui(group, current_user, customers)
        self.apply_style()
    
    def setup_ui(self, group: Group, current_user: User, customers: list[Customer]):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)
        
        # Avatar
        avatar_label = QLabel()
        avatar_label.setFixedSize(48, 48)
        avatar_label.setStyleSheet("""
            QLabel {
                background-color: #3390ec;
                border-radius: 24px;
                font-size: 18px;
                font-weight: bold;
                color: white;
                qproperty-alignment: 'AlignCenter';
            }
        """)
        
        # Get first letter of chat title
        title = group.display_title(current_user, customers)
        if title:
            letter = title[0].upper()
        else:
            letter = "?"
        avatar_label.setText(letter)
        layout.addWidget(avatar_label)
        
        # Chat info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        
        # Title with unread count
        title_text = title
        if group.unread_count > 0:
            title_text = f"({group.unread_count}) {title_text}"
        
        title_label = QLabel(title_text)
        title_label.setStyleSheet("""
            QLabel {
                font-weight: 500;
                font-size: 14px;
            }
        """)
        info_layout.addWidget(title_label)
        
        # Last message preview
        preview_text = ""
        if group.last_message:
            preview_text = group.last_message
        if group.last_message_time:
            preview_text += f" • {group.last_message_time}"
        
        preview_label = QLabel(preview_text[:50] + ("..." if len(preview_text) > 50 else ""))
        preview_label.setStyleSheet("""
            QLabel {
                color: #707579;
                font-size: 13px;
            }
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
                time_label.setStyleSheet("""
                    QLabel {
                        color: #707579;
                        font-size: 12px;
                    }
                """)
                layout.addWidget(time_label)
            except:
                pass
    
    def apply_style(self):
        self.setStyleSheet("""
            QWidget {
                background-color: transparent;
                border: none;
            }
            QWidget:hover {
                background-color: rgba(0, 0, 0, 0.05);
            }
        """)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.group_id)
            event.accept()
    
    def enterEvent(self, event):
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(0, 0, 0, 0.05);
                border: none;
            }
        """)
    
    def leaveEvent(self, event):
        self.setStyleSheet("""
            QWidget {
                background-color: transparent;
                border: none;
            }
        """)