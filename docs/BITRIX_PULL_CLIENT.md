# Bitrix Pull Client (WebSocket) Documentation

## Overview
The `BitrixPullClient` class provides real-time message delivery through WebSocket connections. It handles binary message decoding, connection management, and event processing.

## Core Purpose
- **Real-time Communication**: WebSocket connection to Bitrix24 servers
- **Binary Protocol**: Efficient message encoding/decoding
- **Event Processing**: Routes incoming messages to UI components
- **Connection Management**: Auto-reconnection and error recovery

## Architecture

### Threading Model
Inherits from `QThread` for non-blocking operations:
```
Main UI Thread ←→ BitrixPullClient QThread
                      ↓
                  WebSocket Connection
```

### Signals (PyQt5)
- `message_received(dict)` - New message decoded
- `connection_status(bool, str)` - Connection state changed
- `debug_info(str)` - Debug information
- `raw_message_received(str)` - Raw message for debugging

## Initialization

### Constructor
```python
BitrixPullClient(api, user_id, site_id="ap", use_api_token=False)
```

**Parameters**:
- `api` (BitrixAPI): Authenticated API client
- `user_id` (int): Current user ID (e.g., 2611)
- `site_id` (str): Site identifier (default: "ap")
- `use_api_token` (bool): Whether to use API token for auth

**Example**:
```python
from pull.bitrix_pull import BitrixPullClient

pull_client = BitrixPullClient(api=api, user_id=2611, site_id="ap")
pull_client.message_received.connect(on_new_message)
pull_client.connection_status.connect(on_status_changed)
pull_client.start()  # Start the QThread
```

### Data Loading
On init, the client loads:
1. **Authentication Data** (`bitrix_token.json`)
   - Cookies from browser session
   - Pull channel configuration
   - WebSocket server URLs

2. **Pull Configuration**
   ```json
   {
       "server": {
           "websocket_secure": "wss://ugautodetal.ru/bitrix/subws/",
           "hostname": "www.ugavtopart.ru"
       },
       "channels": {
           "private": {"id": "4e955d1cd..."},
           "shared": {"id": "ecb2373b..."}
       },
       "api": {
           "revision": 19,
           "versionMobile": 3
       }
   }
   ```

3. **Connection State**
   - Channel ID for subscriptions
   - WebSocket URL with parameters
   - Cookie headers for authentication

## WebSocket Connection

### URL Construction
```
wss://ugautodetal.ru/bitrix/subws/?
  CHANNEL_ID=4e955d1cd...
  &user_id=2611
  &site_id=ap
  &hostname=www.ugavtopart.ru
  &timestamp=1769148750331
  &version=2
  &format=json
  &mode=pull
  &binary=true
```

### Headers
```
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)...
X-Bitrix-User-Id: 2611
Accept-Encoding: gzip, deflate, br
Accept-Language: ru-RU,ru;q=0.9...
Origin: https://ugautodetal.ru
Sec-WebSocket-Protocol: binary
Pragma: no-cache
Cache-Control: no-cache
Cookie: <session cookies>
```

## Binary Message Protocol

### Message Encoding
Bitrix Pull uses a custom binary format:
```
[Message Type] [Data Length] [Compressed Data] [Checksum]
   (1 byte)     (4 bytes)      (variable)       (4 bytes)
```

### Decoding Process
```python
def handle_binary_message(data):
    # 1. Decode binary data
    decoded = utf8_decode(data)
    
    # 2. Parse JSON
    message_data = json.loads(decoded)
    
    # 3. Extract group ID from params
    group_id = message_data.get('params', {}).get('group_id')
    
    # 4. Emit signal with context
    self.message_received.emit({
        'data': message_data,
        'group_id': group_id,
        'timestamp': datetime.now().isoformat()
    })
```

### Message Types
| Type | Description | Format |
|------|-------------|--------|
| `push` | New message | JSON with message content |
| `state` | User status | User ID + online status |
| `config` | Config update | Server configuration |
| `ping` | Keep-alive | Minimal message |

## Connection Lifecycle

### States
```
Offline → Connecting → Authenticating → Authenticated → Online
   ↓          ↓              ↓              ↓          ↑
   └──────────────────────────────────────────────────┘
                    (Error → Reconnect)
```

