# Authentication & Token Data Flow

## Complete Authentication Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     START APPLICATION                           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
        ┌────────────────────────────────────────┐
        │  Load Captured Auth Data               │
        │  (auth_data_full.json)                 │
        │  - Cookies from Chromium               │
        │  - LocalStorage                        │
        │  - SessionStorage                      │
        │  - Extract user_id                     │
        └────────────────┬───────────────────────┘
                         │
                         ▼
        ┌────────────────────────────────────────┐
        │  Call get_or_create_token(auth_data)   │
        │  (auth/auth_manager.py)                │
        └────────────────┬───────────────────────┘
                         │
                         ▼
        ┌────────────────────────────────────────┐
        │  Create BitrixTokenManager              │
        │  - user_id: extracted from auth_data   │
        │  - base_url: https://ugautodetal.ru/rest
        └────────────────┬───────────────────────┘
                         │
         ┌───────────────┴───────────────┐
         │                               │
         ▼                               ▼
    SAVED TOKEN?                   NO SAVED TOKEN
    (token_info.json)                   │
         │                              ▼
         │                  ┌──────────────────────────┐
         │                  │  Create New Token        │
         │                  │  via API call to:        │
         │                  │  base.api.user.          │
         │                  │  createTokenApi          │
         │                  │                          │
         │                  │  URL: /rest/1/{temp}/... │
         │                  └──────────────┬───────────┘
         │                                 │
         │                                 ▼
         │                  ┌──────────────────────────┐
         │                  │  Get New Token from      │
         │                  │  API Response            │
         │                  │  result.token            │
         │                  └──────────────┬───────────┘
         │                                 │
         ▼                                 ▼
    Test Token            ┌─────────────────────────┐
    │                     │ Save to token_info.json │
    │                     │ {                       │
    │                     │   "token": "...",       │
    │                     │   "user_id": 1,         │
    │                     │   "created_at": "...",  │
    │                     │   ...                   │
    │                     │ }                       │
    │                     └──────────┬──────────────┘
    │                                │
    └────────────────┬───────────────┘
                     │
                     ▼
    ┌────────────────────────────────────────┐
    │  Validate Token                        │
    │  Call: base.api.user.                  │
    │        getCurrentTokenInfo             │
    │  URL: /rest/{user_id}/{token}/...      │
    └────────────────┬───────────────────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
         ▼ SUCCESS               ▼ FAILED
    Return Token          Error - Retry/Create
         │                       │
         └───────────┬───────────┘
                     │
                     ▼
    ┌────────────────────────────────────────┐
    │  Initialize BitrixAPI                  │
    │  api = BitrixAPI(                      │
    │    user_id=1,                          │
    │    token="abc123xyz..."                │
    │  )                                     │
    └────────────────┬───────────────────────┘
                     │
                     ▼
    ┌────────────────────────────────────────┐
    │  All API Requests Use URL Format:      │
    │  https://ugautodetal.ru/rest/          │
    │    {user_id}/{token}/{method}          │
    │                                        │
    │  Example:                              │
    │  POST .../rest/1/abc123.../             │
    │      uad.shop.api.chat.getMessages    │
    └────────────────┬───────────────────────┘
                     │
                     ▼
    ┌────────────────────────────────────────┐
    │  Start Chat Application                │
    │  All requests authenticated with       │
    │  user_id and token in URL              │
    └────────────────────────────────────────┘
```

## Data Structures

### Auth Data (from captured browser)
```python
auth_data = {
    'user_id': 1,
    'cookies': {
        'UAD_AVATAR': '1',
        'BITRIX_SM_UIDH': '...',
        'bitrix_sessid': '...',
        # ... other cookies
    },
    'local_storage': {
        'bx-pull-1-bx-pull-config': {...},
        # ... other storage items
    },
    'session_storage': {...},
    'pull_config': {...}
}
```

### Token Info (saved file)
```python
token_info = {
    'token': 'generated_api_token_string',
    'created_at': '2026-01-16T10:30:45.123456',
    'name': 'Python-Chat-Client-20260116-103045',
    'expires': '2027-01-16',
    'user_id': 1,
    'base_url': 'https://ugautodetal.ru/rest'
}
```

## API Request Construction

### Step 1: Setup
```
base_domain: https://ugautodetal.ru
rest_path: /rest
user_id: 1
token: abc123xyz...
method: uad.shop.api.chat.getMessages
```

### Step 2: Build URL
```
url = base_domain + rest_path + "/" + user_id + "/" + token + "/" + method
url = https://ugautodetal.ru/rest/1/abc123xyz.../uad.shop.api.chat.getMessages
```

### Step 3: Make Request
```
POST https://ugautodetal.ru/rest/1/abc123xyz.../uad.shop.api.chat.getMessages
Content-Type: application/json
User-Agent: Python-Bitrix-Chat-Client/1.0

{"group": 5}
```

### Step 4: Handle Response
```python
response = {
    "result": [...],
    "error": null  # or error message
}
```

## Token Lifecycle

### Creation Flow
```
1. App starts
2. Check for saved token (token_info.json)
3. If not found:
   a. Call API: base.api.user.createTokenApi
   b. Get token from response
   c. Save to token_info.json
4. Validate token works
5. Use for all requests
```

### Reuse Flow
```
1. App starts
2. Load token from token_info.json
3. Validate token still works
4. Use for all requests
5. If validation fails:
   a. Delete token_info.json
   b. Create new token
   c. Save and use
```

## URL Examples

### Token Creation (before token exists)
```
Request: POST https://ugautodetal.ru/rest/1/{initial_token}/base.api.user.createTokenApi
Result: {"result": {"token": "new_token"}}
```

### Token Validation
```
Request: POST https://ugautodetal.ru/rest/1/abc123xyz.../base.api.user.getCurrentTokenInfo
Result: {"result": {"name": "token_name", "expires": "2027-01-16"}}
```

### Normal API Call
```
Request: POST https://ugautodetal.ru/rest/1/abc123xyz.../uad.shop.api.chat.getGroups
Body: {}
Result: {"result": [{"id": 1, "title": "Group 1"}, ...]}
```

## Error Handling

### Token Invalid
```
Response: {"error": "Invalid token"}
Action: Delete token_info.json and create new token
```

### Token Expired
```
Response: {"error": "Token expired"}
Action: Delete token_info.json and create new token
```

### User Not Authorized
```
Response: {"error": "User not authorized"}
Action: Re-authenticate with browser
```

## Files Involved

```
/.env                          - Environment variables
/auth_data_full.json          - Captured auth data from browser
/token_info.json              - Saved API token
/pull_config.json             - Bitrix Pull config
/cookies.pkl                  - Pickled cookies for browser

/auth/auth_manager.py         - Orchestrates authentication
/auth/bitrix_token_manager.py - Manages tokens
/api/bitrix_api.py            - Makes API requests
/main.py                      - Entry point
```

## Summary

1. **Load** auth data from captured files
2. **Get/Create** API token using Bitrix API
3. **Save** token for future use
4. **Initialize** API client with user_id and token
5. **Use** for all authenticated API requests
6. **Reuse** saved token on subsequent runs
