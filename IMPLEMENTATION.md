# 📚 Bitrix24 Chat Application - Architecture & Implementation Guide

## 🎯 Project Overview

**Bitrix24 Chat Application** is a Python-based PyQt5 desktop client that connects to Bitrix24 via REST API. It provides a Telegram-like interface for managing chats, viewing messages, and real-time updates.

---

## 🏗️ Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Bitrix24 Instance                         │
│                 (ugautodetal.ru)                            │
└────────┬──────────────────────────────┬─────────────────────┘
         │                              │
    ┌────▼─────────┐            ┌─────▼──────────┐
    │  REST API    │            │  WebSocket     │
    │  /rest/...   │            │  /bitrix/subws │
    └────┬─────────┘            └─────┬──────────┘
         │                            │
    ┌────▼──────────────────────────┴──────────────┐
    │      Python Chat Application                  │
    │  ┌──────────────────────────────────────┐   │
    │  │  main.py (Authentication)            │   │
    │  │  • Browser automation (Selenium)     │   │
    │  │  • Token acquisition                 │   │
    │  │  • Cookie management                 │   │
    │  └──────────────────────────────────────┘   │
    │                                              │
    │  ┌──────────────────────────────────────┐   │
    │  │  run_chat.py (Launcher)              │   │
    │  │  • Token loading from .env           │   │
    │  │  • PyQt5 initialization              │   │
    │  │  • Skip auth check if pre-loaded     │   │
    │  └──────────────────────────────────────┘   │
    │                                              │
    │  ┌──────────────────────────────────────┐   │
    │  │  src/ui/ (PyQt5 UI)                  │   │
    │  │  • main_window.py                    │   │
    │  │  • widgets.py (custom components)    │   │
    │  │  • themes.py (colors & styling)      │   │
    │  └──────────────────────────────────────┘   │
    │                                              │
    │  ┌──────────────────────────────────────┐   │
    │  │  src/api/ (REST API Client)          │   │
    │  │  • bitrix_api.py                     │   │
    │  │  • models.py (data structures)       │   │
    │  └──────────────────────────────────────┘   │
    │                                              │
    │  ┌──────────────────────────────────────┐   │
    │  │  src/pull/ (Real-time Updates)       │   │
    │  │  • bitrix_pull.py (WebSocket)        │   │
    │  └──────────────────────────────────────┘   │
    └──────────────────────────────────────────────┘
```

---

## 🔑 Key Changes & Implementation

### 1. Authentication Flow (`main.py`)

**What was changed:**
- Added `import sys` (was missing)
- Added automatic `.env` file writing after token acquisition
- Added subprocess launch of chat UI (`run_chat.py`)

**How it works:**
```
1. Run: python3 main.py
2. Browser opens (Selenium automation)
3. Auto-login with saved cookies
4. Navigate to /getKey/ endpoint
5. Extract CSRF token
6. Request API token
7. Save to bitrix_token.json
8. Write to .env:
   - BITRIX_REST_TOKEN
   - BITRIX_USER_ID
   - BITRIX_CSRF_TOKEN
   - BITRIX_SITE_ID
   - BITRIX_API_URL
9. Launch run_chat.py in background
10. Keep browser open for inspection
```

**Code changes:**
```python
# After token acquisition
try:
    env_path = Path(__file__).parent / '.env'
    env_lines = []
    if env_path.exists():
        with open(env_path, 'r', encoding='utf-8') as ef:
            env_lines = ef.read().splitlines()

    entries = {
        'BITRIX_REST_TOKEN': token,
        'BITRIX_USER_ID': str(user_id),
        'BITRIX_CSRF_TOKEN': csrf_token,
        'BITRIX_SITE_ID': site_id,
        'BITRIX_API_URL': 'https://ugautodetal.ru/stream/'
    }

    # Update or append entries
    for k, v in entries.items():
        found = False
        for i, line in enumerate(env_lines):
            if line.startswith(k + "="):
                env_lines[i] = f"{k}={v}"
                found = True
                break
        if not found:
            env_lines.append(f"{k}={v}")

    with open(env_path, 'w', encoding='utf-8') as ef:
        ef.write("\n".join(env_lines))
    print(f"✓ Token written to {env_path}")
