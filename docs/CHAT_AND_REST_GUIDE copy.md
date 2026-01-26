# Chat Application & REST Client Guide

This guide explains how to use the authenticated token and REST client to fetch chat data from Bitrix24.

## Quick Start

### 1. Get Authentication Token

Run the main application to open Chromium and obtain an API token:

```bash
python3 main.py
```

This will:
- Open Chromium browser
- Auto-login with saved cookies (or prompt for manual login)
- Fetch API token from Bitrix24 via `/me:` endpoint
- Save the token to `.env` file

**Output:**
```
TOKEN OBTAINED SUCCESSFULLY
✓ Token obtained in browser: pkc4eycs2shrl0ko...
✓ User ID from browser: 2611
✓ Token saved - you can now use test_rest_client.py
```

### 2. Test REST API with Token

After token is saved, test API connectivity:

```bash
python3 test_rest_client.py
```

This script will:
- Load token from `.env` file (`API_TOKEN` and `API_USER_ID`)
- Test basic API methods
- Retrieve chat dialogs and messages
- Display summary of successful/failed calls

**Example Output:**
```
BITRIX24 REST API TEST
User ID: 2611
Token: pkc4eycs2shrl0ko... (hidden)

📡 Calling: user.current
   Status: 200
   Time: 0.35s
   ✓ Success - returned 1 item(s)

📡 Calling: im.dialog.list
   Status: 200
   Time: 0.42s
   ✓ Success - returned 5 item(s)

💬 Getting dialogs...
✓ Got 5 dialogs
  • [40] Main Sales Channel
  • [41] Support Team
  • [42] Projects
```

### 3. Manual REST Client Usage

Use the REST client with custom parameters:

```bash
# Using token from .env
python3 test_rest_client.py

# Using explicit token and user_id
python3 test_rest_client.py 2611 pkc4eycs2shrl0ko

# Test specific API method
python3 -c "
from test_rest_client import RestClientTest
import os
from dotenv import load_dotenv

load_dotenv()
client = RestClientTest()
result = client.call_method('im.dialog.list', {'LIMIT': 20})
print(result)
"
```

## API Token Acquisition Flow

### Before: Python-Based (Doesn't Work)
```
Python requests library
    ↓
Bitrix24 API (no browser context, no cookies)
    ↓
✗ 401 Unauthorized / ERROR_METHOD_NOT_FOUND
```

### Now: Browser-Based (Works!)
```
Chromium Browser (with cookies)
    ↓
JavaScript fetch() to /me: endpoint
    ↓
Bitrix24 Token Endpoint (in authenticated session)
    ↓
✓ Token obtained (PASSWORD field in response)
    ↓
Python loads token from .env
    ↓
Python uses token in REST API URL
    ↓
/rest/{user_id}/{token}/{method}
```

## REST API URL Format

All API calls use this format:

```
POST https://ugautodetal.ru/rest/{user_id}/{token}/{method}
Content-Type: application/json

{
  "PARAM1": "value1",
  "PARAM2": "value2"
}
```

### Example: Get Chat Dialogs

```bash
curl -X POST \
  "https://ugautodetal.ru/rest/2611/pkc4eycs2shrl0ko/im.dialog.list" \
  -H "Content-Type: application/json" \
  -d '{"LIMIT": 10}'
```

### Example: Get Messages

```bash
curl -X POST \
  "https://ugautodetal.ru/rest/2611/pkc4eycs2shrl0ko/im.message.list" \
  -H "Content-Type: application/json" \
  -d '{"LIMIT": 20, "LAST_ID": 0}'
```

## Available API Methods

### User Methods
- `user.current` - Get current user info
- `user.get` - Get user by ID
- `user.list` - Get list of users

### Chat/IM Methods
- `im.dialog.list` - Get dialog list
- `im.message.list` - Get messages
- `im.message.get` - Get specific message
- `im.user.list` - Get IM users
- `im.chat.get` - Get chat info
- `im.chat.list` - Get chat list

### Batch Methods
- `batch` - Call multiple methods in one request

## Implementation Details

### Token Retrieval Flow

1. **Browser Authentication** (`chrome_auth.py`)
   ```python
   def get_api_token_in_browser(self):
       # Extract CSRF token from page meta tags
       csrf_data = self.driver.execute_script(csrf_js)
       
       # Execute fetch in browser context
       self.driver.execute_script(token_request_js, csrf_token, site_id)
       
       # Retrieve response from window variable
       result = self.driver.execute_script("return window.tokenResponse;")
   ```

