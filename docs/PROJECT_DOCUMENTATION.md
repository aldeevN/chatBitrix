# Complete Project Documentation Index

## Quick Navigation

### Getting Started
- **[QUICK_START.md](QUICK_START.md)** - Installation and first run
- **[SMART_STARTUP.md](SMART_STARTUP.md)** - Automated startup process

### Core Modules
1. **[API_MODELS.md](API_MODELS.md)** - Data structures (User, Group, Message)
2. **[BITRIX_API_CLIENT.md](BITRIX_API_CLIENT.md)** - REST API client
3. **[AUTHENTICATION_SYSTEM.md](AUTHENTICATION_SYSTEM.md)** - Login and token management
4. **[BITRIX_PULL_CLIENT.md](BITRIX_PULL_CLIENT.md)** - WebSocket real-time messaging
5. **[UI_COMPONENTS.md](UI_COMPONENTS.md)** - PyQt5 GUI components
6. **[UTILITY_FUNCTIONS.md](UTILITY_FUNCTIONS.md)** - Helper functions

### Design & Styling
- **[TELEGRAM_DESIGN_UPDATE.md](TELEGRAM_DESIGN_UPDATE.md)** - Modern UI design
- **[MODERN_UI_GUIDE.md](MODERN_UI_GUIDE.md)** - Theme system documentation

---

## Project Structure Overview

```
chatBitrix/
├── src/                           # Source code
│   ├── api/                       # API communication
│   │   ├── bitrix_api.py          # REST API client ← BITRIX_API_CLIENT.md
│   │   └── models.py              # Data models ← API_MODELS.md
│   │
│   ├── auth/                      # Authentication
│   │   ├── auth_manager.py        # Auth orchestration
│   │   ├── chrome_auth.py         # Browser automation
│   │   ├── env_handler.py         # Environment variables
│   │   └── bitrix_token_manager.py # Token lifecycle
│   │   └─ ← AUTHENTICATION_SYSTEM.md
│   │
│   ├── pull/                      # WebSocket/Real-time
│   │   ├── bitrix_pull.py         # Pull client ← BITRIX_PULL_CLIENT.md
│   │   └── pull_constants.py      # Constants
│   │
│   ├── ui/                        # User Interface
│   │   ├── main_window.py         # Main application
│   │   ├── themes.py              # Color/theme system
│   │   ├── widgets.py             # Custom components
│   │   ├── message_bubble.py      # Message display
│   │   ├── chat_list_item.py      # Chat list entry
│   │   └── new_message_dialog.py  # Compose dialog
│   │   └─ ← UI_COMPONENTS.md
│   │
│   └── utils/                     # Utilities
│       ├── helpers.py             # Helper functions
│       └── file_handlers.py       # File operations
│       └─ ← UTILITY_FUNCTIONS.md
│
├── docs/                          # Documentation (you are here)
│   ├── API_MODELS.md              # ← You are reading
│   ├── BITRIX_API_CLIENT.md
│   ├── AUTHENTICATION_SYSTEM.md
│   ├── BITRIX_PULL_CLIENT.md
│   ├── UI_COMPONENTS.md
│   ├── UTILITY_FUNCTIONS.md
│   ├── PROJECT_DOCUMENTATION.md   # (This file)
│   └── [20+ other docs]           # Previous documentation
│
├── main.py                        # Entry point
├── requirements.txt               # Dependencies
└── .env                          # Configuration (git-ignored)
```

---

## Module Documentation Matrix

