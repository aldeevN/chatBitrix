"""
Chrome authentication for Bitrix24
Uses Selenium for browser automation to capture authentication data
"""

import os
import sys
import time
import json
import pickle
from typing import Optional
from urllib.parse import urlparse, parse_qs
import subprocess
from pathlib import Path

# Selenium imports for browser automation
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

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
        self.target_url = "https://ugautodetal.ru/?login=yes"
        self.url_watch_active = False
    
    def navigate_to_login(self, url):
        """Navigate to login page"""
        self.driver.get(url)
        return self.driver.current_url
    
    def watch_for_target_url(self, timeout=300, check_interval=2):
        """
        Watch for the target URL to appear
        Returns True when target URL is detected
        """
        print(f"\n" + "="*60)
        print(f"WATCHING FOR TARGET URL")
        print(f"Target: {self.target_url}")
        print(f"Timeout: {timeout} seconds")
        print(f"="*60)
        
        start_time = time.time()
        self.url_watch_active = True
        
        while time.time() - start_time < timeout:
            current_url = self.driver.current_url
            
            # Normalize URLs for comparison (remove trailing slashes, etc.)
            target_normalized = self.target_url.rstrip('/')
            current_normalized = current_url.rstrip('/')
            
            # Check if current URL matches target
            if target_normalized == current_normalized:
                print(f"\n✅ TARGET URL DETECTED!")
                print(f"   Current URL: {current_url}")
                print(f"   Target URL: {self.target_url}")
                self.url_watch_active = False
                return True
            
            # Also check if we're on a login-related page
            if "login" in current_url.lower() or "auth" in current_url.lower():
                print(f"   🔍 On login page: {current_url}")
            
            # Print progress every 10 seconds
            elapsed = int(time.time() - start_time)
            if elapsed % 10 == 0:
                print(f"   ⏱️  Watching... {elapsed}s elapsed (timeout: {timeout}s)")
                print(f"   Current URL: {current_url}")
            
            time.sleep(check_interval)
        
        print(f"\n❌ TIMEOUT - Target URL not detected within {timeout} seconds")
        print(f"   Last URL: {self.driver.current_url}")
        self.url_watch_active = False
        return False
    
    def wait_for_login_completion(self, timeout=120, check_interval=2):
        """
        Wait for login to complete by watching for URL changes
        Returns True when login appears complete
        """
        print(f"\n" + "="*60)
        print(f"WAITING FOR LOGIN COMPLETION")
        print(f"Starting URL: {self.driver.current_url}")
        print(f"="*60)
        
        start_time = time.time()
        last_url = self.driver.current_url
        
        # Wait for URL to change from login page
        while time.time() - start_time < timeout:
            current_url = self.driver.current_url
            
            # Check if we've left the login page
            if current_url == 'https://ugautodetal.ru/?login=yes':
                print(f"\n✅ GET LOGIN PAGE")
                print(f"   New URL: {current_url}")
                
                # Wait a bit more to ensure page is fully loaded
                print(f"   Waiting 1 seconds for page to stabilize...")
                time.sleep(1)
                return True
            
            # Check if URL changed
            if current_url != last_url:
                print(f"   🔄 URL changed: {current_url}")
                last_url = current_url
            
            # Print progress every 5 seconds
            elapsed = int(time.time() - start_time)
            if elapsed % 5 == 0:
                print(f"   ⏱️  Still on login page... {elapsed}s")
            
            time.sleep(check_interval)
        
        print(f"\n❌ TIMEOUT - Still on login page after {timeout} seconds")
        return False
    
    def check_bitrix_cookies(self):
        """Check for Bitrix authentication cookies"""
        print("\n" + "="*60)
        print("CHECKING BITRIX AUTHENTICATION COOKIES")
        print("="*60)
        
        # Check via JavaScript
        check_cookie_js = """
        var cookies = document.cookie.split(';');
        var bitrix_cookies = {};
        
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            if (cookie.indexOf('BITRIX_') === 0 || cookie.indexOf('UID') === 0 || cookie.indexOf('USER_ID') === 0) {
                var parts = cookie.split('=');
                var name = parts[0];
                var value = parts[1] || '';
                bitrix_cookies[name] = value;
            }
        }
        
        console.log('Found Bitrix cookies:', Object.keys(bitrix_cookies));
        
        // Also check for any session-related cookies
        var session_cookies = {};
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            if (cookie.indexOf('SESSID') !== -1 || cookie.indexOf('sessid') !== -1 || 
                cookie.indexOf('SESSION') !== -1 || cookie.indexOf('session') !== -1) {
                var parts = cookie.split('=');
                var name = parts[0];
                var value = parts[1] || '';
                session_cookies[name] = value;
            }
        }
        
        console.log('Found session cookies:', Object.keys(session_cookies));
        
        return {
            'bitrix_cookies': bitrix_cookies,
            'session_cookies': session_cookies,
            'all_cookies': document.cookie
        };
        """
        
        cookies_data = self.driver.execute_script(check_cookie_js)
        bitrix_cookies = cookies_data.get('bitrix_cookies', {})
        session_cookies = cookies_data.get('session_cookies', {})
        
        # Check via Selenium get_cookies()
        selenium_cookies = self.driver.get_cookies()
        
        print("\n1. JavaScript Cookie Check:")
        if bitrix_cookies:
            print("   Found Bitrix cookies:")
            for name, value in bitrix_cookies.items():
                display_value = value[:30] + '...' if len(value) > 30 else value
                print(f"   - {name}: {display_value}")
        else:
            print("   ❌ No Bitrix cookies found via JavaScript")
        
        if session_cookies:
            print("\n   Found session cookies:")
            for name, value in session_cookies.items():
                display_value = value[:30] + '...' if len(value) > 30 else value
                print(f"   - {name}: {display_value}")
        
        print("\n2. Selenium Cookie Check:")
        bitrix_selenium = [c for c in selenium_cookies if 'BITRIX' in c['name'].upper()]
        if bitrix_selenium:
            print("   Found Bitrix cookies via Selenium:")
            for cookie in bitrix_selenium:
                value = cookie['value']
                display_value = value[:30] + '...' if len(value) > 30 else value
                print(f"   - {cookie['name']}: {display_value}")
        else:
            print("   ❌ No Bitrix cookies found via Selenium")
        
        # Check for specific important cookies
        important_cookies = {
            'BITRIX_SM_UIDL': 'Primary user authentication cookie',
            'BITRIX_SM_GUEST_ID': 'Guest session identifier',
            'BITRIX_SM_LAST_VISIT': 'Last visit timestamp',
            'BITRIX_SM_LAST_ADV': 'Last advertisement click',
            'PHPSESSID': 'PHP session ID',
            'UID': 'User ID cookie'
        }
        
        print("\n3. Important Authentication Cookies:")
        all_cookies_dict = {c['name']: c['value'] for c in selenium_cookies}
        found_important = []
        
        for cookie_name, description in important_cookies.items():
            if cookie_name in all_cookies_dict:
                value = all_cookies_dict[cookie_name]
                display_value = value[:30] + '...' if len(value) > 30 else value
                print(f"   ✅ {cookie_name}: {display_value}")
                print(f"     Description: {description}")
                found_important.append(cookie_name)
            elif cookie_name.lower() in [c.lower() for c in all_cookies_dict.keys()]:
                # Case insensitive check
                for actual_name in all_cookies_dict.keys():
                    if actual_name.upper() == cookie_name:
                        value = all_cookies_dict[actual_name]
                        display_value = value[:30] + '...' if len(value) > 30 else value
                        print(f"   ✅ {actual_name}: {display_value}")
                        print(f"     Description: {description}")
                        found_important.append(actual_name)
                        break
            else:
                print(f"   ❌ {cookie_name}: Not found")
        
        # Determine authentication status
        has_bitrix_uidl = 'BITRIX_SM_UIDL' in found_important or any('BITRIX_SM_UIDL' in c.upper() for c in all_cookies_dict.keys())
        has_php_sessid = 'PHPSESSID' in found_important or any('PHPSESSID' in c.upper() for c in all_cookies_dict.keys())
        has_any_bitrix = len(bitrix_selenium) > 0 or len(bitrix_cookies) > 0
        
        print("\n4. Authentication Status:")
        if has_bitrix_uidl:
            print("   ✅ STRONGLY AUTHENTICATED - BITRIX_SM_UIDL found")
            print("   This is the main authentication cookie for Bitrix24")
            auth_status = "authenticated"
        elif has_php_sessid and has_any_bitrix:
            print("   ⚠️  PARTIALLY AUTHENTICATED - Session cookies found")
            print("   May be logged in but missing primary auth cookie")
            auth_status = "partial"
        elif has_any_bitrix:
            print("   ⚠️  POSSIBLY AUTHENTICATED - Some Bitrix cookies found")
            print("   But missing key authentication cookies")
            auth_status = "possible"
        else:
            print("   ❌ NOT AUTHENTICATED - No Bitrix cookies found")
            auth_status = "not_authenticated"
        
        print("\n" + "="*60)
        return auth_status, {
            'bitrix_cookies': bitrix_cookies,
            'session_cookies': session_cookies,
            'selenium_cookies': {c['name']: c['value'] for c in selenium_cookies},
            'has_bitrix_uidl': has_bitrix_uidl,
            'has_php_sessid': has_php_sessid
        }
    
    # MAIN METHOD - This is what you should call
    def get_api_token_in_browser(self):
        """
        Main method: Wait for login page, then get token after login completes
        This is the method that should be called from main.py
        """
        print("\n" + "="*60)
        print("BITRIX24 API TOKEN ACQUISITION")
        print("="*60)
        
        # Step 1: Watch for the target login URL
        print("\n1. Waiting for login page...")
        if not self.watch_for_target_url(timeout=300):
            print("❌ Did not reach login page. Starting from current URL...")
        
        current_url = self.driver.current_url
        print(f"   Current URL: {current_url}")
        
        # Step 2: Wait for login to complete
        print("\n2. Waiting for login completion...")
        print("   Please log in manually in the browser window...")
        print("   The script will wait for you to complete login.")
        
        if not self.wait_for_login_completion(timeout=180):
            print("⚠️  Login may not have completed, but continuing...")
        
        # Step 3: Check authentication cookies
        print("\n3. Verifying authentication...")
        auth_status, cookie_info = self.check_bitrix_cookies()
        
        if auth_status in ["not_authenticated", "possible"]:
            print(f"\n⚠️  Weak authentication detected: {auth_status}")
            print("Trying to proceed anyway...")
        
        # Step 4: Navigate to main page if needed
        current_url = self.driver.current_url
        if "?login=yes" not in current_url and "?login=yes" not in current_url:
            print("\n4. Navigating to main Bitrix24 page...")
            main_url = "https://ugautodetal.ru/getKey/"
            print(f"   Going to: {main_url}")
            self.driver.get(main_url)
            time.sleep(5)
        
        # Step 5: Get CSRF token
        print("\n5. Extracting CSRF token...")
        csrf_token, site_id = self.extract_csrf_token()
        
        if not csrf_token:
            print("❌ Failed to extract CSRF token")
            return None, None
        
        # Step 6: Get API token
        print("\n6. Getting API token...")
        token, user_id = self.request_api_token(csrf_token, site_id)
        
        if token:
            print(f"\n" + "="*60)
            print("✅ TOKEN ACQUISITION COMPLETE")
            print("="*60)
            print(f"   Token: {token[:50]}...")
            print(f"   User ID: {user_id}")
            print(f"   Token length: {len(token)} characters")
            
            # Save token
            self.save_token_to_file(token, user_id, csrf_token, site_id)
            
            return token, user_id
        else:
            print("❌ Failed to get API token")
            return None, None
    
    # ALIAS - for backward compatibility
    def get_api_token_after_login(self):
        """Alias for get_api_token_in_browser for backward compatibility"""
        return self.get_api_token_in_browser()
    
    def extract_csrf_token(self):
        """Extract CSRF token and site ID from page"""
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
        
        // Try form input
        if (!csrf_value) {
            var form_csrf = document.querySelector('input[name="sessid"], input[name="csrf"], input[name="bitrix_sessid"]');
            if (form_csrf) {
                csrf_value = form_csrf.value;
            }
        }
        
        // Try from URL parameters
        if (!csrf_value) {
            var urlParams = new URLSearchParams(window.location.search);
            csrf_value = urlParams.get('sessid') || urlParams.get('csrf') || urlParams.get('bitrix_sessid');
        }
        
        // Try to find in page scripts
        if (!csrf_value) {
            var scripts = document.getElementsByTagName('script');
            for (var i = 0; i < scripts.length; i++) {
                var scriptContent = scripts[i].innerText;
                if (scriptContent.includes('bitrix_sessid') && scriptContent.includes('=')) {
                    var match = scriptContent.match(/bitrix_sessid['"]?\\s*[:=]\\s*['"]([^'"]+)['"]/i);
                    if (match) {
                        csrf_value = match[1];
                        break;
                    }
                }
            }
        }
        
        // Get site ID
        var site_id = 'ap'; // Default
        var site_meta = document.querySelector('meta[name="x-bitrix-site-id"]');
        if (site_meta) {
            site_id = site_meta.getAttribute('content');
        } else if (typeof BX !== 'undefined' && typeof BX.message === 'function') {
            // Try to get from BX
            var bx_site_id = BX.message('site_id') || BX.message('SITE_ID');
            if (bx_site_id) {
                site_id = bx_site_id;
            }
        }
        
        console.log('CSRF Token:', csrf_value ? csrf_value.substring(0, 30) + '...' : 'Not found');
        console.log('Site ID:', site_id);
        
        return {
            csrf: csrf_value,
            site_id: site_id
        };
        """
        
        csrf_data = self.driver.execute_script(csrf_js)
        csrf_token = csrf_data.get('csrf')
        site_id = csrf_data.get('site_id', 'ap')
        
        if not csrf_token:
            print("   ⚠️  CSRF token not found in meta tags, trying alternative methods...")
            
            # Last attempt: extract from any script tag
            last_csrf_attempt = """
            // Search through all script content for bitrix_sessid
            var scripts = document.getElementsByTagName('script');
            for (var i = 0; i < scripts.length; i++) {
                var content = scripts[i].innerHTML;
                // Look for bitrix_sessid in various formats
                var patterns = [
                    /bitrix_sessid['"]?\\s*[:=]\\s*['"]([a-f0-9]+)['"]/i,
                    /sessid['"]?\\s*[:=]\\s*['"]([a-f0-9]+)['"]/i,
                    /csrf['"]?\\s*[:=]\\s*['"]([a-f0-9]+)['"]/i,
                    /"bitrix_sessid":"([a-f0-9]+)"/i,
                    /'bitrix_sessid':'([a-f0-9]+)'/i
                ];
                
                for (var j = 0; j < patterns.length; j++) {
                    var match = content.match(patterns[j]);
                    if (match && match[1]) {
                        return {csrf: match[1], site_id: 'ap'};
                    }
                }
            }
            return {csrf: null, site_id: 'ap'};
            """
            
            result = self.driver.execute_script(last_csrf_attempt)
            csrf_token = result.get('csrf')
        
        if csrf_token:
            print(f"   ✅ CSRF Token: {csrf_token[:30]}...")
            print(f"   ✅ Site ID: {site_id}")
            return csrf_token, site_id
        else:
            print("   ❌ Could not find CSRF token")
            return None, None
    
    def request_api_token(self, csrf_token, site_id):
        """Request API token using CSRF token"""
        # First, try to get existing token
        print("   Trying to get existing API token...")
        
        token_request_js = """
        var csrf = arguments[0];
        var site_id = arguments[1];
        
        var url = '/bitrix/services/main/ajax.php?action=me%3Abase.api.user.getTokenApi';
        
        console.log('%c📤 SENDING GET TOKEN REQUEST', 'color: blue; font-weight: bold');
        console.log('URL:', url);
        console.log('CSRF:', csrf ? csrf.substring(0, 30) + '...' : 'null');
        console.log('Site ID:', site_id);
        
        var xhr = new XMLHttpRequest();
        xhr.withCredentials = true;
        
        xhr.onreadystatechange = function() {
            if (xhr.readyState === 4) {
                console.log('%c✅ RESPONSE RECEIVED', 'color: green; font-weight: bold');
                console.log('Status:', xhr.status);
                console.log('Response:', xhr.responseText);
                try {
                    var data = JSON.parse(xhr.responseText);
                    window.tokenResponse = data;
                } catch(e) {
                    console.error('Parse error:', e);
                    window.tokenResponse = {error: 'Parse error', raw: xhr.responseText};
                }
            }
        };
        
        xhr.onerror = function() {
            console.error('%c❌ REQUEST ERROR', 'color: red; font-weight: bold');
            window.tokenResponse = {error: xhr.statusText || 'Network error'};
        };
        
        xhr.open('POST', url, false);
        xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
        xhr.setRequestHeader('x-bitrix-csrf-token', csrf);
        xhr.setRequestHeader('x-bitrix-site-id', site_id);
        xhr.setRequestHeader('bx-ajax', 'true');
        xhr.send('');
        
        return 'Get token request sent';
        """
        
        self.driver.execute_script(token_request_js, csrf_token, site_id)
        time.sleep(3)
        
        response_js = "return window.tokenResponse;"
        result = self.driver.execute_script(response_js)
        
        token = None
        user_id = None
        
        if result and result.get('status') == 'success' and result.get('data'):
            data = result['data']
            if isinstance(data, dict) and data.get('PASSWORD'):
                token = data['PASSWORD']
                user_id = int(data.get('USER_ID', 1))
                print(f"   ✅ Existing token found!")
                print(f"   ✓ Token: {token[:40]}...")
                print(f"   ✓ User ID: {user_id}")
            elif isinstance(data, str):
                token = data
                print(f"   ✅ Existing token found!")
                print(f"   ✓ Token: {token[:40]}...")
        
        # If no existing token, create new one
        if not token:
            print("   No existing token found. Creating new token...")
            time.sleep(2)
            
            create_request_js = """
            var csrf = arguments[0];
            var site_id = arguments[1];
            
            var url = '/bitrix/services/main/ajax.php?action=me%3Abase.api.user.createTokenApi';
            
            console.log('%c📤 CREATING NEW TOKEN', 'color: blue; font-weight: bold');
            console.log('URL:', url);
            
            // Request body with permissions
            var body = 'name=Python-API-Client-' + Date.now() + '&expires_in_days=365&permissions[]=user&permissions[]=crm&permissions[]=im&permissions[]=entity&permissions[]=task';
            
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
                        console.error('Parse error:', e);
                        window.tokenResponse = {error: 'Parse error', raw: xhr.responseText};
                    }
                }
            };
            
            xhr.onerror = function() {
                console.error('%c❌ REQUEST ERROR', 'color: red; font-weight: bold');
                window.tokenResponse = {error: xhr.statusText || 'Network error'};
            };
            
            xhr.open('POST', url, false);
            xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
            xhr.setRequestHeader('x-bitrix-csrf-token', csrf);
            xhr.setRequestHeader('x-bitrix-site-id', site_id);
            xhr.setRequestHeader('bx-ajax', 'true');
            xhr.send(body);
            
            return 'Create token request sent';
            """
            
            self.driver.execute_script(create_request_js, csrf_token, site_id)
            time.sleep(3)
            
            result = self.driver.execute_script(response_js)
            
            if result and result.get('status') == 'success' and result.get('data'):
                data = result['data']
                if isinstance(data, str):
                    token = data
                    print(f"   ✅ New token created!")
                    print(f"   ✓ Token: {token[:40]}...")
                elif isinstance(data, dict) and data.get('PASSWORD'):
                    token = data['PASSWORD']
                    user_id = int(data.get('USER_ID', 1))
                    print(f"   ✅ New token created!")
                    print(f"   ✓ Token: {token[:40]}...")
                    print(f"   ✓ User ID: {user_id}")
                else:
                    print(f"   ❌ Unexpected response format: {data}")
                    return None, None
            else:
                print(f"   ❌ Failed to create token")
                if result:
                    print(f"   Errors: {result.get('errors', 'Unknown error')}")
                return None, None
        
        # Get user_id if not obtained
        if not user_id and token:
            user_id = self.extract_user_id()
        
        return token, user_id
    
    def extract_user_id(self):
        """Extract user ID from page"""
        user_id_js = """
        var user_id = null;
        
        // Method 1: BX API (most reliable)
        if (typeof BX !== 'undefined' && typeof BX.User !== 'undefined') {
            if (typeof BX.User.getId === 'function') {
                user_id = BX.User.getId();
                console.log('User ID from BX.User.getId:', user_id);
            }
        }
        
        // Method 2: Global BX object
        if (!user_id && typeof BX !== 'undefined') {
            if (BX.user_id) {
                user_id = BX.user_id;
                console.log('User ID from BX.user_id:', user_id);
            } else if (BX.userId) {
                user_id = BX.userId;
                console.log('User ID from BX.userId:', user_id);
            }
        }
        
        // Method 3: Cookies
        if (!user_id) {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = cookies[i].trim();
                if (cookie.indexOf('UID=') === 0) {
                    var uid = cookie.substring('UID='.length);
                    if (uid && !isNaN(parseInt(uid))) {
                        user_id = parseInt(uid);
                        console.log('User ID from UID cookie:', user_id);
                        break;
                    }
                }
                if (cookie.indexOf('USER_ID=') === 0) {
                    var uid = cookie.substring('USER_ID='.length);
                    if (uid && !isNaN(parseInt(uid))) {
                        user_id = parseInt(uid);
                        console.log('User ID from USER_ID cookie:', user_id);
                        break;
                    }
                }
                if (cookie.indexOf('BITRIX_SM_UID=') === 0) {
                    var uid = cookie.substring('BITRIX_SM_UID='.length);
                    if (uid && !isNaN(parseInt(uid))) {
                        user_id = parseInt(uid);
                        console.log('User ID from BITRIX_SM_UID cookie:', user_id);
                        break;
                    }
                }
            }
        }
        
        // Method 4: Page elements
        if (!user_id) {
            var selectors = [
                '[data-user-id]',
                '[data-uid]',
                '[data-id]',
                '.user-id',
                '.user_id',
                '#user_id',
                '#userId'
            ];
            
            for (var j = 0; j < selectors.length; j++) {
                var elem = document.querySelector(selectors[j]);
                if (elem) {
                    var uid = elem.getAttribute('data-user-id') || 
                              elem.getAttribute('data-uid') || 
                              elem.getAttribute('data-id') ||
                              elem.getAttribute('value') ||
                              elem.textContent;
                    
                    if (uid) {
                        var match = uid.toString().match(/(\\d+)/);
                        if (match) {
                            user_id = parseInt(match[1]);
                            console.log('User ID from element (' + selectors[j] + '):', user_id);
                            break;
                        }
                    }
                }
            }
        }
        
        // Method 5: Default to 1
        if (!user_id) {
            user_id = 1;
            console.log('User ID defaulting to:', user_id);
        }
        
        return user_id;
        """
        
        user_id = self.driver.execute_script(user_id_js)
        print(f"   ✅ User ID: {user_id}")
        return user_id
    
    def save_token_to_file(self, token, user_id, csrf_token, site_id):
        """Save token to JSON file"""
        try:
            token_data = {
                'token': token,
                'user_id': user_id,
                'local_storage': app.get_local_storage() if hasattr(app, 'get_local_storage') else {},
                'csrf_token': csrf_token,
                'site_id': site_id,
                'timestamp': time.time(),
                'date': time.strftime('%Y-%m-%d %H:%M:%S'),
                'url': self.driver.current_url
            }
            
            with open('bitrix_token.json', 'w') as f:
                json.dump(token_data, f, indent=2)
            
            print(f"   💾 Token saved to bitrix_token.json")
            return True
        except Exception as e:
            print(f"   ⚠️  Could not save token to file: {e}")
            return False
    
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
                    if 'expiry' in cookie:
                        del cookie['expiry']
                    self.driver.add_cookie(cookie)
                except Exception as e:
                    print(f"   ⚠️  Could not add cookie {cookie.get('name', 'unknown')}: {e}")
                    continue
            
            self.driver.refresh()
            time.sleep(3)
            
            return True
        except Exception as e:
            print(f"   ❌ Error loading cookies: {e}")
            return False
    
    def save_cookies(self, filename='cookies.pkl'):
        """Save current cookies to file"""
        cookies = self.driver.get_cookies()
        with open(filename, 'wb') as f:
            pickle.dump(cookies, f)
        print(f"Cookies saved to {filename}")
    
    def close(self):
        """Close browser"""
        self.driver.quit()


# Main execution
if __name__ == "__main__":
    # Create the authentication app
    print("Starting Bitrix24 Authentication...")
    app = ChromeAuthApp(headless=False)
    
    try:
        # Start URL - you can change this to your Bitrix24 domain
        start_url = "https://ugautodetal.ru/"
        print(f"\nNavigating to: {start_url}")
        app.navigate_to_login(start_url)
        
        # Get the token after login process
        # This calls the main method that your main.py expects
        token, user_id = app.get_api_token_in_browser()
        
        if token:
            print(f"\n🎉 Successfully obtained API token!")
            print(f"   Token (first 60 chars): {token[:60]}...")
            print(f"   Full token length: {len(token)} characters")
            print(f"   User ID: {user_id}")
            
            # Save cookies for future use
            app.save_cookies()
            
            print(f"\nYou can now use this token for API calls.")
            print(f"The token has been saved to 'bitrix_token.json'")
            
            # Load csrf_token and site_id from saved file
            try:
                with open('bitrix_token.json', 'r') as f:
                    saved_data = json.load(f)
                    csrf_token = saved_data.get('csrf_token', '')
                    site_id = saved_data.get('site_id', 'ap')
            except Exception as e:
                print(f"   ⚠️ Could not load CSRF token from file: {e}")
                csrf_token = ''
                site_id = 'ap'
            
            # Also write token to .env for the chat launcher
            try:
                env_path = Path(__file__).parent / '.env'
                env_lines = []
                if env_path.exists():
                    with open(env_path, 'r', encoding='utf-8') as ef:
                        env_lines = ef.read().splitlines()

                # Prepare entries to ensure we don't duplicate
                entries = {
                    'BITRIX_REST_TOKEN': token,
                    'BITRIX_USER_ID': str(user_id),
                    'BITRIX_CSRF_TOKEN': csrf_token,
                    'BITRIX_SITE_ID': site_id,
                    'local_storage': app.get_local_storage() if hasattr(app, 'get_local_storage') else {},
                    'BITRIX_API_URL': 'https://ugautodetal.ru/stream/'
                }

                # Update or append entries
                for k, v in entries.items():
                    found = False
                    for i, line in enumerate(env_lines):
                        if line.startswith(k + "="):
                            env_lines[i] = f"{k}={v}"
                            found = True
                            break
                    if not found:
                        env_lines.append(f"{k}={v}")

                with open(env_path, 'w', encoding='utf-8') as ef:
                    ef.write("\n".join(env_lines) + ("\n" if env_lines and not env_lines[-1].endswith("\n") else ""))
                print(f"   ✓ Token and auth data written to {env_path}")
            except Exception as e:
                print(f"   ⚠️ Failed to write .env: {e}")

            # Launch the chat UI in a separate process if launcher exists
            try:
                launcher = Path(__file__).parent / 'run_chat.py'
                if launcher.exists():
                    print("\nLaunching chat UI...")
                    subprocess.Popen([sys.executable, str(launcher)], cwd=str(Path(__file__).parent))
                    print("   ✓ Chat UI started (in background)")
                else:
                    print("   ⚠️ Chat launcher 'run_chat.py' not found; start it manually")
            except Exception as e:
                print(f"   ⚠️ Failed to start chat UI: {e}")
        else:
            print("\n❌ Failed to obtain API token")
            print("Please check:")
            print("1. You successfully logged in")
            print("2. You have permission to create API tokens")
            print("3. The Bitrix24 instance supports API tokens")
        
    except Exception as e:
        print(f"\n❌ Error during authentication: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Keep browser open for inspection
        print("\n" + "="*60)
        print("Browser will remain open for inspection.")
        print("Press Ctrl+C to close immediately.")
        print("="*60)
        
        try:
            # Keep browser open
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nClosing browser...")
            app.close()