2. **Response Format**
   ```json
   {
     "status": "success",
     "data": {
       "ID": "16",
       "PASSWORD": "sjsm7pm51psrf372",
       "USER_ID": "2611",
       "TITLE": "External Access for REST API",
       "DATE_CREATE": "2026-01-15T11:10:19+03:00"
     },
     "errors": []
   }
   ```

3. **Token Storage** (`main.py`)
   ```python
   # Save to .env after obtaining
   with open('.env', 'a') as f:
       f.write(f"\nAPI_TOKEN={api_token}\n")
       f.write(f"API_USER_ID={user_id}\n")
   ```

### REST Client Implementation

```python
class RestClientTest:
    def _build_url(self, method):
        return f"{self.base_url}/{self.user_id}/{self.token}/{method}"
    
    def call_method(self, method, params=None):
        url = self._build_url(method)
        response = self.session.post(url, json=params or {}, timeout=60)
        return response.json()
```

## Environment Variables

After running `python3 main.py`, these are saved in `.env`:

```env
# API Authentication
API_USER_ID=2611
API_TOKEN=pkc4eycs2shrl0ko

# Browser Cookies
COOKIE_PHPSESSID=...
COOKIE_BITRIX_SM_LOGIN=...

# Pull Channel
PULL_CHANNEL_PRIVATE=...
PULL_CHANNEL_SHARED=...
PULL_WEBSOCKET_URL=wss://ugautodetal.ru/bitrix/subws/
```

## Troubleshooting

### "No token in .env"

1. Run `python3 main.py` again
2. Check if browser opened and logged in
3. Verify token fetch in DevTools Network tab

### "API_TOKEN=None or empty"

1. Token was not obtained from browser
2. Check main.py for `.env` write errors
3. Manually run: `echo "API_TOKEN=your_token" >> .env`

### "ERROR_METHOD_NOT_FOUND"

1. API method doesn't exist or is wrong name
2. Check Bitrix24 API documentation
3. Try different method: `user.current`, `im.dialog.list`

### "401 Unauthorized"

1. Token is expired or invalid
2. Run `python3 main.py` again to get new token
3. Verify token and user_id match

## Using Chat Data in Application

### UI Integration

The main application (`main_window.py`) uses the token to:

```python
# Initialize API
self.api = BitrixAPI(
    user_id=int(self.auth_info.get('api_user_id')),
    token=self.auth_info.get('api_token')
)

# Load chat dialogs
dialogs = self.api.call_method("im.dialog.list", {"LIMIT": 50})

# Get messages from dialog
messages = self.api.call_method("im.message.list", {"LIMIT": 100})

# Send message
self.api.call_method("im.message.add", {
    "DIALOG_ID": dialog_id,
    "MESSAGE": "Hello!"
})
```

### WebSocket Integration

For real-time updates, use Pull channel:

```python
# From .env
pull_channel = os.getenv('PULL_CHANNEL_PRIVATE')
websocket_url = os.getenv('PULL_WEBSOCKET_URL')

# Connect WebSocket for updates
ws = websocket.WebSocketApp(websocket_url)
```

## Files Structure

```
chatBitrix/
├── main.py                    # Entry point, token retrieval
├── test_rest_client.py        # REST API testing tool
├── .env                       # Tokens & credentials (created by main.py)
├── auth/
│   ├── chrome_auth.py         # Browser automation for token fetch
│   └── auth_manager.py        # Authentication management
├── api/
│   └── bitrix_api.py          # REST API client
├── ui/
│   └── main_window.py         # Chat UI
├── pull/
│   └── bitrix_pull.py         # WebSocket pull/updates
└── docs/                      # Documentation
    ├── AUTHENTICATION_FLOW_DETAILED.md
    ├── BROWSER_ONLY_TOKEN.md
    └── ...
```

## Next Steps

1. ✅ Get token with `python3 main.py`
2. ✅ Test REST API with `python3 test_rest_client.py`
3. ✅ Verify chat data retrieval (dialogs, messages)
4. 📝 Implement message sending functionality
5. 📝 Add WebSocket for real-time updates
6. 📝 Deploy to production

## References

- Bitrix24 API: https://dev.1c-bitrix.ru/rest_help/
- REST Authentication: https://dev.1c-bitrix.ru/rest_help/auth/
- IM Methods: https://dev.1c-bitrix.ru/rest_help/im/
