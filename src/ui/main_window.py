"""
Main window for Telegram-like Bitrix24 Chat
"""

import os
import sys
import json
import time
import traceback
from datetime import datetime
from typing import Dict, List, Optional

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
    QLabel, QPushButton, QTextEdit, QMenu, QMessageBox,
    QFileDialog, QDialog, QStatusBar, QApplication
)
from PyQt5.QtCore import (
    Qt, QTimer, pyqtSignal, pyqtSlot
)
from PyQt5.QtGui import QFont

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.bitrix_api import BitrixAPI
from api.models import User, Customer, Group, Message
from pull.bitrix_pull import BitrixPullClient
from ui.widgets import TelegramButton, TelegramInput, TelegramSearchBar
from ui.chat_list_item import ChatListItem
from ui.message_bubble import MessageBubble
from ui.themes import COLORS

class TelegramChatWindow(QMainWindow):
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
        
        self.setup_window()
        self.setup_ui()
        
        # Start loading data
        QTimer.singleShot(100, self.initialize_data)
    
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
                "Authentication Required",
                "Authentication data not found. Would you like to authenticate now?",
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
        # This lets the UI use websocket settings from .env without requiring bitrix_token.json
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
        self.setWindowTitle("Telegram-like Business Chat (Bitrix Pull)")
        self.setGeometry(100, 100, 1200, 800)
        
        # Set application style
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {COLORS['BACKGROUND_LIGHT']};
                border: none;
            }}
        """)
    
    def setup_ui(self):
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
        
        # Apply Telegram-like spacing
        self.sidebar.setFixedWidth(380)
        
        # Add connection status indicator to status bar
        self.setup_connection_indicator()
    
    def create_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setStyleSheet(f"""
            QWidget#sidebar {{
                background-color: {COLORS['SIDEBAR_BG_LIGHT']};
                border-right: 1px solid {COLORS['BORDER_LIGHT']};
            }}
        """)
        
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = self.create_sidebar_header()
        layout.addWidget(header)
        
        # Search bar
        search_bar = TelegramSearchBar()
        layout.addWidget(search_bar)
        layout.setAlignment(search_bar, Qt.AlignTop)
        
        # Chats list
        self.chats_scroll = QScrollArea()
        self.chats_scroll.setWidgetResizable(True)
        self.chats_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.chats_scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: {COLORS['SIDEBAR_BG_LIGHT']};
            }}
            QScrollBar:vertical {{
                background-color: {COLORS['BACKGROUND_LIGHT']};
                width: 8px;
                border-radius: 4px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {COLORS['BORDER_LIGHT']};
                border-radius: 4px;
                min-height: 30px;
                margin: 2px 2px 2px 2px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: #c0c0c0;
            }}
            QScrollBar::add-line:vertical {{
                border: none;
                background: none;
            }}
            QScrollBar::sub-line:vertical {{
                border: none;
                background: none;
            }}
        """)
        
        self.chats_container = QWidget()
        self.chats_layout = QVBoxLayout(self.chats_container)
        self.chats_layout.setContentsMargins(0, 0, 0, 0)
        self.chats_layout.setSpacing(0)
        self.chats_layout.addStretch()
        
        self.chats_scroll.setWidget(self.chats_container)
        layout.addWidget(self.chats_scroll, 1)
        
        return sidebar
    
    def create_sidebar_header(self) -> QWidget:
        header = QWidget()
        header.setFixedHeight(60)
        header.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['SIDEBAR_BG_LIGHT']};
                border-bottom: 1px solid {COLORS['BORDER_LIGHT']};
            }}
        """)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(16, 8, 16, 8)
        
        # Title
        title_label = QLabel("Business Chat")
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: 20px;
                font-weight: bold;
                color: {COLORS['TELEGRAM_BLUE']};
            }}
        """)
        layout.addWidget(title_label)
        
        layout.addStretch()
        
        # New chat button
        new_chat_btn = TelegramButton("New Chat")
        new_chat_btn.clicked.connect(self.show_new_chat_dialog)
        layout.addWidget(new_chat_btn)
        
        # Debug button
        debug_btn = TelegramButton("Debug")
        debug_btn.clicked.connect(self.show_debug_info)
        layout.addWidget(debug_btn)
        
        # Menu button
        menu_btn = QPushButton("☰")
        menu_btn.setFixedSize(40, 40)
        menu_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: 20px;
                font-size: 18px;
                color: {COLORS['TELEGRAM_BLUE']};
            }}
            QPushButton:hover {{
                background-color: rgba(51, 144, 236, 0.1);
            }}
        """)
        menu_btn.clicked.connect(self.show_menu)
        layout.addWidget(menu_btn)
        
        return header
    
    def create_chat_area(self) -> QWidget:
        chat_widget = QWidget()
        chat_widget.setObjectName("chatArea")
        chat_widget.setStyleSheet(f"""
            QWidget#chatArea {{
                background-color: {COLORS['CHAT_BG_LIGHT']};
            }}
        """)
        
        layout = QVBoxLayout(chat_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Chat header
        self.chat_header = self.create_chat_header()
        layout.addWidget(self.chat_header)
        
        # Messages area
        messages_widget = QWidget()
        messages_layout = QVBoxLayout(messages_widget)
        messages_layout.setContentsMargins(0, 0, 0, 0)
        
        self.messages_scroll = QScrollArea()
        self.messages_scroll.setWidgetResizable(True)
        self.messages_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.messages_scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: {COLORS['CHAT_BG_LIGHT']};
            }}
            QScrollBar:vertical {{
                background-color: {COLORS['BACKGROUND_LIGHT']};
                width: 8px;
                border-radius: 4px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {COLORS['BORDER_LIGHT']};
                border-radius: 4px;
                min-height: 30px;
                margin: 2px 2px 2px 2px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: #c0c0c0;
            }}
            QScrollBar::add-line:vertical {{
                border: none;
                background: none;
            }}
            QScrollBar::sub-line:vertical {{
                border: none;
                background: none;
            }}
        """)
        
        self.messages_container = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_container)
        self.messages_layout.setContentsMargins(16, 16, 16, 16)
        self.messages_layout.setSpacing(8)
        self.messages_layout.addStretch()
        
        self.messages_scroll.setWidget(self.messages_container)
        messages_layout.addWidget(self.messages_scroll)
        
        layout.addWidget(messages_widget, 1)
        
        # Input area
        self.input_area = self.create_input_area()
        layout.addWidget(self.input_area)
        
        return chat_widget
    
    def create_chat_header(self) -> QWidget:
        header = QWidget()
        header.setFixedHeight(60)
        header.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['SIDEBAR_BG_LIGHT']};
                border-bottom: 1px solid {COLORS['BORDER_LIGHT']};
            }}
        """)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(16, 8, 16, 8)
        
        # Back button (hidden by default)
        self.back_btn = QPushButton("←")
        self.back_btn.setFixedSize(40, 40)
        self.back_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: 20px;
                font-size: 18px;
                color: {COLORS['TELEGRAM_BLUE']};
            }}
            QPushButton:hover {{
                background-color: rgba(51, 144, 236, 0.1);
            }}
        """)
        self.back_btn.clicked.connect(self.go_back)
        self.back_btn.setVisible(False)
        layout.addWidget(self.back_btn)
        
        # Chat title
        self.chat_title = QLabel("Select a chat")
        self.chat_title.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #000000;
            }
        """)
        layout.addWidget(self.chat_title)
        
        layout.addStretch()
        
        # Action buttons
        self.search_btn = QPushButton("🔍")
        self.search_btn.setFixedSize(40, 40)
        self.search_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: 20px;
                font-size: 18px;
                color: {COLORS['TELEGRAM_BLUE']};
            }}
            QPushButton:hover {{
                background-color: rgba(51, 144, 236, 0.1);
            }}
        """)
        layout.addWidget(self.search_btn)
        
        self.menu_btn = QPushButton("⋮")
        self.menu_btn.setFixedSize(40, 40)
        self.menu_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: 20px;
                font-size: 18px;
                color: {COLORS['TELEGRAM_BLUE']};
            }}
            QPushButton:hover {{
                background-color: rgba(51, 144, 236, 0.1);
            }}
        """)
        self.menu_btn.clicked.connect(self.show_chat_menu)
        layout.addWidget(self.menu_btn)
        
        return header
    
    def create_input_area(self) -> QWidget:
        """Setup message input area"""
        input_widget = QWidget()
        input_widget.setFixedHeight(80)
        input_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['SIDEBAR_BG_LIGHT']};
                border-top: 1px solid {COLORS['BORDER_LIGHT']};
            }}
        """)
        
        layout = QHBoxLayout(input_widget)
        layout.setContentsMargins(16, 12, 16, 12)
        
        # Attachment button
        attach_btn = QPushButton("📎")
        attach_btn.setFixedSize(40, 40)
        attach_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: 20px;
                font-size: 18px;
                color: {COLORS['TEXT_SECONDARY_LIGHT']};
            }}
            QPushButton:hover {{
                background-color: rgba(0, 0, 0, 0.1);
            }}
        """)
        attach_btn.clicked.connect(self.attach_file)
        layout.addWidget(attach_btn)
        
        # Message input
        self.message_input = TelegramInput()
        layout.addWidget(self.message_input, 1)
        
        # Send button
        self.send_btn = QPushButton("➤")
        self.send_btn.setFixedSize(40, 40)
        self.send_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['TELEGRAM_BLUE']};
                border: none;
                border-radius: 20px;
                font-size: 18px;
                color: white;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLORS['TELEGRAM_BLUE_DARK']};
            }}
            QPushButton:disabled {{
                background-color: #b0b0b0;
            }}
        """)
        self.send_btn.clicked.connect(self.send_message)
        layout.addWidget(self.send_btn)
        
        return input_widget
    
    def setup_connection_indicator(self):
        """Add connection status indicator to UI"""
        self.connection_label = QLabel()
        self.connection_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['TEXT_SECONDARY_LIGHT']};
                font-size: 12px;
                padding: 4px 8px;
                border-radius: 10px;
                background-color: rgba(0, 0, 0, 0.05);
            }}
        """)
        self.connection_label.setAlignment(Qt.AlignCenter)
        self.update_connection_status(False, "Disconnected")
    
    def update_connection_status(self, connected: bool, message: str):
        """Update connection status display"""
        if connected:
            self.connection_label.setText(f"● {message}")
            self.connection_label.setStyleSheet("""
                QLabel {
                    color: #4CAF50;
                    font-size: 12px;
                    padding: 4px 8px;
                    border-radius: 10px;
                    background-color: rgba(76, 175, 80, 0.1);
                }
            """)
        else:
            self.connection_label.setText(f"○ {message}")
            self.connection_label.setStyleSheet("""
                QLabel {
                    color: #F44336;
                    font-size: 12px;
                    padding: 4px 8px;
                    border-radius: 10px;
                    background-color: rgba(244, 67, 54, 0.1);
                }
            """)
        
        # Add to status bar if not already added
        status_bar = self.statusBar()
        if self.connection_label not in status_bar.children():
            status_bar.addPermanentWidget(self.connection_label)
    
    def initialize_data(self):
        """Initialize all data including WebSocket"""
        self.load_current_user()
        self.load_customers()
        self.load_managers()
        self.load_groups()
        
        # Initialize Pull client AFTER we have user data
        self.initialize_pull_client()
        
        # Start periodic updates (will be disabled when Pull client connects)
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.periodic_update)
        self.update_timer.start(30000)  # 30 seconds (fallback when no Pull connection)
        print("✓ Periodic update timer started (will be disabled when Pull client connects)")
    
    def initialize_pull_client(self):
        """Initialize Bitrix Pull client with proper authentication"""
        if not self.current_user:
            print("Cannot initialize Pull client: no user data")
            return
        
        print("\n" + "="*60)
        print("Initializing Bitrix Pull Client")
        print("="*60)
        
        try:
            # Create Pull client
            # Prefer site ID from auth_info or environment
            site_id = os.environ.get('BITRIX_SITE_ID') or self.auth_info.get('site_id', 'ap')
            use_api_token = os.environ.get('BITRIX_USE_API_TOKEN', '0') == '1'

            self.pull_client = BitrixPullClient(self.api, self.current_user.id, site_id, use_api_token)

            # If we assembled pull_config/cookies from environment, inject them into the client
            env_pull = self.auth_info.get('pull_config')
            env_cookies = self.auth_info.get('cookies')
            # If nothing was found earlier, attempt to build from environment now
            if not env_pull:
                # Build minimal pull_config from environment keys if available
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
                    print("Built Pull config from environment in initialize_pull_client")
            if not env_cookies:
                # collect cookies from env as fallback
                built_cookies = {}
                for k, v in os.environ.items():
                    if k.startswith('COOKIE_'):
                        built_cookies[k[len('COOKIE_'):]] = v
                    elif k in ('PHPSESSID', 'USER_ID', 'BITRIX_SM_LOGIN', 'BITRIX_SM_UID'):
                        built_cookies[k] = v
                if built_cookies:
                    env_cookies = built_cookies
                    print(f"Built cookies from environment in initialize_pull_client ({len(env_cookies)})")
            if env_pull or env_cookies:
                # Overwrite client's auth_data/pull_config/cookies with env-provided values
                try:
                    if env_pull:
                        self.pull_client.auth_data = self.pull_client.auth_data or {}
                        self.pull_client.auth_data['pull_config'] = env_pull
                        self.pull_client.pull_config = env_pull
                        self.pull_client.config = env_pull
                        print("Injected Pull configuration from environment into Pull client")
                    if env_cookies:
                        self.pull_client.auth_data = self.pull_client.auth_data or {}
                        self.pull_client.auth_data['cookies'] = env_cookies
                        self.pull_client.cookies = env_cookies
                        # Rebuild cookie header
                        try:
                            self.pull_client.cookie_header = self.pull_client.build_cookie_header()
                        except Exception:
                            pass
                        print("Injected cookies from environment into Pull client")
                except Exception as e:
                    print(f"Warning: failed to inject env Pull config into client: {e}")
            
            # Connect signals
            self.pull_client.message_received.connect(self.handle_pull_message)
            self.pull_client.connection_status.connect(self.update_connection_status)
            self.pull_client.debug_info.connect(self.handle_debug_info)
            
            # Set up callback for getting user names
            self.pull_client.get_user_name_callback = self.get_user_name
            
            # Start the client
            print("Starting Pull client...")
            self.pull_client.start_client()
            
            print("✓ Pull client initialized successfully")
            print("="*60 + "\n")
            
        except Exception as e:
            print(f"✗ Error initializing Pull client: {e}")
            import traceback
            traceback.print_exc()
            
            self.statusBar().showMessage(f"Pull client error: {str(e)[:50]}", 5000)
    
    def load_current_user(self):
        print("Loading current user...")
        data = self.api.get_current_profile()
        
        if data and not data.get("error"):
            # The response is a single user object, not in "result" field
            if isinstance(data, dict):
                result = data
            else:
                result = data.get("result", {}) if isinstance(data, dict) else data
            
            self.current_user = User(
                id=int(result.get("ID", 2611)),  # Default from captured data
                name=result.get("NAME", ""),
                last_name=result.get("LAST_NAME", ""),
                email=result.get("EMAIL", ""),
                is_manager=result.get("IS_MANAGER", False) == "true" or result.get("IS_MANAGER", False) == True,
                is_moderator=result.get("IS_MODERATOR", False) == "true" or result.get("IS_MODERATOR", False) == True
            )
            print(f"Current user: {self.current_user.display_name} (ID: {self.current_user.id}, Manager: {self.current_user.is_manager})")
        else:
            print("Using user ID from captured data")
            self.current_user = User(
                id=2611,  # From your captured data
                name="Нургали",
                last_name="Алдеев",
                email="Aldeev@ugautodetal.ru",
                is_manager=True,
                is_moderator=False
            )
    
    def load_customers(self):
        print("Loading customers...")
        data = self.api.get_customers()
        
        if data and not data.get("error"):
            # The response appears to be a list of customers
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
                # Handle both response formats
                name = customer.get("NAME", "")
                last_name = customer.get("LAST_NAME", "")
                
                # If there's a NAME_PRICE field, it might contain the full name
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
            
            print(f"Loaded {len(self.customers)} customers")
            
            # Debug: print first few customers
            for i, cust in enumerate(self.customers[:3]):
                print(f"  Customer {i+1}: {cust.full_name} (ID: {cust.id})")
        else:
            print("Using mock customers")
            self.customers = [
                Customer(id=2611, xml_id="USER_2611", name="Нургали", last_name="Алдеев"),
                Customer(id=836, xml_id="8454575b-0a3e-4e17-9e05-afb24da4a52f", name="АВЭКС-К", last_name=""),
            ]
    
    def load_managers(self):
        print("Loading managers...")
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
            print(f"Loaded {len(self.managers)} managers")
        else:
            print("Using mock managers")
            self.managers = [
                User(id=100, name="Иван", last_name="Иванов", email="ivan@example.com", is_manager=True),
                User(id=101, name="Петр", last_name="Петров", email="petr@example.com", is_manager=True),
            ]
    
    def load_groups(self):
        print("Loading chat groups...")
        data = self.api.get_groups()
        
        if data and not data.get("error"):
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
            
            print(f"Loaded {len(self.groups)} groups")
        else:
            print("Using mock groups")
            self.groups = self.get_mock_groups()
        
        # Sort groups (pinned first, then by date)
        self.groups.sort(key=lambda x: (not x.pinned, x.date or ""), reverse=True)
        self.update_chat_list()
    
    def load_messages(self, group_id: int):
        print(f"Loading messages for group {group_id}...")
        
        if group_id != 0:
            self.api.clear_notifications(group_id)
        
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
                message_text = msg.get("text") or msg.get("TEXT") or msg.get("message") or ""
                sender_id = msg.get("author") or msg.get("sender_id") or msg.get("AUTHOR_ID") or 0
                sender_name = msg.get("author_name") or msg.get("sender_name") or msg.get("AUTHOR_NAME") or ""
                
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
                
                message = Message(
                    id=msg.get("id") or msg.get("ID") or len(self.messages),
                    text=message_text,
                    sender_id=int(sender_id) if sender_id else 0,
                    sender_name=sender_name or "Unknown",
                    timestamp=msg.get("date") or msg.get("DATE") or msg.get("timestamp") or "",
                    files=attachments,
                    is_own=(int(sender_id) == self.current_user.id if sender_id and self.current_user else False)
                )
                self.messages.append(message)
            
            print(f"Loaded {len(self.messages)} messages")
        else:
            print("Using demo messages")
            self.load_demo_messages(group_id)
        
        self.update_messages_display()
    
    def update_chat_list(self):
        """Update chat list with Telegram-style items"""
        # Clear existing items
        while self.chats_layout.count() > 1:
            item = self.chats_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add chat items
        for group in self.groups:
            item = ChatListItem(group, self.current_user, self.customers)
            item.clicked.connect(self.select_chat)
            self.chats_layout.insertWidget(0, item)
    
    def update_messages_display(self):
        """Update messages display with Telegram-style bubbles"""
        # Clear current messages
        while self.messages_layout.count() > 1:
            item = self.messages_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add messages with spacing
        for i, message in enumerate(self.messages):
            bubble = MessageBubble(message, self.is_dark_mode)
            
            # Add spacing between different senders
            if i > 0 and self.messages[i-1].sender_id != message.sender_id:
                spacer = QWidget()
                spacer.setFixedHeight(12)
                self.messages_layout.insertWidget(self.messages_layout.count() - 1, spacer)
            
            # Create a container widget for alignment
            container = QWidget()
            container_layout = QHBoxLayout(container)
            container_layout.setContentsMargins(0, 0, 0, 0)
            
            # Align own messages to right, others to left
            if message.is_own:
                container_layout.addStretch()
                container_layout.addWidget(bubble)
                container_layout.setAlignment(Qt.AlignRight)
            else:
                container_layout.addWidget(bubble)
                container_layout.addStretch()
                container_layout.setAlignment(Qt.AlignLeft)
            
            self.messages_layout.insertWidget(self.messages_layout.count() - 1, container)
        
        # Scroll to bottom
        QTimer.singleShot(100, self.scroll_to_bottom)
    
    def scroll_to_bottom(self):
        scrollbar = self.messages_scroll.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def select_chat(self, group_id: int):
        print(f"Selecting chat: {group_id}")
        for group in self.groups:
            if group.id == group_id:
                self.current_group = group
                self.chat_title.setText(group.display_title(self.current_user, self.customers))
                self.load_messages(group_id)
                self.back_btn.setVisible(True)
                break
    
    def send_message(self):
        text = self.message_input.toPlainText().strip()
        if not text or not self.current_group:
            return
        
        print(f"Sending message to group {self.current_group.id}")
        
        # Try to send via HTTP API first
        try:
            data = self.api.add_message(self.current_group, text)
            
            if data and not data.get("error"):
                # Create new message object
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
                
                # Add to messages list
                self.messages.append(new_msg)
                
                # Update UI
                self.update_messages_display()
                self.message_input.clear()
                
                # Update group info
                self.current_group.last_message = text[:50] + ("..." if len(text) > 50 else "")
                self.current_group.last_message_time = "just now"
                self.update_chat_list()
                
                # Show success message
                self.statusBar().showMessage("✓ Message sent successfully", 3000)
                
                # Try to also send via Pull client if available (for real-time updates)
                if self.pull_client and self.pull_client.is_authenticated:
                    try:
                        # Send via Pull client for real-time propagation
                        if hasattr(self.pull_client, 'ws') and self.pull_client.ws:
                            pull_message = {
                                "jsonrpc": "2.0",
                                "method": "publish",
                                "params": {
                                    "channelList": [str(self.current_group.id)],
                                    "body": {
                                        "module_id": "uad.shop.chat",
                                        "command": "newMessage",
                                        "params": {
                                            "author": self.current_user.display_name,
                                            "message": text,
                                            "timestamp": int(time.time() * 1000)
                                        }
                                    }
                                },
                                "id": self.pull_client.get_next_rpc_id() if hasattr(self.pull_client, 'get_next_rpc_id') else 1
                            }
                            self.pull_client.ws.send(json.dumps(pull_message))
                            print("✓ Message also sent via Pull client")
                    except Exception as pull_error:
                        print(f"Note: Could not send via Pull client: {pull_error}")
                
            else:
                # If API returns error, fall back to demo mode
                error_msg = data.get("error_description", "Unknown error") if isinstance(data, dict) else "Unknown error"
                print(f"API error: {error_msg}")
                self.send_demo_message(text)
                
        except Exception as e:
            print(f"Error sending via HTTP API: {e}")
            self.send_demo_message(text)
    
    def send_demo_message(self, text: str):
        """Send message in demo mode (fallback)"""
        reply = QMessageBox.question(
            self,
            "Demo Mode",
            "Failed to send message via API.\nAdd message locally for demo?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        if reply == QMessageBox.Yes:
            # Create demo message
            new_msg = Message(
                id=len(self.messages) + 1,
                text=text,
                sender_id=self.current_user.id,
                sender_name=self.current_user.display_name,
                timestamp=datetime.now().isoformat(),
                files=[],
                is_own=True
            )
            
            # Add to messages
            self.messages.append(new_msg)
            
            # Update UI
            self.update_messages_display()
            self.message_input.clear()
            
            # Update group info
            self.current_group.last_message = text[:50] + ("..." if len(text) > 50 else "")
            self.current_group.last_message_time = "just now"
            self.update_chat_list()
            
            # Show info message
            self.statusBar().showMessage("Message added locally (demo mode)", 3000)
    
    def attach_file(self):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select files",
            "",
            "All files (*.*);;"
            "Images (*.jpg *.jpeg *.png *.gif *.bmp);;"
            "Documents (*.pdf *.doc *.docx *.xls *.xlsx);;"
            "Archives (*.zip *.rar *.7z)"
        )
        
        for file_path in file_paths:
            print(f"Attaching file: {file_path}")
    
    def go_back(self):
        self.current_group = None
        self.chat_title.setText("Select a chat")
        self.back_btn.setVisible(False)
        
        # Clear messages
        self.messages = []
        self.update_messages_display()
    
    def show_new_chat_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("New Chat")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel("New Chat functionality would go here"))
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec()
    
    def show_debug_info(self):
        """Show debug information about Pull client"""
        if self.pull_client:
            debug_info = self.pull_client.get_debug_info()
            
            debug_text = "Bitrix Pull Client Debug Info:\n\n"
            for key, value in debug_info.items():
                debug_text += f"{key}: {value}\n"
            
            # Add authentication info
            debug_text += f"\nAuthentication:\n"
            debug_text += f"User ID: {self.current_user.id if self.current_user else 'N/A'}\n"
            debug_text += f"Cookies loaded: {len(self.pull_client.cookies)}\n"
            debug_text += f"Pull config: {'Loaded' if self.pull_client.pull_config else 'Not loaded'}\n"
            
            QMessageBox.information(self, "Debug Info", debug_text)
        else:
            QMessageBox.warning(self, "Debug Info", "Pull client not initialized")
    
    def show_menu(self):
        menu = QMenu(self)
        
        menu.addAction("Profile", self.show_profile)
        menu.addAction("Settings", self.show_settings)
        menu.addSeparator()
        menu.addAction("Dark Mode", self.toggle_dark_mode)
        menu.addSeparator()
        menu.addAction("Refresh", self.force_refresh)
        menu.addAction("About", self.show_about)
        
        menu.exec(self.sender().mapToGlobal(self.sender().rect().bottomLeft()))
    
    def show_chat_menu(self):
        if not self.current_group:
            return
        
        menu = QMenu(self)
        
        menu.addAction("Chat Info", self.show_chat_info)
        menu.addAction("Manage Participants", self.manage_participants)
        menu.addSeparator()
        menu.addAction("Clear History", self.clear_chat_history)
        menu.addAction("Delete Chat", self.delete_chat)
        
        menu.exec(self.sender().mapToGlobal(self.sender().rect().bottomLeft()))
    
    def show_profile(self):
        if self.current_user:
            QMessageBox.information(
                self,
                "Profile",
                f"Name: {self.current_user.display_name}\n"
                f"Email: {self.current_user.email}\n"
                f"Role: {'Manager' if self.current_user.is_manager else 'User'}\n"
                f"User ID: {self.current_user.id}"
            )
    
    def show_settings(self):
        QMessageBox.information(self, "Settings", "Settings dialog would open here")
    
    def toggle_dark_mode(self):
        self.is_dark_mode = not self.is_dark_mode
        self.apply_theme()
    
    def apply_theme(self):
        from .themes import apply_theme
        apply_theme(self, self.is_dark_mode)
        self.update_messages_display()
    
    def force_refresh(self):
        print("Forcing refresh...")
        self.load_groups()
        if self.current_group:
            self.load_messages(self.current_group.id)
        QMessageBox.information(self, "Refresh", "Data refreshed successfully")
    
    def show_about(self):
        QMessageBox.about(self, "About", "Telegram-like Business Chat with Bitrix Pull\nVersion 1.0")
    
    def show_chat_info(self):
        if not self.current_group:
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Chat Info")
        dialog.setMinimumWidth(300)
        
        layout = QVBoxLayout(dialog)
        
        layout.addWidget(QLabel(f"Chat ID: {self.current_group.id}"))
        layout.addWidget(QLabel(f"Title: {self.current_group.title or 'No title'}"))
        layout.addWidget(QLabel(f"Participants: {len(self.current_group.participants)}"))
        
        if self.current_group.date:
            layout.addWidget(QLabel(f"Created: {self.current_group.date}"))
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec()
    
    def manage_participants(self):
        QMessageBox.information(self, "Participants", "Manage participants dialog would open here")
    
    def clear_chat_history(self):
        reply = QMessageBox.question(
            self,
            "Clear History",
            "Are you sure you want to clear all messages in this chat?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.messages = []
            self.update_messages_display()
    
    def delete_chat(self):
        reply = QMessageBox.question(
            self,
            "Delete Chat",
            "Are you sure you want to delete this chat?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.go_back()
    
    def periodic_update(self):
        print("Periodic update...")
        self.load_groups()
        if self.current_group:
            self.load_messages(self.current_group.id)
    
    def handle_pull_message(self, message_data: dict):
        """Handle messages from Pull client"""
        message_type = message_data.get('type', '')
        data = message_data.get('data', {})
        
        print(f"Pull message: {message_data}")
        
# Pull message: {'type': 'jsonrpc', 'method': None, 'data': {'id': 179, 'mid': '17515572610000000000000179', 'channel': '-', 'tag': '281', 'time': 'Thu, 22 Jan 2026 07:30:38 GMT', 'text': {'module_id': 'uad.shop.chat', 'command': 'newMessage', 'params': {'author': 'Аким Пономарев', 'message': 'fdsfd', 'group': {'touch': '08:20', 'author_name': 'Нургали Алдеев', 'title': 'something', 'importance': 'normal', 'isActive': False, 'members': [], 'managersCount': 0, 'customersCount': 0, 'target': {'ID': '632', 'XML_ID': '632#Akim#Пономарев Аким ', 'NAME': 'Аким', 'LAST_NAME': 'Пономарев', 'SECOND_NAME': '', 'EMAIL': 'ugautodetal0@mail.ru', 'PERSONAL_PHONE': '+79604968609', 'PERSONAL_MOBILE': '+79604968609', 'PERSONAL_STATE': '', 'PERSONAL_CITY': '', 'PERSONAL_STREET': '', 'PERSONAL_ZIP': ''}, 'meta': {'pinned': 'false'}, 'notifications': 0, 'type': 'messageGroup', 'id': '133', 'author': '2611', 'date': '2025-08-12T08:20:27+03:00', 'props': '{"touch":"22.01.26 10:22:21","author_name":"Нургали Алдеев","title":"something","importance":"normal"}', 'state': None, 'site': 'ap', 'sub_id': '319', 'sub_ctgroup': '133', 'sub_ctmember': '632', 'sub_role': 'target', 'sub_moderator': None, 'sub_date': '2025-08-12T08:20:27+03:00'}}, 'extra': {'server_time': '2026-01-22T10:30:38+03:00', 'server_time_unix': 1769067038.270975, 'server_name': 'www.ugavtopart.ru', 'revision_web': 19, 'revision_mobile': 3}}}}

        if message_type == 'uad.shop.chat.newMessage':
            self.handle_uad_new_message(data.get('params', {}))
        elif message_type == 'im.message':
            self.handle_im_message(data.get('params', {}))
        elif message_type == 'im.typing':
            # Typing indicator disabled
            pass
        elif message_type == 'im.read':
            self.handle_read_receipt(data.get('params', {}))
        elif message_type == 'im.chat_update':
            self.handle_chat_update(data.get('params', {}))
        elif message_type == 'pull.channel_replaced':
            print("Channel replaced, client will reconnect automatically")
        elif message_type == 'pull.config_expired':
            print("Config expired, client will reload")
        elif message_type == 'pull.revision_changed':
            self.handle_revision_changed(data.get('params', {}))
        elif message_type == 'pull.connection_status':
            self.handle_pull_connection_status(data.get('params', {}))
    
    def handle_uad_new_message(self, params: dict):
        """Handle new message from uad.shop.chat module"""
        print('msg from pull' , params)
        try:
            author = params.get('author', '')
            message_text = params.get('message', '')
            group = params.get('group', {})
            group_id = group.get('id')
            author_id = group.get('author')  # Extract sender_id from group.author
            group_date = group.get('date')  # Extract timestamp
            
            print(f"New uad.shop.chat message from {author} (ID: {author_id}) in group {group_id}: {message_text[:50]}...")
            
            # Convert group_id to int if possible
            try:
                group_id_int = int(group_id)
            except:
                group_id_int = 0
            
            # Convert author_id to int if possible
            try:
                author_id_int = int(author_id) if author_id else 0
            except:
                author_id_int = 0
            
            # Parse timestamp
            try:
                timestamp = group_date if group_date else datetime.now().isoformat()
            except:
                timestamp = datetime.now().isoformat()
            
            # Check if this message is for the current chat
            if self.current_group and self.current_group.id == group_id_int:
                # Determine if message is from current user
                is_own_message = author_id_int == self.current_user.id if self.current_user else False
                
                # Create message object
                message = Message(
                    id=len(self.messages) + 1,
                    text=message_text,
                    sender_id=author_id_int,
                    sender_name=author,
                    timestamp=timestamp,
                    files=[],
                    is_own=is_own_message
                )
                
                # Add to messages and update display immediately (no delay)
                self.messages.append(message)
                self.update_messages_display()  # Direct call, no QTimer delay
                self.scroll_to_bottom()
                
                print(f"✓ Message added to current chat (total messages: {len(self.messages)}) - INSTANT UPDATE")
                
                # Update group info
                self.current_group.last_message = message_text[:50] + ("..." if len(message_text) > 50 else "")
                self.current_group.last_message_time = "just now"
            else:
                # Update unread count for this group
                for group_obj in self.groups:
                    if group_obj.id == group_id_int:
                        group_obj.unread_count += 1
                        group_obj.last_message = message_text[:50] + ("..." if len(message_text) > 50 else "")
                        group_obj.last_message_time = "just now"
                        self.update_chat_list()
                        break
                
                # Show notification
                self.show_notification(author, message_text, group_id_int)
                print(f"✓ Message received in background group {group_id_int}, notification shown")
            
            # Update groups list
            QTimer.singleShot(1000, self.load_groups)
            
        except Exception as e:
            print(f"Error handling uad.shop.chat message: {e}")
            import traceback
            traceback.print_exc()
    
    def handle_im_message(self, params: dict):
        """Handle IM message from Pull client"""
        try:
            chat_id = params.get('chat_id')
            sender_id = params.get('sender_id')
            text = params.get('text', '')
            timestamp = params.get('timestamp', datetime.now().isoformat())
            
            print(f"New message in chat {chat_id} from {sender_id}: {text[:50]}...")
            
            # Check if this message is for the current chat
            if self.current_group and self.current_group.id == int(chat_id):
                # Create message object
                message = Message(
                    id=params.get('id') or len(self.messages) + 1,
                    text=text,
                    sender_id=int(sender_id) if sender_id else 0,
                    sender_name=self.get_user_name(sender_id),
                    timestamp=timestamp,
                    files=params.get('files', []),
                    is_own=(int(sender_id) == self.current_user.id if sender_id and self.current_user else False)
                )
                
                # Add to messages and update display
                self.messages.append(message)
                self.update_messages_display()
                self.scroll_to_bottom()
                
                # Update group info
                self.current_group.last_message = text[:50] + ("..." if len(text) > 50 else "")
                self.current_group.last_message_time = "just now"
            else:
                # Update unread count for this group
                for group in self.groups:
                    if group.id == int(chat_id):
                        group.unread_count += 1
                        group.last_message = text[:50] + ("..." if len(text) > 50 else "")
                        group.last_message_time = "just now"
                        self.update_chat_list()
                        break
                
                # Show notification
                sender_name = self.get_user_name(sender_id)
                self.show_notification(sender_name, text, chat_id)
            
            # Update groups list
            QTimer.singleShot(1000, self.load_groups)
            
        except Exception as e:
            print(f"Error handling IM message: {e}")
    
    def handle_pull_connection_status(self, params: dict):
        """Handle connection status updates from Pull client"""
        status = params.get('status', 'unknown')
        print(f"Pull connection status: {status}")
        
        if status == 'online':
            self.update_connection_status(True, "Connected to Bitrix")
            # Disable periodic updates when Pull client is connected (real-time updates)
            if self.update_timer and self.update_timer.isActive():
                self.update_timer.stop()
                print("✓ Periodic update timer DISABLED (Pull client connected for real-time updates)")
        elif status == 'offline':
            self.update_connection_status(False, "Disconnected from Bitrix")
            # Re-enable periodic updates when Pull client disconnects
            if self.update_timer and not self.update_timer.isActive():
                self.update_timer.start(30000)
                print("✓ Periodic update timer RE-ENABLED (Pull client disconnected, using fallback)")
    
    def get_user_name(self, user_id):
        """Get user name by ID"""
        if not user_id:
            return "Unknown"
        
        try:
            user_id_int = int(user_id)
        except:
            return f"User {user_id}"
        
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
        
        return f"User {user_id}"
    
    def handle_read_receipt(self, params: dict):
        """Handle message read receipts"""
        message_id = params.get('message_id')
        
        # Update message read status in UI
        for message in self.messages:
            if message.id == message_id:
                message.read = True
                break
        
        self.update_messages_display()
    
    def handle_chat_update(self, params: dict):
        """Handle chat updates"""
        chat_id = params.get('chat_id')
        
        # Reload groups to get updates
        self.load_groups()
        
        # If this is the current group, reload messages
        if self.current_group and self.current_group.id == chat_id:
            self.load_messages(chat_id)
    
    def handle_revision_changed(self, params: dict):
        """Handle revision changes"""
        revision = params.get('revision')
        print(f"Revision changed to: {revision}")
        # Show notification to user
        self.statusBar().showMessage(f"System updated to revision {revision}", 5000)
    
    def handle_debug_info(self, info: str):
        """Handle debug information"""
        print(f"Debug: {info}")
        self.statusBar().showMessage(info, 5000)
    
    def show_notification(self, sender: str, message: str, group_id: int):
        """Show notification for new messages"""
        try:
            # Find group title
            group_title = f"Chat {group_id}"
            for group in self.groups:
                if group.id == int(group_id):
                    group_title = group.display_title(self.current_user, self.customers)
                    break
            
            # Show notification in status bar
            self.statusBar().showMessage(f"New message from {sender} in {group_title}: {message[:50]}...", 5000)
            
        except Exception as e:
            print(f"Error showing notification: {e}")
    
    def get_mock_groups(self):
        return [
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
                title="Project Discussion",
                participants=[632, 2611, 100],
                participant_names=["Аким Пономарев", "Нургали Алдеев", "Иван Иванов"],
                unread_count=0,
                last_message="Meeting at 3 PM",
                last_message_time="10:15",
                author=100,
                date="2025-07-17T14:00:48+03:00",
                pinned=True,
                type="messageGroup",
                site="ap"
            ),
            Group(
                id=94,
                title="Support Team",
                participants=[632, 2611, 101],
                participant_names=["Аким Пономарев", "Нургали Алдеев", "Петр Петров"],
                unread_count=5,
                last_message="Issue resolved",
                last_message_time="Yesterday",
                author=101,
                date="2025-07-17T14:01:21+03:00",
                pinned=False,
                type="messageGroup",
                site="ap"
            ),
        ]
    
    def load_demo_messages(self, group_id: int):
        other_participant = None
        other_participant_name = ""
        
        if self.current_group and self.current_group.participants:
            for i, pid in enumerate(self.current_group.participants):
                if pid != self.current_user.id:
                    other_participant = pid
                    if i < len(self.current_group.participant_names):
                        other_participant_name = self.current_group.participant_names[i]
                    break
        
        self.messages = [
            Message(
                id=1,
                text="Hello! I have a question about the project timeline.",
                sender_id=other_participant or 2611,
                sender_name=other_participant_name or "Нургали Алдеев",
                timestamp="2024-01-15T10:30:00",
                is_own=False,
                read=True
            ),
            Message(
                id=2,
                text="Hi! Sure, I can help. The project is on track for completion by the end of the month.",
                sender_id=self.current_user.id if self.current_user else 632,
                sender_name=self.current_user.display_name if self.current_user else "Аким Пономарев",
                timestamp="2024-01-15T10:32:00",
                is_own=True,
                read=True
            ),
            Message(
                id=3,
                text="Great! Can you send me the latest report?",
                sender_id=other_participant or 2611,
                sender_name=other_participant_name or "Нургали Алдеев",
                timestamp="2024-01-15T10:35:00",
                is_own=False,
                read=True
            ),
            Message(
                id=4,
                text="Of course. I've attached the project report and the updated schedule.",
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
    
    def closeEvent(self, event):
        """Handle application close"""
        # Disconnect Pull client
        if self.pull_client:
            self.pull_client.stop()
        
        # Stop timers
        if hasattr(self, 'update_timer'):
            self.update_timer.stop()
        
        event.accept()