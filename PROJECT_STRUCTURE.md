## Project Structure

```
chatBitrix/
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (API_TOKEN, API_USER_ID, etc)
├── auth_data_full.json     # Full authentication data
├── pull_config.json        # Pull configuration
├── README.md               # This file
├── src/                    # Source code modules
│   ├── __init__.py
│   ├── api/                # Bitrix REST API client
│   │   ├── __init__.py
│   │   ├── bitrix_api.py   # Main API class
│   │   └── models.py       # Data models (User, Group, Message, etc)
│   │
│   ├── auth/               # Authentication & token management
│   │   ├── __init__.py
│   │   ├── chrome_auth.py  # Browser automation & token fetching
│   │   ├── auth_manager.py # Auth flow management
│   │   ├── env_handler.py  # Environment file handling
│   │   └── bitrix_token_manager.py  # Token storage & validation
│   │
│   ├── ui/                 # PyQt5 User Interface
│   │   ├── __init__.py
│   │   ├── main_window.py  # Main application window
│   │   ├── widgets.py      # Custom UI components
│   │   ├── chat_list_item.py       # Chat list item widget
│   │   ├── message_bubble.py       # Message display widget
│   │   └── themes.py       # Styling & themes
│   │
│   ├── pull/               # Bitrix Pull (WebSocket) client
│   │   ├── __init__.py
│   │   ├── bitrix_pull.py  # Pull client implementation
│   │   └── pull_constants.py       # Pull constants
│   │
│   └── utils/              # Utilities & helpers
│       ├── __init__.py
│       ├── helpers.py      # String/date formatting utilities
│       ├── file_handlers.py        # File operations
│       └── README.md
│
└── docs/                   # Documentation
    ├── AUTH_DATA_FLOW.md
    ├── SYSTEM_ARCHITECTURE.md
    └── ...
```

## Quick Start

### 1. Install Dependencies
```bash
pip3 install -r requirements.txt
```

### 2. Run Application
```bash
python3 main.py
```

The app will:
- Check for authentication data (.env, auth_data_full.json)
- If missing, open Chromium browser for authentication
- Extract API token automatically
- Initialize BitrixAPI with token
- Launch the chat UI
- Connect to Bitrix via WebSocket (Pull)

### 3. Key Files

**main.py**
- Application entry point
- Handles authentication flow
- Initializes BitrixAPI and UI
- No test functions - clean startup

**src/ui/main_window.py**
- Main chat interface (1600+ lines)
- Sidebar with chat list
- Message area with typing indicators
- Real-time updates via Pull client
- Only active methods (no stubs)

**src/api/bitrix_api.py**
- REST API client
- Handles token-based authentication
- URL format: `/rest/{user_id}/{token}/{method}`
- Custom methods: `uad.shop.api.chat.*`

**src/auth/chrome_auth.py**
- Selenium WebDriver automation
- XMLHttpRequest for token fetching (DevTools visible)
- 30-second initialization wait
- Login detection via page source

**src/pull/bitrix_pull.py**
- WebSocket client for real-time updates
- Automatic reconnection with exponential backoff
- Handles: messages, typing, user status, channel updates

## Authentication Flow

1. **Token Acquisition** (main.py → src/auth/chrome_auth.py)
   - Opens Chromium browser
   - Auto-login with saved cookies
   - XMLHttpRequest to `/me:` endpoint (visible in DevTools)
   - Saves token & user_id to .env

2. **Token Storage** (.env file)
   ```
   API_TOKEN=pkc4eycs2shrl0ko
   API_USER_ID=2611
   COOKIE_PHPSESSID=...
   PULL_WEBSOCKET_URL=wss://...
   ```

3. **API Initialization** (main.py → src/ui/main_window.py)
   - Loads token from .env
   - Creates BitrixAPI instance
   - TelegramChatWindow loads auth data
   - UI initializes with valid token

4. **WebSocket Connection** (src/pull/bitrix_pull.py)
   - Pull client connects to wss://ugautodetal.ru/bitrix/subws/
   - Receives real-time chat updates
   - Handles reconnection & errors

## API Usage Example

```python
from src.api.bitrix_api import BitrixAPI
import os

# Load from .env
api = BitrixAPI(
    user_id=int(os.getenv('API_USER_ID')),
    token=os.getenv('API_TOKEN')
)

# Get chat groups
groups = api.get_groups()

# Get messages
messages = api.get_messages(group_id=88)

# Send message
api.add_message(group=88, message="Hello!")
```

## Configuration

**.env File**
```
API_TOKEN=<token from browser>
API_USER_ID=<user id from token>
COOKIE_PHPSESSID=<session cookie>
PULL_WEBSOCKET_URL=<ws url from pull config>
```

**pull_config.json** (auto-generated)
```json
{
  "WEBSOCKET": "wss://ugautodetal.ru/bitrix/subws/",
  "CHANNEL_ID": "...",
  "SIGNATURE": "...",
  "REVISION": 0
}
```

## Troubleshooting

**"API token cannot be empty"**
- Run: `python3 main.py`
- Log in when prompted
- Token will be auto-extracted

**"Module not found"**
- Verify `src/` directory exists with all subdirectories
- Check Python path in main.py

**No messages received**
- Pull client connecting automatically
- Check WebSocket URL in .env
- Verify firewall allows WebSocket connections

## Development

### Adding New Methods
1. Add to `BitrixAPI` class in `src/api/bitrix_api.py`
2. Add corresponding UI handlers in `src/ui/main_window.py`
3. Test with real data

### Debugging
- Open DevTools (F12) to see network requests
- Check console for error messages
- Pull client logs to terminal

### Code Organization
- **api/** - REST API calls only
- **auth/** - Token/auth management  
- **pull/** - WebSocket communication
- **ui/** - PyQt5 interface
- **utils/** - Helpers & utilities
