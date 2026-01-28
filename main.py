#!/usr/bin/env python3
"""
Bitrix24 Chat Application - Consolidated Entry Point

Smart Startup Features:
1. Check for REST API credentials in .env
2. If both BITRIX_REST_TOKEN and BITRIX_USER_ID exist: Start chat directly
3. If missing: Open Chromium for authentication
4. After auth: Automatically start chat
5. Handle all three flows in single file

Execution Modes:
- python3 main.py              → Smart startup (auto-detect credentials)
- python3 main.py --auth-only   → Authentication only (get token)
- python3 main.py --chat-only   → Start chat only (assumes credentials exist)
"""

import os
import sys
import time
import json
import pickle
import traceback
import argparse
from pathlib import Path
from typing import Optional, Tuple

# ============================================================================
# CRITICAL: Set Qt platform plugin path BEFORE any PyQt5 imports
# This section MUST come before ANY other imports
# ============================================================================

def setup_qt_plugins():
    """Setup Qt plugin paths for different environments"""
    # Check if we're running as a PyInstaller executable
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        application_path = sys._MEIPASS
        plugin_path = os.path.join(application_path, 'PyQt5', 'Qt5', 'plugins', 'platforms')
        if os.path.exists(plugin_path):
            os.environ['QT_QPA_PLUGIN_PATH'] = plugin_path
            os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path
            print(f"📦 PyInstaller mode - Plugin path: {plugin_path}")
            return True
        else:
            # Try alternative location
            plugin_path = os.path.join(application_path, 'platforms')
            if os.path.exists(plugin_path):
                os.environ['QT_QPA_PLUGIN_PATH'] = plugin_path
                os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path
                print(f"📦 PyInstaller mode - Plugin path (alt): {plugin_path}")
                return True
    
    # Normal Python script mode
    print("🔍 Setting up Qt plugins for normal Python mode...")
    
    # Method 1: Try to find PyQt5 package
    try:
        import site
        import importlib.util
        
        # Get all possible site-packages directories
        site_packages_paths = []
        site_packages_paths.extend(site.getsitepackages())
        
        # Add user site-packages
        if hasattr(site, 'getusersitepackages'):
            user_site = site.getusersitepackages()
            if user_site:
                site_packages_paths.append(user_site)
        
        # Add virtual environment paths
        if hasattr(sys, 'real_prefix'):  # virtualenv
            site_packages_paths.append(os.path.join(sys.prefix, 'lib', f'python{sys.version_info.major}.{sys.version_info.minor}', 'site-packages'))
        elif hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix:  # venv
            site_packages_paths.append(os.path.join(sys.prefix, 'lib', f'python{sys.version_info.major}.{sys.version_info.minor}', 'site-packages'))
        
        # Add current Python path directories
        for path in sys.path:
            if 'site-packages' in path and path not in site_packages_paths:
                site_packages_paths.append(path)
        
        print(f"📁 Searching {len(site_packages_paths)} site-packages locations...")
        
        # Search for PyQt5 in all site-packages directories
        for site_pkg in site_packages_paths:
            if not os.path.exists(site_pkg):
                continue
                
            # Look for PyQt5 directory
            pyqt5_path = os.path.join(site_pkg, 'PyQt5')
            if os.path.exists(pyqt5_path):
                # Try multiple possible plugin locations
                possible_plugin_paths = [
                    os.path.join(pyqt5_path, 'Qt5', 'plugins', 'platforms'),
                    os.path.join(pyqt5_path, 'Qt', 'plugins', 'platforms'),
                    os.path.join(pyqt5_path, 'plugins', 'platforms'),
                ]
                
                for plugin_path in possible_plugin_paths:
                    if os.path.exists(plugin_path):
                        os.environ['QT_QPA_PLUGIN_PATH'] = plugin_path
                        os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path
                        print(f"✅ Found Qt plugins at: {plugin_path}")
                        return True
        
    except Exception as e:
        print(f"⚠️  Could not search site-packages: {e}")
    
    # Method 2: Try to import PyQt5 and find its path
    try:
        import PyQt5
        pyqt5_dir = os.path.dirname(PyQt5.__file__)
        
        # Try different possible plugin locations
        possible_paths = [
            os.path.join(pyqt5_dir, 'Qt5', 'plugins', 'platforms'),
            os.path.join(pyqt5_dir, 'Qt', 'plugins', 'platforms'),
            os.path.join(pyqt5_dir, 'plugins', 'platforms'),
            os.path.join(os.path.dirname(pyqt5_dir), 'PyQt5', 'Qt5', 'plugins', 'platforms'),
        ]
        
        for plugin_path in possible_paths:
            if os.path.exists(plugin_path):
                os.environ['QT_QPA_PLUGIN_PATH'] = plugin_path
                os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path
                print(f"✅ Found Qt plugins via PyQt5 import: {plugin_path}")
                return True
        
        # If we found PyQt5 but not plugins, try to use PyQt5's QLibraryInfo
        try:
            from PyQt5.QtCore import QLibraryInfo
            plugin_path = QLibraryInfo.location(QLibraryInfo.PluginsPath)
            if os.path.exists(plugin_path):
                os.environ['QT_QPA_PLUGIN_PATH'] = plugin_path
                os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path
                print(f"✅ Found Qt plugins via QLibraryInfo: {plugin_path}")
                return True
        except:
            pass
            
    except ImportError:
        print("⚠️  PyQt5 not installed yet, will be imported later")
    
    # Method 3: Common installation locations
    print("🔍 Trying common installation locations...")
    common_paths = []
    
    # Windows common paths
    if sys.platform == 'win32':
        import glob
        # Python installation directories
        python_dirs = [
            os.path.dirname(sys.executable),
            sys.prefix,
            os.path.expanduser('~'),
        ]
        
        for python_dir in python_dirs:
            common_paths.extend([
                os.path.join(python_dir, 'Lib', 'site-packages', 'PyQt5', 'Qt5', 'plugins', 'platforms'),
                os.path.join(python_dir, 'Lib', 'site-packages', 'PyQt5', 'Qt', 'plugins', 'platforms'),
                os.path.join(python_dir, 'AppData', 'Roaming', 'Python', f'Python{sys.version_info.major}{sys.version_info.minor}', 'site-packages', 'PyQt5', 'Qt5', 'plugins', 'platforms'),
                os.path.join(python_dir, 'Local', 'Programs', 'Python', f'Python{sys.version_info.major}{sys.version_info.minor}', 'Lib', 'site-packages', 'PyQt5', 'Qt5', 'plugins', 'platforms'),
            ])
    
    # Linux/Mac common paths
    else:
        home = os.path.expanduser('~')
        common_paths.extend([
            os.path.join(home, '.local', 'lib', f'python{sys.version_info.major}.{sys.version_info.minor}', 'site-packages', 'PyQt5', 'Qt5', 'plugins', 'platforms'),
            f'/usr/lib/python{sys.version_info.major}.{sys.version_info.minor}/site-packages/PyQt5/Qt5/plugins/platforms',
            f'/usr/local/lib/python{sys.version_info.major}.{sys.version_info.minor}/site-packages/PyQt5/Qt5/plugins/platforms',
        ])
    
    for plugin_path in common_paths:
        if os.path.exists(plugin_path):
            os.environ['QT_QPA_PLUGIN_PATH'] = plugin_path
            os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path
            print(f"✅ Found Qt plugins at common location: {plugin_path}")
            return True
    
    print("⚠️  Could not find Qt plugins automatically. The app might need PyQt5 installation.")
    print("💡 Try running: pip install PyQt5 PyQtWebEngine")
    return False

