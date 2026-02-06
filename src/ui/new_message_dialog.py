"""
Telegram-style new message dialog
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QListWidget, QListWidgetItem, QLineEdit, 
    QPushButton, QScrollArea, QWidget
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from .themes import get_theme_colors

class NewMessageDialog(QDialog):
    """Telegram-style dialog for starting new chat"""
    
    message_sent = pyqtSignal(str, int)
    
    def __init__(self, parent=None, groups=None, current_user=None, customers=None, is_dark=False):
        super().__init__(parent)
        self.groups = groups or []
        self.current_user = current_user
        self.customers = customers or []
        self.is_dark = is_dark
        self.colors = get_theme_colors(is_dark)
        
        self.setup_ui()
        self.apply_style()
    
    def setup_ui(self):
        self.setWindowTitle("New Message")
        self.setMinimumSize(400, 500)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = QWidget()
        header.setFixedHeight(56)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 12, 16, 12)
        
        title_label = QLabel("New Message")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setWeight(QFont.Bold)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(32, 32)
        close_btn.clicked.connect(self.reject)
        header_layout.addWidget(close_btn)
        
        layout.addWidget(header)
        
        # Search
        search_input = QLineEdit()
        search_input.setPlaceholderText("Search contacts...")
        search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {self.colors['SURFACE_VARIANT']};
                border: none;
                border-radius: 8px;
                padding: 12px 16px;
                margin: 8px 16px;
                font-size: 14px;
                color: {self.colors['ON_SURFACE']};
            }}
        """)
        layout.addWidget(search_input)
        
        # Contacts list
        self.contacts_list = QListWidget()
        self.contacts_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {self.colors['SURFACE']};
                border: none;
                font-size: 14px;
            }}
            QListWidget::item {{
                padding: 12px 16px;
                border-bottom: 1px solid {self.colors['BORDER']};
            }}
            QListWidget::item:selected {{
                background-color: {self.colors['HIGHLIGHT']};
            }}
        """)
        
        # Add contacts
        for customer in self.customers[:10]:  # Limit to first 10
            item = QListWidgetItem(customer.full_name)
            item.setData(Qt.UserRole, customer.id)
            self.contacts_list.addItem(item)
        
        layout.addWidget(self.contacts_list, 1)
        
        # Message input
        input_widget = QWidget()
        input_layout = QHBoxLayout(input_widget)
        input_layout.setContentsMargins(16, 8, 16, 16)
        
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type a message...")
        input_layout.addWidget(self.message_input, 1)
        
        send_btn = QPushButton("Send")
        send_btn.setFixedWidth(80)
        send_btn.clicked.connect(self.send_message)
        input_layout.addWidget(send_btn)
        
        layout.addWidget(input_widget)
    
    def apply_style(self):
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {self.colors['SURFACE']};
                border: 1px solid {self.colors['BORDER']};
                border-radius: 12px;
            }}
            QLabel {{
                color: {self.colors['ON_SURFACE']};
            }}
        """)
    
    def send_message(self):
        message = self.message_input.text().strip()
        if not message:
            return
        
        selected_items = self.contacts_list.selectedItems()
        if not selected_items:
            return
        
        # Get selected contact
        contact_item = selected_items[0]
        contact_id = contact_item.data(Qt.UserRole)
        
        self.message_sent.emit(message, contact_id)
        self.accept()