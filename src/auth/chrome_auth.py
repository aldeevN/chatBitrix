"""
Chrome authentication for Bitrix24
Uses Selenium for browser automation to capture authentication data
"""

import os
import time
import json
import pickle
from typing import Optional

# Selenium imports for browser automation
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

class ChromeAuthApp:
    def __init__(self, headless=False):
        self.chrome_options = Options()
        
        if not headless:
            self.chrome_options.add_argument("--start-maximized")
        else:
            self.chrome_options.add_argument("--headless")
        
        self.chrome_options.add_argument("--disable-notifications")
        self.chrome_options.add_argument("--disable-popup-blocking")
        self.chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.chrome_options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = webdriver.Chrome(options=self.chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
        
        self.tokens = {}
        self.csrf_tokens = {}
    
    def navigate_to_login(self, url):
        """Navigate to login page"""
        self.driver.get(url)
        time.sleep(2)
    
    def get_cookies(self):
        """Get all cookies from browser"""
        cookies = self.driver.get_cookies()
        return {cookie['name']: cookie['value'] for cookie in cookies}
    
    def get_local_storage(self):
        """Get local storage data"""
        return self.driver.execute_script("""
            var items = {};
            for (var i = 0; i < localStorage.length; i++) {
                var key = localStorage.key(i);
                items[key] = localStorage.getItem(key);
            }
            return items;
        """)
    
    def get_session_storage(self):
        """Get session storage data"""
        return self.driver.execute_script("""
            var items = {};
            for (var i = 0; i < sessionStorage.length; i++) {
                var key = sessionStorage.key(i);
                items[key] = sessionStorage.getItem(key);
            }
            return items;
        """)
    
    def auto_login_with_saved_cookies(self, url, cookies_file='cookies.pkl'):
        """Auto login with saved cookies"""
        if not os.path.exists(cookies_file):
            return False
        
        self.driver.get(url)
        
        try:
            with open(cookies_file, 'rb') as f:
                cookies = pickle.load(f)
            
            for cookie in cookies:
                try:
                    # Handle cookies that might have issues
                    if 'expiry' in cookie:
                        del cookie['expiry']
                    self.driver.add_cookie(cookie)
                except Exception as e:
                    print(f"   ⚠️  Could not add cookie {cookie.get('name', 'unknown')}: {e}")
                    continue
            
            self.driver.refresh()
            time.sleep(3)
            
            # Check if we're logged in by looking for auth indicators
            page_source = self.driver.page_source
            is_logged_in = any([
                "logout" in page_source.lower(),
                "profile" in page_source.lower() and "user" in page_source.lower(),
                "bitrix_sessid" in page_source.lower()
            ])
            
            if is_logged_in and "login" not in self.driver.current_url.lower():
                print(f"   ✅ Cookies loaded successfully - appears to be logged in")
                return True
            else:
                print(f"   ⚠️  Could not verify login with cookies")
                return False
        except Exception as e:
            print(f"   ❌ Error loading cookies: {e}")
            return False
    
    def get_api_token_in_browser(self):
        """
        Get API token directly in Chromium browser using fetch with CDP monitoring
        ONLY works when current URL is 'https://ugautodetal.ru/?login=yes'
        Shows request/response in DevTools
        
        Correct endpoint format:
        - POST /bitrix/services/main/ajax.php?action=me%3Abase.api.user.getTokenApi
        - Content-Type: application/x-www-form-urlencoded
        - Headers: x-bitrix-csrf-token, x-bitrix-site-id, bx-ajax
        
        Returns: (token, user_id)
        """
        print("\n" + "="*60)
        print("GETTING API TOKEN IN BROWSER")
        print("="*60)
        
        # Check current URL and authentication status
        current_url = self.driver.current_url
        
        print(f"\n1. Checking authentication status...")
        print(f"   Current URL: {current_url}")
        
        # Check if logged in by looking for logout button or auth indicators
        page_source = self.driver.page_source
        is_logged_in = any([
            'logout' in page_source.lower(),
            'выход' in page_source.lower(),  # Russian "logout"
            '/bitrix/admin/user_admin.php' in page_source,
            'bitrix_sessid' in page_source
        ])
        
        if not is_logged_in:
            print(f"\n❌ Not logged in!")
            print(f"   Please log in to Bitrix24 first")
            print(f"   Current page: {current_url}")
            print(f"\n   After logging in, press Enter to continue...")
            input()
        else:
            print(f"   ✅ Logged in detected!")
        
        print(f"   ✓ Proceeding with token request...")
        
        try:
            print("\n2. Getting CSRF token from page...")
            
            # Extract CSRF token and site ID from page
            csrf_js = """
            var csrf = document.querySelector('meta[name="x-bitrix-csrf-token"]');
            var csrf_value = csrf ? csrf.getAttribute('content') : null;
            
            // Try to get from BX if meta tag not found
            if (!csrf_value && typeof BX !== 'undefined' && typeof BX.message === 'function') {
                csrf_value = BX.message('bitrix_sessid');
            }
            
            // Try from window object
            if (!csrf_value && typeof window.bitrix_sessid !== 'undefined') {
                csrf_value = window.bitrix_sessid;
            }
            
            // Get site ID
            var site_id = 'ap'; // Default
            var site_meta = document.querySelector('meta[name="x-bitrix-site-id"]');
            if (site_meta) {
                site_id = site_meta.getAttribute('content');
            }
            
            console.log('CSRF Token:', csrf_value);
            console.log('Site ID:', site_id);
            
            return {
                csrf: csrf_value,
                site_id: site_id
            };
            """
            
            csrf_data = self.driver.execute_script(csrf_js)
            csrf_token = csrf_data.get('csrf')
            site_id = csrf_data.get('site_id', 'ap')
            
            print(f"   ✓ CSRF Token: {csrf_token[:30] if csrf_token else 'Not found'}...")
            print(f"   ✓ Site ID: {site_id}")
            
            # Wait 30 seconds after page load before sending request
            print(f"\n3. Waiting 30 seconds for page to fully initialize...")
            print(f"   (This allows all page scripts to load and initialize)")
            
            import time
            for i in range(30, 0, -1):
                print(f"   {i}s remaining...", end='\r', flush=True)
                time.sleep(1)
            print(f"   ✓ 30 seconds elapsed, now sending request!             \n")
            
            # Now make the token request with XMLHttpRequest (synchronous, visible in DevTools)
            print(f"4. Sending token request...")
            print(f"   URL: /bitrix/services/main/ajax.php?action=me:base.api.user.getTokenApi")
            print(f"   Method: POST")
            print(f"   ⓘ Check DevTools Network tab to see the request!")
            
            token_request_js = """
            var csrf = arguments[0];
            var site_id = arguments[1];
            
            var url = '/bitrix/services/main/ajax.php?action=me%3Abase.api.user.getTokenApi';
            
            console.log('%c📤 SENDING TOKEN REQUEST', 'color: blue; font-weight: bold');
            console.log('URL:', url);
            console.log('CSRF:', csrf);
            console.log('Site ID:', site_id);
            
            var xhr = new XMLHttpRequest();
            xhr.withCredentials = true;  // Include cookies
            
            xhr.onreadystatechange = function() {
                if (xhr.readyState === 4) {
                    console.log('%c✅ RESPONSE RECEIVED', 'color: green; font-weight: bold');
                    console.log('Status:', xhr.status);
                    console.log('Response:', xhr.responseText);
                    try {
                        var data = JSON.parse(xhr.responseText);
                        window.tokenResponse = data;
                    } catch(e) {
                        window.tokenResponse = {error: 'Parse error', raw: xhr.responseText};
                    }
                }
            };
            
            xhr.onerror = function() {
                console.error('%c❌ REQUEST ERROR', 'color: red; font-weight: bold');
                window.tokenResponse = {error: xhr.statusText};
            };
            
            // Send POST request
            xhr.open('POST', url, false);  // false = synchronous
            xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
            xhr.setRequestHeader('x-bitrix-csrf-token', csrf);
            xhr.setRequestHeader('x-bitrix-site-id', site_id);
            xhr.setRequestHeader('bx-ajax', 'true');
            xhr.send('');
            
            console.log('%c📨 REQUEST COMPLETE', 'color: orange; font-weight: bold');
            """
            
            # Execute the request
            self.driver.execute_script(token_request_js, csrf_token, site_id)
            
            # Wait a moment for response to be captured
            print("   ⏳ Processing response...")
            import time
            time.sleep(1)
            
            # Get the response from window
            response_js = "return window.tokenResponse;"
            result = self.driver.execute_script(response_js)
            
            print(f"   ✓ Response: {result}")
            
            # Check if we got a token
            # Response format: {'data': {'PASSWORD': 'token_value', 'USER_ID': '2611', ...}, 'status': 'success'}
            token = None
            user_id = None
            
            if result and result.get('status') == 'success' and result.get('data'):
                data = result['data']
                # For getTokenApi, token is in 'PASSWORD' field
                if isinstance(data, dict) and data.get('PASSWORD'):
                    print(f"\n   ✅ Token obtained!")
                    token = data['PASSWORD']
                    user_id = int(data.get('USER_ID', 1))
                    print(f"   ✓ Token: {token[:40]}...")
                    print(f"   ✓ User ID: {user_id}")
                    print(f"   ✓ Title: {data.get('TITLE', 'N/A')}")
                    print(f"   ✓ Created: {data.get('DATE_CREATE', 'N/A')}")
                # For createTokenApi, token is in 'data' directly as string
                elif isinstance(data, str):
                    print(f"\n   ✅ Token created!")
                    token = data
                    print(f"   ✓ New Token: {token[:40]}...")
            
            # If no token yet, try to create one
            if not token:
                print(f"\n5. No existing token, creating new one...")
                print("   URL: /bitrix/services/main/ajax.php?action=me:base.api.user.createTokenApi")
                
                # Wait another 30 seconds before creating token
                print(f"\n   Waiting 30 seconds before creating token...")
                import time
                for i in range(30, 0, -1):
                    print(f"   {i}s remaining...", end='\r', flush=True)
                    time.sleep(1)
                print(f"   ✓ Now sending create token request!             \n")
                
                print(f"   ⓘ Check DevTools Network tab to see the request!")
                
                create_request_js = """
                var csrf = arguments[0];
                var site_id = arguments[1];
                
                var url = '/bitrix/services/main/ajax.php?action=me%3Abase.api.user.createTokenApi';
                
                console.log('%c📤 CREATING NEW TOKEN', 'color: blue; font-weight: bold');
                console.log('URL:', url);
                
                var body = 'name=Python-Chat-Client&expires_in_days=365';
                
                var xhr = new XMLHttpRequest();
                xhr.withCredentials = true;
                
                xhr.onreadystatechange = function() {
                    if (xhr.readyState === 4) {
                        console.log('%c✅ CREATE RESPONSE RECEIVED', 'color: green; font-weight: bold');
                        console.log('Status:', xhr.status);
                        console.log('Response:', xhr.responseText);
                        try {
                            var data = JSON.parse(xhr.responseText);
                            window.tokenResponse = data;
                        } catch(e) {
                            window.tokenResponse = {error: 'Parse error', raw: xhr.responseText};
                        }
                    }
                };
                
                xhr.onerror = function() {
                    console.error('%c❌ REQUEST ERROR', 'color: red; font-weight: bold');
                    window.tokenResponse = {error: xhr.statusText};
                };
                
                xhr.open('POST', url, false);
                xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
                xhr.setRequestHeader('x-bitrix-csrf-token', csrf);
                xhr.setRequestHeader('x-bitrix-site-id', site_id);
                xhr.setRequestHeader('bx-ajax', 'true');
                xhr.send(body);
                
                console.log('%c📨 CREATE REQUEST COMPLETE', 'color: orange; font-weight: bold');
                """
                
                self.driver.execute_script(create_request_js, csrf_token, site_id)
                print("   ⏳ Processing response...")
                time.sleep(1)
                
                result = self.driver.execute_script(response_js)
                print(f"   ✓ Response: {result}")
                
                if result and result.get('status') == 'success' and result.get('data'):
                    data = result['data']
                    if isinstance(data, str):
                        print(f"\n   ✅ Token created successfully!")
                        token = data
                        print(f"   ✓ New Token: {token[:40]}...")
                    elif isinstance(data, dict) and data.get('PASSWORD'):
                        print(f"\n   ✅ Token created successfully!")
                        token = data['PASSWORD']
                        user_id = int(data.get('USER_ID', 1))
                        print(f"   ✓ New Token: {token[:40]}...")
                        print(f"   ✓ User ID: {user_id}")
                    else:
                        print(f"❌ Unexpected data format: {data}")
                        return None, None
                else:
                    if result and result.get('errors'):
                        print(f"✗ Errors: {result.get('errors')}")
                    else:
                        print(f"✗ Failed to create token")
                    return None, None
            
            # If we still don't have a token, something went wrong
            if not token:
                print(f"\n✗ Failed to obtain token")
                return None, None
            
            # If we don't have user_id yet, extract from browser
            if not user_id:
                print(f"\n3. Extracting user_id from browser...")
                
                user_id_js = """
                // Try multiple methods to get user_id
                var user_id = null;
                
                // Method 1: BX API
                if (typeof BX !== 'undefined' && typeof BX.User !== 'undefined') {
                    if (typeof BX.User.getId === 'function') {
                        user_id = BX.User.getId();
                        console.log('User ID from BX.User.getId:', user_id);
                    }
                }
                
                // Method 2: Cookies
                if (!user_id) {
                    var cookies = document.cookie.split(';');
                    for (var i = 0; i < cookies.length; i++) {
                        var cookie = cookies[i].trim();
                        if (cookie.indexOf('UAD_AVATAR=') === 0) {
                            user_id = parseInt(cookie.substring('UAD_AVATAR='.length));
                            console.log('User ID from UAD_AVATAR cookie:', user_id);
                            break;
                        }
                    }
                }
                
                // Method 3: Page elements
                if (!user_id) {
                    var elem = document.querySelector('[data-user-id], [data-uid]');
                    if (elem) {
                        var uid = elem.getAttribute('data-user-id') || elem.getAttribute('data-uid');
                        if (uid && uid.match(/\\d+/)) {
                            user_id = parseInt(uid.match(/(\\d+)/)[1]);
                            console.log('User ID from element:', user_id);
                        }
                    }
                }
                
                // Default to 1
                if (!user_id) {
                    user_id = 1;
                    console.log('User ID defaulting to:', user_id);
                }
                
                return user_id;
                """
                
                user_id = self.driver.execute_script(user_id_js)
                print(f"   ✓ User ID: {user_id}")
            
            print(f"\n✓ Successfully obtained in browser:")
            print(f"   Token: {token[:30]}...")
            print(f"   User ID: {user_id}")
            
            return token, user_id
            
        except Exception as e:
            print(f"\n✗ Exception: {e}")
            import traceback
            traceback.print_exc()
            return None, None
    
    def close(self):
        """Close browser"""
        self.driver.quit()