### Connection Process
```python
def run(self):
    while self.running:
        try:
            # 1. Connect to WebSocket
            self.ws = WebSocketApp(url)
            self.ws.on_message = self.on_message
            self.ws.on_error = self.on_error
            
            # 2. Send initial subscription
            self.send_subscription()
            
            # 3. Start ping timer
            self.start_ping_timer()
            
            # 4. Listen for messages
            self.ws.run_forever()
            
        except Exception as e:
            self.handle_connection_error(e)
            self.attempt_reconnect()
```

### Subscription Message
```json
{
    "jsonrpc": "2.0",
    "method": "subscribe",
    "params": {
        "channels": {
            "private": ["4e955d1cd0624e2325..."],
            "shared": ["ecb2373bf233f38f9..."]
        }
    }
}
```

## Message Handling

### On Message Received
```python
def on_message(self, ws, message):
    # Binary message from WebSocket
    try:
        # Decode binary data
        decoded = message.decode('utf-8')
        
        # Parse JSON
        data = json.loads(decoded)
        
        # Extract group context
        group_id = data.get('params', {}).get('group_id')
        
        # Route to UI
        self.message_received.emit({
            'text': data.get('text'),
            'sender': data.get('sender'),
            'group_id': group_id,
            'timestamp': data.get('timestamp')
        })
        
    except Exception as e:
        self.debug_info.emit(f"Error: {e}")
```

### Message Routing in UI
```python
# In main_window.py
pull_client.message_received.connect(self.handle_pull_message)

def handle_pull_message(self, message):
    group_id = message.get('group_id')
    
    # Update current chat if it's the active group
    if self.current_group and self.current_group.id == group_id:
        self.display_new_message(message)
    
    # Update chat list unread count
    self.update_chat_unread(group_id)
```

## Keep-Alive & Ping

### Ping Timer
Sends periodic ping to keep connection alive:
```python
# Every 20 seconds
def send_ping(self):
    ping_message = {
        "jsonrpc": "2.0",
        "method": "ping",
        "id": self.next_rpc_id()
    }
    self.ws.send(json.dumps(ping_message))
```

### Server Response
```json
{
    "jsonrpc": "2.0",
    "result": {},
    "id": 1
}
```

## Error Handling & Recovery

### Reconnection Strategy
```
Connection Lost
    ↓
Wait [exponential backoff]
    ↓
Attempt Reconnect
    ├─ Success: Resume normal operation
    └─ Failure: Retry up to 10 times
```

### Backoff Calculation
```python
wait_time = min(2 ** attempts, 300)  # Max 5 minutes

# Attempt 1: 2 seconds
# Attempt 2: 4 seconds
# Attempt 3: 8 seconds
# Attempt 4: 16 seconds
# ...
# Attempt 10+: 300 seconds (5 minutes)
```

### Error Types

| Error | Cause | Action |
|-------|-------|--------|
| Connection refused | Server down | Auto-reconnect |
| SSL error | Certificate issue | Retry with SSL bypass |
| Timeout | Network slow | Retry with longer timeout |
| Invalid token | Auth expired | Emit signal to refresh |

## Statistics & Monitoring

### Connection Statistics
```python
pull_client.message_count          # Total messages received
pull_client.bytes_received         # Total bytes decoded
pull_client.bytes_sent             # Total bytes sent
pull_client.connection_start_time  # When connected
pull_client.last_message_time      # Last activity
```

### Debug Information
```python
pull_client.debug_info.connect(print_debug)

def print_debug(info):
    print(f"[Pull] {info}")
    # Output examples:
    # [Pull] WebSocket connected
    # [Pull] Received message from group 133
    # [Pull] Ping sent (20s interval)
```

## Configuration

### SSL Settings
```python
# Disable SSL verification (for development)
ssl_options = {
    'cert_reqs': ssl.CERT_NONE,
    'check_hostname': False,
}
```

### Timeouts
```python
PING_TIMEOUT = 10  # seconds
RECONNECT_TIMEOUT = 2  # seconds (initial)
MAX_RECONNECT_ATTEMPTS = 10
```

### Logging
```python
self.logging_enabled = True  # Enable debug logging
```

## Usage Example

