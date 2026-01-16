#!/usr/bin/env python3
"""
Main entry point for Telegram-like Bitrix24 Chat with Authentication and Real-time WebSocket
"""

import sys
import os
from datetime import datetime

# Добавляем пути к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ui.main_window import TelegramChatWindow
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

def test_api_tokens(api):
    """Test API token functionality"""
    print("\n" + "="*60)
    print("Testing API Token Functionality")
    print("="*60)
    
    try:
        # Test getting current token
        print("1. Getting current token info...")
        result = api.get_current_token_info()
        if result and not result.get("error"):
            token_info = result.get("result", {})
            if token_info:
                print(f"   ✓ Current token: {token_info.get('name', 'N/A')}")
                print(f"   ✓ Expires: {token_info.get('expires', 'N/A')}")
            else:
                print("   ⓘ No active token found")
        else:
            print(f"   ✗ Error: {result.get('error', 'Unknown error')}")
        
        # Test creating new token
        print("\n2. Testing token creation...")
        result = api.create_token_api(
            name=f"Test Token - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            expires_in_days=30
        )
        
        if result and not result.get("error"):
            token = result.get("result", {}).get("token")
            if token:
                print(f"   ✓ Token created successfully")
                print(f"   ✓ Token (first 20 chars): {token[:20]}...")
                
                # Test using the token
                print("\n3. Testing token usage...")
                # Здесь можно добавить тест использования токена
            else:
                print("   ✗ No token returned")
        else:
            print(f"   ✗ Error creating token: {result.get('error', 'Unknown error')}")
        
        print("\n" + "="*60)
        print("API Token Test Complete")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"✗ API token test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main application entry point"""
    print("\n" + "="*60)
    print("TELEGRAM-LIKE BUSINESS CHAT WITH BITRIX PULL")
    print("="*60)
    
    # Check for existing authentication data
    auth_files_exist = os.path.exists('.env') and os.path.exists('auth_data_full.json')
    
    if not auth_files_exist:
        print("Authentication data not found.")
        print("Starting authentication capture...")
        
        try:
            # Import auth manager
            from auth.auth_manager import authenticate_and_get_env
            # Run authentication
            authenticate_and_get_env()
            print("✓ Authentication completed")
        except Exception as e:
            print(f"✗ Authentication failed: {e}")
            print("Continuing with limited functionality...")
    else:
        print("✓ Authentication data found")
    
    # Load authentication from captured data
    print("\nLoading authentication from captured data...")
    from auth.auth_manager import authenticate_from_captured_data
    auth_data = authenticate_from_captured_data()
    
    if not auth_data:
        print("✗ Failed to load authentication data")
        print("Please run authentication first.")
        
        # Ask user if they want to authenticate now
        app = QApplication([])  # Create temporary app for message box
        reply = QMessageBox.question(
            None,
            "Authentication Required",
            "Authentication data not found. Would you like to authenticate now?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        if reply == QMessageBox.Yes:
            from auth.auth_manager import authenticate_and_get_env
            authenticate_and_get_env()
            auth_data = authenticate_from_captured_data()
        else:
            print("Exiting application...")
            return
        app.quit()
    
    # Create .env file from auth data
    from auth.env_handler import create_env_file_from_auth
    create_env_file_from_auth(auth_data)
    
    # Extract user ID
    user_id = auth_data.get('user_id', 1)  # Default from your data
    
    print(f"\n✓ Authenticated as user ID: {user_id}")
    print(f"✓ Pull configuration: {'Loaded' if auth_data.get('pull_config') else 'Not loaded'}")
    print(f"✓ {len(auth_data.get('cookies', {}))} cookies available")
    
    # Initialize API with webhook URL
    from api.bitrix_api import BitrixAPI
    api = BitrixAPI(f"https://ugautodetal.ru/rest/{user_id}/{auth_data.get('tokens[0]','none')}/")
    
    # Test API tokens
    print("\nTesting API token functionality...")
    test_api_tokens(api)
    
    print("\n" + "="*60 + "\n")
    
    # Now start the chat application
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # Set application font
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    # Set application name
    app.setApplicationName("Bitrix Pull")
    
    # Create and show window
    window = TelegramChatWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()