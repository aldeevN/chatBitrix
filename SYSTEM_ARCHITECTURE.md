# Complete System Architecture & Token Flow

## System Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                    BITRIX24 CHAT APPLICATION                      │
└──────────────────────────────────────────────────────────────────┘

┌─────────────────────┐     ┌──────────────────┐     ┌───────────────┐
│                     │     │                  │     │               │
│   Chromium Browser  │────▶│   Bitrix24 API   │────▶│  .env File    │
│   (auth/chrome_...) │     │  (/me: endpoint) │     │  (Storage)    │
│                     │     │                  │     │               │
└─────────────────────┘     └──────────────────┘     └───────────────┘
         │                           │                       │
         │                           │                       │
    1. Auto-login            2. Fetch token            3. Save token
    2. Extract CSRF          3. Get USER_ID           4. Persist
    3. Fetch token                                    credentials


              │
              │
              ▼

┌────────────────────────────────────────────────────────────────────┐
│                        REST API ACCESS                             │
│                  (api/bitrix_api.py)                               │
├────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. Load API_TOKEN & API_USER_ID from .env                         │
│  2. Initialize BitrixAPI(user_id, token)                           │
│  3. Build URL: /rest/{user_id}/{token}/{method}                    │
│  4. Send POST request to Bitrix24                                  │
│  5. Receive JSON response                                          │
│                                                                     │
└────────────────────────────────────────────────────────────────────┘

              │
              │
              ▼

┌────────────────────────────────────────────────────────────────────┐
│                       APPLICATION LAYER                            │
├────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  • UI (ui/main_window.py) - Display chat/messages                  │
│  • Pull/WebSocket (pull/bitrix_pull.py) - Real-time updates       │
│  • Test Tools (test_rest_client.py) - API verification             │
│                                                                     │
└────────────────────────────────────────────────────────────────────┘
```

---

## Detailed Token Flow

### Phase 1: Token Acquisition (main.py)

```
Start main.py
    │
    ├─ Load auth_data_full.json
    │
    ├─ Check if API_TOKEN exists
    │   ├─ YES: Skip to Phase 3 (REST API)
    │   └─ NO: Continue to token fetch
    │
    ├─ Open Chromium (chrome_auth.py)
    │
    ├─ Navigate to https://ugautodetal.ru
    │
    ├─ Auto-login with saved cookies
    │   ├─ Load cookies from auth_data_full.json
    │   ├─ Set browser cookies
    │   └─ Navigate to login page
    │
    ├─ Get API token in browser (JavaScript fetch)
    │   │
    │   ├─ Extract CSRF token from page
    │   │   └─ From: <meta name="x-bitrix-csrf-token" content="...">
    │   │
    │   ├─ Extract site ID from page
    │   │   └─ From: <meta name="x-bitrix-site-id" content="ap">
    │   │
    │   ├─ Execute fetch in browser:
    │   │   POST /bitrix/services/main/ajax.php?action=me%3Abase.api.user.getTokenApi
    │   │   Headers:
    │   │     - x-bitrix-csrf-token: 99ebd3e7b86df2f9b18e83eb176d1a...
    │   │     - x-bitrix-site-id: ap
    │   │     - bx-ajax: true
    │   │   Body: (empty)
    │   │
    │   └─ Receive response
    │       {
    │         "status": "success",
    │         "data": {
    │           "ID": "16",
    │           "PASSWORD": "pkc4eycs2shrl0ko",  ◄─ TOKEN
    │           "USER_ID": "2611",                ◄─ USER_ID
    │           "TITLE": "External Access for REST API",
    │           "DATE_CREATE": "2026-01-16T16:37:17+03:00"
    │         },
    │         "errors": []
    │       }
    │
    ├─ Close Chromium
    │
    └─ Save to .env
        ├─ API_TOKEN=pkc4eycs2shrl0ko
        └─ API_USER_ID=2611
```

### Phase 2: Credential Storage (.env)

```
.env file
─────────────────────────────────────────
API_TOKEN=pkc4eycs2shrl0ko
API_USER_ID=2611
COOKIE_BITRIX_SM_LOGIN=...
PULL_CHANNEL_PRIVATE=...
PULL_CHANNEL_SHARED=...
PULL_WEBSOCKET_URL=wss://...
─────────────────────────────────────────

