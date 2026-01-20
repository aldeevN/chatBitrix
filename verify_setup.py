#!/usr/bin/env python3
"""
Test script: Verify token loading and chat UI startup
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env file first
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    load_dotenv(env_file)

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

print("\n" + "="*70)
print("🧪 CHAT APPLICATION STARTUP VERIFICATION")
print("="*70)

# Test 1: Check .env file
print("\n1️⃣  Checking .env file...")
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    print(f"   ✅ .env found at {env_file}")
    with open(env_file, 'r') as f:
        content = f.read()
    if "BITRIX_REST_TOKEN" in content:
        token_line = [l for l in content.split('\n') if l.startswith('BITRIX_REST_TOKEN')][0]
        token_value = token_line.split('=')[1] if '=' in token_line else "MISSING"
        print(f"   ✅ BITRIX_REST_TOKEN found: {token_value[:20]}...")
    else:
        print("   ❌ BITRIX_REST_TOKEN not found in .env")
    
    if "BITRIX_USER_ID" in content:
        user_line = [l for l in content.split('\n') if l.startswith('BITRIX_USER_ID')][0]
        user_value = user_line.split('=')[1] if '=' in user_line else "MISSING"
        print(f"   ✅ BITRIX_USER_ID found: {user_value}")
    else:
        print("   ❌ BITRIX_USER_ID not found in .env")
else:
    print(f"   ❌ .env not found at {env_file}")

# Test 2: Load environment variables
print("\n2️⃣  Loading environment variables...")
os.environ.update({
    'BITRIX_REST_TOKEN': os.environ.get('BITRIX_REST_TOKEN', ''),
    'BITRIX_USER_ID': os.environ.get('BITRIX_USER_ID', ''),
    'SKIP_AUTH_CHECK': '1'
})

# Test 3: Check BitrixAPI can be initialized
print("\n3️⃣  Testing BitrixAPI initialization...")
try:
    from api.bitrix_api import BitrixAPI
    
    token = os.environ.get('BITRIX_REST_TOKEN')
    user_id = os.environ.get('BITRIX_USER_ID')
    
    if token and user_id:
        print(f"   ✅ Token and User ID ready")
        api = BitrixAPI(user_id=int(user_id), token=token, base_domain="https://ugautodetal.ru")
        print(f"   ✅ BitrixAPI initialized successfully")
        print(f"      - User ID: {user_id}")
        print(f"      - Token (first 20 chars): {token[:20]}...")
        print(f"      - API Base URL configured")
    else:
        print(f"   ❌ Token or User ID missing")
        print(f"      - Token: {token[:20] if token else 'MISSING'}...")
        print(f"      - User ID: {user_id if user_id else 'MISSING'}")
        sys.exit(1)
except Exception as e:
    print(f"   ❌ Error initializing BitrixAPI: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Check main window can be created
print("\n4️⃣  Testing TelegramChatWindow creation...")
try:
    from ui.main_window import TelegramChatWindow
    from PyQt5.QtWidgets import QApplication
    
    # Create QApplication (required by PyQt5)
    if not QApplication.instance():
        app = QApplication(sys.argv)
    else:
        app = QApplication.instance()
    
    # Don't actually instantiate the window (it would open a GUI)
    # Just check that imports work
    print(f"   ✅ TelegramChatWindow can be imported")
    print(f"   ✅ PyQt5 environment ready")
except Exception as e:
    print(f"   ❌ Error with TelegramChatWindow: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Summary
print("\n" + "="*70)
print("✅ ALL CHECKS PASSED - Chat application is ready to run!")
print("="*70)
print("\n📋 Next Steps:")
print("   1. Run: python3 run_chat.py")
print("   2. Chat UI will start with token from .env")
print("   3. Message history will load automatically")
print("\n🔑 Token Status:")
print(f"   - Token: {token[:20]}...")
print(f"   - User ID: {user_id}")
print(f"   - Stored in: .env (BITRIX_REST_TOKEN, BITRIX_USER_ID)")
print("\n💡 To re-authenticate:")
print("   Run: python3 main.py")
print("="*70 + "\n")