except Exception as e:
    print(f"⚠️ Failed to write .env: {e}")

# Launch chat UI
try:
    launcher = Path(__file__).parent / 'run_chat.py'
    if launcher.exists():
        subprocess.Popen([sys.executable, str(launcher)], 
                        cwd=str(Path(__file__).parent))
        print("✓ Chat UI started")
except Exception as e:
    print(f"⚠️ Failed to start chat: {e}")
```

---

### 2. Chat Launcher (`run_chat.py`)

**What was created:**
- New file to launch chat UI with pre-loaded token
- Loads credentials from `.env` using `python-dotenv`
- Sets `SKIP_AUTH_CHECK=1` environment variable

**How it works:**
```
1. Load .env file with dotenv
2. Read BITRIX_REST_TOKEN and BITRIX_USER_ID
3. Initialize BitrixAPI with credentials
4. Create QApplication
5. Instantiate TelegramChatWindow
6. Show window
7. Start event loop
```

**Usage:**
```bash
python3 run_chat.py
```

---

### 3. Main Window Token Loading (`src/ui/main_window.py`)

**What was changed:**
- Added `SKIP_AUTH_CHECK` environment variable check
- Added multiple token source fallbacks:
  1. `.env` file (primary)
  2. Environment variables
  3. `bitrix_token.json` (backup)

**How it works:**
```python
def check_auth_data(self):
    """Skip auth if token pre-loaded from launcher"""
    if os.getenv('SKIP_AUTH_CHECK') == '1':
        print("✅ Skipping auth check (token pre-loaded)")
        return

def load_auth_data(self):
    """Load with multiple fallbacks"""
    # 1. Read .env file
    # 2. Check env vars BITRIX_REST_TOKEN / BITRIX_USER_ID
    # 3. Fall back to bitrix_token.json
    # 4. Provide final diagnostic output
```

---

### 4. API URL Format (`src/api/bitrix_api.py`)

**What was changed:**
- Updated print statement from `<method>` to `user.current` (a real method)
- Shows actual API call format

**Before:**
```
API base URL: https://ugautodetal.ru/rest/2611/eu3rd5op69723b59.../<method>
```

**After:**
```
API base URL: https://ugautodetal.ru/rest/2611/eu3rd5op69723b59...user.current
```

**API URL Format Explained:**
```
https://ugautodetal.ru/rest/{user_id}/{token}/{method}
                                  │         │        │
                    User ID (2611) │         │        │
               Token (eu3rd5op69...) │        │
              Method (e.g. user.current)     │
```

---

## 📁 File Structure

```
/Users/aldeev/projects/ff/chatBitrix/
├── main.py                          # Authentication (Selenium)
├── run_chat.py                      # Chat launcher
├── verify_setup.py                  # Setup verification
├── .env                             # Configuration (token stored here)
├── bitrix_token.json               # Backup token file
├── requirements.txt                # Python dependencies
├── cookies.pkl                     # Saved browser cookies
│
├── src/
│   ├── ui/                         # PyQt5 User Interface
│   │   ├── main_window.py          # Main chat window
│   │   ├── widgets.py              # Custom widgets
│   │   ├── themes.py               # Colors & styling
│   │   ├── message_bubble.py       # Message display
│   │   ├── chat_list_item.py       # Chat list items
│   │   └── __init__.py
│   │
│   ├── api/                        # REST API Client
│   │   ├── bitrix_api.py           # API client
│   │   ├── models.py               # Data models
│   │   └── __init__.py
│   │
│   ├── auth/                       # Authentication
│   │   ├── chrome_auth.py          # Selenium browser automation
│   │   ├── auth_manager.py         # Auth flow management
│   │   └── env_handler.py          # .env file handling
│   │
│   └── pull/                       # Real-time Updates
│       ├── bitrix_pull.py          # WebSocket Pull client
│       └── __init__.py
│
└── docs/                           # Documentation
    ├── API.md
    ├── ARCHITECTURE.md
    └── ...
