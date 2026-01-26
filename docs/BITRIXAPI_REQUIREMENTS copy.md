# BitrixAPI Requirements - Token & User_ID Access

## ⚠️ CRITICAL: What You MUST Have to Use BitrixAPI

To use `BitrixAPI` for REST API access, you **must** provide two things:

### 1. API Token (Required)
- **What it is**: Authentication token for REST API calls
- **How to get it**: Run `python3 main.py`
- **Where it's stored**: `.env` file as `API_TOKEN`
- **Format**: Alphanumeric string (example: `pkc4eycs2shrl0ko`)
- **How it's used**: Embedded in URL path: `/rest/{user_id}/{token}/{method}`

### 2. User ID (Required)
- **What it is**: ID of the user who generated the token
- **How to get it**: Run `python3 main.py` (extracted from token response)
- **Where it's stored**: `.env` file as `API_USER_ID`
- **Format**: Integer (example: `2611`)
- **How it's used**: Embedded in URL path: `/rest/{user_id}/{token}/{method}`

---

## Token Acquisition Flow

```
Step 1: Get Credentials
  $ python3 main.py
  
  ↓
  
Step 2: Browser Opens
  • Navigates to https://ugautodetal.ru
  • Auto-logs in with saved cookies
  
  ↓
  
Step 3: Fetch Token in Browser
  • JavaScript fetch to /me: endpoint
  • Response contains PASSWORD (token) and USER_ID
  
  ↓
  
Step 4: Save to .env
  API_TOKEN=pkc4eycs2shrl0ko
  API_USER_ID=2611
  
  ↓
  
Step 5: Use with BitrixAPI
  api = BitrixAPI(
      user_id=2611,
      token="pkc4eycs2shrl0ko"
  )
```

---

## How to Initialize BitrixAPI

### Method 1: Load from .env (Recommended)
```python
import os
from dotenv import load_dotenv
from api.bitrix_api import BitrixAPI

# Load credentials from .env
load_dotenv()

# Initialize with loaded credentials
api = BitrixAPI(
    user_id=int(os.getenv('API_USER_ID')),
    token=os.getenv('API_TOKEN')
)

# Use the API
result = api.call_method('user.current', {})
```

### Method 2: Direct Parameters
```python
from api.bitrix_api import BitrixAPI

api = BitrixAPI(
    user_id=2611,
    token="pkc4eycs2shrl0ko"
)

result = api.call_method('im.dialog.list', {'LIMIT': 10})
```

### Method 3: From Environment Variables
```python
import os
from api.bitrix_api import BitrixAPI

# Set in environment first:
# export API_TOKEN="pkc4eycs2shrl0ko"
# export API_USER_ID="2611"

api = BitrixAPI(
    user_id=int(os.getenv('API_USER_ID')),
    token=os.getenv('API_TOKEN')
)
```

---

## REST API URL Structure

All API calls use this format:

```
POST https://ugautodetal.ru/rest/{user_id}/{token}/{method}
```

### URL Components

| Component | Example | Source |
|-----------|---------|--------|
| Base | `https://ugautodetal.ru` | Bitrix24 domain |
| Service | `rest` | REST API endpoint |
| User ID | `2611` | From API_USER_ID in .env |
| Token | `pkc4eycs2shrl0ko` | From API_TOKEN in .env |
| Method | `user.current` | Bitrix24 API method |

### Examples

| Method | URL |
|--------|-----|
| Get current user | `https://ugautodetal.ru/rest/2611/pkc4eycs2shrl0ko/user.current` |
| Get dialogs | `https://ugautodetal.ru/rest/2611/pkc4eycs2shrl0ko/im.dialog.list` |
| Get messages | `https://ugautodetal.ru/rest/2611/pkc4eycs2shrl0ko/im.message.list` |

---

## API Request/Response Example

### Request
```bash
curl -X POST \
  "https://ugautodetal.ru/rest/2611/pkc4eycs2shrl0ko/im.dialog.list" \
  -H "Content-Type: application/json" \
  -d '{"LIMIT": 10}'
```

### Response
```json
{
  "result": [
    {
      "ID": "40",
      "TITLE": "Main Sales Channel",
      "TYPE": "open",
      "USERS": ["2611", "2612"]
    },
    {
      "ID": "41",
      "TITLE": "Support Team",
      "TYPE": "open"
    }
  ]
}
```

---

## Verification Checklist

Before using BitrixAPI:

