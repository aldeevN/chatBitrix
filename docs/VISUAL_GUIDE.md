# Visual Guide: Token-Based Authentication

## URL Construction Visualization

```
┌─────────────────────────────────────────────────────────────────┐
│ BITRIX24 REST API TOKEN-BASED AUTHENTICATION                    │
└─────────────────────────────────────────────────────────────────┘

┌─ PARTS OF THE URL ────────────────────────────────────────────┐
│                                                                │
│  https://ugautodetal.ru/rest/1/abc123xyz.../method            │
│  └────┬────┘└──┬──┘└┬─┘└─┬─┘└─────┬─────┘└────┬────┘         │
│     scheme  domain path user token          method           │
│            :port             (API)                           │
│                                                                │
└────────────────────────────────────────────────────────────────┘

┌─ BUILDING THE URL STEP BY STEP ───────────────────────────────┐
│                                                                │
│  Base Domain:  https://ugautodetal.ru                        │
│  REST Path:    /rest                                          │
│  User ID:      /1                                             │
│  Token:        /abc123xyz...                                  │
│  Method:       /uad.shop.api.chat.getMessages               │
│  ─────────────────────────────────────────────               │
│  COMPLETE:     https://ugautodetal.ru/rest/1/abc123xyz.../  │
│                uad.shop.api.chat.getMessages                │
│                                                                │
└────────────────────────────────────────────────────────────────┘

┌─ DATA FLOW ────────────────────────────────────────────────────┐
│                                                                │
│  Request:                                                      │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ POST /rest/1/token/method                              │ │
│  │ Content-Type: application/json                         │ │
│  │ User-Agent: Python-Bitrix-Chat-Client/1.0             │ │
│  │                                                         │ │
│  │ {parameters}                                           │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                                │
│  Response:                                                     │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ {                                                       │ │
│  │   "result": {...data...},                             │ │
│  │   "error": null                                        │ │
│  │ }                                                       │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

## Component Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     MAIN APPLICATION                         │
│                        (main.py)                             │
└────────────┬─────────────────────────┬──────────────────────┘
             │                         │
             ▼                         ▼
    ┌─────────────────┐      ┌──────────────────────┐
    │ Auth Manager    │      │ Bitrix API Client    │
    │ (auth_manager.  │      │ (bitrix_api.py)      │
    │  py)            │      │                      │
    │                 │      │ Methods:             │
    │ get_or_create_  │      │ - get_groups()       │
    │ token()         │      │ - get_messages()     │
    └────────┬────────┘      │ - add_message()      │
             │               │ - get_customers()    │
             ▼               └──────────┬───────────┘
    ┌─────────────────────────┐         │
    │ Token Manager           │         │
    │ (bitrix_token_manager   │         │
    │ .py)                    │         │
    │                         │         │
    │ - get_or_create()       │         │
    │ - load_saved()          │         │
    │ - test_token()          │         │
    │ - save_token()          │         │
    └────────┬────────────────┘         │
             │                          │
    ┌────────┴──────────┬───────────────┴──────────┐
    ▼                   ▼                          ▼
[API Call]      [token_info.json]      [Bitrix24 Server]
Create/Get      Save/Load Token         Process Request
Token            File                   Return Data
```

## Authentication Sequence Diagram

```
┌────────────┐     ┌────────────┐     ┌──────────┐     ┌──────────┐
│    App     │     │   Auth     │     │  Token   │     │ Bitrix   │
│           │     │  Manager   │     │  Manager │     │  Server  │
└─────┬──────┘     └─────┬──────┘     └────┬─────┘     └────┬─────┘
      │                  │                  │               │
      │  start()         │                  │               │
      ├────────────────>│                  │               │
      │                  │                  │               │
      │                  │  get_or_create() │               │
      │                  ├────────────────>│               │
      │                  │                  │               │
      │                  │                  │ load_saved()  │
      │                  │                  ├──────┐        │
      │                  │                  |<─────┘        │
      │                  │                  │               │
      │                  │                  │ not found     │
      │                  │                  │               │
      │                  │                  │               │
      │                  │                  │ create_token()
      │                  │                  ├──────────────>│
      │                  │                  │               │
      │                  │                  │<──token───────┤
      │                  │                  │               │
      │                  │                  │ save_token()  │
      │                  │                  ├──────┐        │
      │                  │                  |<─────┘        │
      │                  │                  │               │
      │                  │                  │ test_token()  │
      │                  │                  ├──────────────>│
      │                  │                  │               │
      │                  │                  │<──valid───────┤
      │                  │ token ready      │               │
      │                  |<────────────────┤               │
      │  initialized     │                  │               │
      |<─────────────────┤                  │               │
      │                  │                  │               │
      │  api_call()      │                  │               │
      ├────────────────────────────────────────────────────>│
      │                  │                  │               │
      │  result          │                  │               │
      |<────────────────────────────────────────────────────┤
      │                  │                  │               │
```

