"""
Main window for Telegram-like Bitrix24 Chat
"""

import os
import sys
import json
import time
import traceback
import html
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
    QLabel, QPushButton, QTextEdit, QMenu, QMessageBox,
    QFileDialog, QDialog, QStatusBar, QApplication, QLineEdit,
    QSizePolicy, QFrame, QSpacerItem
)
from PyQt5.QtCore import (
    Qt, QTimer, pyqtSignal, QSize, QPoint, QEvent
)
from PyQt5.QtGui import (
    QFont, QMouseEvent, QColor, QPainter, QPainterPath, 
    QPalette, QBrush, QLinearGradient
)

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.api.bitrix_api import BitrixAPI
from src.api.models import User, Customer, Group, Message
from src.pull.bitrix_pull import BitrixPullClient
from src.ui.widgets import TelegramButton, TelegramInput, TelegramSearchBar, TelegramFrame
from src.ui.chat_list_item import TelegramChatListItem, ChatListItem
from src.ui.message_bubble import TelegramMessageBubble, MessageBubble
from src.ui.new_message_dialog import NewMessageDialog
from src.ui.themes import apply_telegram_theme, get_theme_colors, toggle_dark_mode

class TelegramChatWindow(QMainWindow):
    """Main Telegram-like chat window with Bitrix24 integration"""
    
    # Signals
    connection_status_changed = pyqtSignal(bool, str)
    
    def __init__(self):
        super().__init__()
        
        # Check for authentication data
        self.check_auth_data()
        
        # Load authentication data
        self.auth_info = self.load_auth_data()
        
        # Initialize API with user_id and token
        self.api = BitrixAPI(
            user_id=int(self.auth_info.get('user_id', 1)),
            token=self.auth_info.get('token', ''),
            base_domain="https://ugautodetal.ru"
        )
        
        # Data storage
        self.current_user = None
        self.customers = []
        self.managers = []
        self.groups = []
        self.current_group = None
        self.messages = []
        self.is_dark_mode = False
        
        # Bitrix Pull client
        self.pull_client = None
        
        # UI state
        self.last_sender_id = None
        
        # Setup window
        self.setup_window()
        self.setup_ui()
        
        # Apply Telegram theme
        apply_telegram_theme(self, self.is_dark_mode)
        
        # Start loading data
        QTimer.singleShot(100, self.initialize_data)
        
        # Setup auto-refresh
        self.setup_timers()
    
    def check_auth_data(self):
        """Check if authentication data exists, prompt if not"""
        # Skip auth check if running from launcher with pre-loaded token
        if os.getenv('SKIP_AUTH_CHECK') == '1':
            print("✅ Skipping auth check (token pre-loaded from launcher)")
            return
            
        if not os.path.exists('.env') or not os.path.exists('bitrix_token.json'):
            print("Authentication data not found.")
            reply = QMessageBox.question(
                None,
                "Требуется авторизация",
                "Данные авторизации не найдены. Хотите выполнить авторизацию сейчас?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                print("Starting authentication process...")
                # Import here to avoid circular imports
                from auth.auth_manager import authenticate_and_get_env
                authenticate_and_get_env()
            else:
                print("Proceeding without authentication (limited functionality)")
    
    def load_auth_data(self):
        """Load authentication data from files"""
        print("Loading authentication data...")
        
        auth_data = {
            'user_id': 1,
            'token': None
        }
        
        # Load environment variables from .env
        if os.path.exists('.env'):
            with open('.env', 'r', encoding='utf-8') as f:
                env_lines = f.readlines()
            
            for line in env_lines:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    os.environ[key] = value
                    print(f"  Loaded env: {key}")
                    
                    # Extract API credentials from .env
                    if key == 'API_TOKEN' or key == 'BITRIX_REST_TOKEN':
                        auth_data['token'] = value
                        print(f"    → Token loaded: {value[:30]}...")
                    elif key == 'API_USER_ID' or key == 'BITRIX_USER_ID':
                        try:
                            auth_data['user_id'] = int(value)
                            print(f"    → User ID: {value}")
                        except:
                            pass
        else:
            print("  Warning: .env file not found")
        
        # Load auth data from JSON for reference
        if os.path.exists('bitrix_token.json'):
            try:
                with open('bitrix_token.json', 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                print(f"  Loaded auth data from JSON ({len(json_data)} items)")
                # Merge with auth_data (prefer .env values)
                if not auth_data['token'] and 'tokens' in json_data and 'api_token' in json_data['tokens']:
                    auth_data['token'] = json_data['tokens']['api_token']
                if auth_data['user_id'] == 1 and 'user_id' in json_data:
                    auth_data['user_id'] = json_data['user_id']
            except Exception as e:
                print(f"  Error loading bitrix_token.json: {e}")
        
        print(f"  Final auth_data: user_id={auth_data.get('user_id')}, token={'present' if auth_data.get('token') else 'MISSING'}")
        # Additional fallbacks: check environment variables directly
        if not auth_data.get('token'):
            env_token = os.environ.get('BITRIX_REST_TOKEN') or os.environ.get('API_TOKEN')
            if env_token:
                auth_data['token'] = env_token
                print(f"  → Token obtained from environment variable BITRIX_REST_TOKEN")

        if auth_data.get('user_id') == 1:
            env_user = os.environ.get('BITRIX_USER_ID') or os.environ.get('API_USER_ID')
            if env_user:
                try:
                    auth_data['user_id'] = int(env_user)
                    print(f"  → User ID obtained from environment variable BITRIX_USER_ID: {auth_data['user_id']}")
                except:
                    pass

        # Build Pull/WebSocket config from environment variables as a higher-priority source
        pull_config = {}
        cookies = {}

        # Server/websocket URLs
        ws_url = os.environ.get('PULL_WEBSOCKET_URL') or os.environ.get('PULL_WEBSOCKET')
        if ws_url:
            pull_config.setdefault('server', {})
            pull_config['server']['websocket'] = ws_url
            pull_config['server']['websocket_secure'] = ws_url
            pull_config['server']['hostname'] = os.environ.get('PULL_WEBSOCKET_HOSTNAME') or os.environ.get('BITRIX_HOSTNAME', '')
            pull_config['server']['websocket_enabled'] = True
            print(f"  → Pull websocket URL from env: {ws_url}")

        # Channels (private/shared) as provided in .env
        channels = {}
        private_channel = os.environ.get('PULL_CHANNEL_PRIVATE') or os.environ.get('PULL_CHANNEL')
        shared_channel = os.environ.get('PULL_CHANNEL_SHARED')
        now_ts = int(time.time())
        if private_channel:
            channels['private'] = {
                'id': private_channel,
                'start': now_ts,
                'end': now_ts + 43200,
                'type': 'private'
            }
            print(f"  → Private Pull channel from env: {private_channel[:40]}...")
        if shared_channel:
            channels['shared'] = {
                'id': shared_channel,
                'start': now_ts,
                'end': now_ts + 43200,
                'type': 'shared'
            }
            print(f"  → Shared Pull channel from env: {shared_channel[:40]}...")

        if channels:
            pull_config['channels'] = channels

        # Cookies from .env (keys starting with COOKIE_ or common cookie names)
        for k, v in os.environ.items():
            if k.startswith('COOKIE_'):
                cookie_name = k[len('COOKIE_'):]
                cookies[cookie_name] = v
            elif k in ('PHPSESSID', 'USER_ID', 'BITRIX_SM_LOGIN', 'BITRIX_SM_UID'):
                cookies[k] = v

        if cookies:
            print(f"  → Loaded {len(cookies)} cookies from environment")

        # Attach pull config and cookies into auth_data so the Pull client can use them
        if pull_config:
            auth_data['pull_config'] = pull_config
        if cookies:
            auth_data['cookies'] = cookies

        # Final fallback: try reading bitrix_token.json saved by the auth script
        if not auth_data.get('token') and os.path.exists('bitrix_token.json'):
            try:
                with open('bitrix_token.json', 'r', encoding='utf-8') as f:
                    tdata = json.load(f)
                token_from_file = tdata.get('token')
                user_from_file = tdata.get('user_id')
                if token_from_file:
                    auth_data['token'] = token_from_file
                    print(f"  → Token loaded from bitrix_token.json")
                if auth_data.get('user_id') == 1 and user_from_file:
                    try:
                        auth_data['user_id'] = int(user_from_file)
                        print(f"  → User ID loaded from bitrix_token.json: {auth_data['user_id']}")
                    except:
                        pass
            except Exception as e:
                print(f"  Warning: cannot read bitrix_token.json: {e}")

        print(f"  Final auth_data: user_id={auth_data.get('user_id')}, token={'present' if auth_data.get('token') else 'MISSING'}")
        return auth_data
    
    def setup_window(self):
        """Setup main window properties"""
        self.setWindowTitle("ЮГАВТОДЕТАЛЬ - Telegram Chat")
        self.setGeometry(100, 100, 1200, 800)
        
        # Set minimum size
        self.setMinimumSize(800, 600)
        
        # Set window icon if exists
        icon_path = os.path.join(os.path.dirname(__file__), "icon.png")
        if os.path.exists(icon_path):
            from PyQt5.QtGui import QIcon
            self.setWindowIcon(QIcon(icon_path))
    
    def setup_ui(self):
        """Setup main UI layout"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Sidebar
        self.sidebar = self.create_sidebar()
        main_layout.addWidget(self.sidebar)
        
        # Chat area
        self.chat_area = self.create_chat_area()
        main_layout.addWidget(self.chat_area, 1)
        
        # Set sidebar width
        self.sidebar.setFixedWidth(360)
        
        # Add status bar
        self.setup_status_bar()
    
    def create_sidebar(self) -> QWidget:
        """Create Telegram-style sidebar"""
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header with profile
        header = self.create_sidebar_header()
        layout.addWidget(header)
        
        # Search bar
        search_widget = QWidget()
        search_layout = QHBoxLayout(search_widget)
        search_layout.setContentsMargins(12, 8, 12, 8)
        
        self.search_input = TelegramSearchBar(is_dark=self.is_dark_mode)
        self.search_input.setPlaceholderText("Поиск чатов...")
        self.search_input.textChanged.connect(self.filter_chats)
        search_layout.addWidget(self.search_input)
        
        layout.addWidget(search_widget)
        
        # Chats list
        self.chats_scroll = QScrollArea()
        self.chats_scroll.setWidgetResizable(True)
        self.chats_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.chats_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        self.chats_container = QWidget()
        self.chats_layout = QVBoxLayout(self.chats_container)
        self.chats_layout.setContentsMargins(8, 8, 8, 8)
        self.chats_layout.setSpacing(2)
        self.chats_layout.addStretch()
        
        self.chats_scroll.setWidget(self.chats_container)
        layout.addWidget(self.chats_scroll, 1)
        
        # New chat button at bottom
        new_chat_widget = QWidget()
        new_chat_layout = QHBoxLayout(new_chat_widget)
        new_chat_layout.setContentsMargins(12, 8, 12, 12)
        
        self.new_chat_btn = TelegramButton("✏️ Новый чат", is_dark=self.is_dark_mode)
        self.new_chat_btn.setMinimumHeight(48)
        self.new_chat_btn.clicked.connect(self.show_new_chat_dialog)
        new_chat_layout.addWidget(self.new_chat_btn)
        
        layout.addWidget(new_chat_widget)
        
        return sidebar
    
    def create_sidebar_header(self) -> QWidget:
        """Create sidebar header with user info"""
        header = QWidget()
        header.setFixedHeight(64)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(16, 12, 12, 12)
        layout.setSpacing(12)
        
        # User avatar
        avatar_frame = QFrame()
        avatar_frame.setFixedSize(40, 40)
        avatar_frame.setStyleSheet("""
            QFrame {
                background-color: #3390ec;
                border-radius: 20px;
            }
        """)
        
        avatar_label = QLabel("Ю")
        avatar_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 18px;
                font-weight: bold;
                qproperty-alignment: 'AlignCenter';
            }
        """)
        avatar_layout = QVBoxLayout(avatar_frame)
        avatar_layout.addWidget(avatar_label)
        
        layout.addWidget(avatar_frame)
        
        # User info
        user_info_layout = QVBoxLayout()
        user_info_layout.setSpacing(2)
        
        self.user_name_label = QLabel("Югвдететаль")
        self.user_name_label.setStyleSheet("""
            QLabel {
                font-size: 15px;
                font-weight: 600;
            }
        """)
        user_info_layout.addWidget(self.user_name_label)
        
        self.user_status_label = QLabel("онлайн")
        self.user_status_label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                color: #4CAF50;
            }
        """)
        user_info_layout.addWidget(self.user_status_label)
        
        layout.addLayout(user_info_layout, 1)
        
        # Menu button
        menu_btn = QPushButton("⋯")
        menu_btn.setFixedSize(36, 36)
        menu_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 18px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(0, 0, 0, 0.1);
            }
        """)
        menu_btn.clicked.connect(self.show_main_menu)
        layout.addWidget(menu_btn)
        
        return header
    
    def create_chat_area(self) -> QWidget:
        """Create main chat area"""
        chat_widget = QWidget()
        chat_widget.setObjectName("chatArea")
        
        layout = QVBoxLayout(chat_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Chat header
        self.chat_header = self.create_chat_header()
        layout.addWidget(self.chat_header)
        
        # Messages area
        messages_container = QWidget()
        messages_layout = QVBoxLayout(messages_container)
        messages_layout.setContentsMargins(0, 0, 0, 0)
        
        self.messages_scroll = QScrollArea()
        self.messages_scroll.setWidgetResizable(True)
        self.messages_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.messages_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        self.messages_container = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_container)
        self.messages_layout.setContentsMargins(8, 8, 8, 8)
        self.messages_layout.setSpacing(4)
        self.messages_layout.addStretch()
        
        self.messages_scroll.setWidget(self.messages_container)
        messages_layout.addWidget(self.messages_scroll)
        
        layout.addWidget(messages_container, 1)
        
        # Input area
        self.input_area = self.create_input_area()
        layout.addWidget(self.input_area)
        
        return chat_widget
    
    def create_chat_header(self) -> QWidget:
        """Create chat header with chat info"""
        header = QWidget()
        header.setFixedHeight(64)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)
        
        # Back button (visible only when chat is selected)
        self.back_btn = QPushButton("←")
        self.back_btn.setFixedSize(36, 36)
        self.back_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 18px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(0, 0, 0, 0.1);
            }
        """)
        self.back_btn.clicked.connect(self.go_back)
        self.back_btn.setVisible(False)
        layout.addWidget(self.back_btn)
        
        # Chat info
        chat_info_layout = QVBoxLayout()
        chat_info_layout.setSpacing(2)
        
        self.chat_title_label = QLabel("Выберите чат")
        self.chat_title_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: 600;
            }
        """)
        chat_info_layout.addWidget(self.chat_title_label)
        
        self.chat_status_label = QLabel("")
        self.chat_status_label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                color: #666;
            }
        """)
        chat_info_layout.addWidget(self.chat_status_label)
        
        layout.addLayout(chat_info_layout, 1)
        
        # Action buttons
        self.search_chat_btn = self.create_header_button("🔍", "Поиск в чате")
        layout.addWidget(self.search_chat_btn)
        
        self.chat_menu_btn = self.create_header_button("⋯", "Меню чата")
        self.chat_menu_btn.clicked.connect(self.show_chat_menu)
        layout.addWidget(self.chat_menu_btn)
        
        return header
    
    def create_header_button(self, icon: str, tooltip: str) -> QPushButton:
        """Create header action button"""
        btn = QPushButton(icon)
        btn.setFixedSize(36, 36)
        btn.setToolTip(tooltip)
        btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 18px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: rgba(0, 0, 0, 0.1);
            }
        """)
        return btn
    
    def create_input_area(self) -> QWidget:
        """Create message input area"""
        input_widget = QWidget()
        input_widget.setFixedHeight(72)
        
        layout = QHBoxLayout(input_widget)
        layout.setContentsMargins(16, 8, 16, 16)
        layout.setSpacing(8)
        
        # Attachment button
        self.attach_btn = QPushButton("📎")
        self.attach_btn.setFixedSize(40, 40)
        self.attach_btn.setToolTip("Прикрепить файл")
        self.attach_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 20px;
                font-size: 20px;
            }
            QPushButton:hover {
                background-color: rgba(0, 0, 0, 0.1);
            }
        """)
        self.attach_btn.clicked.connect(self.attach_file)
        layout.addWidget(self.attach_btn)
        
        # Message input
        self.message_input = TelegramInput(is_dark=self.is_dark_mode)
        self.message_input.setPlaceholderText("Введите сообщение...")
        self.message_input.setMinimumHeight(40)
        self.message_input.returnPressed.connect(self.send_message)
        layout.addWidget(self.message_input, 1)
        
        # Send button
        self.send_btn = QPushButton("↑")
        self.send_btn.setFixedSize(40, 40)
        self.send_btn.setToolTip("Отправить сообщение")
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #3390ec;
                border: none;
                border-radius: 20px;
                font-size: 18px;
                font-weight: bold;
                color: white;
            }
            QPushButton:hover {
                background-color: #2b7bc2;
            }
            QPushButton:pressed {
                background-color: #1f5a8e;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.send_btn.clicked.connect(self.send_message)
        layout.addWidget(self.send_btn)
        
        # Initially disable input area
        self.set_input_enabled(False)
        
        return input_widget
    
    def setup_status_bar(self):
        """Setup status bar with connection indicator"""
        status_bar = self.statusBar()
        
        # Connection status label
        self.connection_label = QLabel("○ Подключение...")
        self.connection_label.setStyleSheet("""
            QLabel {
                padding: 2px 8px;
                border-radius: 10px;
                font-size: 11px;
            }
        """)
        status_bar.addPermanentWidget(self.connection_label)
        
        # Version info
        version_label = QLabel("v1.0 • Bitrix24 Chat")
        version_label.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 11px;
                padding-right: 8px;
            }
        """)
        status_bar.addPermanentWidget(version_label)
    
    def setup_timers(self):
        """Setup auto-refresh timers"""
        # Groups refresh timer (every 60 seconds)
        self.groups_timer = QTimer(self)
        self.groups_timer.timeout.connect(self.refresh_groups)
        self.groups_timer.start(60000)
        
        # Messages refresh timer for active chat (every 30 seconds)
        self.messages_timer = QTimer(self)
        self.messages_timer.timeout.connect(self.refresh_current_messages)
        self.messages_timer.start(30000)
    
    def initialize_data(self):
        """Initialize all data"""
        print("Initializing data...")
        
        # Load user data
        self.load_current_user()
        
        # Load other data
        self.load_customers()
        self.load_managers()
        self.load_groups()
        
        # Initialize Pull client
        self.initialize_pull_client()
        
        # Update UI
        self.update_user_info()
    
    def load_current_user(self):
        """Load current user profile"""
        print("Loading current user...")
        
        try:
            data = self.api.get_current_profile()
            
            if data and not data.get("error"):
                # Handle different response formats
                if isinstance(data, dict):
                    result = data
                else:
                    result = data.get("result", {}) if isinstance(data, dict) else data
                
                self.current_user = User(
                    id=int(result.get("ID", self.auth_info.get('user_id', 1))),
                    name=result.get("NAME", ""),
                    last_name=result.get("LAST_NAME", ""),
                    email=result.get("EMAIL", ""),
                    is_manager=result.get("IS_MANAGER", False) == "true" or result.get("IS_MANAGER", False) == True,
                    is_moderator=result.get("IS_MODERATOR", False) == "true" or result.get("IS_MODERATOR", False) == True
                )
                print(f"✓ Current user: {self.current_user.display_name} (ID: {self.current_user.id})")
            else:
                # Create default user
                self.current_user = User(
                    id=self.auth_info.get('user_id', 1),
                    name="Пользователь",
                    last_name="",
                    email="",
                    is_manager=False,
                    is_moderator=False
                )
                print("⚠ Using default user")
                
        except Exception as e:
            print(f"✗ Error loading user: {e}")
            traceback.print_exc()
            
            # Create fallback user
            self.current_user = User(
                id=self.auth_info.get('user_id', 1),
                name="Пользователь",
                last_name="",
                email="",
                is_manager=False,
                is_moderator=False
            )
    
    def load_customers(self):
        """Load customers list"""
        print("Loading customers...")
        
        try:
            data = self.api.get_customers()
            
            if data and not data.get("error"):
                # Handle different response formats
                if isinstance(data, list):
                    customers_data = data
                elif isinstance(data, dict) and "result" in data:
                    customers_data = data["result"]
                    if not isinstance(customers_data, list):
                        customers_data = [customers_data]
                else:
                    customers_data = []
                
                self.customers = []
                
                for customer in customers_data:
                    # Extract name
                    name = customer.get("NAME", "")
                    last_name = customer.get("LAST_NAME", "")
                    
                    # Try to get from NAME_PRICE field
                    if not name and not last_name and customer.get("NAME_PRICE"):
                        name_parts = customer.get("NAME_PRICE", "").split(" ", 1)
                        name = name_parts[0] if name_parts else ""
                        last_name = name_parts[1] if len(name_parts) > 1 else ""
                    
                    customer_obj = Customer(
                        id=int(customer.get("ID", 0)),
                        xml_id=customer.get("XML_ID", f"CUSTOMER_{customer.get('ID', '')}"),
                        name=name,
                        last_name=last_name
                    )
                    self.customers.append(customer_obj)
                
                print(f"✓ Loaded {len(self.customers)} customers")
                
                # Show sample
                for i, cust in enumerate(self.customers[:3]):
                    print(f"  {i+1}. {cust.full_name} (ID: {cust.id})")
                    
            else:
                print("⚠ Using mock customers")
                self.load_mock_customers()
                
        except Exception as e:
            print(f"✗ Error loading customers: {e}")
            traceback.print_exc()
            self.load_mock_customers()
    
    def load_mock_customers(self):
        """Load mock customers for testing"""
        self.customers = [
            Customer(id=2611, xml_id="USER_2611", name="Нургали", last_name="Алдеев"),
            Customer(id=836, xml_id="8454575b-0a3e-4e17-9e05-afb24da4a52f", name="АВЭКС-К", last_name=""),
            Customer(id=1001, xml_id="USER_1001", name="Иван", last_name="Иванов"),
            Customer(id=1002, xml_id="USER_1002", name="Петр", last_name="Петров"),
        ]
        print(f"✓ Loaded {len(self.customers)} mock customers")
    
    def load_managers(self):
        """Load managers list"""
        print("Loading managers...")
        
        try:
            data = self.api.list_managers()
            
            if data and not data.get("error"):
                result = data.get("result", [])
                self.managers = []
                
                for manager in result:
                    user = User(
                        id=manager.get("ID"),
                        name=manager.get("NAME", manager.get("FIRST_NAME", "")),
                        last_name=manager.get("LAST_NAME", ""),
                        email=manager.get("EMAIL", ""),
                        is_manager=True
                    )
                    self.managers.append(user)
                print(f"✓ Loaded {len(self.managers)} managers")
            else:
                print("⚠ Using mock managers")
                self.load_mock_managers()
                
        except Exception as e:
            print(f"✗ Error loading managers: {e}")
            traceback.print_exc()
            self.load_mock_managers()
    
    def load_mock_managers(self):
        """Load mock managers for testing"""
        self.managers = [
            User(id=100, name="Алексей", last_name="Сидоров", email="alexey@example.com", is_manager=True),
            User(id=101, name="Мария", last_name="Петрова", email="maria@example.com", is_manager=True),
        ]
        print(f"✓ Loaded {len(self.managers)} mock managers")
    
    def load_groups(self):
        """Load chat groups"""
        print("Loading chat groups...")
        
        try:
            data = self.api.get_groups()
            
            if data and not data.get("error"):
                # Handle different response formats
                if isinstance(data, list):
                    groups_data = data
                elif isinstance(data, dict) and "result" in data:
                    groups_data = data["result"]
                    if not isinstance(groups_data, list):
                        groups_data = [groups_data]
                else:
                    groups_data = []
                
                self.groups = []
                
                for i, chat in enumerate(groups_data):
                    group_id = chat.get("id")
                    if group_id == "0":
                        continue
                        
                    try:
                        group_id_int = int(group_id) if group_id else i
                    except:
                        group_id_int = i
                    
                    # Parse properties
                    props_str = chat.get("props", "{}")
                    try:
                        props = json.loads(props_str)
                        title = props.get("title", "")
                        author_name = props.get("author_name", "")
                        touch = props.get("touch", "")
                    except:
                        props = {}
                        title = ""
                        author_name = ""
                        touch = ""
                    
                    # Parse participants
                    participants = []
                    participant_names = [] 
                    members = chat.get("members", [])
                    
                    if isinstance(members, list):
                        for member in members:
                            ctmember = member.get("ctmember")
                            if ctmember:
                                try:
                                    participant_id = int(ctmember)
                                    participants.append(participant_id)
                                    
                                    member_name = f"{member.get('NAME', '')} {member.get('LAST_NAME', '')}".strip()
                                    if member_name:
                                        participant_names.append(member_name)
                                    else:
                                        participant_names.append(f"User {participant_id}")
                                except:
                                    pass
                    
                    # Parse notifications
                    notifications = chat.get("notifications", 0)
                    try:
                        unread_count = int(notifications) if notifications else 0
                    except:
                        unread_count = 0
                    
                    # Parse metadata
                    meta = chat.get("meta", {})
                    pinned = meta.get("pinned", "false") == "true"
                    
                    group = Group(
                        id=group_id_int,
                        title=title,
                        participants=participants,
                        participant_names=participant_names,
                        unread_count=unread_count,
                        last_message=author_name,
                        last_message_time=touch,
                        author=int(chat.get("author", 0)) if chat.get("author") else None,
                        date=chat.get("date", ""),
                        pinned=pinned,
                        type=chat.get("type", "messageGroup"),
                        site=chat.get("site", "")
                    )
                    self.groups.append(group)
                
                print(f"✓ Loaded {len(self.groups)} groups")
                
            else:
                print("⚠ Using mock groups")
                self.load_mock_groups()
                
        except Exception as e:
            print(f"✗ Error loading groups: {e}")
            traceback.print_exc()
            self.load_mock_groups()
        
        # Sort groups (pinned first, then by date)
        self.groups.sort(key=lambda x: (not x.pinned, x.date or ""), reverse=True)
        self.update_chat_list()
    
    def load_mock_groups(self):
        """Load mock groups for testing"""
        self.groups = [
            Group(
                id=88,
                title="",
                participants=[632, 2611],
                participant_names=["Аким Пономарев", "Нургали Алдеев"],
                unread_count=2,
                last_message="Hello! How are you?",
                last_message_time="16:40",
                author=2611,
                date="2025-07-17T13:35:54+03:00",
                pinned=False,
                type="messageGroup",
                site="ap"
            ),
            Group(
                id=91,
                title="Обсуждение проекта",
                participants=[632, 2611, 100],
                participant_names=["Аким Пономарев", "Нургали Алдеев", "Алексей Сидоров"],
                unread_count=0,
                last_message="Встреча в 15:00",
                last_message_time="10:15",
                author=100,
                date="2025-07-17T14:00:48+03:00",
                pinned=True,
                type="messageGroup",
                site="ap"
            ),
        ]
        print(f"✓ Loaded {len(self.groups)} mock groups")
    
    def load_messages(self, group_id: int):
        """Load messages for a group"""
        print(f"Loading messages for group {group_id}...")
        
        # Clear notifications
        if group_id != 0:
            try:
                self.api.clear_notifications(group_id)
            except:
                pass
        
        # Load messages
        try:
            if group_id == 0:
                data = self.api.get_user_news_content()
            else:
                data = self.api.get_messages(group_id)
            
            self.messages = []
            
            if data and not data.get("error"):
                result = data.get("result", data)
                
                if isinstance(result, dict) and "messages" in result:
                    messages_list = result["messages"]
                elif isinstance(result, dict) and "result" in result:
                    messages_list = result["result"]
                    if not isinstance(messages_list, list):
                        messages_list = [messages_list]
                elif isinstance(result, list):
                    messages_list = result
                else:
                    messages_list = []
                
                for msg in messages_list:
                    message_text = msg.get("message") or ""
                    sender_id = msg.get("author") or 0
                    
                    # Parse props
                    msg_prop = {}
                    try:
                        msg_prop = json.loads(msg.get("props", "{}"))
                    except:
                        pass
                    
                    sender_name = msg_prop.get("author_name") or ""
                    
                    # Parse attachments
                    attachments = []
                    files = msg.get("files") or msg.get("attachments") or []
                    if files and isinstance(files, list):
                        for file in files:
                            attachment = {
                                "id": file.get("id") or file.get("ID") or 0,
                                "name": file.get("name") or file.get("NAME") or "file",
                                "size": file.get("size") or file.get("SIZE") or 0,
                                "url": file.get("url"),
                                "download_link": file.get("downloadLink")
                            }
                            attachments.append(attachment)
                    
                    # Determine if message is from current user
                    is_own = False
                    if self.current_user:
                        try:
                            is_own = int(sender_id) == self.current_user.id
                        except:
                            pass
                    
                    message = Message(
                        id=msg.get("id") or msg.get("ID") or len(self.messages),
                        text=message_text,
                        sender_id=int(sender_id) if sender_id else 0,
                        sender_name=sender_name or "Неизвестно",
                        timestamp=msg.get("date") or msg.get("DATE") or msg.get("timestamp") or "",
                        files=attachments,
                        is_own=is_own
                    )
                    self.messages.append(message)
                
                print(f"✓ Loaded {len(self.messages)} messages")
                
            else:
                print("⚠ Using mock messages")
                self.load_mock_messages(group_id)
                
        except Exception as e:
            print(f"✗ Error loading messages: {e}")
            traceback.print_exc()
            self.load_mock_messages(group_id)
        
        # Update UI
        self.update_messages_display()
        
        # Enable input area
        self.set_input_enabled(True)
    
    def load_mock_messages(self, group_id: int):
        """Load mock messages for testing"""
        self.messages = [
            Message(
                id=1,
                text="Здравствуйте! У меня есть вопрос по поводу сроков проекта.",
                sender_id=2611,
                sender_name="Нургали Алдеев",
                timestamp="2024-01-15T10:30:00",
                is_own=False,
                read=True
            ),
            Message(
                id=2,
                text="Привет! Конечно, я помогу. Проект идет по графику, завершение планируется к концу месяца.",
                sender_id=self.current_user.id if self.current_user else 632,
                sender_name=self.current_user.display_name if self.current_user else "Аким Пономарев",
                timestamp="2024-01-15T10:32:00",
                is_own=True,
                read=True
            ),
            Message(
                id=3,
                text="Отлично! Можете прислать последний отчет?",
                sender_id=2611,
                sender_name="Нургали Алдеев",
                timestamp="2024-01-15T10:35:00",
                is_own=False,
                read=True
            ),
            Message(
                id=4,
                text="Конечно. Я прикрепил отчет по проекту и обновленный график.",
                sender_id=self.current_user.id if self.current_user else 632,
                sender_name=self.current_user.display_name if self.current_user else "Аким Пономарев",
                timestamp="2024-01-15T10:40:00",
                files=[
                    {"name": "project_report.pdf", "size": 2457600},
                    {"name": "schedule.xlsx", "size": 102400}
                ],
                is_own=True,
                read=False
            ),
        ]
        print(f"✓ Loaded {len(self.messages)} mock messages")
    
    def initialize_pull_client(self):
        """Initialize Bitrix Pull client"""
        print("\n" + "="*60)
        print("Initializing Bitrix Pull Client")
        print("="*60)
        
        if not self.current_user:
            print("✗ Cannot initialize Pull client: no user data")
            return
        
        try:
            # Create Pull client
            site_id = os.environ.get('BITRIX_SITE_ID') or self.auth_info.get('site_id', 'ap')
            use_api_token = os.environ.get('BITRIX_USE_API_TOKEN', '0') == '1'
            
            self.pull_client = BitrixPullClient(self.api, self.current_user.id, site_id, use_api_token)
            
            # Inject environment config if available
            env_pull = self.auth_info.get('pull_config')
            env_cookies = self.auth_info.get('cookies')
            
            if not env_pull:
                # Build from environment
                ws_url = os.environ.get('PULL_WEBSOCKET_URL') or os.environ.get('PULL_WEBSOCKET')
                private_channel = os.environ.get('PULL_CHANNEL_PRIVATE') or os.environ.get('PULL_CHANNEL')
                shared_channel = os.environ.get('PULL_CHANNEL_SHARED')
                
                if ws_url or private_channel or shared_channel:
                    built = {}
                    if ws_url:
                        built['server'] = {
                            'websocket': ws_url,
                            'websocket_secure': ws_url,
                            'hostname': os.environ.get('PULL_WEBSOCKET_HOSTNAME') or os.environ.get('BITRIX_HOSTNAME', ''),
                            'websocket_enabled': True
                        }
                    
                    ch = {}
                    now_ts = int(time.time())
                    if private_channel:
                        ch['private'] = {'id': private_channel, 'start': now_ts, 'end': now_ts + 43200, 'type': 'private'}
                    if shared_channel:
                        ch['shared'] = {'id': shared_channel, 'start': now_ts, 'end': now_ts + 43200, 'type': 'shared'}
                    if ch:
                        built['channels'] = ch
                    
                    env_pull = built
            
            if not env_cookies:
                # Collect cookies from env
                built_cookies = {}
                for k, v in os.environ.items():
                    if k.startswith('COOKIE_'):
                        built_cookies[k[len('COOKIE_'):]] = v
                    elif k in ('PHPSESSID', 'USER_ID', 'BITRIX_SM_LOGIN', 'BITRIX_SM_UID'):
                        built_cookies[k] = v
                if built_cookies:
                    env_cookies = built_cookies
            
            # Inject config into client
            if env_pull:
                try:
                    self.pull_client.auth_data = self.pull_client.auth_data or {}
                    self.pull_client.auth_data['pull_config'] = env_pull
                    self.pull_client.pull_config = env_pull
                    self.pull_client.config = env_pull
                    print("✓ Injected Pull configuration from environment")
                except Exception as e:
                    print(f"⚠ Failed to inject Pull config: {e}")
            
            if env_cookies:
                try:
                    self.pull_client.auth_data = self.pull_client.auth_data or {}
                    self.pull_client.auth_data['cookies'] = env_cookies
                    self.pull_client.cookies = env_cookies
                    # Rebuild cookie header
                    try:
                        self.pull_client.cookie_header = self.pull_client.build_cookie_header()
                    except:
                        pass
                    print(f"✓ Injected {len(env_cookies)} cookies from environment")
                except Exception as e:
                    print(f"⚠ Failed to inject cookies: {e}")
            
            # Connect signals
            self.pull_client.message_received.connect(self.handle_pull_message)
            self.pull_client.connection_status.connect(self.handle_pull_connection_status)
            self.pull_client.debug_info.connect(self.handle_debug_info)
            
            # Set up user name callback
            self.pull_client.get_user_name_callback = self.get_user_name
            
            # Start the client
            print("Starting Pull client...")
            self.pull_client.start_client()
            
            print("✓ Pull client initialized successfully")
            print("="*60 + "\n")
            
            # Update connection status
            self.update_connection_status(True, "Подключение к Bitrix...")
            
        except Exception as e:
            print(f"✗ Error initializing Pull client: {e}")
            traceback.print_exc()
            
            self.statusBar().showMessage(f"Ошибка Pull клиента: {str(e)[:50]}", 5000)
            self.update_connection_status(False, "Pull клиент не подключен")
    
    def update_user_info(self):
        """Update user info in UI"""
        if self.current_user:
            self.user_name_label.setText(self.current_user.display_name)
            self.user_status_label.setText("онлайн")
    
    def update_chat_list(self):
        """Update chat list in sidebar"""
        # Clear existing items
        while self.chats_layout.count() > 1:
            item = self.chats_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add chat items
        for group in self.groups:
            # Skip if filtered by search
            if hasattr(self, 'search_filter') and self.search_filter:
                search_lower = self.search_filter.lower()
                title = group.display_title(self.current_user, self.customers).lower()
                if search_lower not in title:
                    continue
            
            item = TelegramChatListItem(group, self.current_user, self.customers, self.is_dark_mode)
            item.clicked.connect(self.select_chat)
            self.chats_layout.insertWidget(0, item)
    
    def update_messages_display(self):
        """Update messages display"""
        # Clear current messages
        while self.messages_layout.count() > 1:
            item = self.messages_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Reset last sender
        self.last_sender_id = None
        
        # Add messages
        for i, message in enumerate(self.messages):
            # Add spacer between messages from different senders
            if self.last_sender_id is not None and self.last_sender_id != message.sender_id:
                spacer = QWidget()
                spacer.setFixedHeight(8)
                spacer.setStyleSheet("background-color: transparent;")
                self.messages_layout.insertWidget(self.messages_layout.count() - 1, spacer)
            
            # Create message bubble
            bubble = TelegramMessageBubble(message, self.is_dark_mode)
            
            # Create container for alignment
            container = QWidget()
            container_layout = QHBoxLayout(container)
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.setSpacing(0)
            
            # Align based on sender
            if message.is_own:
                container_layout.addStretch()
                container_layout.addWidget(bubble)
                container_layout.setStretchFactor(bubble, 0)
            else:
                container_layout.addWidget(bubble)
                container_layout.addStretch()
                container_layout.setStretchFactor(bubble, 0)
            
            self.messages_layout.insertWidget(self.messages_layout.count() - 1, container)
            self.last_sender_id = message.sender_id
        
        # Scroll to bottom
        QTimer.singleShot(50, self.scroll_to_bottom)
    
    def scroll_to_bottom(self):
        """Scroll messages to bottom"""
        scrollbar = self.messages_scroll.verticalScrollBar()
        if scrollbar:
            scrollbar.setValue(scrollbar.maximum())
    
    def select_chat(self, group_id: int):
        """Select a chat"""
        print(f"Selecting chat: {group_id}")
        
        for group in self.groups:
            if group.id == group_id:
                self.current_group = group
                
                # Update chat header
                self.chat_title_label.setText(group.display_title(self.current_user, self.customers))
                
                # Update chat status
                member_count = len(group.participants)
                if member_count > 0:
                    self.chat_status_label.setText(f"{member_count} участников")
                else:
                    self.chat_status_label.setText("Личный чат")
                
                # Show back button
                self.back_btn.setVisible(True)
                
                # Load messages
                self.load_messages(group_id)
                
                # Clear unread count
                group.unread_count = 0
                self.update_chat_list()
                
                break
    
    def send_message(self):
        """Send a message"""
        text = self.message_input.text().strip()
        if not text or not self.current_group:
            return
        
        print(f"Sending message to group {self.current_group.id}")
        
        # Disable input temporarily
        self.set_input_enabled(False)
        
        try:
            # Send via API
            data = self.api.add_message(self.current_group, text)
            
            if data and not data.get("error"):
                # Create message object
                new_msg = Message(
                    id=len(self.messages) + 1,
                    text=text,
                    sender_id=self.current_user.id,
                    sender_name=self.current_user.display_name,
                    timestamp=datetime.now().isoformat(),
                    files=[],
                    is_own=True,
                    read=True
                )
                
                # Add to messages
                self.messages.append(new_msg)
                
                # Update UI
                self.update_messages_display()
                self.message_input.clear()
                
                # Update group info
                self.current_group.last_message = text[:50] + ("..." if len(text) > 50 else "")
                self.current_group.last_message_time = "только что"
                self.update_chat_list()
                
                # Show success
                self.statusBar().showMessage("✓ Сообщение отправлено", 3000)
                
            else:
                error_msg = data.get("error_description", "Неизвестная ошибка") if isinstance(data, dict) else "Неизвестная ошибка"
                print(f"API error: {error_msg}")
                QMessageBox.warning(self, "Ошибка", f"Не удалось отправить сообщение: {error_msg}")
                
        except Exception as e:
            print(f"Error sending message: {e}")
            traceback.print_exc()
            QMessageBox.warning(self, "Ошибка", f"Не удалось отправить сообщение: {str(e)}")
            
        finally:
            # Re-enable input
            self.set_input_enabled(True)
            self.message_input.setFocus()
    
    def attach_file(self):
        """Attach a file"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Выберите файлы",
            "",
            "Все файлы (*.*);;"
            "Изображения (*.jpg *.jpeg *.png *.gif *.bmp);;"
            "Документы (*.pdf *.doc *.docx *.xls *.xlsx);;"
            "Архивы (*.zip *.rar *.7z)"
        )
        
        for file_path in file_paths:
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            
            print(f"Attaching file: {file_name} ({file_size} bytes)")
            
            # TODO: Implement actual file upload
            # For now, just show a notification
            self.statusBar().showMessage(f"Файл '{file_name}' выбран для отправки", 3000)
    
    def go_back(self):
        """Go back to chat list"""
        self.current_group = None
        self.chat_title_label.setText("Выберите чат")
        self.chat_status_label.setText("")
        self.back_btn.setVisible(False)
        
        # Clear messages
        self.messages = []
        self.update_messages_display()
        
        # Disable input
        self.set_input_enabled(False)
    
    def show_new_chat_dialog(self):
        """Show new chat dialog"""
        dialog = NewMessageDialog(
            parent=self,
            groups=self.groups,
            current_user=self.current_user,
            customers=self.customers,
            is_dark=self.is_dark_mode
        )
        
        def on_message_sent(text, group_id):
            # Find and select group
            for group in self.groups:
                if group.id == group_id:
                    self.select_chat(group_id)
                    break
            
            # Send the message
            if self.current_group:
                self.message_input.setText(text)
                self.send_message()
        
        dialog.message_sent.connect(on_message_sent)
        dialog.exec_()
    
    def filter_chats(self, text):
        """Filter chats by search text"""
        self.search_filter = text
        self.update_chat_list()
    
    def set_input_enabled(self, enabled: bool):
        """Enable or disable input area"""
        self.message_input.setEnabled(enabled)
        self.send_btn.setEnabled(enabled)
        self.attach_btn.setEnabled(enabled)
        
        if not enabled:
            self.message_input.setPlaceholderText("Выберите чат...")
        else:
            self.message_input.setPlaceholderText("Введите сообщение...")
            self.message_input.setFocus()
    
    def update_connection_status(self, connected: bool, message: str):
        """Update connection status display"""
        if connected:
            self.connection_label.setText(f"● {message}")
            self.connection_label.setStyleSheet("""
                QLabel {
                    background-color: rgba(76, 175, 80, 0.1);
                    color: #4CAF50;
                }
            """)
        else:
            self.connection_label.setText(f"○ {message}")
            self.connection_label.setStyleSheet("""
                QLabel {
                    background-color: rgba(244, 67, 54, 0.1);
                    color: #F44336;
                }
            """)
    
    def get_user_name(self, user_id):
        """Get user name by ID"""
        if not user_id:
            return "Неизвестно"
        
        try:
            user_id_int = int(user_id)
        except:
            return f"Пользователь {user_id}"
        
        # Check customers
        for customer in self.customers:
            if customer.id == user_id_int:
                return customer.full_name
        
        # Check managers
        for manager in self.managers:
            if manager.id == user_id_int:
                return manager.display_name
        
        # Check current user
        if self.current_user and self.current_user.id == user_id_int:
            return self.current_user.display_name
        
        return f"Пользователь {user_id}"
    
    def handle_pull_message(self, message_data: dict):
        """Handle messages from Pull client"""
        try:
            # Handle uad.shop.chat messages
            if message_data.get('module_id') == 'uad.shop.chat':
                self.handle_uad_new_message(message_data)
            else:
                print(f"Received Pull message: {message_data}")
                
        except Exception as e:
            print(f"Error handling Pull message: {e}")
            traceback.print_exc()
    
    def handle_uad_new_message(self, params: dict):
        """Handle new message from uad.shop.chat module"""
        try:
            msg_data = params.get("data", {}).get("text", {}).get("params", {})
            
            message_text = msg_data.get('message', '')
            group = msg_data.get('group', {})
            author = msg_data.get('author', '')
            group_id = group.get('id')
            author_id = group.get('sub_ctmember') if group.get('sub_ctmember') else group.get('author')
            group_date = msg_data.get('sub_date')
            
            # Convert IDs
            try:
                group_id_int = int(group_id) if group_id else 0
            except:
                group_id_int = 0
            
            try:
                author_id_int = int(author_id) if author_id else 0
            except:
                author_id_int = 0
            
            # Parse timestamp
            try:
                timestamp = group_date if group_date else datetime.now().isoformat()
            except:
                timestamp = datetime.now().isoformat()
            
            # Check if for current chat
            if self.current_group and self.current_group.id == group_id_int:
                is_own = author_id_int == self.current_user.id if self.current_user else False
                
                message = Message(
                    id=len(self.messages) + 1,
                    text=message_text,
                    sender_id=author_id_int,
                    sender_name=author,
                    timestamp=timestamp,
                    files=[],
                    is_own=is_own
                )
                
                self.messages.append(message)
                self.update_messages_display()
                
                print(f"✓ New message in current chat")
                
                # Update group info
                self.current_group.last_message = message_text[:50] + ("..." if len(message_text) > 50 else "")
                self.current_group.last_message_time = "только что"
                self.update_chat_list()
                
            else:
                # Update unread count for other chats
                for group_obj in self.groups:
                    if group_obj.id == group_id_int:
                        group_obj.unread_count += 1
                        group_obj.last_message = message_text[:50] + ("..." if len(message_text) > 50 else "")
                        group_obj.last_message_time = "только что"
                        self.update_chat_list()
                        
                        # Show notification
                        self.show_notification(author, message_text, group_id_int)
                        break
                
                print(f"✓ New message in background chat {group_id_int}")
            
            # Refresh groups list
            QTimer.singleShot(1000, self.refresh_groups)
            
        except Exception as e:
            print(f"Error handling uad.shop.chat message: {e}")
            traceback.print_exc()
    
    def handle_pull_connection_status(self, params: dict):
    # Handle both boolean and dictionary formats
        if isinstance(params, bool):
            # Direct boolean received
            status = 'online' if params else 'offline'
        elif isinstance(params, dict):
            # Dictionary format
            status = params.get('status', 'unknown')
        else:
            # Unknown format, try to convert
            try:
                status = str(params)
                if status.lower() in ['true', 'online', 'connected']:
                    status = 'online'
                elif status.lower() in ['false', 'offline', 'disconnected']:
                    status = 'offline'
                else:
                    status = 'unknown'
            except:
                status = 'unknown'

        print(f"Pull connection status: {status}")

        if status == 'online':
            self.update_connection_status(True, "Подключено к Bitrix")
        elif status == 'offline':
            self.update_connection_status(False, "Отключено от Bitrix")
        else:
            self.update_connection_status(False, f"Статус: {status}")
    
    def handle_debug_info(self, info: str):
        """Handle debug information"""
        print(f"Debug: {info}")
        self.statusBar().showMessage(info, 5000)
    
    def show_notification(self, sender: str, message: str, group_id: int):
        """Show notification for new messages"""
        try:
            # Find group title
            group_title = f"Чат {group_id}"
            for group in self.groups:
                if group.id == int(group_id):
                    group_title = group.display_title(self.current_user, self.customers)
                    break
            
            # Show in status bar
            self.statusBar().showMessage(f"Новое сообщение от {sender} в {group_title}: {message[:50]}...", 5000)
            
        except Exception as e:
            print(f"Error showing notification: {e}")
    
    def refresh_groups(self):
        """Refresh groups list"""
        if not self.search_filter:
            self.load_groups()
    
    def refresh_current_messages(self):
        """Refresh messages for current chat"""
        if self.current_group:
            self.load_messages(self.current_group.id)
    
    def show_main_menu(self):
        """Show main menu"""
        menu = QMenu(self)
        
        menu.addAction("👤 Профиль", self.show_profile)
        menu.addAction("⚙️ Настройки", self.show_settings)
        menu.addSeparator()
        
        theme_action = menu.addAction("🌙 Темная тема" if not self.is_dark_mode else "☀️ Светлая тема")
        theme_action.triggered.connect(self.toggle_theme)
        
        menu.addSeparator()
        menu.addAction("🔄 Обновить", self.force_refresh)
        menu.addAction("ℹ️ О программе", self.show_about)
        menu.addSeparator()
        menu.addAction("🚪 Выход", self.close)
        
        menu.exec_(self.sender().mapToGlobal(self.sender().rect().bottomLeft()))
    
    def show_chat_menu(self):
        """Show chat menu"""
        if not self.current_group:
            return
        
        menu = QMenu(self)
        
        menu.addAction("ℹ️ Информация о чате", self.show_chat_info)
        menu.addAction("👥 Участники", self.manage_participants)
        menu.addSeparator()
        menu.addAction("🗑️ Очистить историю", self.clear_chat_history)
        menu.addAction("❌ Удалить чат", self.delete_chat)
        
        menu.exec_(self.sender().mapToGlobal(self.sender().rect().bottomLeft()))
    
    def show_profile(self):
        """Show profile dialog"""
        if self.current_user:
            QMessageBox.information(
                self,
                "Профиль",
                f"Имя: {self.current_user.display_name}\n"
                f"Email: {self.current_user.email}\n"
                f"Роль: {'Менеджер' if self.current_user.is_manager else 'Пользователь'}\n"
                f"ID: {self.current_user.id}"
            )
    
    def show_settings(self):
        """Show settings dialog"""
        QMessageBox.information(self, "Настройки", "Диалог настроек будет реализован позже")
    
    def toggle_theme(self):
        """Toggle between dark and light theme"""
        self.is_dark_mode = not self.is_dark_mode
        apply_telegram_theme(self, self.is_dark_mode)
        
        # Update chat list and messages
        self.update_chat_list()
        if self.messages:
            self.update_messages_display()
    
    def force_refresh(self):
        """Force refresh all data"""
        print("Force refreshing all data...")
        
        # Show loading indicator
        self.statusBar().showMessage("Обновление данных...", 3000)
        
        # Refresh data
        self.load_groups()
        if self.current_group:
            self.load_messages(self.current_group.id)
        
        # Update status
        self.statusBar().showMessage("Данные обновлены", 3000)
    
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "О программе",
            "ЮГАВТОДЕТАЛЬ - Telegram Chat\n\n"
            "Версия 1.0\n"
            "© 2024 ЮГАВТОДЕТАЛЬ"
        )
    
    def show_chat_info(self):
        """Show chat info dialog"""
        if not self.current_group:
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Информация о чате")
        dialog.setMinimumWidth(300)
        
        layout = QVBoxLayout(dialog)
        
        layout.addWidget(QLabel(f"ID чата: {self.current_group.id}"))
        layout.addWidget(QLabel(f"Название: {self.current_group.title or 'Без названия'}"))
        layout.addWidget(QLabel(f"Участников: {len(self.current_group.participants)}"))
        
        if self.current_group.date:
            try:
                dt = datetime.fromisoformat(self.current_group.date.replace('Z', '+00:00'))
                layout.addWidget(QLabel(f"Создан: {dt.strftime('%d.%m.%Y %H:%M')}"))
            except:
                pass
        
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec_()
    
    def manage_participants(self):
        """Manage chat participants"""
        QMessageBox.information(self, "Участники", "Управление участниками будет реализовано позже")
    
    def clear_chat_history(self):
        """Clear chat history"""
        if not self.current_group:
            return
        
        reply = QMessageBox.question(
            self,
            "Очистить историю",
            "Вы уверены, что хотите очистить историю этого чата?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.messages = []
            self.update_messages_display()
            self.statusBar().showMessage("История чата очищена", 3000)
    
    def delete_chat(self):
        """Delete chat"""
        if not self.current_group:
            return
        
        reply = QMessageBox.question(
            self,
            "Удалить чат",
            "Вы уверены, что хотите удалить этот чат?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.go_back()
            self.statusBar().showMessage("Чат удален", 3000)
    
    def closeEvent(self, event):
        """Handle application close"""
        print("Closing application...")
        
        # Stop timers
        if hasattr(self, 'groups_timer'):
            self.groups_timer.stop()
        if hasattr(self, 'messages_timer'):
            self.messages_timer.stop()
        
        # Stop Pull client
        if self.pull_client:
            print("Stopping Pull client...")
            try:
                self.pull_client.stop()
            except:
                pass
        
        event.accept()


TelegramChatWindow = TelegramChatWindow