- [ ] Run `python3 main.py` to get token and user_id
- [ ] Verify `.env` file exists
- [ ] Check `.env` contains `API_TOKEN=...`
- [ ] Check `.env` contains `API_USER_ID=...`
- [ ] Run `python3 verify_api_credentials.py` to verify setup
- [ ] Run `python3 test_rest_client.py` to test API calls

---

## Troubleshooting

### Error: "token and token required"
**Cause**: Missing API_TOKEN or API_USER_ID

**Solution**:
```bash
python3 main.py          # Get credentials
cat .env | grep API_     # Verify they were saved
```

### Error: "ERROR_METHOD_NOT_FOUND"
**Cause**: Invalid API method name

**Solution**:
- Use `user.current` to test connectivity first
- Check method name spelling
- Refer to Bitrix24 API documentation

### Error: "Unauthorized" or "401"
**Cause**: Invalid token or user_id mismatch

**Solution**:
```bash
python3 main.py          # Get fresh token
rm .env && python3 main.py  # Force re-authentication
```

### Error: "No token in .env"
**Cause**: main.py didn't save credentials

**Solution**:
1. Check if browser opened and logged in
2. Verify .env file is writable
3. Run with debug: `python3 main.py 2>&1 | tail -50`

---

## Code Examples

### Example 1: Get Current User
```python
from api.bitrix_api import BitrixAPI
import os
from dotenv import load_dotenv

load_dotenv()
api = BitrixAPI(
    user_id=int(os.getenv('API_USER_ID')),
    token=os.getenv('API_TOKEN')
)

# Get current user info
user = api.call_method('user.current', {})
print(user['result'])
```

### Example 2: Get Chat Dialogs
```python
# Get list of dialogs/chats
dialogs = api.call_method('im.dialog.list', {
    'LIMIT': 20,
    'OFFSET': 0
})

for dialog in dialogs['result']:
    print(f"Dialog: {dialog['TITLE']}")
```

### Example 3: Get Messages from Dialog
```python
# Get messages from a dialog
messages = api.call_method('im.message.list', {
    'LIMIT': 50,
    'LAST_ID': 0
})

for msg_id, msg in messages['result'].items():
    print(f"[{msg_id}] {msg['MESSAGE']}")
```

### Example 4: Batch Requests
```python
# Call multiple methods in one request
result = api.call_method('batch', {
    'halt': 0,
    'cmd': {
        'current_user': 'user.current',
        'dialogs': 'im.dialog.list?LIMIT=5',
        'messages': 'im.message.list?LIMIT=10'
    }
})

print(result['result']['current_user']['result'])
print(result['result']['dialogs']['result'])
print(result['result']['messages']['result'])
```

---

## Environment Variables

### Required
```env
API_TOKEN=pkc4eycs2shrl0ko
API_USER_ID=2611
```

### Optional (Cookies)
```env
COOKIE_PHPSESSID=...
COOKIE_BITRIX_SM_LOGIN=...
```

### WebSocket/Pull
```env
PULL_CHANNEL_PRIVATE=bae7c9ae45f3db320dbd2053f468452b:...
PULL_CHANNEL_SHARED=40e089bc7f2e0b31aaa36d665fea041a...
PULL_WEBSOCKET_URL=wss://ugautodetal.ru/bitrix/subws/
```

---

## Key Points to Remember

1. **Token is NOT obtained via Python** - Must be fetched in browser via Chromium
2. **Token is in URL** - Not in headers like standard Bearer tokens
3. **Token + User ID required** - Both must be provided to BitrixAPI
4. **Token saved to .env** - Reusable for subsequent runs
5. **Run main.py first** - Gets and saves token before using BitrixAPI
6. **Verify with verify_api_credentials.py** - Test setup before using in app

---

## Files Involved

| File | Purpose |
|------|---------|
| `main.py` | Gets token via browser, saves to .env |
| `auth/chrome_auth.py` | Browser automation for token fetch |
| `api/bitrix_api.py` | REST API client using token + user_id |
| `test_rest_client.py` | Tests API with token |
| `verify_api_credentials.py` | Verifies token & user_id setup |
| `.env` | Stores API_TOKEN and API_USER_ID |

---

## Next Steps

1. ✅ Run `python3 main.py` to get token
2. ✅ Verify `.env` has API_TOKEN and API_USER_ID
3. ✅ Run `python3 verify_api_credentials.py` to test
4. ✅ Use BitrixAPI in your application
5. 📝 Implement chat features using the API