## Data Storage Visualization

```
┌─────────────────────────────────────────────────────────┐
│ File System Storage                                     │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  .env                                                   │
│  ├─ BITRIX_USER_ID=1                                   │
│  ├─ BITRIX_DOMAIN=ugautodetal.ru                       │
│  └─ ... other env vars                                │
│                                                         │
│  auth_data_full.json                                   │
│  ├─ cookies: {...}                                     │
│  ├─ local_storage: {...}                               │
│  ├─ session_storage: {...}                             │
│  └─ user_id: 1                                         │
│                                                         │
│  token_info.json ✨ (NEW - Token Persistence)          │
│  ├─ token: "generated_token_string"                    │
│  ├─ created_at: "2026-01-16T10:30:45.123456"          │
│  ├─ expires: "2027-01-16"                              │
│  ├─ user_id: 1                                         │
│  └─ base_url: "https://ugautodetal.ru/rest"           │
│                                                         │
│  pull_config.json                                      │
│  ├─ channels: {...}                                    │
│  ├─ server: {...}                                      │
│  └─ ... pull config                                    │
│                                                         │
│  cookies.pkl                                           │
│  └─ Pickled browser cookies                            │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## API Method URL Examples

```
┌────────────────────────────────────────────────────────────┐
│ METHOD NAME              │ FULL API URL                     │
├────────────────────────────────────────────────────────────┤
│ get_groups()             │ .../rest/1/token/               │
│                          │ uad.shop.api.chat.getGroups     │
├────────────────────────────────────────────────────────────┤
│ get_messages(gid)        │ .../rest/1/token/               │
│                          │ uad.shop.api.chat.getMessages   │
├────────────────────────────────────────────────────────────┤
│ add_message(g, msg)      │ .../rest/1/token/               │
│                          │ uad.shop.api.chat.addMessage    │
├────────────────────────────────────────────────────────────┤
│ get_notifications()      │ .../rest/1/token/               │
│                          │ uad.shop.api.chat.               │
│                          │ getNotifications                │
├────────────────────────────────────────────────────────────┤
│ get_customers()          │ .../rest/1/token/               │
│                          │ uad.shop.api.profile.            │
│                          │ listCustomers                   │
├────────────────────────────────────────────────────────────┤
│ get_current_profile()    │ .../rest/1/token/profile        │
├────────────────────────────────────────────────────────────┤
│ create_group(t,msg,uids) │ .../rest/1/token/               │
│                          │ uad.shop.api.chat.createGroup   │
└────────────────────────────────────────────────────────────┘

All URLs follow format:
https://ugautodetal.ru/rest/{user_id}/{token}/{method}
```

## Code Flow Visualization

```
┌─────────────────────────────────────────────────────────┐
│ Application Startup Flow                                │
└─────────────────────────────────────────────────────────┘

     main()
       │
       ├─> Load auth data (auth_data_full.json)
       │   └─> Extract user_id ✓
       │
       ├─> get_or_create_token(auth_data)
       │   ├─> Create BitrixTokenManager
       │   │
       │   ├─> Load saved token?
       │   │   ├─ YES → Use saved token
       │   │   │         └─> Test token ✓
       │   │   └─ NO → Continue
       │   │
       │   ├─> Create new token
       │   │   ├─> Call API: base.api.user.createTokenApi
       │   │   ├─> Parse response
       │   │   └─> Save to token_info.json ✓
       │   │
       │   ├─> Test token
       │   │   └─> Call API: base.api.user.getCurrentTokenInfo ✓
       │   │
       │   └─> Return (success, token, message)
       │
       ├─> Initialize BitrixAPI(user_id, token)
       │   └─> URL: https://ugautodetal.ru/rest/{user_id}/{token}/
       │
       ├─> Test API functionality
       │   ├─> api.get_groups() ✓
       │   ├─> api.get_messages() ✓
       │   └─> api.get_customers() ✓
       │
       └─> Start Chat Application ✓
```

## Before vs After

```
┌─────────────────────────────────────┬─────────────────────────────────────┐
│ BEFORE (Webhook)                    │ AFTER (Token REST API)              │
├─────────────────────────────────────┼─────────────────────────────────────┤
│                                     │                                     │
│ URL:                                │ URL:                                │
│ /webhook/.../method                 │ /rest/{user_id}/{token}/method      │
│                                     │                                     │
│ No token management                 │ Automatic token management          │
│ No token persistence                │ Token saved to file                 │
│ Manual webhook setup                │ REST API standard                   │
│ Limited error handling              │ Comprehensive error handling        │
│ No token validation                 │ Token validation before use         │
│ Hard-coded auth                     │ Flexible token-based auth           │
│                                     │                                     │
└─────────────────────────────────────┴─────────────────────────────────────┘
```

---

**Visual Guide Complete** ✓
All components properly illustrated and documented.
