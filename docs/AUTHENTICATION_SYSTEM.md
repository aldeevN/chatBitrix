# Authentication System Documentation

## Overview
The authentication system handles user login, credential management, and token acquisition from Bitrix24. It uses Selenium-based browser automation to extract API credentials securely.

## Components

### 1. auth_manager.py
Main authentication orchestration module

#### `authenticate_and_get_env()`
Handles interactive browser-based authentication

**Flow**:
1. Launches Chromium browser
2. Navigates to Bitrix24 instance
3. Attempts auto-login with saved cookies
4. Falls back to manual login if needed
5. Extracts API token directly in browser
6. Saves credentials to `.env` file

**Process**:
```
Start → Navigate to Bitrix → Check Cookies
    ├─ Yes: Auto-login → Get Token → Save .env
    └─ No: Manual Login → Prompt User → Get Token → Save .env
```

**Returns**: `List[str]` - List of environment variable entries

**Example**:
```python
from auth.auth_manager import authenticate_and_get_env

env_lines = authenticate_and_get_env()
print(f"Saved {len(env_lines)} configuration entries")
```

**User Flow**:
1. Script opens browser window
2. If cookies exist: Auto-logs in (usually instant)
3. If no cookies: User manually logs in
   - Waits for manual login
   - Shows message: "Press Enter after logging in..."
4. Extracts token automatically
5. Saves to `.env`

#### `authenticate_from_captured_data()`
Loads authentication from previously saved data without opening browser

**Process**:
```
Check → Load from JSON → Extract User ID → Save to .env
```

**Returns**: `Dict` - Authentication data

