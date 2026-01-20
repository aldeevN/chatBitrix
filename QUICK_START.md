# ⚡ Quick Reference

## 🎯 One Command to Start Everything

```bash
python3 start.py
```

**That's it!** The script will:
1. ✅ Check for credentials in `.env`
2. ✅ Start chat if they exist
3. ✅ Open browser for login if they don't

---

## 📋 What Gets Checked

| File | Variable | Status |
|------|----------|--------|
| `.env` | `BITRIX_REST_TOKEN` | ✅ Required |
| `.env` | `BITRIX_USER_ID` | ✅ Required |

**If both exist** → Chat starts immediately 🚀
**If any missing** → Browser opens for authentication 🔐

---

## 🔍 Check Your Credentials

```bash
# View token and user ID
grep -E "BITRIX_REST_TOKEN|BITRIX_USER_ID" .env

# Expected output:
# BITRIX_REST_TOKEN=eu3rd5op69723b59
# BITRIX_USER_ID=2611
```

---

## 🔑 Manual Setup (If Needed)

```bash
# Edit .env manually
nano .env

# Add these lines:
BITRIX_REST_TOKEN=your_token_here
BITRIX_USER_ID=2611

# Save (Ctrl+O, Enter, Ctrl+X)

# Now run:
python3 start.py
```

---

## 🆘 If Something Goes Wrong

```bash
# Get new token
python3 main.py

# Start chat directly (if you have token)
python3 run_chat.py

# Test setup
python3 verify_setup.py
```

---

## 📁 File Structure

```
chatBitrix/
├── start.py              ← Use this! (smart startup)
├── main.py               ← For authentication
├── run_chat.py           ← Chat UI launcher
├── verify_setup.py       ← Test components
├── .env                  ← Your credentials (auto-created)
├── bitrix_token.json     ← Backup credentials (auto-created)
├── src/
│   ├── ui/              ← Chat UI components
│   └── api/             ← REST API client
└── START_GUIDE.md        ← Full documentation
```

---

## ⏱️ Typical Usage

### First Time
```bash
python3 start.py
# → Browser opens → Login → Token saved → Chat starts
```

### Every Time After
```bash
python3 start.py
# → Token found → Chat starts immediately (2-3 seconds)
```

### Need New Token?
```bash
python3 main.py
# → Browser opens → Login → New token saved → Chat starts
```

---

## ✨ Key Features

- 🤖 **Auto-detection** - Checks for credentials automatically
- ⚡ **Fast startup** - No browser if credentials exist
- 🔐 **Secure** - Token stored in `.env` (added to `.gitignore`)
- 💾 **Backup** - Credentials backed up to `bitrix_token.json`
- 🔄 **Auto-flow** - Browser → Login → Token save → Chat start

---

**Start chatting**: `python3 start.py`