```

---

## 🔐 Token Management

### Token Acquisition Flow

```
1. User runs: python3 main.py
2. Selenium opens browser
3. Auto-login with cookies.pkl
4. Navigate to https://ugautodetal.ru/?login=yes
5. Extract CSRF token from page
6. Call: /bitrix/services/main/ajax.php?action=me:base.api.user.getTokenApi
7. Receive token: eu3rd5op69723b59 (16 chars)
8. Extract user_id: 2611
9. Save to:
   - bitrix_token.json (JSON backup)
   - .env (for app)
10. Launch chat UI with token
```

### Token Storage

**Primary (.env):**
```env
BITRIX_REST_TOKEN=eu3rd5op69723b59
BITRIX_USER_ID=2611
BITRIX_CSRF_TOKEN=418cc92083b4b92729c12d85375ee9b4
BITRIX_SITE_ID=ap
BITRIX_API_URL=https://ugautodetal.ru/stream/
```

**Backup (bitrix_token.json):**
```json
{
  "token": "eu3rd5op69723b59",
  "user_id": 2611,
  "csrf_token": "418cc92083b4b92729c12d85375ee9b4",
  "site_id": "ap",
  "timestamp": 1768887340.4,
  "date": "2026-01-20 08:35:40",
  "url": "https://ugautodetal.ru/stream/"
}
```

---

## 🔌 REST API Integration

### BitrixAPI Client

**Initialization:**
```python
from api.bitrix_api import BitrixAPI
import os
from dotenv import load_dotenv

load_dotenv()
api = BitrixAPI(
    user_id=int(os.getenv('BITRIX_USER_ID')),
    token=os.getenv('BITRIX_REST_TOKEN'),
    base_domain="https://ugautodetal.ru"
)
```

**API URL Format:**
```
https://ugautodetal.ru/rest/{user_id}/{token}/{method}

Examples:
- https://ugautodetal.ru/rest/2611/eu3rd5op69723b59/user.current
- https://ugautodetal.ru/rest/2611/eu3rd5op69723b59/im.dialog.list
- https://ugautodetal.ru/rest/2611/eu3rd5op69723b59/im.message.add
```

**Method Calls:**
```python
# Get current user
current_user = api.call_method('user.current')

# Get dialog list
dialogs = api.call_method('im.dialog.list', {'LIMIT': 10})

# Send message
api.call_method('im.message.add', {
    'DIALOG_ID': 'channel_123',
    'MESSAGE': 'Hello, world!'
})
```

---

## 🎨 UI Architecture

### Component Hierarchy

```
QMainWindow (TelegramChatWindow)
├── Sidebar (380px width)
│   ├── Header
│   │   ├── Title "Business Chat"
│   │   ├── Buttons (New Chat, Debug, Menu)
│   │   └── Colors: COLORS['TELEGRAM_BLUE']
│   │
│   └── Chat List
│       ├── Search bar
│       ├── QScrollArea
│       └── ChatListItem(s)
│           ├── Avatar (48x48 circle)
│           ├── Title
│           ├── Preview text
│           └── Time
│
└── Main Chat Area (1:1 ratio)
    ├── Chat Header
    │   ├── Back button
    │   ├── Chat title
    │   ├── Search button
    │   └── Menu button
    │
    ├── Messages Area
    │   ├── QScrollArea
    │   └── MessageBubble(s)
    │       ├── Sender name
    │       ├── Message text
    │       ├── File attachments
    │       ├── Time
    │       └── Status (✓✓)
    │
    └── Input Area
        ├── Attachment button
        ├── Message input
        └── Send button