| Module | Purpose | Key Classes | Documentation |
|--------|---------|------------|-----------------|
| `api/bitrix_api.py` | REST API calls | `BitrixAPI` | [BITRIX_API_CLIENT.md](BITRIX_API_CLIENT.md) |
| `api/models.py` | Data structures | `User`, `Group`, `Message`, `Customer` | [API_MODELS.md](API_MODELS.md) |
| `auth/auth_manager.py` | Authentication flow | Functions | [AUTHENTICATION_SYSTEM.md](AUTHENTICATION_SYSTEM.md) |
| `auth/chrome_auth.py` | Browser automation | `ChromeAuthApp` | [AUTHENTICATION_SYSTEM.md](AUTHENTICATION_SYSTEM.md) |
| `auth/env_handler.py` | Env management | Functions | [AUTHENTICATION_SYSTEM.md](AUTHENTICATION_SYSTEM.md) |
| `pull/bitrix_pull.py` | WebSocket client | `BitrixPullClient` | [BITRIX_PULL_CLIENT.md](BITRIX_PULL_CLIENT.md) |
| `ui/main_window.py` | Main UI window | `TelegramChatWindow` | [UI_COMPONENTS.md](UI_COMPONENTS.md) |
| `ui/themes.py` | Color system | Functions + constants | [UI_COMPONENTS.md](UI_COMPONENTS.md) |
| `ui/widgets.py` | Reusable components | `TelegramButton`, `TelegramInput`, `TelegramSearchBar` | [UI_COMPONENTS.md](UI_COMPONENTS.md) |
| `ui/message_bubble.py` | Message display | `MessageBubble` | [UI_COMPONENTS.md](UI_COMPONENTS.md) |
| `ui/chat_list_item.py` | Chat list entry | `ChatListItem` | [UI_COMPONENTS.md](UI_COMPONENTS.md) |
| `ui/new_message_dialog.py` | Compose dialog | `NewMessageDialog` | [UI_COMPONENTS.md](UI_COMPONENTS.md) |
| `utils/helpers.py` | Utility functions | Various functions | [UTILITY_FUNCTIONS.md](UTILITY_FUNCTIONS.md) |
| `utils/file_handlers.py` | File operations | Various functions | [UTILITY_FUNCTIONS.md](UTILITY_FUNCTIONS.md) |

---

## Data Flow Diagrams

### Authentication Flow
```
User runs: python3 main.py
    ↓
Check .env for credentials
    ├─ Complete → Skip to Chat
    └─ Incomplete → Authenticate
        ↓
    Launch Chromium browser
        ↓
    Check saved cookies
        ├─ Found → Auto-login
        └─ Not found → Wait for manual login
        ↓
    Extract API token from browser
        ↓
    Save to .env + auth_data.json
        ↓
    Start Chat Application
```

### Message Loading Flow
```
User selects chat in sidebar
    ↓
select_chat(group_id)
    ↓
BitrixAPI.get_messages(group_id)
    ↓
Parse response → [Message objects]
    ↓
Create MessageBubble widgets
    ↓
Display in scroll area
```

### Real-time Message Flow
```
BitrixPullClient (WebSocket)
    ↓
Receives binary message
    ↓
Decode & parse JSON
    ↓
Extract group_id
    ↓
Emit message_received signal
    ↓
Main Window: handle_pull_message()
    ↓
If group is active:
    └─ Display message
       Update chat unread count
```

---

## Key Concepts

### Authentication
- **Token-based**: API token obtained from browser
- **Cookie-based**: Session stored as pickle file
- **User ID**: Extracted from cookies or API response

### API Communication
- **REST API**: Standard HTTP POST requests
- **URL format**: `/rest/{user_id}/{token}/{method}`
- **Async**: Requests block main thread (improve with threading)

### Real-time Messaging
- **WebSocket**: Binary protocol for efficiency
- **Channels**: Private (user-specific) and shared (all users)
- **Auto-reconnect**: Up to 10 attempts with exponential backoff

### UI Architecture
- **PyQt5**: Cross-platform GUI framework
- **Signals/Slots**: Thread-safe communication
- **Themes**: Dynamic light/dark mode switching
- **Material Design**: Modern, professional appearance

---

## Common Tasks