**Use Cases**:
- Subsequent app runs (don't need to log in again)
- Running on servers without display
- Batch operations

**Example**:
```python
from auth.auth_manager import authenticate_from_captured_data

auth_data = authenticate_from_captured_data()
user_id = auth_data.get('user_id')
```

### 2. chrome_auth.py
Browser automation for credential extraction

#### `ChromeAuthApp` Class
Handles browser operations and token extraction

**Key Methods**:
- `navigate_to_login(url)` - Open Bitrix24 URL
- `auto_login_with_saved_cookies(url)` - Use saved cookies for login
- `get_api_token_in_browser()` - Extract token directly from browser
- `save_cookies_pickle()` - Save session cookies for future use
- `get_cookies()` - Get all browser cookies
- `close()` - Clean up browser session

**Example**:
```python
from auth.chrome_auth import ChromeAuthApp

app = ChromeAuthApp(headless=False)
try:
    app.navigate_to_login("https://ugautodetal.ru")
    token, user_id = app.get_api_token_in_browser()
    app.save_cookies_pickle()
finally:
    app.close()
```

**Token Extraction Method**:
1. Injects JavaScript into browser
2. Accesses `/me:` endpoint
3. Extracts `USER_ID` and token from response
4. Returns both values

### 3. env_handler.py
Environment file and variable management

#### `load_env_file(filename)`
Load variables from `.env` file

**Parameters**:
- `filename` (str, default: `.env`)

**Returns**: `Dict[str, str]` - Environment variables

**Example**:
```python
from auth.env_handler import load_env_file

env_vars = load_env_file()
token = env_vars.get('BITRIX_REST_TOKEN')
```

#### `save_env_file(env_vars, filename)`
Save variables to `.env` file

**Parameters**:
- `env_vars` (Dict[str, str]): Variables to save
- `filename` (str, default: `.env`)

**Example**:
```python
env_vars = {
    'BITRIX_REST_TOKEN': 'my_token',
    'BITRIX_USER_ID': '2611'
}
save_env_file(env_vars)
```

#### `create_env_file_from_auth(auth_data)`
Convert authentication data to `.env` format

**Parameters**:
- `auth_data` (Dict): Authentication data from browser

**Creates**:
- `BITRIX_REST_TOKEN` - API token
- `BITRIX_USER_ID` - User ID
- `COOKIE_*` - Browser cookies
- `PULL_*` - WebSocket configuration

**Example**:
```python
from auth.env_handler import create_env_file_from_auth

env_lines = create_env_file_from_auth(auth_data)
print(f"Created .env with {len(env_lines)} entries")
```

### 4. bitrix_token_manager.py
Token lifecycle management

**Features**:
- Token validation
- Token refresh/renewal
- Token expiration checking
- Secure token storage

## Authentication Flow

### First Run (Interactive)
```
python3 main.py
    ↓
Launches browser
    ↓
Checks for saved cookies
    ├─ Found: Auto-login
    └─ Not found: Wait for manual login
    ↓
Extracts API token from browser
    ↓
Saves to .env and auth_data.json
    ↓
Starts chat application
```

### Subsequent Runs (Automatic)
```
python3 main.py
    ↓
Check .env for credentials
    ├─ Complete: Use directly
    └─ Incomplete: Load from auth_data.json
    ↓
Verify token validity
    ├─ Valid: Continue
    └─ Invalid: Re-authenticate
    ↓
Start chat application
```

## Credential Storage

### Files Generated

#### `.env` (Main configuration)
```
BITRIX_REST_TOKEN=your_api_token
BITRIX_USER_ID=your_user_id
BITRIX_CSRF_TOKEN=...
BITRIX_SITE_ID=ap
```

#### `auth_data_full.json` (Complete auth data)
```json
{
    "user_id": 2611,
    "cookies": {
        "UAD_AVATAR": "2611",
        "BITRIX_SM_UIDH": "..."
    },
    "local_storage": {
        "bx-pull-2611-ap-bx-pull-config": "{...}"
    },
    "session_storage": {...},
    "tokens": {
        "api_token": "your_token"
    }
}
```

#### `cookies.pkl` (Pickled cookies)
Binary file containing browser session cookies for auto-login

## Security Features

### 1. Cookie-Based Auto-Login
- Saves session cookies from browser
- No password stored in plaintext
- Automatic login on subsequent runs

### 2. Token Extraction
- Token obtained directly from browser API
- Not transmitted through third parties
- Validated before use

### 3. Secure Storage
- `.env` file (should be gitignored)
- JSON with sensitive data encrypted
- Pickled cookies for session

### 4. Environment Variable Protection
```python
# Token is truncated in logs
print(f"Token: {token[:20]}...")  # Shows: "Token: pkc4eycs2shrl0ko..."
```

## Usage in Application

### Starting the Chat
```bash
# First run (interactive)
python3 main.py

# Subsequent runs (automatic, uses saved credentials)
python3 main.py
```

### Programmatic Use
```python
from auth.auth_manager import authenticate_from_captured_data
from api.bitrix_api import BitrixAPI

# Load saved credentials
auth_data = authenticate_from_captured_data()

# Create API client
api = BitrixAPI(
    user_id=auth_data['user_id'],
    token=auth_data['tokens']['api_token']
)
```

## Environment Variables

### Required Variables
| Variable | Description | Source |
|----------|-------------|--------|
| `BITRIX_REST_TOKEN` | API authentication token | Browser extraction |
| `BITRIX_USER_ID` | Current user ID | Browser extraction |
| `BITRIX_API_URL` | Bitrix instance URL | Config |
| `BITRIX_SITE_ID` | Site identifier | Config (default: "ap") |

### Optional Variables
| Variable | Description |
|----------|-------------|
| `BITRIX_CSRF_TOKEN` | CSRF protection token |
| `PULL_CHANNEL_PRIVATE` | WebSocket channel for private messages |
| `PULL_CHANNEL_SHARED` | WebSocket channel for shared messages |
| `PULL_WEBSOCKET_URL` | WebSocket server URL |

## Error Handling

### Common Issues

#### "Auto-login failed"
```
Solution: Cookies expired
Action: Delete cookies.pkl and re-run python3 main.py
```

#### "Token not found"
```
Solution: Token extraction failed
Action: Check browser console, ensure you're logged in
```

#### "User ID not found"
```
Solution: Cannot extract user ID from cookies
Action: Check UAD_AVATAR cookie is set
```

### Debug Mode
```python
from auth.auth_manager import authenticate_and_get_env

# Enable verbose output
import logging
logging.basicConfig(level=logging.DEBUG)

env_lines = authenticate_and_get_env()
```

## Troubleshooting

### Reset Authentication
```bash
# Remove all auth files
rm .env auth_data_full.json cookies.pkl

# Re-authenticate
python3 main.py
```

### Verify Credentials
```python
from auth.env_handler import load_env_file

env = load_env_file()
print(f"User ID: {env.get('BITRIX_USER_ID')}")
print(f"Token: {env.get('BITRIX_REST_TOKEN', 'NOT SET')[:20]}...")
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
if "error" not in result:
    print("✅ Authentication successful!")
else:
    print(f"❌ Error: {result['error']}")
```

## Security Best Practices

1. **Never commit `.env` file**
   ```
   # Add to .gitignore
   .env
   auth_data_full.json
   cookies.pkl
   ```

2. **Protect sensitive files**
   ```bash
   chmod 600 .env
   chmod 600 auth_data_full.json
   chmod 600 cookies.pkl
   ```

3. **Rotate tokens regularly**
   ```bash
   # Reset authentication monthly
   rm .env cookies.pkl
   python3 main.py
   ```

4. **Don't share credentials**
   - Never paste token in messages/emails
   - Don't expose .env in error reports
   - Use separate accounts for testing

## Integration Points

### With BitrixAPI
```python
api = BitrixAPI(
    user_id=auth_data['user_id'],
    token=auth_data['tokens']['api_token']
)
```

### With BitrixPullClient
```python
pull_client = BitrixPullClient(
    api=api,
    user_id=auth_data['user_id']
)
```

### With UI
```python
# Main window receives authenticated API
window = TelegramChatWindow(api=api, auth_data=auth_data)
```
