"""
Modern dialog for composing new messages
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QPushButton, QComboBox, QMessageBox, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from api.models import User, Customer, Group
from .themes import get_theme_colors

class NewMessageDialog(QDialog):
    """Modern new message compose dialog"""
    
    message_sent = pyqtSignal(str, int)  # text, group_id
    
    def __init__(self, parent=None, groups=None, current_user=None, customers=None, is_dark=False):
        super().__init__(parent)
        self.groups = groups or []
        self.current_user = current_user
        self.customers = customers or []
        self.is_dark = is_dark
        self.colors = get_theme_colors(is_dark)
        self.selected_group_id = None
        
        self.setWindowTitle("New Message")
        self.setGeometry(100, 100, 500, 400)
        self.setup_ui()
        self.apply_theme()
    
    def setup_ui(self):
        """Setup modern UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header = QLabel("Compose Message")
        header_font = QFont()
        header_font.setPointSize(16)
        header_font.setBold(True)
        header.setFont(header_font)
        layout.addWidget(header)
        
        # Chat selection
        chat_layout = QHBoxLayout()
        chat_label = QLabel("Select Chat:")
        chat_label.setStyleSheet(f"font-weight: 600; color: {self.colors['ON_SURFACE']};")
        chat_layout.addWidget(chat_label)
        
        self.chat_combo = QComboBox()
        self.chat_combo.setMinimumHeight(40)
        self.chat_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {self.colors['SURFACE']};
                border: 2px solid {self.colors['BORDER']};
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
                color: {self.colors['ON_SURFACE']};
            }}
            QComboBox:focus {{
                border: 2px solid {self.colors['PRIMARY']};
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox::down-arrow {{
                image: none;
            }}
        """)
        
        # Populate with groups
        for group in self.groups:
            display_name = group.display_title(self.current_user, self.customers)
            self.chat_combo.addItem(display_name, group.id)
        
        chat_layout.addWidget(self.chat_combo, 1)
        layout.addLayout(chat_layout)
        
        # Message input
        msg_label = QLabel("Message:")
        msg_label.setStyleSheet(f"font-weight: 600; color: {self.colors['ON_SURFACE']};")
        layout.addWidget(msg_label)
        
        self.message_input = QTextEdit()
        self.message_input.setPlaceholderText("Type your message here...")
        self.message_input.setMinimumHeight(150)
        self.message_input.setStyleSheet(f"""
            QTextEdit {{
                background-color: {self.colors['SURFACE']};
                border: 2px solid {self.colors['BORDER']};
                border-radius: 12px;
                padding: 12px;
                font-size: 14px;
                color: {self.colors['ON_SURFACE']};
                selection-background-color: {self.colors['PRIMARY']};
            }}
            QTextEdit:focus {{
                border: 2px solid {self.colors['PRIMARY']};
            }}
        """)
        layout.addWidget(self.message_input)
        
        # Character count
        self.char_count_label = QLabel("0 characters")
        self.char_count_label.setStyleSheet(f"color: {self.colors['ON_SURFACE_VARIANT']}; font-size: 12px;")
        self.message_input.textChanged.connect(self.update_char_count)
        layout.addWidget(self.char_count_label)
        
        layout.addSpacing(8)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setMinimumHeight(40)
        cancel_btn.setMinimumWidth(120)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.colors['SURFACE_VARIANT']};
                border: 1px solid {self.colors['BORDER']};
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 600;
                color: {self.colors['ON_SURFACE']};
            }}
            QPushButton:hover {{
                background-color: {self.colors['BORDER']};
            }}
            QPushButton:pressed {{
                background-color: {self.colors['BORDER']};
            }}
        """)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        send_btn = QPushButton("Send Message")
        send_btn.setMinimumHeight(40)
        send_btn.setMinimumWidth(140)
        send_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.colors['PRIMARY']};
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 600;
                color: white;
            }}
            QPushButton:hover {{
                background-color: {self.colors['PRIMARY_DARK']};
            }}
            QPushButton:pressed {{
                background-color: {self.colors['PRIMARY_DARK']};
            }}
        """)
        send_btn.clicked.connect(self.send_message)
        button_layout.addWidget(send_btn)
        
        layout.addLayout(button_layout)
    
    def update_char_count(self):
        """Update character count label"""
        text_len = len(self.message_input.toPlainText())
        self.char_count_label.setText(f"{text_len} characters")
    
    def send_message(self):
        """Send the message"""
        text = self.message_input.toPlainText().strip()
        
        if not text:
            QMessageBox.warning(
                self,
                "Empty Message",
                "Please enter a message before sending.",
                QMessageBox.Ok
            )
            return
        
        if self.chat_combo.currentIndex() >= 0:
            group_id = self.chat_combo.currentData()
            self.message_sent.emit(text, group_id)
            self.accept()
        else:
            QMessageBox.warning(
                self,
                "No Chat Selected",
                "Please select a chat first.",
                QMessageBox.Ok
            )
    
    def apply_theme(self):
        """Apply theme to dialog"""
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {self.colors['SURFACE']};
                color: {self.colors['ON_SURFACE']};
            }}
            QLabel {{
                color: {self.colors['ON_SURFACE']};
            }}
        """)
