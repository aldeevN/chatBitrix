"""
Authentication manager for Bitrix24
"""

import os
import json
import re
from typing import Dict, Any, Optional

def authenticate_and_get_env():
    """Enhanced authentication function with better error handling"""
    print("\n" + "="*60)
    print("BITRIX24 AUTHENTICATION")
    print("="*60)
    
    from .chrome_auth import ChromeAuthApp
    app = ChromeAuthApp(headless=False)
    
    try:
        login_url = "https://ugautodetal.ru"
        
        print(f"Navigating to: {login_url}")
        app.navigate_to_login(login_url)
        
        print("\nAttempting auto-login with saved cookies...")
        if not app.auto_login_with_saved_cookies(login_url):
            print("Auto-login failed or no cookies found.")
            print("\n" + "-"*40)
            print("MANUAL LOGIN REQUIRED")
            print("-"*40)
            print("1. Log in to Bitrix24 in the browser window")
            print("2. Navigate to your chat/workspace if needed")
            print("3. Wait for the page to fully load")
            print("4. Return here and press Enter")
            print("-"*40)
            input("\nPress Enter after logging in...")
            
            # Save cookies for future use
            app.save_cookies_pickle()
            print("✓ Cookies saved for future use")
        else:
            print("✓ Auto-login successful")
        
        # Extract CSRF token
        print("\nExtracting CSRF token...")
        csrf_token = app.extract_csrf_token_bitrix()
        if csrf_token:
            app.csrf_tokens['bitrix_sessid'] = csrf_token
            print(f"✓ CSRF token extracted: {csrf_token[:20]}...")
        else:
            print("✗ Could not extract CSRF token")
        
        # Save authentication data
        print("\nSaving authentication data...")
        env_content = app.save_auth_to_env()
        
        print(f"\n✓ Auth data saved to .env file ({len(env_content)} entries)")
        print(f"✓ Full auth data saved to auth_data_full.json")
        print(f"✓ Current URL: {app.driver.current_url[:80]}...")
        print(f"✓ Page title: {app.driver.title}")
        
        # Extract and display important cookies
        auth_data = app.capture_auth_data()
        cookies = auth_data['cookies']
        bitrix_cookies = {k: v for k, v in cookies.items() 
                         if 'bitrix' in k.lower() or 'bx' in k.lower() or 'sess' in k.lower()}
        
        print(f"\nImportant cookies found ({len(bitrix_cookies)}):")
        for cookie_name in list(bitrix_cookies.keys())[:5]:  # Show first 5
            print(f"  {cookie_name}: {bitrix_cookies[cookie_name][:30]}...")
        
        print("\n" + "="*60)
        print("AUTHENTICATION COMPLETE")
        print("="*60)
        
        return env_content
        
    except KeyboardInterrupt:
        print("\n✗ Authentication cancelled by user")
        raise
    except Exception as e:
        print(f"\n✗ Authentication error: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        app.close()
        print("\nBrowser closed")

def authenticate_from_captured_data():
    """Load authentication data from captured files without browser"""
    print("\n" + "="*60)
    print("BITRIX24 AUTHENTICATION FROM CAPTURED DATA")
    print("="*60)
    
    try:
        # Load auth data from JSON
        if os.path.exists('auth_data_full.json'):
            with open('auth_data_full.json', 'r', encoding='utf-8') as f:
                auth_data = json.load(f)
            
            print("✓ Loaded authentication data from auth_data_full.json")
            
            # Extract user ID from various sources
            user_id = None
            
            # Try to get user ID from UAD_AVATAR cookie
            cookies = auth_data.get('cookies', {})
            if 'UAD_AVATAR' in cookies:
                try:
                    user_id = int(cookies['UAD_AVATAR'])
                    print(f"✓ User ID from UAD_AVATAR cookie: {user_id}")
                except (ValueError, TypeError):
                    pass
            
            # Try to get user ID from BITRIX_SM_UIDH or other cookies
            if not user_id:
                for cookie_name, cookie_value in cookies.items():
                    if 'user' in cookie_name.lower() or 'uid' in cookie_name.lower():
                        try:
                            # Try to extract numeric ID
                            match = re.search(r'\d+', cookie_value)
                            if match:
                                user_id = int(match.group())
                                print(f"✓ User ID from {cookie_name}: {user_id}")
                                break
                        except:
                            pass
            
            # Fallback to default user ID
            if not user_id:
                user_id = 1  # From your data
                print(f"✓ Using default user ID: {user_id}")
            
            # Extract Pull configuration
            local_storage = auth_data.get('local_storage', {})
            session_storage = auth_data.get('session_storage', {})
            
            # Try to find Pull config in local or session storage
            pull_config = None
            
            # Try various key patterns
            key_patterns = [
                f"bx-pull-{user_id}-ap-bx-pull-config",
                f"bx-pull-{user_id}-bx-pull-config",
                "bx-pull-config",
                "pull-config",
            ]
            
            for pattern in key_patterns:
                for storage in [local_storage, session_storage]:
                    if pattern in storage:
                        try:
                            pull_config = json.loads(storage[pattern])
                            print(f"✓ Found Pull config with key: {pattern}")
                            break
                        except json.JSONDecodeError:
                            continue
                if pull_config:
                    break
            
            # If still no config found, search for any key containing 'pull' and 'config'
            if not pull_config:
                for storage in [local_storage, session_storage]:
                    for key in storage.keys():
                        if 'pull' in key.lower() and 'config' in key.lower():
                            try:
                                pull_config = json.loads(storage[key])
                                print(f"✓ Found Pull config with alternative key: {key}")
                                break
                            except json.JSONDecodeError:
                                continue
                    if pull_config:
                        break
            
            # Create result dictionary
            result = {
                'user_id': user_id,
                'cookies': cookies,
                'local_storage': local_storage,
                'session_storage': session_storage
            }
            
            if pull_config:
                result['pull_config'] = pull_config
                
                # Save Pull config to separate file
                with open('pull_config.json', 'w', encoding='utf-8') as f:
                    json.dump(pull_config, f, indent=2, ensure_ascii=False)
                
                print(f"✓ Pull configuration saved to pull_config.json")
                
                # Extract and display channel info
                channels = pull_config.get('channels', {})
                if 'shared' in channels:
                    shared_channel = channels['shared']['id']
                    print(f"✓ Shared channel ID: {shared_channel[:50]}...")
                
                if 'private' in channels:
                    private_channel = channels['private']['id']
                    print(f"✓ Private channel ID: {private_channel[:50]}...")
                
                # Extract server configuration
                server_config = pull_config.get('server', {})
                if server_config:
                    websocket_url = server_config.get('websocket_secure') or server_config.get('websocket')
                    if websocket_url:
                        print(f"✓ WebSocket URL: {websocket_url}")
            
            return result
            
        else:
            print("✗ auth_data_full.json not found")
        
        return None
        
    except Exception as e:
        print(f"✗ Error loading authentication data: {e}")
        import traceback
        traceback.print_exc()
        return None