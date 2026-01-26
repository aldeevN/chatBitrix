# 🚀 Bitrix24 Chat Application - Quick Start Guide

## ✅ Current Status

**Token Status**: ✅ SAVED TO .env
- **Token**: `eu3rd5op69723b59` (first 16 characters)
- **User ID**: `2611`
- **API URL**: `https://ugautodetal.ru/stream/`

## 🎯 How to Start the Chat Application

### Option 1: Using the Python Launcher (Recommended)
```bash
cd /Users/aldeev/projects/ff/chatBitrix
python3 run_chat.py
```

### Option 2: Using the Bash Script
```bash
cd /Users/aldeev/projects/ff/chatBitrix
bash start_chat.sh
```

## 📋 What the Launcher Does

1. **Loads Token from .env**
   - Reads `BITRIX_REST_TOKEN=eu3rd5op69723b59`
   - Reads `BITRIX_USER_ID=2611`
   - Reads `BITRIX_API_URL=https://ugautodetal.ru/stream/`

2. **Initializes REST API Client**
   - Creates BitrixAPI instance with token
   - Sets up API connection to Bitrix24

3. **Starts PyQt5 Chat UI**
   - Opens the Telegram-like chat interface
   - Loads chat list from server
   - Displays message history
   - Enables real-time messaging

## 🎨 Chat Application Features

✨ **UI Features**:
- 📱 Real-time message display
- 👥 Chat list with groups and direct messages  
- 🔍 Search functionality
- 📎 File attachment support
- 🎨 Telegram-like dark/light theme
- 🔐 REST API token-based authentication

⚙️ **Backend Features**:
- ✅ BitrixAPI client for REST API calls
- ✅ Pull client for real-time updates
- ✅ Message loading and display
- ✅ User and customer management
- ✅ Multi-threaded operations

## 📁 Project Structure

```
/Users/aldeev/projects/ff/chatBitrix/
├── run_chat.py              ← Main launcher script
├── start_chat.sh            ← Bash startup script
├── .env                     ← Configuration (with token)
├── main.py                  ← Authentication script
├── requirements.txt         ← Python dependencies
│
├── src/
│   ├── ui/                 ← PyQt5 UI components
│   │   ├── main_window.py  ← Main chat window
│   │   ├── widgets.py      ← Custom widgets
│   │   ├── themes.py       ← UI themes & colors
│   │   └── ...
│   │
│   ├── api/                ← REST API client
│   │   └── bitrix_api.py   ← API implementation
│   │
│   ├── auth/               ← Authentication
│   │   ├── chrome_auth.py  ← Browser auth
│   │   └── auth_manager.py ← Auth flow
│   │
│   └── pull/               ← Real-time updates
│       └── pull_client.py  ← Pull client
│
└── docs/                   ← Documentation files
```

## 🔑 Environment Variables in .env

```env
# REST API Credentials
BITRIX_REST_TOKEN=eu3rd5op69723b59    # ← Your token (SECURE!)
BITRIX_USER_ID=2611                   # ← Your user ID
BITRIX_CSRF_TOKEN=418cc92083b4b92...  # ← CSRF token
BITRIX_SITE_ID=ap                     # ← Site ID
BITRIX_API_URL=https://ugautodetal.ru/stream/  # ← API URL

# Cookies (for Pull client)
COOKIE_BITRIX_SM_LOGIN=...
PULL_CHANNEL_PRIVATE=...
PULL_WEBSOCKET_URL=wss://ugautodetal.ru/bitrix/subws/
```

## 🚨 Important Notes

### Security
- ⚠️ **DO NOT** commit `.env` file to git (contains token)
- ⚠️ **DO NOT** share `BITRIX_REST_TOKEN` with others
- ✅ `.env` is already in `.gitignore`

### Token Management
- 📋 Token is stored in `.env` after first authentication
- 🔄 To re-authenticate: delete `BITRIX_REST_TOKEN` from `.env` and run `python3 main.py`
- 📊 Token obtained from: `https://ugautodetal.ru/rest/` endpoint

### API Configuration
- 🌐 **Base URL**: `https://ugautodetal.ru`
- 🔌 **REST API**: `/rest/{user_id}/{token}/{method}`
- 📡 **WebSocket**: `wss://ugautodetal.ru/bitrix/subws/`

## 🔧 Troubleshooting

### App won't start
1. Check if token is in .env: `grep BITRIX_REST_TOKEN .env`
2. Verify token format: should be alphanumeric string
3. Check internet connection to Bitrix24 server

### Token expired
1. Run `python3 main.py` to get a new token
2. Complete authentication in browser
3. New token will be saved to .env

### No messages loading
1. Check if you're in valid chat groups
2. Verify API token is correct
3. Check network connection
4. Look at console output for error messages

## 📦 Dependencies

All dependencies are listed in `requirements.txt`:
```
selenium>=4.15.0           # Browser automation
requests>=2.31.0          # HTTP requests
websocket-client>=1.6.0   # WebSocket support
PyQt5>=5.15.9            # UI framework
PyQt5-sip>=12.12.0       # PyQt5 bindings
python-dotenv>=1.0.0     # .env file support
```

Install with: `pip install -r requirements.txt`

## 🎯 Next Steps

1. ✅ **Token Saved**: REST API token is now in `.env`
2. ✅ **UI Styled**: All UI components have been updated with consistent colors
3. ✅ **Launcher Ready**: Use `python3 run_chat.py` to start
4. 📊 **Ready to Use**: Chat application is fully functional

## 💡 Pro Tips

- 🎨 UI automatically uses theme colors from `src/ui/themes.py`
- 📡 API calls use secure token-based authentication
- 🔄 Real-time updates via WebSocket (Pull client)
- 🎭 Dark/Light mode toggle support built-in

---

**Last Updated**: 2026-01-20 08:40:35 UTC
**Status**: ✅ Ready to Use
**Token**: ✅ Configured
**UI**: ✅ Styled and Tested