These are persistent and reusable
for subsequent application runs
```

### Phase 3: REST API Access (BitrixAPI)

```
Initialize BitrixAPI
    │
    ├─ Load from .env
    │   ├─ os.getenv('API_USER_ID') → 2611
    │   └─ os.getenv('API_TOKEN') → pkc4eycs2shrl0ko
    │
    ├─ Create API instance
    │   ├─ self.user_id = 2611
    │   ├─ self.token = pkc4eycs2shrl0ko
    │   └─ self.base_url = https://ugautodetal.ru/rest
    │
    └─ Ready for API calls


Make API Call
    │
    ├─ api.call_method('im.dialog.list', {'LIMIT': 10})
    │
    ├─ Build URL
    │   └─ https://ugautodetal.ru/rest/2611/pkc4eycs2shrl0ko/im.dialog.list
    │
    ├─ Create request
    │   ├─ Method: POST
    │   ├─ Headers:
    │   │   Content-Type: application/json
    │   │   Accept: application/json
    │   │   User-Agent: Python-Bitrix-Chat-Client/1.0
    │   └─ Body: {"LIMIT": 10}
    │
    ├─ Send to Bitrix24
    │
    └─ Receive response
        {
          "result": [
            {"ID": "40", "TITLE": "Main Chat"},
            {"ID": "41", "TITLE": "Support"}
          ]
        }
```

---

## Key Components

### 1. Browser Authentication (chrome_auth.py)

**Purpose**: Obtain API token in authenticated browser session

**Key Method**: `get_api_token_in_browser()`
```python
def get_api_token_in_browser(self):
    # 1. Extract CSRF token from page
    csrf_data = self.driver.execute_script(csrf_js)
    csrf_token = csrf_data.get('csrf')
    
    # 2. Execute fetch in browser
    self.driver.execute_script(token_request_js, csrf_token, site_id)
    
    # 3. Wait for response
    time.sleep(2)
    
    # 4. Retrieve from window variable
    result = self.driver.execute_script("return window.tokenResponse;")
    
    # 5. Parse and return
    return token, user_id
```

**Why Browser?**
- REST API token requires authenticated session
- Cookies automatically included in browser requests
- Python requests library can't access browser cookies
- /me: endpoint only works in browser context

### 2. REST API Client (bitrix_api.py)

**Purpose**: Make authenticated API calls to Bitrix24

**Key Method**: `call_method(method, params)`
```python
def call_method(self, method: str, params: Dict = None) -> Dict:
    # Build URL with token and user_id
    url = f"{self.base_url}/{self.user_id}/{self.token}/{method}"
    
    # Send request
    response = self.session.post(url, json=params or {})
    
    # Return parsed JSON
    return response.json()
```

**URL Format**:
```
https://ugautodetal.ru/rest/{user_id}/{token}/{method}
     ↓                    ↓     ↓       ↓         ↓
  Domain              Service  Auth Credentials  API Method
```

### 3. Token Storage (.env)

**Purpose**: Persist credentials between runs

**Contents**:
```env
# API Credentials (from main.py)
API_TOKEN=pkc4eycs2shrl0ko
API_USER_ID=2611

# Browser Cookies (auto-saved)
COOKIE_PHPSESSID=...
COOKIE_BITRIX_SM_LOGIN=...

# Pull/WebSocket Config
PULL_CHANNEL_PRIVATE=...
PULL_CHANNEL_SHARED=...
PULL_WEBSOCKET_URL=wss://ugautodetal.ru/bitrix/subws/
```

---

## Request/Response Lifecycle

### Example: Get Chat Dialogs

```
1. APPLICATION CALL
   ────────────────
   api.call_method('im.dialog.list', {'LIMIT': 10})


2. URL CONSTRUCTION
   ────────────────
   base_url: https://ugautodetal.ru/rest
   user_id:  2611
   token:    pkc4eycs2shrl0ko
   method:   im.dialog.list
   
   Final URL: https://ugautodetal.ru/rest/2611/pkc4eycs2shrl0ko/im.dialog.list


3. HTTP REQUEST
   ────────────
   POST https://ugautodetal.ru/rest/2611/pkc4eycs2shrl0ko/im.dialog.list
   
   Headers:
     Content-Type: application/json
     Accept: application/json
     User-Agent: Python-Bitrix-Chat-Client/1.0
   
   Body:
     {
       "LIMIT": 10
     }


4. BITRIX24 PROCESSING
   ────────────────────
   Bitrix24 server receives request
   │
   ├─ Extracts from URL: user_id=2611, token=pkc4eycs2shrl0ko
   ├─ Verifies token is valid and belongs to user 2611
   ├─ Processes method: im.dialog.list with params
   └─ Generates response


