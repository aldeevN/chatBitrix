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
import struct
import base64
import urllib3
import certifi

try:
    import websocket
    from websocket import WebSocketApp, WebSocketException
except ImportError:
    import subprocess
    subprocess.check_call(["pip", "install", "websocket-client"])
    import websocket
    from websocket import WebSocketApp, WebSocketException

from PyQt5.QtCore import QThread, pyqtSignal, QTimer

from .pull_constants import (
    REVISION, JSON_RPC_VERSION, JSON_RPC_PING, JSON_RPC_PONG,
    PullStatus, CloseReasons, ConnectionType, SenderType
)


class BitrixPullClient(QThread):
    """Enhanced Bitrix Pull client for binary WebSocket communication"""
    message_received = pyqtSignal(dict)
    connection_status = pyqtSignal(bool, str)
    debug_info = pyqtSignal(str)
    raw_message_received = pyqtSignal(str)  # New: for raw message debugging
    
    def __init__(self, api, user_id: int, site_id: str = "ap", use_api_token: bool = False):
        super().__init__()
        self.api = api
        self.user_id = user_id
        self.site_id = site_id
        self.use_api_token = use_api_token
        
        # Load captured authentication data
        self.auth_data = self.load_auth_data()
        self.pull_config = self.auth_data.get('pull_config', {})
        self.cookies = self.auth_data.get('cookies', {})
        
        print(f"=== Initializing Bitrix Pull client for user {user_id} ===")
        print(f"✓ Site ID: {site_id}")
        print(f"✓ Use API Token: {use_api_token}")
        
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
        
        # Binary communication
        self.binary_mode = True
        self.message_buffer = bytearray()
        
        # Message counter
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
        
        # Cookie header
        self.cookie_header = self.build_cookie_header()
        
        # Statistics
        self.message_count = 0
        self.bytes_received = 0
        self.bytes_sent = 0
        self.connection_start_time = None
        self.last_message_time = None
        
        print(f"=== Pull client initialized ===")
    
    def load_auth_data(self):
        """Load authentication data from captured files"""
        print("\n" + "="*60)
        print("Loading authentication data...")
        print("="*60)
        
        try:
            # Try to load from bitrix_token.json first
            if os.path.exists('bitrix_token.json'):
                with open('bitrix_token.json', 'r', encoding='utf-8') as f:
                    auth_data = json.load(f)
                
                print(f"✓ Loaded bitrix_token.json ({len(auth_data)} items)")
                
                # Extract Pull configuration
                local_storage = auth_data.get('local_storage', {})
                print(f"✓ Local storage items: {len(local_storage)}")
                
                # Find Pull config key
                pull_config_found = False
                for key in local_storage.keys():
                    if 'bx-pull' in key and 'config' in key:
                        try:
                            pull_config = json.loads(local_storage[key])
                            print(f"✓ Found Pull config in key: {key}")
                            print(f"  Pull config keys: {list(pull_config.keys())}")
                            
                            # Debug server config
                            if 'server' in pull_config:
                                server = pull_config['server']
                                print(f"  Server config:")
                                print(f"    WebSocket: {server.get('websocket')}")
                                print(f"    WebSocket Secure: {server.get('websocket_secure')}")
                                print(f"    Hostname: {server.get('hostname')}")
                            
                            # Debug channels
                            if 'channels' in pull_config:
                                channels = pull_config['channels']
                                print(f"  Channels: {list(channels.keys())}")
                                for chan_type, chan_info in channels.items():
                                    if chan_info:
                                        print(f"    {chan_type}: ID={chan_info.get('id', 'N/A')[:30]}...")
                            
                            pull_config_found = True
                            return {
                                'user_id': self.user_id,
                                'pull_config': pull_config,
                                'cookies': auth_data.get('cookies', {}),
                                'local_storage': local_storage,
                                'session_storage': auth_data.get('session_storage', {})
                            }
                        except json.JSONDecodeError as e:
                            print(f"✗ Error parsing Pull config: {e}")
                            continue
                
                if not pull_config_found:
                    print("⚠ No Pull config found in local storage")
                    print("Available keys with 'bx-pull':")
                    for key in local_storage.keys():
                        if 'bx-pull' in key:
                            print(f"  - {key}")
                
                # If no config found, try to create minimal config
                print("\nCreating minimal Pull configuration from auth data...")
                
                # Extract important cookies for authentication
                cookies = auth_data.get('cookies', {})
                print(f"✓ Cookies available: {len(cookies)}")
                print("Important cookies:")
                for cookie_name in cookies.keys():
                    if any(keyword in cookie_name.lower() for keyword in 
                          ['bitrix_', 'phpsessid', 'sid_', 'bx_user_id', 'login_hash']):
                        print(f"  - {cookie_name}")
                
                # Create minimal config
                server_config = {
                    'websocket': 'wss://ugautodetal.ru/bitrix/subws/',
                    'websocket_secure': 'wss://ugautodetal.ru/bitrix/subws/',
                    'long_polling': 'http://ugautodetal.ru/bitrix/sub/',
                    'long_pooling_secure': 'https://ugautodetal.ru/bitrix/sub/',
                    'publish': 'https://ugautodetal.ru/bitrix/rest/',
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
                            'end': timestamp + 43200,
                            'type': 'private'
                        }
                    },
                    'api': {
                        'revision_web': 19,
                        'revision_mobile': 3
                    }
                }
                
                print(f"✓ Created minimal Pull config with channel ID: {channel_id[:30]}...")
                
                return {
                    'user_id': self.user_id,
                    'pull_config': pull_config,
                    'cookies': cookies,
                    'local_storage': local_storage,
                    'session_storage': auth_data.get('session_storage', {})
                }
            else:
                print("✗ bitrix_token.json not found")
            
            return {}
            
        except Exception as e:
            print(f"✗ Error loading auth data: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def build_cookie_header(self):
        """Build Cookie header from captured cookies"""
        print("\n" + "="*60)
        print("Building Cookie header...")
        print("="*60)
        
        cookie_parts = []
        
        for cookie_name, cookie_value in self.cookies.items():
            # Include important Bitrix cookies
            if any(keyword in cookie_name.lower() for keyword in 
                  ['bitrix_', 'phpsessid', 'sid_', 'bx_user_id', 'login_hash']):
                cookie_parts.append(f"{cookie_name}={cookie_value}")
                print(f"✓ Adding cookie: {cookie_name} ({len(str(cookie_value))} chars)")
        
        if cookie_parts:
            header = f"Cookie: {'; '.join(cookie_parts)}"
            print(f"✓ Cookie header length: {len(header)} characters")
            return header
        
        print("⚠ No important cookies found")
        return ""
    
    def get_or_create_api_token(self):
        """Get or create API token for authentication"""
        print("\n" + "="*60)
        print("Getting API token...")
        print("="*60)
        
        try:
            # Try to get existing token
            result = self.api.get_token_api()
            
            if result and not result.get("error"):
                self.api_token = result.get("result", {}).get("token")
                if self.api_token:
                    print(f"✓ Using existing API token (length: {len(self.api_token)})")
                    print(f"Token preview: {self.api_token[:30]}...")
                    return self.api_token
            
            # Create new token
            print("Creating new API token...")
            result = self.api.create_token_api(
                name=f"Python Bitrix Pull Client - {datetime.now().strftime('%Y-%m-%d')}",
                expires_in_days=365
            )
            
            if result and not result.get("error"):
                self.api_token = result.get("result", {}).get("token")
                if self.api_token:
                    print(f"✓ Created new API token (length: {len(self.api_token)})")
                    print(f"Token preview: {self.api_token[:30]}...")
                    return self.api_token
            
            print("✗ Failed to get or create API token")
            return None
            
        except Exception as e:
            print(f"✗ Error getting API token: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def load_config(self):
        """Load configuration"""
        print("\n" + "="*60)
        print("Loading configuration...")
        print("="*60)
        
        # Use captured pull config if available
        if self.pull_config:
            self.config = self.pull_config
            print("✓ Using captured Pull configuration")
            
            # Extract channel IDs
            channels = self.config.get('channels', {})
            if 'private' in channels:
                self.channel_id = channels['private']['id']
                print(f"✓ Using private channel: {self.channel_id[:50]}...")
            elif 'shared' in channels:
                self.channel_id = channels['shared']['id']
                print(f"✓ Using shared channel: {self.channel_id[:50]}...")
            else:
                print("⚠ No channels found in config")
            
            # Print server info
            server_config = self.config.get('server', {})
            print(f"✓ Server config:")
            print(f"  WebSocket Secure: {server_config.get('websocket_secure', 'N/A')}")
            print(f"  WebSocket: {server_config.get('websocket', 'N/A')}")
            print(f"  Hostname: {server_config.get('hostname', 'N/A')}")
            print(f"  WebSocket Enabled: {server_config.get('websocket_enabled', 'N/A')}")
            
            # Print API info
            api_config = self.config.get('api', {})
            print(f"✓ API info:")
            print(f"  Revision Web: {api_config.get('revision_web', 'N/A')}")
            print(f"  Revision Mobile: {api_config.get('revision_mobile', 'N/A')}")
            
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
            print("⚠ Client already running")
            return
        
        self.running = True
        self.log("Starting Bitrix Pull client...")
        
        # Load configuration
        if not self.load_config():
            self.log("Failed to load config")
            return
        
        # Get API token if needed
        if self.use_api_token:
            self.api_token = self.get_or_create_api_token()
            if not self.api_token:
                self.log("Failed to get API token, using cookies only")
                self.use_api_token = False
        
        # Start connection
        self.connect()
    
    def connect(self):
        """Connect to WebSocket server"""
        if self.ws:
            self.disconnect()
        
        try:
            # Ensure we have config
            if not self.config:
                self.log("No config available")
                return
            
            # Build WebSocket URL with authentication
            ws_url = self.build_websocket_url()
            if not ws_url:
                self.log("Failed to build WebSocket URL")
                self.schedule_reconnect()
                return
            
            print("\n" + "="*60)
            print("Connecting to WebSocket...")
            print("="*60)
            print(f"URL: {ws_url[:100]}...")
            
            self.status = PullStatus.Connecting
            self.connection_status.emit(False, "Connecting...")
            
            # Build headers
            headers = [
                "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                f"X-Bitrix-User-Id: {self.user_id}",
                "Accept-Encoding: gzip, deflate, br",
                "Accept-Language: ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
                "Origin: https://ugautodetal.ru",
                "Sec-WebSocket-Protocol: binary",
                "Pragma: no-cache",
                "Cache-Control: no-cache"
            ]
            
            # Add Cookie header if available
            if self.cookie_header:
                headers.append(self.cookie_header)
                print(f"✓ Added Cookie header ({len(self.cookie_header)} chars)")
            
            # Add API token if using
            if self.use_api_token and self.api_token:
                headers.append(f"Authorization: Bearer {self.api_token}")
                print(f"✓ Added Authorization header")
            
            print(f"Headers ({len(headers)}):")
            for header in headers:
                print(f"  {header[:80]}...")
            
            # Create WebSocket connection with disabled Origin check
            self.ws = WebSocketApp(
                ws_url,
                on_message=self.on_message,
                on_error=self.on_error,
                on_close=self.on_close,
                on_open=self.on_open,
                header=headers
            )
            
            # Start WebSocket in background thread
            ws_thread = threading.Thread(
                target=self.run_websocket,
                name=f"BitrixWebSocket-{self.user_id}",
                daemon=True
            )
            ws_thread.start()
            
        except Exception as e:
            self.log(f"Error connecting: {e}")
            import traceback
            traceback.print_exc()
            self.schedule_reconnect()
    
    def build_websocket_url(self) -> str:
        """Build WebSocket URL"""
        if not self.config:
            self.load_config()
            if not self.config:
                return None
        
        # Get WebSocket URL from config
        server_config = self.config.get('server', {})
        
        # Prefer secure WebSocket
        websocket_url = server_config.get('websocket_secure')
        if not websocket_url:
            websocket_url = server_config.get('websocket')
        
        if not websocket_url:
            # Default URL
            websocket_url = "wss://ugautodetal.ru/bitrix/subws/"
        
        print(f"\nBuilding WebSocket URL:")
        print(f"  Base URL: {websocket_url}")
        
        # Ensure channel ID
        if not self.channel_id:
            channels = self.config.get('channels', {})
            if 'private' in channels:
                self.channel_id = channels['private']['id']
                print(f"  Using channel from config: {self.channel_id[:50]}...")
            elif 'shared' in channels:
                self.channel_id = channels['shared']['id']
                print(f"  Using channel from config: {self.channel_id[:50]}...")
            else:
                # Generate channel ID
                timestamp = int(time.time())
                random_part = hashlib.md5(f"{self.user_id}{timestamp}".encode()).hexdigest()
                self.channel_id = f"{random_part}:private{self.user_id}"
                print(f"  Generated channel ID: {self.channel_id[:50]}...")
        
        # Build query parameters
        params = {
            'CHANNEL_ID': self.channel_id,
            'user_id': str(self.user_id),
            'site_id': self.site_id,
            'hostname': server_config.get('hostname', 'www.ugavtopart.ru'),
            'timestamp': str(int(time.time() * 1000)),
            'version': '2',
            'format': 'json',
            'mode': 'pull',
            'binary': 'true' if self.binary_mode else 'false'
        }
        
        print(f"  Query parameters:")
        for key, value in params.items():
            print(f"    {key}: {value}")
        
        # Add authentication parameters
        if self.use_api_token and self.api_token:
            params['auth_token'] = self.api_token
            params['api_token'] = self.api_token
            print(f"  Added API token parameters")
        else:
            # Add session parameters
            params['session_id'] = self.cookies.get('PHPSESSID', '')
            params['bitrix_sid'] = self.cookies.get('BITRIX_SM_LOGIN', '')
            print(f"  Added session parameters")
        
        # Build URL
        query_string = urllib.parse.urlencode(params)
        final_url = f"{websocket_url}?{query_string}"
        
        print(f"  Final URL length: {len(final_url)} characters")
        
        return final_url
    
    def run_websocket(self):
        """Run WebSocket connection"""
        try:
            # Disable SSL verification for development
            sslopt = {
                "cert_reqs": ssl.CERT_NONE,
                "check_hostname": False,
                "ssl_version": ssl.PROTOCOL_TLS
            }
            
            print(f"\n" + "="*60)
            print("Starting WebSocket connection...")
            print(f"SSL Options: {sslopt}")
            print("="*60)
            
            self.connection_start_time = time.time()
            
            # Run WebSocket with proper settings
            self.ws.run_forever(
                sslopt=sslopt,
                ping_interval=30,
                ping_timeout=10,
                reconnect=5,
                skip_utf8_validation=True,
                origin=None  # Disable Origin check
            )
            
        except WebSocketException as e:
            self.log(f"WebSocket exception: {e}")
            if self.running:
                self.schedule_reconnect()
        except Exception as e:
            self.log(f"WebSocket run error: {e}")
            import traceback
            traceback.print_exc()
            if self.running:
                self.schedule_reconnect()
    
    def on_open(self, ws):
        """Handle WebSocket open"""
        print(f"\n" + "="*60)
        print("✓ WebSocket connection established")
        print(f"  Connection time: {time.time() - self.connection_start_time:.2f}s")
        print("="*60)
        
        # Update status
        self.status = PullStatus.Online
        self.is_authenticated = True
        self.reconnect_attempts = 0
        self.connection_status.emit(True, "Connected to Bitrix")
        
        # Send initial subscription
        self.send_initial_subscription()
        
        # Start ping timer
        self.start_ping_timer()
        
        # Debug info
        self.debug_info.emit(f"Connected with channel: {self.channel_id[:30]}...")
        
        print("✓ Connection fully established")
    
    def send_initial_subscription(self):
        """Send initial subscription message"""
        try:
            subscription = {
                "jsonrpc": "2.0",
                "method": "subscribe",
                "params": {
                    "channels": {
                        "private": [self.channel_id],
                        "shared": []
                    },
                    "user_id": self.user_id,
                    "site_id": self.site_id,
                    "timestamp": int(time.time() * 1000)
                },
                "id": self.get_next_rpc_id()
            }
            
            subscription_json = json.dumps(subscription)
            self.ws.send(subscription_json)
            self.bytes_sent += len(subscription_json)
            
            print(f"\n✓ Sent initial subscription")
            print(f"  Subscription ID: {subscription['id']}")
            print(f"  Channel: {self.channel_id[:50]}...")
            print(f"  Message size: {len(subscription_json)} bytes")
            print(f"  Subscription JSON: {subscription_json[:200]}...")
            
        except Exception as e:
            print(f"✗ Error sending subscription: {e}")
            import traceback
            traceback.print_exc()
    
    def start_ping_timer(self):
        """Start ping timer"""
        if self.ping_timer:
            self.ping_timer.stop()
        
        self.ping_timer = QTimer()
        self.ping_timer.timeout.connect(self.send_keepalive)
        self.ping_timer.start(20000)  # 20 seconds
        print(f"✓ Started ping timer (20s interval)")
    
    def send_keepalive(self):
        """Send keepalive message"""
        if self.ws and self.is_authenticated:
            try:
                keepalive = {
                    "jsonrpc": "2.0",
                    "method": "ping",
                    "params": {
                        "timestamp": int(time.time() * 1000)
                    },
                    "id": self.get_next_rpc_id()
                }
                
                keepalive_json = json.dumps(keepalive)
                self.ws.send(keepalive_json)
                self.bytes_sent += len(keepalive_json)
                
                print(f"✓ Sent keepalive (ID: {keepalive['id']})")
                
            except Exception as e:
                print(f"✗ Error sending keepalive: {e}")
    
    def on_message(self, ws, message):
        """Handle incoming messages"""
        try:
            self.message_count += 1
            self.last_message_time = time.time()
            
            # Check message type
            if isinstance(message, bytes):
                # Binary message
                self.bytes_received += len(message)
                self.handle_binary_message(message)
            elif isinstance(message, str):
                # Text message
                self.bytes_received += len(message.encode('utf-8'))
                self.handle_text_message(message)
            else:
                print(f"⚠ Unknown message type: {type(message)}")
                
        except Exception as e:
            print(f"✗ Error processing message: {e}")
            import traceback
            traceback.print_exc()
    
    def handle_binary_message(self, binary_data: bytes):
        """Handle binary message"""
        try:
            print(f"\n" + "="*60)
            print(f"📦 Received binary message #{self.message_count}")
            print("="*60)
            
            # Try to decode as UTF-8
            try:
                text_data = binary_data.decode('utf-8', errors='ignore')
                if text_data.strip():
                    print(f"  Decoded as UTF-8: {len(text_data)} characters")
                    self.process_text_message(text_data)
                else:
                    # Try Base64
                    try:
                        base64_str = base64.b64encode(binary_data[:100]).decode('utf-8')
                        print(f"  Base64 preview: {base64_str}")
                    except:
                        print(f"  Raw binary data")
            except:
                print('recived msg')
                
        except Exception as e:
            print(f"✗ Error handling binary message: {e}")
    
    def handle_text_message(self, text_data: str):
        """Handle text message"""
        print(f"\n" + "="*60)
        print(f"📝 Received text message #{self.message_count}")
        print("="*60)
        print(f"  Size: {len(text_data)} characters")
        
        # Emit raw message for debugging
        self.raw_message_received.emit(f"Text: {text_data[:200]}...")
        
        self.process_text_message(text_data)
    
    def process_text_message(self, text_data: str):
        """Process text message"""
        try:
            # Clean up the message
            text_data = text_data.strip()
            
            if not text_data:
                print("  Empty message, skipping")
                return
            
            print(f"  Content preview: {text_data[:2000]}...")
            
            # Try to parse as JSON
            try:
                data = json.loads(text_data)
                print(f"  ✓ Parsed as JSON")
                self.handle_json_message(data)
            except json.JSONDecodeError as e:
                print(f"  ✗ JSON decode error: {e}")
                
                # Check for special messages
                if text_data == "ping":
                    self.ws.send("pong")
                    self.bytes_sent += 4
                    print("  Responded to ping")
                elif text_data == "pong":
                    print("  Received pong")
                else:
                    # Try to find JSON in the text
                    import re
                    json_match = re.search(r'\{.*\}', text_data)
                    if json_match:
                        try:
                            data = json.loads(json_match.group())
                            print(f"  ✓ Found JSON in text")
                            self.handle_json_message(data)
                        except:
                            print(f"  Non-JSON message: {text_data[:100]}")
                    else:
                        print(f"  Plain text message: {text_data[:100]}")
                        
        except Exception as e:
            print(f"✗ Error processing text message: {e}")
    
    def handle_json_message(self, data):
        """Handle JSON message"""
        try:
            method = data.get('method')
            params = data.get('params', {})
            message_id = data.get('id')
            
            print(f"\n📨 Processing JSON-RPC message")
            print(f"  Method: {method}")
            print(f"  Message ID: {message_id}")
            print(f"  Has params: {'yes' if params else 'no'}")
            
            if method == 'message':
                # Handle actual message
                print(f"  ↳ Handling message notification")
                self.handle_incoming_message(params)
            elif method == 'ping':
                # Respond to ping
                print(f"  ↳ Responding to ping")
                if self.ws:
                    pong_response = {
                        "jsonrpc": "2.0",
                        "result": "pong",
                        "id": message_id
                    }
                    pong_json = json.dumps(pong_response)
                    self.ws.send(pong_json)
                    self.bytes_sent += len(pong_json)
            elif method == 'result':
                # Handle result
                result = data.get('result', {})
                print(f"  ↳ Processing result")
                print(f"  Result: {result}")
            elif method == 'error':
                # Handle error
                error = data.get('error', {})
                print(f"  ↳ Processing error")
                print(f"  Error: {error}")
            else:
                # Unknown method, emit for handling
                print(f"  ↳ Emitting unknown method")
                self.message_received.emit({
                    'type': 'jsonrpc',
                    'method': method,
                    'data': data
                })
                
        except Exception as e:
            print(f"✗ Error handling JSON message: {e}")
    
    def handle_incoming_message(self, params):
        """Handle incoming message"""
        try:
            message_id = params.get('mid')
            body = params.get('body', {})
            extra = params.get('extra', {})
            
            print(f"\n📩 Processing incoming message")
            print(f"  Message ID: {message_id}")
            print(f"  Module: {body.get('module_id', 'unknown')}")
            print(f"  Command: {body.get('command', 'unknown')}")
            print(f"  Extra keys: {list(extra.keys())}")
            
            # Update session
            if message_id:
                self.session['mid'] = message_id
                # Keep track of last messages
                self.session['lastMessageIds'].append(message_id)
                if len(self.session['lastMessageIds']) > 10:
                    self.session['lastMessageIds'] = self.session['lastMessageIds'][-10:]
                print(f"  ↳ Updated session MID: {message_id}")
            
            # Extract message data
            module_id = body.get('module_id', '').lower()
            command = body.get('command', '')
            message_params = body.get('params', {})
            
            print(f"  ↳ Processing {module_id}.{command}")
            
            # Process based on module
            if module_id == 'uad.shop.chat':
                print(f"  ↳ Handling uad.shop.chat message")
                self.handle_uad_shop_chat(command, message_params, extra)
            elif module_id == 'im':
                print(f"  ↳ Handling IM message")
                self.handle_im_event(command, message_params, extra)
            elif module_id == 'online':
                print(f"  ↳ Handling online message")
                self.handle_online_event(command, message_params, extra)
            elif module_id == 'pull':
                print(f"  ↳ Handling pull message")
                self.handle_pull_event(command, message_params, extra)
            else:
                print(f"  ↳ Handling generic message")
                self.handle_generic_event(module_id, command, message_params, extra)
            
            # Send acknowledgment
            if message_id:
                self.send_acknowledgment(message_id)
                
        except Exception as e:
            print(f"✗ Error handling incoming message: {e}")
            import traceback
            traceback.print_exc()
    
    def handle_uad_shop_chat(self, command, params, extra):
        """Handle uad.shop.chat messages"""
        print(f"\n🛒 uad.shop.chat.{command}")
        print(f"  Params keys: {list(params.keys())}")
        print(f"  Extra keys: {list(extra.keys())}")
        
        # Special handling for newMessage
        if command == 'newMessage':
            message = params.get('message', '')
            author = params.get('author', '')
            group = params.get('group', {})
            
            print(f"  ↳ New message from {author}")
            print(f"  Message preview: {message[:100]}...")
            print(f"  Group ID: {group.get('id', 'N/A')}")
            
            # Emit raw data for debugging
            self.raw_message_received.emit(f"uad.shop.chat.{command}: {message[:100]}...")
        
        # Emit to UI
        self.message_received.emit({
            'type': f'uad.shop.chat.{command}',
            'data': {
                'params': params,
                'extra': extra
            }
        })
    
    def handle_im_event(self, command, params, extra):
        """Handle IM events"""
        print(f"\n💬 IM.{command}")
        print(f"  Params keys: {list(params.keys())}")
        
        # Emit to UI
        self.message_received.emit({
            'type': f'im.{command}',
            'data': {
                'params': params,
                'extra': extra
            }
        })
    
    def handle_online_event(self, command, params, extra):
        """Handle online events"""
        print(f"\n🌐 Online.{command}")
        print(f"  Params keys: {list(params.keys())}")
        
        # Emit to UI
        self.message_received.emit({
            'type': f'online.{command}',
            'data': {
                'params': params,
                'extra': extra
            }
        })
    
    def handle_pull_event(self, command, params, extra):
        """Handle pull events"""
        print(f"\n🔄 Pull.{command}")
        print(f"  Params keys: {list(params.keys())}")
        
        if command == 'channel_replaced':
            new_channel = params.get('channel_id')
            if new_channel:
                print(f"  ↳ Channel replaced: {new_channel[:30]}...")
                self.channel_id = new_channel
        
        # Emit to UI
        self.message_received.emit({
            'type': f'pull.{command}',
            'data': {
                'params': params,
                'extra': extra
            }
        })
    
    def handle_generic_event(self, module_id, command, params, extra):
        """Handle generic events"""
        print(f"\n📦 {module_id}.{command}")
        print(f"  Params keys: {list(params.keys())}")
        
        # Emit to UI
        self.message_received.emit({
            'type': f'{module_id}.{command}',
            'data': {
                'params': params,
                'extra': extra
            }
        })
    
    def send_acknowledgment(self, message_id):
        """Send message acknowledgment"""
        try:
            ack = {
                "jsonrpc": "2.0",
                "method": "ack",
                "params": {
                    "mid": message_id
                },
                "id": self.get_next_rpc_id()
            }
            
            ack_json = json.dumps(ack)
            self.ws.send(ack_json)
            self.bytes_sent += len(ack_json)
            
            print(f"  ✓ Sent acknowledgment for message {message_id}")
            
        except Exception as e:
            print(f"  ✗ Error sending acknowledgment: {e}")
    
    def on_error(self, ws, error):
        """Handle WebSocket error"""
        print(f"\n" + "="*60)
        print("✗ WebSocket error")
        print("="*60)
        print(f"Error: {error}")
        
        # Extract details if available
        if hasattr(error, 'status_code'):
            print(f"Status code: {error.status_code}")
        if hasattr(error, 'headers'):
            print(f"Headers: {error.headers}")
        if hasattr(error, 'body'):
            print(f"Body: {error.body}")
        
        # Update status
        self.status = PullStatus.Offline
        error_msg = str(error)[:100]
        self.connection_status.emit(False, f"Error: {error_msg}")
        
        # Try to reconnect if not authentication error
        if "401" not in str(error) and "403" not in str(error):
            self.schedule_reconnect(delay=5)
    
    def on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket close"""
        print(f"\n" + "="*60)
        print("🔌 WebSocket closed")
        print("="*60)
        print(f"Status code: {close_status_code}")
        print(f"Message: {close_msg}")
        print(f"Connection duration: {time.time() - self.connection_start_time:.2f}s")
        print(f"Messages received: {self.message_count}")
        print(f"Bytes received: {self.bytes_received}")
        print(f"Bytes sent: {self.bytes_sent}")
        
        self.is_authenticated = False
        
        # Stop timers
        if self.ping_timer:
            self.ping_timer.stop()
            self.ping_timer = None
        
        # Update status
        self.status = PullStatus.Offline
        self.connection_status.emit(False, "Disconnected")
        
        # Reconnect if not manual disconnect
        if self.running and close_status_code != 1000 and not self.is_manual_disconnect:
            self.schedule_reconnect()
    
    def schedule_reconnect(self, delay: int = None):
        """Schedule reconnection"""
        if not self.running:
            return
        
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            print(f"\n✗ Max reconnect attempts reached ({self.reconnect_attempts})")
            self.debug_info.emit("Max reconnection attempts reached")
            return
        
        if not delay:
            # Exponential backoff
            delay = min(5 * (2 ** self.reconnect_attempts), 60)
        
        self.reconnect_attempts += 1
        print(f"\n⏰ Scheduling reconnect in {delay} seconds (attempt {self.reconnect_attempts})")
        
        QTimer.singleShot(delay * 1000, self.reconnect)
    
    def reconnect(self):
        """Reconnect to server"""
        if self.running:
            print(f"\n🔄 Reconnecting...")
            self.connect()
    
    def disconnect(self, code: int = 1000, reason: str = "Normal closure"):
        """Disconnect WebSocket"""
        print(f"\n" + "="*60)
        print("👋 Manual disconnect")
        print("="*60)
        print(f"Code: {code}")
        print(f"Reason: {reason}")
        
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
        
        self.status = PullStatus.Offline
    
    def send_message(self, chat_id: int, text: str):
        """Send message to chat"""
        if not self.ws or not self.is_authenticated:
            print(f"✗ Cannot send message: WebSocket not connected")
            return False
        
        try:
            message = {
                "jsonrpc": "2.0",
                "method": "publish",
                "params": {
                    "channelList": [str(chat_id)],
                    "body": {
                        "module_id": "uad.shop.chat",
                        "command": "newMessage",
                        "params": {
                            "author": f"User {self.user_id}",
                            "message": text,
                            "timestamp": int(time.time() * 1000)
                        }
                    }
                },
                "id": self.get_next_rpc_id()
            }
            
            message_json = json.dumps(message, ensure_ascii=False)
            self.ws.send(message_json)
            self.bytes_sent += len(message_json)
            
            print(f"\n" + "="*60)
            print("📤 Sending message via WebSocket")
            print("="*60)
            print(f"Chat ID: {chat_id}")
            print(f"Message ID: {message['id']}")
            print(f"Message size: {len(message_json)} bytes")
            print(f"Message preview: {text[:100]}...")
            print(f"JSON preview: {message_json[:200]}...")
            
            return True
            
        except Exception as e:
            print(f"✗ Error sending message: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_next_rpc_id(self):
        """Get next RPC ID"""
        self.rpc_id_counter += 1
        return self.rpc_id_counter
    
    def stop(self):
        """Stop the client"""
        print(f"\n" + "="*60)
        print("🛑 Stopping Pull client")
        print("="*60)
        self.running = False
        self.disconnect()
    
    def get_debug_info(self) -> Dict:
        """Get debug information"""
        connection_duration = 0
        if self.connection_start_time:
            connection_duration = time.time() - self.connection_start_time
        
        last_msg_age = "N/A"
        if self.last_message_time:
            last_msg_age = f"{time.time() - self.last_message_time:.1f}s"
        
        return {
            'status': self.status,
            'connected': self.is_authenticated,
            'user_id': self.user_id,
            'channel_id': self.channel_id[:30] + "..." if self.channel_id and len(self.channel_id) > 30 else self.channel_id,
            'site_id': self.site_id,
            'reconnect_attempts': self.reconnect_attempts,
            'revision': self.revision,
            'use_api_token': self.use_api_token,
            'has_cookies': len(self.cookies) > 0,
            'session_mid': self.session['mid'],
            'message_count': self.message_count,
            'bytes_received': self.bytes_received,
            'bytes_sent': self.bytes_sent,
            'connection_duration': f"{connection_duration:.1f}s",
            'last_message_age': last_msg_age,
            'websocket_open': self.ws is not None,
            'ping_timer_active': self.ping_timer is not None and self.ping_timer.isActive()
        }
    
    def print_statistics(self):
        """Print detailed statistics"""
        print(f"\n" + "="*60)
        print("📊 Pull Client Statistics")
        print("="*60)
        
        debug_info = self.get_debug_info()
        for key, value in debug_info.items():
            print(f"  {key}: {value}")
        
        print(f"\n  Session data:")
        print(f"    Last MID: {self.session['mid']}")
        print(f"    Last message IDs: {len(self.session['lastMessageIds'])}")
        
        if self.config:
            print(f"\n  Configuration:")
            server = self.config.get('server', {})
            print(f"    WebSocket URL: {server.get('websocket_secure', 'N/A')}")
            print(f"    Hostname: {server.get('hostname', 'N/A')}")
            
        print("="*60)