### Load All Chats
```python
from api.bitrix_api import BitrixAPI

api = BitrixAPI(user_id=2611, token="your_token")
response = api.get_groups()
groups = response.get("result", [])
```
See: [BITRIX_API_CLIENT.md](BITRIX_API_CLIENT.md#get_groups)

### Load Messages from Chat
```python
response = api.get_messages(group_id=133)
messages = response.get("result", [])
```
See: [BITRIX_API_CLIENT.md](BITRIX_API_CLIENT.md#get_messagess)

### Display Message
```python
from ui.message_bubble import MessageBubble

bubble = MessageBubble(
    message=message_obj,
    current_user=user,
    is_own=True,
    is_dark=False
)
```
See: [UI_COMPONENTS.md](UI_COMPONENTS.md#4-message_bubblepy)

### Listen for Real-time Messages
```python
from pull.bitrix_pull import BitrixPullClient

pull = BitrixPullClient(api=api, user_id=2611)
pull.message_received.connect(on_new_message)
pull.start()
```
See: [BITRIX_PULL_CLIENT.md](BITRIX_PULL_CLIENT.md)

### Format Timestamp
```python
from utils.helpers import format_timestamp

time_str = format_timestamp("2025-01-26T09:30:00Z")  # "09:30"
```
See: [UTILITY_FUNCTIONS.md](UTILITY_FUNCTIONS.md#timestamp-formatting)

---

## Error Handling

### API Errors
```python
result = api.get_groups()
if "error" in result:
    print(f"API Error: {result['error']}")
else:
    groups = result.get("result", [])
```

### Authentication Errors
```python
try:
    auth_data = authenticate_from_captured_data()
except FileNotFoundError:
    print("Run 'python3 main.py' first to authenticate")
```

### WebSocket Errors
```
Pull client auto-reconnects on error
Check debug_info signal for error messages
```

---

## Performance Tips

1. **Cache frequently accessed data**
   - Don't reload groups repeatedly
   - Cache user display names

2. **Lazy load messages**
   - Load on demand when user opens chat
   - Implement pagination for large chats

3. **Optimize UI updates**
   - Batch message updates
   - Use signals for thread-safe updates

4. **Handle large datasets**
   - Limit message display (e.g., last 100 messages)
   - Remove old messages from memory

---

## Security Considerations

1. **Token Management**
   - Never hardcode tokens
   - Load from `.env` file (gitignored)
   - Rotate tokens regularly

2. **Credential Storage**
   - `.env` contains sensitive data
   - `auth_data.json` contains all auth info
   - `cookies.pkl` contains session

3. **Data Transmission**
   - Use HTTPS/WSS for all connections
   - Don't expose tokens in logs
   - API truncates token in debug output

---

## Testing Guide

### Test Authentication
```bash
python3 main.py
# Opens browser, completes login, saves credentials
```

### Test API Connection
```python
from api.bitrix_api import BitrixAPI
import os
from dotenv import load_dotenv

load_dotenv()
api = BitrixAPI(
    user_id=int(os.getenv('BITRIX_USER_ID')),
    token=os.getenv('BITRIX_REST_TOKEN')
)
result = api.get_current_profile()
print("✅ Connected!" if "error" not in result else "❌ Error")
```

### Test Pull Client
```python
from pull.bitrix_pull import BitrixPullClient

pull = BitrixPullClient(api=api, user_id=2611)
pull.message_received.connect(print)
pull.start()
# Wait for messages
```

### Test UI
```bash
python3 run_chat.py
# Starts chat application
```

---

## Troubleshooting

### "Token is invalid"
```bash
# Get fresh token
python3 main.py
```

### "User ID not found"
```python
from auth.env_handler import load_env_file
env = load_env_file()
print(env.get('BITRIX_USER_ID'))
```

### "WebSocket connection failed"
```
Check internet connection
Verify pull config in auth_data.json
Check server URL is accessible
```

### "Messages not loading"
```python
# Check API response
response = api.get_messages(group_id=133)
if "error" in response:
    print(response["error"])
```

---

## Dependencies

### Core Libraries
- **PyQt5** - GUI framework
- **requests** - HTTP client
- **websocket-client** - WebSocket support
- **selenium** - Browser automation
- **python-dotenv** - Environment variables

### Installation
```bash
pip install -r requirements.txt
```

---

## Version Information

- **Python**: 3.9+
- **PyQt5**: 5.15.0+
- **Bitrix24**: 2024+

---

## Contributing

When adding new features:
1. Update relevant documentation
2. Add docstrings to functions
3. Include type hints
4. Create utility functions for repeated logic

---

## See Also

- **[QUICK_START.md](QUICK_START.md)** - First-time setup
- **[SMART_STARTUP.md](SMART_STARTUP.md)** - Startup automation
- **[SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md)** - Technical architecture
- **[TELEGRAM_DESIGN_UPDATE.md](TELEGRAM_DESIGN_UPDATE.md)** - Design specifications

---

## Document Changelog

### Latest Updates
- ✅ Created API_MODELS.md
- ✅ Created BITRIX_API_CLIENT.md
- ✅ Created AUTHENTICATION_SYSTEM.md
- ✅ Created BITRIX_PULL_CLIENT.md
- ✅ Created UI_COMPONENTS.md
- ✅ Created UTILITY_FUNCTIONS.md
- ✅ Created PROJECT_DOCUMENTATION.md (this file)

### Coverage
- 🟢 Core API modules: 100%
- 🟢 Authentication system: 100%
- 🟢 WebSocket client: 100%
- 🟢 UI components: 100%
- 🟢 Utility functions: 100%

---

**Last Updated**: January 26, 2025  
**Status**: Complete - All modules documented