5. HTTP RESPONSE
   ──────────────
   Status: 200 OK
   
   Body:
     {
       "result": [
         {
           "ID": "40",
           "TITLE": "Main Sales Channel",
           "TYPE": "open",
           "USERS": ["2611", "2612"],
           "LAST_MESSAGE_ID": "12345"
         },
         {
           "ID": "41",
           "TITLE": "Support Team",
           "TYPE": "open",
           "USERS": ["2611"],
           "LAST_MESSAGE_ID": "12346"
         }
       ]
     }


6. APPLICATION PARSING
   ────────────────────
   response = {
     "result": [...]
   }
   
   for dialog in response['result']:
       print(dialog['TITLE'])


OUTPUT
──────
Main Sales Channel
Support Team
```

---

## Error Handling Flow

```
API Call Made
    │
    ├─ Build URL
    │
    ├─ Send Request
    │   │
    │   ├─ Network Error?
    │   │   └─ Return: {"error": "Request exception"}
    │   │
    │   ├─ Timeout?
    │   │   └─ Return: {"error": "Request timeout"}
    │   │
    │   ├─ HTTP 200 OK?
    │   │   └─ Parse response JSON
    │   │
    │   └─ Other HTTP status?
    │       └─ Parse response body (may contain error)
    │
    ├─ Parse JSON Response
    │   │
    │   ├─ JSON Parse Error?
    │   │   └─ Return: {"error": "JSON decode error"}
    │   │
    │   └─ Success?
    │       └─ Return: response as-is
    │
    └─ Return to Caller
        ├─ Check result.get('error')
        ├─ Check result.get('result')
        └─ Handle accordingly
```

---

## Files & Responsibilities

| File | Responsibility | Depends On |
|------|-----------------|-----------|
| `main.py` | Orchestration, token acquisition | chrome_auth.py, auth_manager.py |
| `auth/chrome_auth.py` | Browser automation, token fetch | Selenium, Chromium |
| `auth/auth_manager.py` | Auth data loading/saving | .json files, .env |
| `api/bitrix_api.py` | REST API calls with token | requests library, .env |
| `test_rest_client.py` | API testing tool | BitrixAPI, .env |
| `verify_api_credentials.py` | Setup verification | BitrixAPI, .env |
| `.env` | Credential storage | Generated by main.py |

---

## Security Considerations

### Token Security
- ✅ Token only obtained in browser (secure session)
- ✅ Stored in .env (local only, not committed to git)
- ⚠️ Token should not be logged in console output
- ⚠️ Token should not be shared or exposed

### .env File
- ✅ Contains API credentials
- ⚠️ Should be in .gitignore
- ⚠️ Accessible only to application
- ⚠️ Should have restricted file permissions

### Recommendations
1. Add to `.gitignore`:
   ```
   .env
   auth_data_full.json
   pull_config.json
   *.pyc
   __pycache__/
   ```

2. Use separate credentials for different environments:
   ```
   .env.local (local development)
   .env.prod (production)
   ```

3. Rotate token periodically:
   ```bash
   python3 main.py  # Get fresh token
   ```

---

## Testing the System

### 1. Verify Setup
```bash
python3 verify_api_credentials.py
```

### 2. Test API Calls
```bash
python3 test_rest_client.py
```

### 3. Manual Testing
```python
from api.bitrix_api import BitrixAPI
import os
from dotenv import load_dotenv

load_dotenv()
api = BitrixAPI(
    user_id=int(os.getenv('API_USER_ID')),
    token=os.getenv('API_TOKEN')
)

# Test various methods
print(api.call_method('user.current', {}))
print(api.call_method('im.dialog.list', {'LIMIT': 5}))
```

---

## Troubleshooting Guide

### Problem: "ERROR_METHOD_NOT_FOUND"
- **Cause**: Invalid API method or wrong endpoint
- **Solution**: Verify method name, test with `user.current`

### Problem: "Unauthorized" (401)
- **Cause**: Invalid token or user_id mismatch
- **Solution**: Run `python3 main.py` to get fresh token

### Problem: "No token in .env"
- **Cause**: main.py didn't save credentials
- **Solution**: Check browser auth process, verify .env write permissions

### Problem: "JSON Parse Error"
- **Cause**: Response is not valid JSON (might be HTML error page)
- **Solution**: Verify token is valid, check server logs

---

## Next Steps

1. ✅ Run `python3 main.py` - Get token
2. ✅ Run `python3 verify_api_credentials.py` - Verify setup
3. ✅ Run `python3 test_rest_client.py` - Test API
4. 📝 Integrate BitrixAPI into UI (main_window.py)
5. 📝 Implement chat features
6. 📝 Add WebSocket for real-time updates