# Run the Qt plugin setup
qt_plugins_found = setup_qt_plugins()

# Now we can safely import dotenv
from dotenv import load_dotenv

# ============================================================================
# SECTION 1: CHROME AUTHENTICATION APPLICATION
# ============================================================================

class ChromeAuthApp:
    """Browser automation for Bitrix24 authentication"""
    
    def __init__(self, headless=False):
        # Import selenium here to avoid issues if Qt has problems
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.support.ui import WebDriverWait
        
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
        """Watch for the target URL to appear"""
        print(f"\n" + "="*60)
        print(f"WATCHING FOR TARGET URL")
        print(f"Target: {self.target_url}")
        print(f"Timeout: {timeout} seconds")
        print(f"="*60)
        
        start_time = time.time()
        self.url_watch_active = True
        
        while time.time() - start_time < timeout:
            current_url = self.driver.current_url
            target_normalized = self.target_url.rstrip('/')
            current_normalized = current_url.rstrip('/')
            
            if target_normalized == current_normalized:
                print(f"\n✅ TARGET URL DETECTED!")
                print(f"   Current URL: {current_url}")
                print(f"   Target URL: {self.target_url}")
                self.url_watch_active = False
                return True
            
            if "login" in current_url.lower() or "auth" in current_url.lower():
                print(f"   🔍 On login page: {current_url}")
            
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
        """Wait for login to complete by watching for URL changes"""
        print(f"\n" + "="*60)
        print(f"WAITING FOR LOGIN COMPLETION")
        print(f"Starting URL: {self.driver.current_url}")
        print(f"="*60)
        
        start_time = time.time()
        last_url = self.driver.current_url
        
        while time.time() - start_time < timeout:
            current_url = self.driver.current_url
            
            if current_url != last_url:
                print(f"   🔄 URL changed: {current_url}")
                last_url = current_url
            
            # Check if we're off the login page
            if "?login=yes" not in current_url and "login" not in current_url.lower():
                print(f"\n✅ LOGIN COMPLETED!")
                print(f"   Current URL: {current_url}")
                return True
            
            elapsed = int(time.time() - start_time)
            if elapsed % 10 == 0:
                print(f"   ⏱️  Waiting... {elapsed}s elapsed (timeout: {timeout}s)")
            
            time.sleep(check_interval)
        
        print(f"\n❌ TIMEOUT - Still on login page after {timeout} seconds")
        return False
    
    def check_bitrix_cookies(self):
        """Check for Bitrix authentication cookies"""
        print("\n" + "="*60)
        print("CHECKING BITRIX AUTHENTICATION COOKIES")
        print("="*60)
        
        check_cookie_js = """
        var cookies = document.cookie.split(';');
        var bitrix_cookies = {};
        
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            if (cookie.indexOf('BITRIX_') === 0 || cookie.indexOf('UID') === 0) {
                var parts = cookie.split('=');
                bitrix_cookies[parts[0]] = parts[1] || '';
            }
        }
        
        var session_cookies = {};
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            if (cookie.indexOf('SESSID') !== -1 || cookie.indexOf('SESSION') !== -1) {
                var parts = cookie.split('=');
                session_cookies[parts[0]] = parts[1] || '';
            }
        }
        
        return {
            'bitrix_cookies': bitrix_cookies,
            'session_cookies': session_cookies,
        };
        """
        
        cookies_data = self.driver.execute_script(check_cookie_js)
        bitrix_cookies = cookies_data.get('bitrix_cookies', {})
        
        print("\n1. Bitrix Cookies Found:")
        if bitrix_cookies:
            for name, value in bitrix_cookies.items():
                print(f"   ✅ {name}: {value[:30]}..." if len(str(value)) > 30 else f"   ✅ {name}: {value}")
        else:
            print("   ❌ No Bitrix cookies found")
        
        selenium_cookies = self.driver.get_cookies()
        bitrix_selenium = [c for c in selenium_cookies if 'BITRIX' in c['name'].upper()]
        
        print("\n2. Selenium Cookie Check:")
        if bitrix_selenium:
            for c in bitrix_selenium[:3]:
                print(f"   ✅ {c['name']}")
        else:
            print("   ❌ No Bitrix cookies via Selenium")
        
        print("\n" + "="*60)
    
    def get_api_token_in_browser(self):
        """Main method: Get token after login completes"""
        print("\n" + "="*60)
        print("BITRIX24 API TOKEN ACQUISITION")
        print("="*60)
        
        print("\n1. Waiting for login page...")
        if not self.watch_for_target_url(timeout=300):
            print("❌ Failed to reach login page")
            return None, None
        
        print("\n2. Waiting for login completion...")
        print("   Please log in manually in the browser window...")
        
        if not self.wait_for_login_completion(timeout=180):
            print("❌ Login timeout")
            return None, None
        
        print("\n3. Verifying authentication...")
        self.check_bitrix_cookies()
        
        print("\n4. Extracting CSRF token...")
        csrf_token, site_id = self.extract_csrf_token()
        
        if not csrf_token:
            print("❌ Failed to extract CSRF token")
            return None, None
        
        print("\n5. Getting API token...")
        token, user_id = self.request_api_token(csrf_token, site_id)
        
        if token:
            print(f"\n✅ SUCCESS!")
            print(f"   Token: {token[:30]}...")
            print(f"   User ID: {user_id}")
            self.save_token_to_file_with_storage(token, user_id, csrf_token, site_id)
            return token, user_id
        else:
            print("❌ Failed to get API token")
            return None, None
    
    def extract_csrf_token(self):
        """Extract CSRF token and site ID from page"""
        csrf_js = """
        var csrf = document.querySelector('meta[name="x-bitrix-csrf-token"]');
        var csrf_value = csrf ? csrf.getAttribute('content') : null;
        
        if (!csrf_value && typeof BX !== 'undefined') {
            csrf_value = BX.message('bitrix_sessid');
        }
        
        if (!csrf_value && typeof window.bitrix_sessid !== 'undefined') {
            csrf_value = window.bitrix_sessid;
        }
        
        var site_id = 'ap';
        var site_meta = document.querySelector('meta[name="x-bitrix-site-id"]');
        if (site_meta) {
            site_id = site_meta.getAttribute('content');
        }
        
        return {csrf: csrf_value, site_id: site_id};
        """
        
        csrf_data = self.driver.execute_script(csrf_js)
        csrf_token = csrf_data.get('csrf')
        site_id = csrf_data.get('site_id', 'ap')
        
        if csrf_token:
            print(f"   ✅ CSRF Token: {csrf_token[:30]}...")
            print(f"   ✅ Site ID: {site_id}")
        else:
            print("   ❌ CSRF Token not found")
        
        return csrf_token, site_id
    
    def request_api_token(self, csrf_token, site_id):
        """Request API token using CSRF token"""
        print("   Requesting token...")
        
        token_request_js = """
        var csrf = arguments[0];
        var site_id = arguments[1];
        var url = '/bitrix/services/main/ajax.php?action=me%3Abase.api.user.getTokenApi';
        
        var xhr = new XMLHttpRequest();
        xhr.withCredentials = true;
        
        xhr.onreadystatechange = function() {
            if (xhr.readyState === 4) {
                try {
                    var data = JSON.parse(xhr.responseText);
                    window.tokenResponse = data;
                } catch(e) {
                    window.tokenResponse = {error: 'Parse error', raw: xhr.responseText};
                }
            }
        };
        
        xhr.open('POST', url, false);
        xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
        xhr.setRequestHeader('x-bitrix-csrf-token', csrf);
        xhr.setRequestHeader('x-bitrix-site-id', site_id);
        xhr.setRequestHeader('bx-ajax', 'true');
        xhr.send('');
        
        return 'Token request sent';
        """
        
        self.driver.execute_script(token_request_js, csrf_token, site_id)
        
        response_js = "return window.tokenResponse;"
        result = self.driver.execute_script(response_js)

        token = None
        user_id = None
        
        if result and result.get('status') == 'success' and result.get('data'):
            token = result['data'].get('PASSWORD')
            user_id = result['data'].get('USER_ID')
        
        if not token:
            user_id = self.extract_user_id()
        
        return token, user_id
    
    def extract_user_id(self):
        """Extract user ID from page"""
        user_id_js = """
        var user_id = null;
        
        if (typeof BX !== 'undefined' && typeof BX.User !== 'undefined') {
            if (typeof BX.User.getId === 'function') {
                user_id = BX.User.getId();
            }
        }
        
        if (!user_id && typeof BX !== 'undefined' && BX.user_id) {
            user_id = BX.user_id;
        }
        
        if (!user_id) {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = cookies[i].trim();
                if (cookie.indexOf('UID=') === 0) {
                    user_id = parseInt(cookie.substring(4));
                    break;
                }
            }
        }
        
        if (!user_id) {
            user_id = 2611;
        }
        
        return user_id;
        """
        
        user_id = self.driver.execute_script(user_id_js)
        print(f"   ✅ User ID: {user_id}")
        return user_id
    
    def get_local_storage_data(self):
        """Extract local storage data from browser"""
        print("\n6. Extracting local storage data...")
        
        try:
            # JavaScript to get all local storage items
            local_storage_js = """
            var items = {};
            for (var i = 0; i < localStorage.length; i++) {
                var key = localStorage.key(i);
                var value = localStorage.getItem(key);
                
                // Only save Bitrix-related items to avoid storing too much data
                if (key.toLowerCase().includes('bitrix') || 
                    key.toLowerCase().includes('bx') ||
                    key.includes('USER') ||
                    key.includes('SESSION') ||
                    key.includes('AUTH')) {
                    items[key] = value;
                }
            }
            return items;
            """
            
            local_storage = self.driver.execute_script(local_storage_js)
            
            print(f"   Found {len(local_storage)} Bitrix-related local storage items")
            
            # Get some session storage items too
            session_storage_js = """
            var items = {};
            for (var i = 0; i < sessionStorage.length; i++) {
                var key = sessionStorage.key(i);
                var value = sessionStorage.getItem(key);
                
                if (key.toLowerCase().includes('bitrix') || 
                    key.toLowerCase().includes('bx') ||
                    key.includes('USER') ||
                    key.includes('SESSION')) {
                    items[key] = value;
                }
            }
            return items;
            """
            
            session_storage = self.driver.execute_script(session_storage_js)
            print(f"   Found {len(session_storage)} Bitrix-related session storage items")
            
            # Combine both
            all_storage = {
                'local_storage': local_storage,
                'session_storage': session_storage,
                'timestamp': time.time(),
                'user_agent': self.driver.execute_script("return navigator.userAgent;"),
                'url': self.driver.current_url
            }
            
            return all_storage
            
        except Exception as e:
            print(f"   ⚠️  Could not extract local storage: {e}")
            return {}
    
    def get_local_storage(self):
        """Get local storage data from .env file"""
        try:
            env_path = Path('.env')
            if not env_path.exists():
                return {}
            
            local_storage_json = None
            session_storage_json = None
            
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.startswith('BITRIX_LOCAL_STORAGE='):
                        local_storage_json = line.split('=', 1)[1].strip()
                    elif line.startswith('BITRIX_SESSION_STORAGE='):
                        session_storage_json = line.split('=', 1)[1].strip()
            
            result = {}
            if local_storage_json:
                result['local_storage'] = json.loads(local_storage_json)
            if session_storage_json:
                result['session_storage'] = json.loads(session_storage_json)
            
            return result
        except Exception as e:
            print(f"⚠️  Could not load local storage from .env: {e}")
            return {}
    
    def save_token_to_file_with_storage(self, token, user_id, csrf_token, site_id):
        """Save token to files (.env and JSON) with local storage"""
        try:
            # Get local storage data
            storage_data = self.get_local_storage_data()
            
            # Save to .env file
            env_path = Path('.env')
            env_content = []
            
            if env_path.exists():
                with open(env_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if not any(line.startswith(key) for key in ['BITRIX_REST_TOKEN=', 'BITRIX_USER_ID=', 
                                                                    'BITRIX_LOCAL_STORAGE=', 'BITRIX_SESSION_STORAGE=',
                                                                    'BITRIX_API_URL=', 'BITRIX_SITE_ID=']):
                            env_content.append(line.rstrip())
            
            env_content.append(f"BITRIX_REST_TOKEN={token}")
            env_content.append(f"BITRIX_USER_ID={user_id}")
            env_content.append(f"BITRIX_API_URL=https://ugautodetal.ru")
            env_content.append(f"BITRIX_SITE_ID={site_id}")
            
            # Save local storage (encoded to avoid newline issues)
            if storage_data.get('local_storage'):
                local_storage_json = json.dumps(storage_data['local_storage'], separators=(',', ':'))
                env_content.append(f"BITRIX_LOCAL_STORAGE={local_storage_json}")
            
            # Save session storage
            if storage_data.get('session_storage'):
                session_storage_json = json.dumps(storage_data['session_storage'], separators=(',', ':'))
                env_content.append(f"BITRIX_SESSION_STORAGE={session_storage_json}")
            
            with open(env_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(env_content))
            
            print(f"\n   ✅ Saved to .env")
            print(f"   - Token, User ID, CSRF token, Site ID")
            print(f"   - Local storage: {len(storage_data.get('local_storage', {}))} items")
            print(f"   - Session storage: {len(storage_data.get('session_storage', {}))} items")
            
            # Save to JSON file with full data
            auth_data = {
                'token': token,
                'user_id': user_id,
                'csrf_token': csrf_token,
                'site_id': site_id,
                'storage': storage_data,
                'cookies': self.get_cookies(),
                'timestamp': time.time()
            }
            
            with open('bitrix_token.json', 'w', encoding='utf-8') as f:
                json.dump(auth_data, f, indent=2, ensure_ascii=False)
            
            print(f"   ✅ Saved full data to bitrix_token.json")
            
            # Also save to a pickle file for easier loading
            with open('bitrix_auth.pkl', 'wb') as f:
                pickle.dump({
                    'token': token,
                    'user_id': user_id,
                    'cookies': self.driver.get_cookies(),
                    'local_storage': storage_data.get('local_storage', {}),
                    'session_storage': storage_data.get('session_storage', {})
                }, f)
            
            print(f"   ✅ Saved to bitrix_auth.pkl")
            
        except Exception as e:
            print(f"   ⚠️  Warning: Could not save all data to file: {e}")
            traceback.print_exc()
    
    def get_cookies(self):
        """Get all cookies from browser"""
        cookies = self.driver.get_cookies()
        return {cookie['name']: cookie['value'] for cookie in cookies}
    
    def close(self):
        """Close browser"""
        self.driver.quit()


# ============================================================================
# SECTION 2: CREDENTIAL MANAGEMENT
# ============================================================================

def check_credentials() -> Tuple[Optional[str], Optional[str]]:
    """Check if both REST API credentials exist in .env"""
    env_path = Path('.env')
    
    token = None
    user_id = None
    
    if env_path.exists():
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('BITRIX_REST_TOKEN=') and '=' in line:
                    token = line.split('=', 1)[1].strip()
                elif line.startswith('BITRIX_USER_ID=') and '=' in line:
                    user_id = line.split('=', 1)[1].strip()
    
    return token, user_id


# ============================================================================
# SECTION 3: AUTHENTICATION FLOW
# ============================================================================

def run_authentication() -> Tuple[Optional[str], Optional[int]]:
    """Run browser-based authentication"""
    print("\n" + "="*75)
    print("🔐 CREDENTIALS MISSING - OPENING CHROMIUM FOR AUTHENTICATION")
    print("="*75)
    print("\n   📱 Chromium will open automatically...")
    print("   1️⃣  Log in to Bitrix24")
    print("   2️⃣  System will capture authentication data")
    print("   3️⃣  Credentials will be saved to .env")
    print("\n" + "="*75 + "\n")
    
    app = ChromeAuthApp(headless=False)
    
    try:
        start_url = "https://ugautodetal.ru/"
        print(f"Navigating to: {start_url}")
        app.navigate_to_login(start_url)
        
        token, user_id = app.get_api_token_in_browser()
        
        if token:
            print("\n" + "="*60)
            print("✅ AUTHENTICATION SUCCESSFUL")
            print("="*60)
            return token, user_id
        else:
            print("\n" + "="*60)
            print("❌ AUTHENTICATION FAILED")
            print("="*60)
            return None, None
    
    except KeyboardInterrupt:
        print("\n\n❌ Authentication cancelled by user")
        return None, None
    except Exception as e:
        print(f"\n\n❌ Error during authentication: {e}")
        traceback.print_exc()
        return None, None
    finally:
        app.close()


# ============================================================================
# SECTION 4: CHAT APPLICATION
# ============================================================================

def start_chat(token: str, user_id: int) -> None:
    """Start the chat application"""
    print("\n" + "="*60)
    print("🎨 Starting PyQt5 Chat UI...")
    print("="*60)
    
    try:
        # Set environment variables
        os.environ['BITRIX_REST_TOKEN'] = token
        os.environ['BITRIX_USER_ID'] = str(user_id)
        os.environ['BITRIX_API_URL'] = 'https://ugautodetal.ru'
        os.environ['SKIP_AUTH_CHECK'] = '1'
        
        # Import PyQt5 modules here, after environment variables are set
        from PyQt5.QtWidgets import QApplication
        
        # Add src to path for imports
        src_dir = Path(__file__).parent / "src"
        if src_dir.exists():
            sys.path.insert(0, str(src_dir))
        
        from ui.main_window import TelegramChatWindow
        from api.bitrix_api import BitrixAPI
        
        # Initialize API client
        print(f"\n🔌 Initializing REST API client...")
        api_client = BitrixAPI(user_id=user_id, token=token, base_domain="https://ugautodetal.ru")
        print("✅ REST API client initialized")
        
        # Final check for Qt plugins
        if not os.environ.get('QT_QPA_PLATFORM_PLUGIN_PATH'):
            print("⚠️  Qt plugin path not set, trying one more time...")
            # Try to use PyQt5's built-in method
            try:
                from PyQt5.QtCore import QLibraryInfo
                plugin_path = QLibraryInfo.location(QLibraryInfo.PluginsPath)
                if os.path.exists(plugin_path):
                    os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path
                    print(f"✅ Set Qt plugin path via QLibraryInfo: {plugin_path}")
            except Exception as e:
                print(f"⚠️  Could not set Qt plugin path: {e}")
                print("💡 Make sure PyQt5 is installed: pip install PyQt5")
        
        # Create PyQt5 application
        print("🚀 Creating Qt application...")
        app = QApplication(sys.argv)
        
        # Create and show main window
        print("🖼️  Creating main window...")
        window = TelegramChatWindow()
        window.show()
        
        print("\n✅ Chat application started successfully")
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
    
    except ImportError as e:
        print(f"\n❌ Missing required module: {e}")
        print("💡 Install required packages with:")
        print("  pip install PyQt5 PyQtWebEngine selenium python-dotenv")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error starting chat application: {e}")
        traceback.print_exc()
        sys.exit(1)


# ============================================================================
# SECTION 5: MAIN ENTRY POINT
# ============================================================================

def main():
    """Main entry point - smart startup logic"""
    parser = argparse.ArgumentParser(description='Bitrix24 Chat Application')
    parser.add_argument('--auth-only', action='store_true', help='Run authentication only')
    parser.add_argument('--chat-only', action='store_true', help='Run chat only (skip auth check)')
    parser.add_argument('--skip-credentials-check', action='store_true', help='Skip credentials check')
    args = parser.parse_args()
    
    print("\n" + "="*75)
    print("🚀 BITRIX24 CHAT - SMART STARTUP")
    print("="*75)
    
    # Authentication-only mode
    if args.auth_only:
        print("\n🔐 Running authentication only...")
        token, user_id = run_authentication()
        if token:
            print("\n✅ Authentication saved. You can now run: python3 main.py --chat-only")
        else:
            print("\n❌ Authentication failed")
            sys.exit(1)
        return
    
    # Chat-only mode (skip credential check)
    if args.chat_only or args.skip_credentials_check:
        print("\n⏭️  Skipping credential check (chat-only mode)...")
        load_dotenv()
        token = os.getenv('BITRIX_REST_TOKEN')
        user_id_str = os.getenv('BITRIX_USER_ID')
        
        if not token or not user_id_str:
            print("❌ Error: Credentials not found in .env")
            print("Run: python3 main.py (to authenticate first)")
            sys.exit(1)
        
        start_chat(token, int(user_id_str))
        return
    
    # Smart startup (default mode)
    print("\n🔍 Checking credentials in .env...")
    token, user_id = check_credentials()
    
    has_token = token and len(token.strip()) > 0
    has_user_id = user_id and len(user_id.strip()) > 0
    
    if has_token and has_user_id:
        print(f"   ✅ Token found: {token[:25]}...")
        print(f"   ✅ User ID found: {user_id}")
        print("\n   🎯 Both credentials present - starting chat...\n")
        start_chat(token, int(user_id))
    else:
        if not has_token:
            print("   ❌ BITRIX_REST_TOKEN not found or empty")
        if not has_user_id:
            print("   ❌ BITRIX_USER_ID not found or empty")
        print("\n   🔐 Missing credentials - opening browser authentication...\n")
        
        token, user_id = run_authentication()
        
        if token and user_id:
            print("\n   ✅ Starting chat application...\n")
            start_chat(token, user_id)
        else:
            print("\n❌ Could not start chat without credentials")
            sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Application closed by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        traceback.print_exc()
        sys.exit(1)