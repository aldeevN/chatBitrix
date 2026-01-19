# Quick Reference: Token-Based Authentication

## What Was Fixed

✅ **Authentication Flow**: Now properly uses Bitrix24 token-based REST API
✅ **URL Format**: All requests use `https://ugautodetal.ru/rest/{user_id}/{token}/{method}`
✅ **Token Management**: Automatic token creation/retrieval via Bitrix API
✅ **Token Persistence**: Saves token to `token_info.json` for reuse
✅ **Chromium Integration**: Uses saved auth data from browser authentication

## Key Components

### 1. Token Manager (`auth/bitrix_token_manager.py`)
- Handles token lifecycle
- Creates new tokens via API
- Validates tokens
- Saves/loads tokens from files

### 2. Auth Manager (`auth/auth_manager.py`)
- Orchestrates authentication flow
- Calls token manager
- Returns user_id and token

### 3. Bitrix API (`api/bitrix_api.py`)
- Constructs URLs with user_id and token
- All methods use authenticated URLs
- Handles API requests/responses

### 4. Main App (`main.py`)
- Calls get_or_create_token()
- Initializes API with user_id and token
- Starts chat application

## Authentication URL Structure

```
Base Domain: https://ugautodetal.ru
REST Path: /rest
User ID: 1 (or your user ID)
Token: abc123xyz... (from token manager)
Method: uad.shop.api.chat.getMessages

Complete: https://ugautodetal.ru/rest/1/abc123xyz.../uad.shop.api.chat.getMessages
```

## Running the Application

```bash
cd /Users/aldeev/projects/ff/chatBitrix
python3 main.py
```

**First Run**:
1. Loads auth data from captured files
2. Creates new API token
3. Saves token to `token_info.json`
4. Starts chat application

**Subsequent Runs**:
1. Loads auth data
2. Loads saved token from `token_info.json`
3. Validates token
4. Starts chat application

## Files Modified

| File | Changes |
|------|---------|
| `auth/bitrix_token_manager.py` | NEW - Token management module |
| `auth/auth_manager.py` | Added get_or_create_token() function |
| `main.py` | Integrated token flow, updated API init |
| `api/bitrix_api.py` | Refactored for user_id + token auth |

## Environment Files

| File | Purpose |
|------|---------|
| `.env` | Environment variables from auth data |
| `auth_data_full.json` | Captured auth data (cookies, storage) |
| `token_info.json` | Saved API token for reuse |
| `pull_config.json` | Bitrix Pull configuration |

## API Request Example

```python
from auth.auth_manager import get_or_create_token
from api.bitrix_api import BitrixAPI

# Get authentication
auth_data = authenticate_from_captured_data()
success, token, msg = get_or_create_token(auth_data)

# Initialize API
api = BitrixAPI(user_id=1, token=token)

# Make requests - URL automatically includes user_id and token
groups = api.get_groups()
messages = api.get_messages(group_id=5)
```

## Troubleshooting

**Token not found?**
- Check `token_info.json` exists
- Token file contains valid token
- Run with `python3 main.py` to create new token

**API requests failing?**
- Verify token is in URL: Check terminal output
- Check user_id is correct
- Ensure Bitrix server is accessible

**Token expired?**
- Delete `token_info.json`
- Run application to create new token
- Token will be recreated automatically

## Key Improvements

1. **Secure**: Token-based auth via REST API
2. **Persistent**: Tokens saved and reused
3. **Automatic**: Token creation/management handled
4. **Clear URLs**: User_id and token visible in requests
5. **Validated**: Each token tested before use
