#!/usr/bin/env python3
"""
Main entry point for Telegram-like Bitrix24 Chat with Authentication and Real-time WebSocket
"""

import sys
import os
from datetime import datetime

# Add src to path for module imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from ui.main_window import TelegramChatWindow
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

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
    
    # Extract user ID and token from multiple sources
    user_id = auth_data.get('user_id', 1)  # Default from your data
    
    # First, check if token was obtained in browser
    api_token = None
    
    # Try to load from .env first (most recent)
    print("\n🔍 Attempting to load API credentials from .env...")
    try:
        if os.path.exists('.env'):
            # Read .env file directly instead of using dotenv
            with open('.env', 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('API_TOKEN='):
                        api_token = line.split('=', 1)[1].strip()
                        print(f"   ✓ Found API_TOKEN in .env: {api_token[:30]}...")
                    elif line.startswith('API_USER_ID='):
                        user_id_str = line.split('=', 1)[1].strip()
                        try:
                            user_id = int(user_id_str)
                            print(f"   ✓ Found API_USER_ID in .env: {user_id}")
                        except:
                            print(f"   ⚠ Could not parse API_USER_ID: {user_id_str}")
        else:
            print(f"   ⚠ .env file not found at {os.path.abspath('.env')}")
    except Exception as e:
        print(f"   ❌ Error reading .env: {e}")
        import traceback
        traceback.print_exc()
    
    # If not in .env, try from auth_data
    if not api_token and auth_data.get('tokens', {}).get('api_token'):
        api_token = auth_data['tokens']['api_token']
        print(f"\n✓ Using token obtained in browser")
        print(f"   Token: {api_token[:30]}...")
    
    # If STILL no token, open chromium to get it
    if not api_token:
        
        try:
            from auth.chrome_auth import ChromeAuthApp
            chrome_app = ChromeAuthApp(headless=False)
            
            try:
                print("\nNavigating to Bitrix...")
                chrome_app.navigate_to_login("https://ugautodetal.ru")
                
                print("Attempting auto-login...")
                if not chrome_app.auto_login_with_saved_cookies("https://ugautodetal.ru"):
                    print("\nManual login required:")
                    print("1. Log in to Bitrix24")
                    print("2. Wait for page to load")
                    print("3. Press Enter when ready")
                    input("\nPress Enter after logging in...")
                
                # Get token directly in browser
                api_token, browser_user_id = chrome_app.get_api_token_in_browser()
                
                if api_token:
                    print(f"\n✓ Token obtained in browser: {api_token[:30]}...")
                    if browser_user_id:
                        user_id = browser_user_id
                        print(f"✓ User ID from browser: {user_id}")
                    
                    # Save token to .env for REST client testing
                    print(f"\n💾 Saving token to .env file...")
                    with open('.env', 'a') as f:
                        f.write(f"\nAPI_TOKEN={api_token}\n")
                        f.write(f"API_USER_ID={user_id}\n")
                    print(f"✓ Token saved - you can now use test_rest_client.py")
                else:
                    print(f"\n✗ Failed to get token in browser")
                    print("\n" + "="*60)
                    print("CHECK CHROMIUM DEVTOOLS FOR ERRORS:")
                    print("- Open DevTools (F12 or Cmd+Option+I)")
                    print("- Go to Network tab to see API requests")
                    print("- Go to Console tab to see error messages")
                    print("="*60)
                    print("\nPress Enter to close browser and exit...")
                    input()
                    chrome_app.close()
                    return
                
                # Keep browser open for inspection
                print("\n" + "="*60)
                print("TOKEN OBTAINED SUCCESSFULLY")
                print("="*60)
                print("\nBrowser is still open. You can:")
                print("- Inspect the Network tab (F12) to see the API request")
                print("- Check the Console tab for any messages")
                print("- Verify the request headers and response")
                print("\nPress Enter to close browser and continue...")
                print("="*60)
                input()
                    
            finally:
                chrome_app.close()
                
        except Exception as e:
            print(f"✗ Failed to open chromium: {e}")
            import traceback
            traceback.print_exc()
            print("Exiting application...")
            return
    
    if not api_token:
        print("✗ No API token available - API requests may fail")
        print("Exiting application...")
        return
    
    print(f"\n✓ Authenticated as user ID: {user_id}")
    print(f"✓ Pull configuration: {'Loaded' if auth_data.get('pull_config') else 'Not loaded'}")
    print(f"✓ {len(auth_data.get('cookies', {}))} cookies available")
    
    # Initialize API with user_id and token in URL
    from api.bitrix_api import BitrixAPI
    api = BitrixAPI(user_id=user_id, token=api_token)
    
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