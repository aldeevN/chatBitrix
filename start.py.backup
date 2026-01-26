#!/usr/bin/env python3
"""
Smart Chat Startup Script
- Checks for existing credentials in .env (BITRIX_REST_TOKEN, BITRIX_USER_ID)
- If both exist: Starts chat directly
- If missing: Opens Chromium for authentication first
"""

import os
import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv

def check_credentials():
    """Check if both REST API credentials exist in .env"""
    env_path = Path(__file__).parent / '.env'
    
    token = None
    user_id = None
    
    # Load from .env file
    if env_path.exists():
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('BITRIX_REST_TOKEN=') and not line.startswith('BITRIX_REST_TOKEN='):
                    continue
                if line.startswith('BITRIX_REST_TOKEN='):
                    token = line.split('=', 1)[1].strip()
                elif line.startswith('BITRIX_USER_ID='):
                    user_id = line.split('=', 1)[1].strip()
    
    return token, user_id

def start_browser_auth():
    """Open Chromium browser for authentication"""
    print("\n" + "="*75)
    print("🔐 CREDENTIALS MISSING - OPENING CHROMIUM FOR AUTHENTICATION")
    print("="*75)
    print("\n   📱 Chromium will open automatically...")
    print("   1️⃣  Log in to Bitrix24")
    print("   2️⃣  System will capture authentication data")
    print("   3️⃣  Credentials will be saved to .env")
    print("   4️⃣  Chat will start automatically")
    print("\n" + "="*75 + "\n")
    
    main_script = Path(__file__).parent / "main.py"
    if not main_script.exists():
        print("❌ Error: main.py not found!")
        sys.exit(1)
    
    try:
        subprocess.run([sys.executable, str(main_script)], check=False)
    except KeyboardInterrupt:
        print("\n\n❌ Authentication cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error during authentication: {e}")
        sys.exit(1)

def start_chat():
    """Start the chat application with existing credentials"""
    print("\n" + "="*75)
    print("✅ CREDENTIALS LOADED - STARTING CHAT")
    print("="*75 + "\n")
    
    chat_script = Path(__file__).parent / "run_chat.py"
    if not chat_script.exists():
        print("❌ Error: run_chat.py not found!")
        sys.exit(1)
    
    try:
        subprocess.run([sys.executable, str(chat_script)], check=False)
    except KeyboardInterrupt:
        print("\n\n👋 Chat closed by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Error starting chat: {e}")
        sys.exit(1)

def main():
    """Main entry point - smart startup logic"""
    print("\n" + "="*75)
    print("🚀 BITRIX24 CHAT - SMART STARTUP")
    print("="*75)
    
    print("\n🔍 Checking credentials in .env...")
    token, user_id = check_credentials()
    
    # Check if both credentials exist
    has_token = token and len(token.strip()) > 0
    has_user_id = user_id and len(user_id.strip()) > 0
    
    if has_token and has_user_id:
        print(f"   ✅ Token found: {token[:25]}...")
        print(f"   ✅ User ID found: {user_id}")
        print("\n   🎯 Both credentials present - starting chat...\n")
        start_chat()
    else:
        if not has_token:
            print("   ❌ BITRIX_REST_TOKEN not found or empty")
        if not has_user_id:
            print("   ❌ BITRIX_USER_ID not found or empty")
        print("\n   🔐 Missing credentials - opening browser authentication...\n")
        start_browser_auth()

if __name__ == "__main__":
    main()
