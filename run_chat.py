#!/usr/bin/env python3
"""
Chat Application Launcher
Loads REST API token from .env and starts the PyQt5 chat UI
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv
from PyQt5.QtWidgets import QApplication

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ui.main_window import TelegramChatWindow
from api.bitrix_api import BitrixAPI

def load_token_from_env():
    """Load REST API token from .env file"""
    # Load .env file
    load_dotenv()
    
    token = os.getenv('BITRIX_REST_TOKEN')
    user_id = os.getenv('BITRIX_USER_ID')
    base_url = os.getenv('BITRIX_API_URL', 'https://ugautodetal.ru/stream/')
    
    if not token or not user_id:
        print("❌ Error: REST API credentials not found in .env file")
        print("\nTo obtain credentials:")
        print("1. Run: python3 main.py")
        print("2. Complete the authentication process")
        print("3. Token will be automatically saved to .env")
        return None, None, None
    
    return token, int(user_id), base_url

def main():
    """Main application entry point"""
    print("\n" + "="*60)
    print("🚀 Bitrix24 Chat Application")
    print("="*60)
    
    # Load token from environment
    print("\n📋 Loading API credentials from .env...")
    token, user_id, base_url = load_token_from_env()
    
    if not token:
        sys.exit(1)
    
    print(f"✅ Token loaded successfully")
    print(f"   User ID: {user_id}")
    print(f"   Token: {token[:20]}...")
    print(f"   API URL: {base_url}")
    
    # Set environment variables so main window doesn't try to re-authenticate
    os.environ['BITRIX_REST_TOKEN'] = token
    os.environ['BITRIX_USER_ID'] = str(user_id)
    os.environ['BITRIX_API_URL'] = base_url
    os.environ['SKIP_AUTH_CHECK'] = '1'  # Skip authentication check in main window
    
    # Initialize REST API client
    print("\n🔌 Initializing REST API client...")
    try:
        api_client = BitrixAPI(user_id=user_id, token=token, base_domain="https://ugautodetal.ru")
        print("✅ REST API client initialized")
    except Exception as e:
        print(f"❌ Failed to initialize API client: {e}")
        sys.exit(1)
    
    # Create PyQt5 application
    print("\n🎨 Starting PyQt5 Chat UI...")
    app = QApplication(sys.argv)
    
    try:
        # Create and show main window
        window = TelegramChatWindow()
        window.show()
        
        print("✅ Chat application started successfully")
        print("\n" + "="*60)
        print("💬 Chat Interface Ready")
        print("="*60)
        print("\nFeatures:")
        print("  • 📱 Real-time message display")
        print("  • 👥 Chat list with groups and direct messages")
        print("  • 🔍 Search functionality")
        print("  • 📎 File attachment support")
        print("  • 🎨 Telegram-like dark/light theme")
        print("\nQuit with Ctrl+C or close the window")
        print("="*60 + "\n")
        
        sys.exit(app.exec_())
    
    except Exception as e:
        print(f"\n❌ Error starting chat application: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
