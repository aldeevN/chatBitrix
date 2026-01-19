"""
Authentication manager for Bitrix24
"""

import os
import json
import re
from typing import Dict, Optional

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
        
        # GET API TOKEN DIRECTLY IN BROWSER (CRITICAL)
        print("\n" + "="*60)
        print("GETTING API TOKEN FROM BITRIX")
        print("="*60)
        api_token, browser_user_id = app.get_api_token_in_browser()
        
        if api_token and browser_user_id:
            print(f"\n✓ API token obtained in browser!")
            print(f"✓ User ID from browser: {browser_user_id}")
            print(f"✓ Token saved: {api_token[:30]}...")
            user_id = browser_user_id
        else:
            print(f"\n⚠ Could not get API token in browser")
            print("Continuing with captured cookies instead...")
            user_id = 1  # Fallback
        
        # Save authentication data using env_handler
        print("\nSaving authentication data...")
        from .env_handler import create_env_file_from_auth
        
        # Get auth data from browser
        auth_data = {
            'user_id': user_id,
            'cookies': app.get_cookies() if hasattr(app, 'get_cookies') else {},
            'local_storage': app.get_local_storage() if hasattr(app, 'get_local_storage') else {},
            'session_storage': app.get_session_storage() if hasattr(app, 'get_session_storage') else {},
            'current_url': app.driver.current_url,
            'page_title': app.driver.title,
            'tokens': {'api_token': api_token} if api_token else {},
            'csrf_tokens': app.csrf_tokens if hasattr(app, 'csrf_tokens') else {}
        }
        
        # Save to file
        with open('auth_data_full.json', 'w', encoding='utf-8') as f:
            json.dump(auth_data, f, indent=2, default=str)
        
        env_content = create_env_file_from_auth(auth_data)
        
        print(f"\n✓ Auth data saved to .env file ({len(env_content)} entries)")
        print(f"✓ Full auth data saved to auth_data_full.json")
        print(f"✓ Current URL: {app.driver.current_url[:80]}...")
        
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