```

### Color System

**COLORS Dictionary (src/ui/themes.py):**
```python
COLORS = {
    'BACKGROUND_LIGHT': '#f1f3f4',
    'CHAT_BG_LIGHT': '#ffffff',
    'SIDEBAR_BG_LIGHT': '#ffffff',
    'TELEGRAM_BLUE': '#3390ec',
    'TELEGRAM_BLUE_DARK': '#2b7bc2',
    'BORDER_LIGHT': '#e7e8ec',
    'TEXT_LIGHT': '#000000',
    'TEXT_SECONDARY_LIGHT': '#707579',
    # ... (light mode colors)
}
```

All UI components reference COLORS dictionary instead of hard-coded hex values.

---

## 📦 Dependencies

### Python Packages

| Package | Version | Purpose |
|---------|---------|---------|
| `selenium` | >=4.15.0 | Browser automation for token acquisition |
| `requests` | >=2.31.0 | HTTP requests for REST API calls |
| `websocket-client` | >=1.6.0 | WebSocket for real-time updates |
| `PyQt5` | >=5.15.9 | Desktop UI framework |
| `PyQt5-sip` | >=12.12.0 | PyQt5 C extension bindings |
| `python-dotenv` | >=1.0.0 | Load .env configuration files |

**Install:**
```bash
pip install -r requirements.txt
```

---

## 🚀 Usage Workflows

### Workflow 1: First-time Setup

```bash
# 1. Get token via browser
cd /Users/aldeev/projects/ff/chatBitrix
python3 main.py
# → Browser opens
# → Auto-login
# → Token saved to .env
# → Chat UI auto-starts

# 2. Keep browser open to inspect
# 3. Press Ctrl+C to close
```

### Workflow 2: Normal Usage (Token exists)

```bash
cd /Users/aldeev/projects/ff/chatBitrix
python3 run_chat.py
# → Token loaded from .env
# → Chat UI starts immediately
# → Message history loads
# → Real-time updates enabled
```

### Workflow 3: Setup Verification

```bash
cd /Users/aldeev/projects/ff/chatBitrix
python3 verify_setup.py
# → Checks .env file
# → Verifies token format
# → Tests BitrixAPI initialization
# → Confirms PyQt5 environment
# → Reports overall status
```

### Workflow 4: Re-authentication

```bash
# If token expires or needs refresh
python3 main.py
# Same as Workflow 1
```

---

## 🔍 Debugging

### View Current Token
```bash
grep "BITRIX_REST_TOKEN\|BITRIX_USER_ID" .env
```

### Test API Connection
```bash
python3 verify_setup.py
```

### Check .env File
```bash
cat .env | grep BITRIX
```

### View Backup Token
```bash
cat bitrix_token.json | python3 -m json.tool
```

---

## ✅ Testing Checklist

- [x] `import sys` added to `main.py`
- [x] Token written to `.env` after acquisition
- [x] `.env` file has all required keys
- [x] Chat UI launches automatically
- [x] Token loads from `.env` in `run_chat.py`
- [x] API URL shows real method (`user.current`)
- [x] No syntax errors in all Python files
- [x] All imports working correctly
- [x] BitrixAPI initializes successfully
- [x] PyQt5 environment ready

---

## 📊 Current Status

**Token Configuration:**
- ✅ Token: `eu3rd5op69723b59`
- ✅ User ID: `2611`
- ✅ Stored in: `.env` and `bitrix_token.json`
- ✅ API Base URL: `https://ugautodetal.ru/rest/2611/eu3rd5op69723b59/user.current`

**Application Status:**
- ✅ Authentication working
- ✅ Token persistence implemented
- ✅ Chat UI launcher created
- ✅ All components tested
- ✅ Documentation complete

**Ready to Use:**
```bash
python3 run_chat.py  # Start chat
# or
python3 main.py      # Get new token and start
```

---

## 📞 Summary of Changes

### Files Modified:
1. **main.py** - Added token writing and auto-launcher
2. **src/ui/main_window.py** - Added fallback token loading
3. **src/api/bitrix_api.py** - Updated API URL format display

### Files Created:
1. **run_chat.py** - Chat UI launcher
2. **verify_setup.py** - Setup verification script
3. **USAGE_GUIDE.md** - User guide
4. **IMPLEMENTATION.md** - This file

### Files Modified (Dependencies):
1. **requirements.txt** - Added `python-dotenv`
2. **.env** - Token and auth data

---

**Project Status**: ✅ **COMPLETE & TESTED**
**Last Updated**: 2026-01-20 09:15 UTC
