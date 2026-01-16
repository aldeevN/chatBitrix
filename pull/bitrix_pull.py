"""
Bitrix Pull client for WebSocket communication using captured authentication
"""

import os
import json
import time
import hashlib
import random
import ssl
import urllib.parse
import threading
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any

try:
    import websocket
    from websocket import WebSocketApp
except ImportError:
    import subprocess
    subprocess.check_call(["pip", "install", "websocket-client"])
    import websocket
    from websocket import WebSocketApp

from PyQt5.QtCore import QThread, pyqtSignal, QTimer

from .pull_constants import (
    REVISION, JSON_RPC_VERSION, JSON_RPC_PING, JSON_RPC_PONG,
    PullStatus, CloseReasons, ConnectionType, SenderType
)

class BitrixPullClient(QThread):
    """Enhanced Bitrix Pull client using captured authentication data"""
    message_received = pyqtSignal(dict)
    connection_status = pyqtSignal(bool, str)
    debug_info = pyqtSignal(str)
    
    def __init__(self, api, user_id: int, site_id: str = "ap", use_api_token: bool = False):
        super().__init__()
        self.api = api
        self.user_id = user_id
        self.site_id = site_id
        self.use_api_token = use_api_token  # Новый параметр
        self.api_token = None
        
        # Load captured authentication data
        self.auth_data = self.load_auth_data()
        self.pull_config = self.auth_data.get('pull_config', {})
        self.cookies = self.auth_data.get('cookies', {})
        
        print(f"Initializing Pull client for user {user_id} with {len(self.cookies)} cookies")
        
        # Connection state
        self.ws = None
        self.running = False
        self.is_authenticated = False
        self.channel_id = None
        self.config = self.pull_config
        
        # Reconnection
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 10
        self.reconnect_timeout = None
        self.restart_timeout = None
        
        # Configuration
        self.revision = REVISION
        self.config_timestamp = int(time.time())
        self.logging_enabled = True
        
        # Timers
        self.ping_timer = None
        self.offline_timer = None
        self.ping_wait_timeout = None
        self.PING_TIMEOUT = 10
        
        # State
        self.status = PullStatus.Offline
        self.connection_type = ConnectionType.WebSocket
        self.unloading = False
        
        # Cache for configuration
        self.server_time = None
        self.server_time_offset = 0
        
        # Message counter for JSON-RPC
        self.rpc_id_counter = 0
        self.rpc_response_awaiters = {}
        
        # User callbacks
        self.get_user_name_callback = None
        self.user_status_callbacks = {}
        
        # Subscribers
        self._subscribers = {}
        
        # Flags
        self.starting = False
        self.is_manual_disconnect = False
        
        # Session data
        self.session = {
            'mid': 0,
            'lastMessageIds': []
        }
    
    def load_auth_data(self):
        """Load authentication data from captured files"""
        try:
            # Try to load from auth_data_full.json first
            if os.path.exists('auth_data_full.json'):
                with open('auth_data_full.json', 'r', encoding='utf-8') as f:
                    auth_data = json.load(f)
                
                # Extract Pull configuration
                local_storage = auth_data.get('local_storage', {})
                
                # Find Pull config key (pattern: bx-pull-{user_id}-{site_id}-bx-pull-config)
                for key in local_storage.keys():
                    if 'bx-pull' in key and 'config' in key:
                        try:
                            pull_config = json.loads(local_storage[key])
                            return {
                                'user_id': self.user_id,
                                'pull_config': pull_config,
                                'cookies': auth_data.get('cookies', {}),
                                'local_storage': local_storage,
                                'session_storage': auth_data.get('session_storage', {})
                            }
                        except json.JSONDecodeError:
                            continue
                
                # If no config found, try to create minimal config
                print("Creating minimal Pull configuration from auth data...")
                
                # Extract important cookies for authentication
                cookies = auth_data.get('cookies', {})
                important_cookies = [
                    f"{k}={v}" for k, v in cookies.items()
                    if 'bitrix' in k.lower() or 'phpsessid' in k.lower()
                ]
                
                # Create minimal config
                server_config = {
                    'websocket': 'ws://ugautodetal.ru/bitrix/subws/',
                    'websocket_secure': 'wss://ugautodetal.ru/bitrix/subws/',
                    'long_polling': 'http://ugautodetal.ru/bitrix/sub/',
                    'long_pooling_secure': 'https://ugautodetal.ru/bitrix/sub/',
                    'publish': 'http://ugautodetal.ru/bitrix/rest/',
                    'publish_secure': 'https://ugautodetal.ru/bitrix/rest/',
                    'hostname': 'www.ugavtopart.ru',
                    'websocket_enabled': True
                }
                
                # Create channel ID
                timestamp = int(time.time())
                random_part = hashlib.md5(f"{self.user_id}{timestamp}{random.random()}".encode()).hexdigest()
                channel_id = f"{random_part}:{hashlib.sha1(f'private{self.user_id}'.encode()).hexdigest()}"
                
                pull_config = {
                    'server': server_config,
                    'channels': {
                        'private': {
                            'id': channel_id,
                            'start': timestamp,
                            'end': timestamp + 43200,  # 12 hours
                            'type': 'private'
                        }
                    },
                    'api': {
                        'revision_web': 19,
                        'revision_mobile': 3
                    }
                }
                
                return {
                    'user_id': self.user_id,
                    'pull_config': pull_config,
                    'cookies': cookies,
                    'local_storage': local_storage,
                    'session_storage': auth_data.get('session_storage', {})
                }
            
            return {}
            
        except Exception as e:
            print(f"Error loading auth data: {e}")
            return {}
    
    def get_or_create_api_token(self):
        """Get or create API token for authentication"""
        try:
            # Сначала пытаемся получить существующий токен
            result = self.api.get_token_api()
            
            if result and not result.get("error"):
                self.api_token = result.get("result", {}).get("token")
                if self.api_token:
                    print(f"✓ Using existing API token")
                    return self.api_token
            
            # Если токена нет, создаем новый
            print("Creating new API token...")
            result = self.api.create_token_api(
                name=f"Python Bitrix Pull Client - {datetime.now().strftime('%Y-%m-%d')}",
                expires_in_days=365
            )
            
            if result and not result.get("error"):
                self.api_token = result.get("result", {}).get("token")
                if self.api_token:
                    print(f"✓ Created new API token")
                    return self.api_token
            
            print("✗ Failed to get or create API token")
            return None
            
        except Exception as e:
            print(f"Error getting API token: {e}")
            return None
    
    def load_config(self):
        """Load configuration"""
        print("Loading configuration...")
        
        # Use captured pull config if available
        if self.pull_config:
            self.config = self.pull_config
            
            # Extract channel IDs
            channels = self.config.get('channels', {})
            if 'private' in channels:
                self.channel_id = channels['private']['id']
            elif 'shared' in channels:
                self.channel_id = channels['shared']['id']
            
            print(f"✓ Using captured Pull configuration")
            if self.channel_id:
                print(f"✓ Channel ID: {self.channel_id[:50]}...")
            
            return True
        
        print("✗ No captured configuration found")
        return False
    
    def log(self, message: str, *args):
        """Log message to console"""
        if self.logging_enabled:
            timestamp = time.strftime("%H:%M:%S")
            print(f"{timestamp} [BitrixPull] {message}", *args)
    
    def start_client(self):
        """Start the Pull client"""
        if self.running:
            return
        
        self.running = True
        self.log("Starting Bitrix Pull client...")
        
        # Load configuration
        if not self.load_config():
            self.log("Failed to load config, will try during connect")
        
        # Get API token if needed
        if self.use_api_token:
            self.api_token = self.get_or_create_api_token()
            if not self.api_token:
                self.log("Failed to get API token, falling back to cookies")
                self.use_api_token = False
        
        # Start connection
        self.connect()
    
    def connect(self):
        """Connect to WebSocket server using captured authentication"""
        if self.ws:
            self.disconnect()
        
        try:
            # Ensure we have config
            if not self.config:
                self.load_config()
            
            # Build WebSocket URL with authentication
            ws_url = self.build_websocket_url()
            if not ws_url:
                self.log("Failed to build WebSocket URL")
                self.schedule_reconnect()
                return
            
            self.log(f"Connecting to: {ws_url[:100]}...")
            
            self.status = PullStatus.Connecting
            self.connection_status.emit(False, "Connecting...")
            
            # Create WebSocket connection
            self.ws = WebSocketApp(
                ws_url,
                on_message=self.on_message,
                on_error=self.on_error,
                on_close=self.on_close,
                on_open=self.on_open,
                header=[
                    "User-Agent: Python-Bitrix-Pull-Client/1.0",
                    f"X-Bitrix-User-Id: {self.user_id}",
                    "Accept-Encoding: gzip, deflate, br"
                ]
            )
            
            # Start WebSocket in background thread
            ws_thread = threading.Thread(target=self.run_websocket, daemon=True)
            ws_thread.start()
            
        except Exception as e:
            self.log(f"Error connecting: {e}")
            self.schedule_reconnect()
    
    def build_websocket_url(self) -> str:
        """Build WebSocket URL with authentication"""
        if not self.config:
            self.config = self.load_config()
        
        # Get WebSocket URL from config
        server_config = self.config.get('server', {})
        websocket_url = server_config.get('websocket_secure', 
                         server_config.get('websocket', 
                         'wss://ugautodetal.ru/bitrix/subws/'))
        
        # Get channel ID
        channels = self.config.get('channels', {})
        if 'private' in channels:
            self.channel_id = channels['private']['id']
        elif 'shared' in channels:
            self.channel_id = channels['shared']['id']
        else:
            # Generate channel ID
            self.channel_id = f"private-{self.user_id}"
        
        # Build query parameters
        params = {
            'CHANNEL_ID': self.channel_id,
            'user_id': str(self.user_id),
            'site_id': self.site_id,
            'hostname': server_config.get('hostname', 'www.ugavtopart.ru'),
            'binaryMode': 'true'
        }
        
        # Добавление аутентификации
        if self.use_api_token and self.api_token:
            # Используем API токен
            params['api_token'] = self.api_token
            self.log("Using API token for WebSocket authentication")
        else:
            # Используем cookies из захваченных данных
            important_cookies = []
            for cookie_name, cookie_value in self.cookies.items():
                # Add important authentication cookies
                if any(keyword in cookie_name.lower() for keyword in 
                      ['bitrix_sm_', 'phpsessid', 'uid', 'login']):
                    important_cookies.append(f"{cookie_name}={cookie_value}")
            
            if important_cookies:
                params['cookies'] = '; '.join(important_cookies)
                self.log(f"Added {len(important_cookies)} authentication cookies to WebSocket request")
        
        # Build URL
        query_string = urllib.parse.urlencode(params)
        final_url = f"{websocket_url}?{query_string}"
        
        # Debug logging
        self.log(f"Built WebSocket URL")
        if self.channel_id:
            self.log(f"Channel ID: {self.channel_id[:50]}...")
        
        return final_url
    
    def run_websocket(self):
        """Run WebSocket connection"""
        try:
            self.ws.run_forever(
                sslopt={"cert_reqs": ssl.CERT_NONE},
                ping_interval=30,
                ping_timeout=10,
                reconnect=5
            )
        except Exception as e:
            self.log(f"WebSocket run error: {e}")
            if self.running:
                self.schedule_reconnect()
    
    def on_open(self, ws):
        """Handle WebSocket open"""
        self.log("WebSocket connection opened")
        
        # Start ping timer
        self.start_ping_timer()
        
        # Update status
        self.status = PullStatus.Online
        self.is_authenticated = True
        self.reconnect_attempts = 0
        self.connection_status.emit(True, "Connected to Bitrix")
        
        # Send debug info
        if self.channel_id:
            self.debug_info.emit(f"Connected with channel ID: {self.channel_id[:50]}...")
        else:
            self.debug_info.emit("Connected to Bitrix")
    
    def start_ping_timer(self):
        """Start ping timer to keep connection alive"""
        if self.ping_timer:
            self.ping_timer.stop()
        
        self.ping_timer = QTimer()
        self.ping_timer.timeout.connect(self.send_ping)
        self.ping_timer.start(25000)  # 25 seconds
    
    def send_ping(self):
        """Send ping to keep connection alive"""
        if self.ws and self.is_authenticated:
            try:
                # Send JSON-RPC ping
                ping_data = {
                    "jsonrpc": JSON_RPC_VERSION,
                    "method": "ping",
                    "params": {},
                    "id": self.get_next_rpc_id()
                }
                self.ws.send(json.dumps(ping_data))
                self.log("Sent ping")
            except Exception as e:
                self.log(f"Error sending ping: {e}")
    
    def on_message(self, ws, message):
        """Handle incoming messages"""
        try:
            self.log(f"Received message, length: {len(message)}")
            
            if message == JSON_RPC_PING:
                # Handle ping
                self.ws.send(JSON_RPC_PONG)
                self.update_ping_wait_timeout()
                return
            
            # Try to parse as JSON
            try:
                data = json.loads(message)
                self.handle_jsonrpc_message(data)
            except json.JSONDecodeError:
                # Might be binary/protobuf data
                self.handle_binary_message(message)
                
        except Exception as e:
            self.log(f"Error processing message: {e}")
    
    def handle_binary_message(self, message):
        """Handle binary/protobuf message"""
        try:
            # Try to decode as UTF-8 text
            text = message.decode('utf-8', errors='ignore')
            if text.startswith('{') or text.startswith('['):
                # Actually JSON
                try:
                    self.handle_jsonrpc_message(json.loads(text))
                except:
                    self.log(f"Failed to parse JSON from binary: {text[:100]}")
            else:
                self.log(f"Binary message (first 100 bytes): {message[:100].hex()}")
        except:
            self.log(f"Raw binary message (length: {len(message)})")
    
    def handle_jsonrpc_message(self, data):
        """Handle JSON-RPC message"""
        try:
            method = data.get('method')
            params = data.get('params', {})
            message_id = data.get('id')
            
            if method == 'message':
                self.handle_incoming_message(params)
            elif method == 'ping':
                # Respond to ping
                if self.ws:
                    pong_response = {
                        "jsonrpc": JSON_RPC_VERSION,
                        "result": "pong",
                        "id": message_id
                    }
                    self.ws.send(json.dumps(pong_response))
            elif method == 'result':
                # Handle result response
                if message_id in self.rpc_response_awaiters:
                    callback = self.rpc_response_awaiters.pop(message_id, None)
                    if callback:
                        try:
                            callback(data.get('result'))
                        except:
                            pass
            else:
                self.log(f"Unknown JSON-RPC method: {method}")
                # Emit generic message
                self.message_received.emit({
                    'type': 'jsonrpc',
                    'data': data
                })
                
        except Exception as e:
            self.log(f"Error handling JSON-RPC message: {e}")
    
    def handle_incoming_message(self, params):
        """Handle incoming message notification"""
        try:
            message_id = params.get('mid')
            body = params.get('body', {})
            
            # Update session
            if message_id:
                self.session['mid'] = message_id
            
            # Check for duplicates
            if message_id and message_id in self.session['lastMessageIds']:
                self.log(f"Duplicate message {message_id} skipped")
                return
            
            # Add to last message IDs
            if message_id:
                self.session['lastMessageIds'].append(message_id)
                # Keep only last MAX_IDS_TO_STORE
                if len(self.session['lastMessageIds']) > 10:
                    self.session['lastMessageIds'] = self.session['lastMessageIds'][-10:]
            
            # Extract message data
            module_id = body.get('module_id', '').lower()
            command = body.get('command', '')
            message_params = body.get('params', {})
            extra = body.get('extra', {})
            
            # Add sender info
            sender = params.get('sender', {})
            if sender:
                extra['sender'] = sender
            
            # Handle different module types
            if module_id == 'pull':
                self.handle_pull_event(command, message_params, extra)
            elif module_id == 'online':
                self.handle_online_event(command, message_params, extra)
            elif module_id == 'im':
                self.handle_im_event(command, message_params, extra)
            elif module_id == 'uad.shop.chat':
                self.handle_uad_shop_chat_event(command, message_params, extra)
            else:
                # Generic module
                self.handle_generic_event(module_id, command, message_params, extra)
            
            # Send acknowledgment
            if message_id:
                self.send_acknowledgment(message_id)
                
        except Exception as e:
            self.log(f"Error handling incoming message: {e}")
    
    def send_acknowledgment(self, message_id):
        """Send message acknowledgment"""
        try:
            ack_data = {
                "jsonrpc": JSON_RPC_VERSION,
                "method": "ack",
                "params": {
                    "mid": message_id
                },
                "id": self.get_next_rpc_id()
            }
            self.ws.send(json.dumps(ack_data))
        except Exception as e:
            self.log(f"Error sending acknowledgment: {e}")
    
    def handle_pull_event(self, command, params, extra):
        """Handle pull module events"""
        self.log(f"Pull event: {command}")
        
        if command == 'channel_replaced':
            self.handle_channel_replaced(params)
        elif command == 'config_expired':
            self.handle_config_expired()
        elif command == 'revision_changed':
            self.handle_revision_changed(params)
        elif command == 'connection_status':
            self.handle_connection_status(params)
        
        # Emit to UI
        self.message_received.emit({
            'type': f'pull.{command}',
            'data': {
                'params': params,
                'extra': extra
            }
        })
    
    def handle_online_event(self, command, params, extra):
        """Handle online module events"""
        self.log(f"Online event: {command}")
        
        if command == 'userStatusChange':
            user_id = params.get('user_id')
            is_online = params.get('online', False)
            
            # Call user status callbacks
            if user_id in self.user_status_callbacks:
                for callback in self.user_status_callbacks[user_id]:
                    try:
                        callback({'userId': user_id, 'isOnline': is_online})
                    except:
                        pass
        
        # Emit to UI
        self.message_received.emit({
            'type': f'online.{command}',
            'data': {
                'params': params,
                'extra': extra
            }
        })
    
    def handle_im_event(self, command, params, extra):
        """Handle IM module events"""
        self.log(f"IM event: {command}")
        
        # Emit to UI
        self.message_received.emit({
            'type': f'im.{command}',
            'data': {
                'params': params,
                'extra': extra
            }
        })
    
    def handle_uad_shop_chat_event(self, command, params, extra):
        """Handle uad.shop.chat module events"""
        self.log(f"UAD Shop Chat event: {command}")
        
        # Emit to UI
        self.message_received.emit({
            'type': f'uad.shop.chat.{command}',
            'data': {
                'params': params,
                'extra': extra
            }
        })
    
    def handle_generic_event(self, module_id, command, params, extra):
        """Handle generic module events"""
        self.log(f"Generic event: {module_id}.{command}")
        
        # Emit to UI
        self.message_received.emit({
            'type': f'{module_id}.{command}',
            'data': {
                'params': params,
                'extra': extra
            }
        })
    
    def handle_channel_replaced(self, params):
        """Handle channel replacement"""
        new_channel_id = params.get('channel_id')
        if new_channel_id:
            self.log(f"Channel replaced: {new_channel_id[:50]}...")
            self.channel_id = new_channel_id
            
            # Reconnect with new channel
            self.schedule_reconnect(delay=1)
    
    def handle_config_expired(self):
        """Handle config expiration"""
        self.log("Config expired, reloading...")
        self.load_config()
        self.schedule_reconnect(delay=2)
    
    def handle_revision_changed(self, params):
        """Handle revision change"""
        new_revision = params.get('revision')
        self.log(f"Revision changed: {self.revision} -> {new_revision}")
        self.revision = new_revision
        
        # Show notification
        self.debug_info.emit(f"System updated to revision {new_revision}")
    
    def handle_connection_status(self, params):
        """Handle connection status update"""
        status = params.get('status', 'unknown')
        self.log(f"Connection status: {status}")
        
        if status == 'online':
            self.status = PullStatus.Online
            self.connection_status.emit(True, "Online")
        elif status == 'offline':
            self.status = PullStatus.Offline
            self.connection_status.emit(False, "Offline")
    
    def handle_server_restarted(self):
        """Handle server restart"""
        self.log("Server restarted, reconnecting...")
        self.schedule_reconnect(delay=15)
    
    def handle_user_status_change(self, params):
        """Handle user status change"""
        user_id = params.get('userId')
        is_online = params.get('isOnline', False)
        
        if user_id in self.user_status_callbacks:
            for callback in self.user_status_callbacks[user_id]:
                try:
                    callback(params)
                except Exception as e:
                    self.log(f"Error in user status callback: {e}")
    
    def update_ping_wait_timeout(self):
        """Update ping wait timeout"""
        if self.ping_wait_timeout:
            self.ping_wait_timeout.stop()
        
        self.ping_wait_timeout = QTimer()
        self.ping_wait_timeout.setSingleShot(True)
        self.ping_wait_timeout.timeout.connect(self.on_ping_timeout)
        self.ping_wait_timeout.start(self.PING_TIMEOUT * 2 * 1000)
    
    def on_ping_timeout(self):
        """Handle ping timeout"""
        self.ping_wait_timeout = None
        if not self.running or not self.is_authenticated:
            return
        
        self.log(f"No pings received in {self.PING_TIMEOUT * 2} seconds. Reconnecting")
        self.disconnect(CloseReasons.STUCK, "connection stuck")
        self.schedule_reconnect()
    
    def clear_ping_wait_timeout(self):
        """Clear ping wait timeout"""
        if self.ping_wait_timeout:
            self.ping_wait_timeout.stop()
            self.ping_wait_timeout = None
    
    def on_error(self, ws, error):
        """Handle WebSocket error"""
        self.log(f"WebSocket error: {error}")
        
        # Check for authentication errors
        if "401" in str(error) or "403" in str(error):
            self.log("Authentication error")
            self.debug_info.emit("Authentication failed. Please re-authenticate.")
        
        self.connection_status.emit(False, f"Error: {error}")
    
    def on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket close"""
        self.log(f"WebSocket closed: {close_status_code} - {close_msg}")
        
        self.is_authenticated = False
        
        # Stop timers
        if self.ping_timer:
            self.ping_timer.stop()
            self.ping_timer = None
        
        self.clear_ping_wait_timeout()
        
        # Update status
        self.status = PullStatus.Offline
        self.connection_status.emit(False, "Disconnected")
        
        # Schedule reconnect if not manual disconnect
        if self.running and close_status_code != CloseReasons.NORMAL_CLOSURE and not self.is_manual_disconnect:
            self.schedule_reconnect()
    
    def schedule_reconnect(self, delay: int = None):
        """Schedule reconnection"""
        if not self.running:
            return
        
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            self.log("Max reconnect attempts reached")
            self.debug_info.emit("Max reconnection attempts reached")
            return
        
        if not delay:
            # Exponential backoff
            delay = min(5 * (2 ** self.reconnect_attempts), 60)
        
        self.reconnect_attempts += 1
        self.log(f"Scheduling reconnect in {delay} seconds (attempt {self.reconnect_attempts})")
        
        QTimer.singleShot(delay * 1000, self.reconnect)
    
    def reconnect(self):
        """Reconnect to server"""
        if self.running:
            self.log("Reconnecting...")
            self.connect()
    
    def disconnect(self, code: int = None, reason: str = "Normal closure"):
        """Disconnect WebSocket"""
        if not code:
            code = CloseReasons.NORMAL_CLOSURE
        
        self.is_manual_disconnect = True
        
        if self.ws:
            try:
                self.ws.close(code=code, reason=reason)
            except:
                pass
            self.ws = None
        
        self.is_authenticated = False
        
        # Stop timers
        if self.ping_timer:
            self.ping_timer.stop()
            self.ping_timer = None
        
        if self.reconnect_timeout:
            self.reconnect_timeout = None
        
        self.status = PullStatus.Offline
        self.connection_status.emit(False, "Disconnected")
    
    def send_message(self, chat_id: int, text: str, files: List[Dict] = None, group_info: Dict = None):
        """Send message to chat using JSON-RPC protocol"""
        if not self.ws or not self.is_authenticated:
            return False
        
        try:
            # Get user name using callback if available
            author_name = "Unknown"
            if self.get_user_name_callback:
                author_name = self.get_user_name_callback(self.user_id)
            
            # Create message in JSON-RPC format
            current_time = datetime.now()
            message_data = {
                "jsonrpc": JSON_RPC_VERSION,
                "method": "publish",
                "params": {
                    "channelList": [str(chat_id)],  # Send to specific channel
                    "body": {
                        "module_id": "uad.shop.chat",
                        "command": "newMessage",
                        "params": {
                            "author": author_name,
                            "message": text,
                            "group": group_info or {
                                "id": str(chat_id),
                                "touch": current_time.strftime("%H:%M"),
                                "author_name": author_name,
                                "title": "",
                                "importance": "normal",
                                "isActive": False,
                                "members": [],
                                "managersCount": 0,
                                "customersCount": 0,
                                "meta": {"pinned": "false"},
                                "notifications": 0,
                                "type": "messageGroup",
                                "author": str(self.user_id),
                                "date": current_time.isoformat(),
                                "props": json.dumps({
                                    "touch": current_time.strftime("%d.%m.%y %H:%M:%S"),
                                    "author_name": author_name,
                                    "title": "",
                                    "importance": "normal"
                                }),
                                "state": None,
                                "site": self.site_id
                            }
                        }
                    },
                    "extra": {
                        "server_time": current_time.isoformat(),
                        "server_time_unix": time.time(),
                        "server_name": "www.ugavtopart.ru",
                        "revision_web": self.revision,
                        "revision_mobile": 3
                    }
                },
                "id": self.get_next_rpc_id()
            }
            
            # Send message
            self.ws.send(json.dumps(message_data))
            self.log(f"Sent message to chat {chat_id}")
            return True
            
        except Exception as e:
            self.log(f"Error sending message: {e}")
            return False
    
    def send_typing(self, chat_id: int, is_typing: bool = True):
        """Send typing indicator"""
        if not self.ws or not self.is_authenticated:
            return False
        
        try:
            typing_data = {
                "jsonrpc": JSON_RPC_VERSION,
                "method": "publish",
                "params": {
                    "channelList": [str(chat_id)],
                    "body": {
                        "module_id": "im",
                        "command": "typing",
                        "params": {
                            "chat_id": chat_id,
                            "typing": is_typing
                        }
                    }
                },
                "id": self.get_next_rpc_id()
            }
            
            self.ws.send(json.dumps(typing_data))
            return True
            
        except Exception as e:
            self.log(f"Error sending typing: {e}")
            return False
    
    def subscribe_user_status_change(self, user_id: int, callback):
        """Subscribe to user status changes"""
        if not self.ws or not self.is_authenticated:
            return False
        
        try:
            # Store callback
            if user_id not in self.user_status_callbacks:
                self.user_status_callbacks[user_id] = []
            
            if callback not in self.user_status_callbacks[user_id]:
                self.user_status_callbacks[user_id].append(callback)
            
            # Send subscription request
            subscribe_data = {
                "jsonrpc": JSON_RPC_VERSION,
                "method": "subscribeStatusChange",
                "params": {
                    "userId": user_id
                },
                "id": self.get_next_rpc_id()
            }
            
            self.ws.send(json.dumps(subscribe_data))
            return True
            
        except Exception as e:
            self.log(f"Error subscribing to user status: {e}")
            return False
    
    def unsubscribe_user_status_change(self, user_id: int, callback):
        """Unsubscribe from user status changes"""
        if user_id in self.user_status_callbacks:
            if callback in self.user_status_callbacks[user_id]:
                self.user_status_callbacks[user_id].remove(callback)
            
            # If no more callbacks, send unsubscribe request
            if not self.user_status_callbacks[user_id]:
                try:
                    unsubscribe_data = {
                        "jsonrpc": JSON_RPC_VERSION,
                        "method": "unsubscribeStatusChange",
                        "params": {
                            "userId": user_id
                        },
                        "id": self.get_next_rpc_id()
                    }
                    
                    if self.ws and self.is_authenticated:
                        self.ws.send(json.dumps(unsubscribe_data))
                except Exception as e:
                    self.log(f"Error unsubscribing from user status: {e}")
    
    def get_debug_info(self) -> Dict:
        """Get debug information"""
        return {
            'status': self.status,
            'connected': self.is_authenticated,
            'user_id': self.user_id,
            'channel_id': self.channel_id[:30] + "..." if self.channel_id and len(self.channel_id) > 30 else self.channel_id,
            'site_id': self.site_id,
            'reconnect_attempts': self.reconnect_attempts,
            'revision': self.revision,
            'config_timestamp': self.config_timestamp,
            'connection_type': self.connection_type,
            'rpc_id_counter': self.rpc_id_counter,
            'use_api_token': self.use_api_token,
            'has_api_token': self.api_token is not None
        }
    
    def get_next_rpc_id(self):
        """Get next RPC ID"""
        self.rpc_id_counter += 1
        return self.rpc_id_counter
    
    def stop(self):
        """Stop the client"""
        self.running = False
        self.disconnect(CloseReasons.MANUAL, "client stopped")