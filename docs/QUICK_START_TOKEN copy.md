# Quick Start - Get Token & Use REST API

## TL;DR - 3 Steps

### Step 1: Get Token (2 minutes)
```bash
python3 main.py
```
- Opens browser
- Auto-logs in
- Fetches and saves token to `.env`

### Step 2: Verify Setup (1 minute)
```bash
python3 verify_api_credentials.py
```
- Checks token is in `.env`
- Tests BitrixAPI initialization
- Verifies API connectivity

### Step 3: Use the API (Any time)
```python
from api.bitrix_api import BitrixAPI
import os
from dotenv import load_dotenv

load_dotenv()
api = BitrixAPI(
    user_id=int(os.getenv('API_USER_ID')),
    token=os.getenv('API_TOKEN')
)

# Get chat dialogs
dialogs = api.call_method('im.dialog.list', {'LIMIT': 10})
print(dialogs)
```

---

## What BitrixAPI Needs

| Parameter | Value | Source |
|-----------|-------|--------|
| `user_id` | `2611` | `.env` (API_USER_ID) |
| `token` | `pkc4eycs2shrl0ko` | `.env` (API_TOKEN) |

**Both obtained by running**: `python3 main.py`

---

## API URL Format

```
https://ugautodetal.ru/rest/{user_id}/{token}/{method}
https://ugautodetal.ru/rest/2611/pkc4eycs2shrl0ko/im.dialog.list
```

---

## Common API Methods

```python
# Get current user
api.call_method('user.current', {})

# Get chat dialogs
api.call_method('im.dialog.list', {'LIMIT': 10})

# Get messages
api.call_method('im.message.list', {'LIMIT': 20})

# Get users in IM
api.call_method('im.user.list', {})

# Batch call
api.call_method('batch', {
    'halt': 0,
    'cmd': {
        'user': 'user.current',
        'dialogs': 'im.dialog.list?LIMIT=5'
    }
})
```

---

## Documentation

- **BITRIXAPI_REQUIREMENTS.md** - Detailed requirements and examples
- **SYSTEM_ARCHITECTURE.md** - Complete system design and flow
- **CHAT_AND_REST_GUIDE.md** - Usage guide and troubleshooting

---

## Files Involved

| File | Purpose |
|------|---------|
| `main.py` | Gets token via browser |
| `auth/chrome_auth.py` | Browser automation |
| `api/bitrix_api.py` | REST API client |
| `test_rest_client.py` | API testing tool |
| `verify_api_credentials.py` | Setup verification |
| `.env` | Token storage |

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| No token in .env | Run `python3 main.py` |
| "ERROR_METHOD_NOT_FOUND" | Check method name, use `user.current` to test |
| "Unauthorized" | Token expired, run `python3 main.py` again |
| API returns error | Check .env has API_TOKEN and API_USER_ID |

---

**Status**: ✅ BitrixAPI is ready for REST API access with token & user_id
