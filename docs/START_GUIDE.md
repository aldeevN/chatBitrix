# 🚀 Smart Chat Startup Guide

## Quick Start

### Start Chat (Auto-Detection Mode)
```bash
python3 start.py
```

This is the **recommended way** to start the chat application. It intelligently:
- ✅ Checks if `BITRIX_REST_TOKEN` and `BITRIX_USER_ID` exist in `.env`
- ✅ If **both exist**: Starts chat immediately
- ✅ If **missing**: Opens Chromium for authentication automatically

---

## How It Works

### 📊 Startup Decision Tree

```
python3 start.py
    │
    ├─ Check .env for credentials
    │
    ├─ BOTH FOUND (Token + User ID)?
    │   │
    │   ├─ YES → Start Chat immediately ✅
    │   │         └─ run_chat.py launches PyQt5 UI
    │   │
    │   └─ NO → Open Chromium for Auth 🔐
    │           ├─ main.py opens browser
    │           ├─ User logs in to Bitrix24
    │           ├─ Token captured automatically
    │           ├─ Saved to .env
    │           └─ Chat starts automatically
```

---

## Usage Scenarios

### Scenario 1: First Time (No Credentials)
```bash
$ python3 start.py

🚀 BITRIX24 CHAT - SMART STARTUP
═════════════════════════════════════

🔍 Checking credentials in .env...
   ❌ BITRIX_REST_TOKEN not found or empty
   ❌ BITRIX_USER_ID not found or empty

   🔐 Missing credentials - opening browser authentication...

═════════════════════════════════════
🔐 CREDENTIALS MISSING - OPENING CHROMIUM FOR AUTHENTICATION
═════════════════════════════════════

   📱 Chromium will open automatically...
   1️⃣  Log in to Bitrix24
   2️⃣  System will capture authentication data
   3️⃣  Credentials will be saved to .env
   4️⃣  Chat will start automatically
```

→ Browser opens → Login → Token saved → Chat starts automatically

---

### Scenario 2: Token Already Saved (Typical Usage)
```bash
$ python3 start.py

🚀 BITRIX24 CHAT - SMART STARTUP
═════════════════════════════════════

🔍 Checking credentials in .env...
   ✅ Token found: eu3rd5op69723b59...
   ✅ User ID found: 2611

   🎯 Both credentials present - starting chat...

═════════════════════════════════════
✅ CREDENTIALS LOADED - STARTING CHAT
═════════════════════════════════════
```

→ Chat starts immediately (no browser needed)

---

### Scenario 3: Manual Authentication (Token Expired)
```bash
python3 main.py
```

This opens the browser directly for re-authentication without checking credentials.

---

### Scenario 4: Chat Only (Token Already Saved)
```bash
python3 run_chat.py
```

Directly start chat with credentials from `.env`. Fails if credentials are missing.

---

## 🔧 Configuration Files

### `.env` (Primary Configuration)
Contains all credentials needed to start chat:
```env
BITRIX_REST_TOKEN=eu3rd5op69723b59      # API Token
BITRIX_USER_ID=2611                     # Your user ID
BITRIX_CSRF_TOKEN=418cc92083b4b92729... # CSRF Token (optional)
BITRIX_SITE_ID=ap                       # Site ID (optional)
BITRIX_API_URL=https://ugautodetal.ru   # API Base URL
```

### `bitrix_token.json` (Backup)
Automatic backup of credentials with timestamp:
```json
{
  "token": "eu3rd5op69723b59",
  "user_id": 2611,
  "csrf_token": "418cc92083b4b92729...",
  "site_id": "ap",
  "timestamp": 1768887340.4,
  "date": "2026-01-20 08:35:40",
  "url": "https://ugautodetal.ru/stream/"
}
```

---

## 📋 Credential Check Logic

The `start.py` script checks:

1. **BITRIX_REST_TOKEN**
   - Must exist in `.env`
   - Must be non-empty (length > 0)
   - Format: Alphanumeric string

2. **BITRIX_USER_ID**
   - Must exist in `.env`
   - Must be non-empty (length > 0)
   - Format: Numeric string or integer

**Result**:
- Both found → Start chat ✅
- Either missing → Open browser 🔐
- Both missing → Open browser 🔐

---

## 🔐 Authentication Flow

When credentials are missing, `start.py` triggers:

```
start.py
  └─ main.py (opens Chromium)
      ├─ Navigate to Bitrix24 login page
      ├─ User logs in manually
      ├─ System extracts CSRF token
      ├─ System requests API token
      ├─ Save token to .env
      ├─ Save token to bitrix_token.json
      └─ Launch run_chat.py automatically
          └─ Chat UI displays (PyQt5)
```

---

## ✅ Verification

### Check What Credentials Are Loaded
```bash
grep -E "BITRIX_REST_TOKEN|BITRIX_USER_ID" .env
```

Output:
```
BITRIX_REST_TOKEN=eu3rd5op69723b59
BITRIX_USER_ID=2611
```

### Verify Setup
```bash
python3 verify_setup.py
```

This tests all components and credentials.

---

## 🚨 Troubleshooting

### Chat Doesn't Start After Login
1. Check if `.env` exists
2. Verify `BITRIX_REST_TOKEN` has a value
3. Verify `BITRIX_USER_ID` has a value
4. Run: `cat .env | grep BITRIX`

### Can't Find Credentials Error
1. Run: `python3 main.py` to re-authenticate
2. Complete the login process in browser
3. Token will be automatically saved
4. Run: `python3 start.py` again

### Token Seems Invalid
1. Delete `bitrix_token.json`
2. Clear `BITRIX_REST_TOKEN` from `.env`
3. Run: `python3 main.py` to get new token
4. Chat will start automatically

### Chromium Won't Open
1. Check if Chromium is installed
2. Run: `python3 main.py --debug` for more details
3. Manually provide token in `.env` with format:
   ```env
   BITRIX_REST_TOKEN=your_token_here
   BITRIX_USER_ID=2611
   ```

---

## 📊 Startup Commands Reference

| Command | Purpose | Prerequisites |
|---------|---------|-----------------|
| `python3 start.py` | Smart startup (recommended) | None - auto-detects |
| `python3 main.py` | Get new token via browser | Chromium installed |
| `python3 run_chat.py` | Start chat directly | `.env` with token & user_id |
| `python3 verify_setup.py` | Test all components | None |

---

## 🎯 Best Practices

1. **Use `start.py` as default**
   - Always use this for convenience
   - It handles all scenarios automatically

2. **Keep `.env` safe**
   - Never commit to git
   - Contains sensitive API token
   - Added to `.gitignore`

3. **Backup credentials**
   - `bitrix_token.json` is automatic backup
   - Kept with full timestamp
   - Can restore if `.env` lost

4. **Re-authenticate when needed**
   - Token expires in 1 year (default)
   - Simply run: `python3 main.py`
   - New token automatically saved

---

## 🔄 How Credentials Persist

```
First Run (No .env)
  └─ python3 start.py
      └─ Opens main.py
          └─ Chromium login
              └─ Token obtained
                  └─ Saved to .env
                      └─ Chat starts

Second Run (With .env)
  └─ python3 start.py
      └─ Reads .env
          └─ Found credentials
              └─ Chat starts immediately
                  └─ No browser needed
```

---

## 📱 Chat Application Features

Once started, the chat provides:
- ✅ Real-time messaging
- ✅ Multiple chat rooms
- ✅ User profiles
- ✅ Message history
- ✅ File attachments (in development)
- ✅ WebSocket real-time updates
- ✅ Telegram-like UI design

---

**Status**: ✅ Ready to use
**Last Updated**: 2026-01-20