### Basic Setup
```python
from pull.bitrix_pull import BitrixPullClient
from api.bitrix_api import BitrixAPI

# Initialize API client
api = BitrixAPI(user_id=2611, token="your_token")

# Create Pull client
pull = BitrixPullClient(api=api, user_id=2611)

# Connect signals
pull.message_received.connect(on_message)
pull.connection_status.connect(on_status_changed)

# Start listening
pull.start()  # Starts QThread
```

### Handling Messages
```python
def on_message(message_data):
    group_id = message_data.get('group_id')
    text = message_data['data'].get('text')
    sender = message_data['data'].get('sender')
    
    print(f"[Group {group_id}] {sender}: {text}")
    
    # Update UI
    if group_id == current_group_id:
        update_chat_display(message_data)
```

### Monitoring Connection
```python
def on_status_changed(connected, message):
    if connected:
        print(f"✅ Pull connected: {message}")
        status_bar.setText("Connected")
    else:
        print(f"❌ Pull disconnected: {message}")
        status_bar.setText(f"Disconnected: {message}")
```

## Performance Considerations

### Binary Message Efficiency
- Compressed data reduces bandwidth
- Binary format faster than JSON
- Less CPU needed for parsing

### Threading
- WebSocket runs in separate thread
- UI remains responsive
- Signal/slot communication is thread-safe

### Memory Usage
```python
# Message buffer
self.message_buffer = bytearray()  # Grows/shrinks as needed

# Cookies storage
self.cookies = {}  # Small, static size

# Configuration
self.config = {}  # Single copy shared
```

## Troubleshooting

### Connection won't establish
```python
# Check logs
pull.debug_info.connect(print)

# Verify credentials
print(f"User ID: {pull.user_id}")
print(f"Channel ID: {pull.channel_id}")

# Check network
import socket
socket.create_connection(("ugautodetal.ru", 443))
```

### Messages not received
```python
# Verify signal connection
pull.message_received.connect(my_handler)

# Check group ID
print(f"Current group: {current_group_id}")
print(f"Message group: {message.get('group_id')}")

# Monitor raw messages
pull.raw_message_received.connect(print)
```

### High memory usage
```python
# Clear old messages periodically
def cleanup_old_messages():
    # Remove messages older than 1 hour
    cutoff = datetime.now() - timedelta(hours=1)
    messages[:] = [m for m in messages if m['timestamp'] > cutoff]
```

## Integration with Main UI

### In TelegramChatWindow
```python
class TelegramChatWindow(QMainWindow):
    def setup_pull_client(self):
        self.pull = BitrixPullClient(api=self.api, user_id=self.current_user.id)
        self.pull.message_received.connect(self.handle_pull_message)
        self.pull.connection_status.connect(self.update_connection_status)
        self.pull.start()
    
    def handle_pull_message(self, message):
        group_id = message.get('group_id')
        if group_id == self.current_group.id:
            self.display_message(message)
```

## Constants

### From pull_constants.py
```python
REVISION = 19
JSON_RPC_VERSION = "2.0"
JSON_RPC_PING = {"jsonrpc": "2.0", "method": "ping"}
JSON_RPC_PONG = {"jsonrpc": "2.0", "result": {}}

class PullStatus:
    Online = "online"
    Offline = "offline"
    Connecting = "connecting"

class ConnectionType:
    WebSocket = "websocket"
    LongPoll = "longpoll"

class SenderType:
    User = 1
    Bot = 2
    System = 3
```

## Advanced Features

### Custom Callbacks
```python
# Monitor specific events
pull.get_user_name_callback = get_user_display_name
pull.user_status_callbacks[2611] = on_user_status_changed
```

### Message Filtering
```python
def should_display_message(message):
    group_id = message.get('group_id')
    sender_id = message['data'].get('sender_id')
    
    # Don't show own messages (already displayed locally)
    if sender_id == current_user_id:
        return False
    
    # Only show if group is loaded
    if group_id not in loaded_groups:
        return False
    
    return True
```

## See Also
- `BITRIX_API_CLIENT.md` - REST API documentation
- `AUTHENTICATION_SYSTEM.md` - Auth and token management
- Main UI integration in `MAIN_WINDOW.md`
