"""
Chrome authentication for Bitrix24
Uses Selenium for browser automation to capture authentication data
"""

import os
import sys
import time
import json
import pickle
import urllib.parse
import re
from typing import Dict, Any, Optional

# Selenium imports for initial authentication
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

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
    
    def manual_login(self):
        """Wait for manual login"""
        input("Please log in manually, then press Enter...")
    
    def capture_auth_data(self):
        """Capture all authentication data from browser"""
        auth_data = {
            'cookies': self.get_cookies(),
            'local_storage': self.get_local_storage(),
            'session_storage': self.get_session_storage(),
            'current_url': self.driver.current_url,
            'page_title': self.driver.title,
            'tokens': self.tokens,
            'csrf_tokens': self.csrf_tokens
        }
        return auth_data
    
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
    
    def save_auth_to_env(self, filename='.env'):
        """Save authentication data to .env file format"""
        auth_data = self.capture_auth_data()
        
        env_content = []
        
        # Add tokens
        for token_name, token_value in self.tokens.items():
            if token_value:
                env_content.append(f"{token_name.upper()}={token_value}")
        
        # Add CSRF tokens
        for csrf_name, csrf_value in self.csrf_tokens.items():
            if csrf_value:
                env_content.append(f"CSRF_{csrf_name.upper()}={csrf_value}")
        
        # Add important cookies
        bitrix_cookies = {k: v for k, v in auth_data['cookies'].items() 
                         if 'bitrix' in k.lower() or 'bx' in k.lower() or 'sess' in k.lower()}
        for cookie_name, cookie_value in bitrix_cookies.items():
            env_content.append(f"COOKIE_{cookie_name.upper()}={cookie_value}")
        
        # Add current URL
        env_content.append(f"CURRENT_URL={auth_data['current_url']}")
        
        # Write to .env file
        with open(filename, 'w') as f:
            f.write('\n'.join(env_content))
        
        # Also save full data to JSON for reference
        with open('auth_data_full.json', 'w') as f:
            json.dump(auth_data, f, indent=2, default=str)
        
        return env_content
    
    def save_cookies_pickle(self, filename='cookies.pkl'):
        """Save cookies to pickle file"""
        cookies = self.driver.get_cookies()
        with open(filename, 'wb') as f:
            pickle.dump(cookies, f)
    
    def load_cookies_and_refresh(self, filename='cookies.pkl'):
        """Load cookies from pickle file and refresh page"""
        with open(filename, 'rb') as f:
            cookies = pickle.load(f)
        
        for cookie in cookies:
            self.driver.add_cookie(cookie)
        
        self.driver.refresh()
    
    def auto_login_with_saved_cookies(self, url, cookies_file='cookies.pkl'):
        """Auto login with saved cookies"""
        if not os.path.exists(cookies_file):
            return False
        
        self.driver.get(url)
        self.load_cookies_and_refresh(cookies_file)
        time.sleep(2)
        
        if "login" not in self.driver.current_url.lower():
            return True
        else:
            return False
    
    def extract_csrf_token_bitrix(self):
        """Extract CSRF token from Bitrix24 page"""
        try:
            csrf_js = """
            if (typeof BX !== 'undefined' && BX.message && BX.message('bitrix_sessid')) {
                return BX.message('bitrix_sessid');
            }
            
            if (window.bitrix_sessid) {
                return window.bitrix_sessid;
            }
            
            const metaTag = document.querySelector('meta[name="csrf-token"]') || 
                           document.querySelector('meta[name="bitrix_sessid"]') ||
                           document.querySelector('meta[name="csrf"]');
            if (metaTag && metaTag.content) {
                return metaTag.content;
            }
            
            const csrfInputs = document.querySelectorAll('input[name="sessid"], input[name="csrf_token"], input[name="csrf-token"]');
            for (let input of csrfInputs) {
                if (input.value) return input.value;
            }
            
            const scripts = document.getElementsByTagName('script');
            for (let script of scripts) {
                const text = script.textContent;
                const patterns = [
                    /BX\.bitrix_sessid\s*=\s*['"]([^'"]+)['"]/,
                    /bitrix_sessid\s*:\s*['"]([^'"]+)['"]/,
                    /sessid\s*:\s*['"]([^'"]+)['"]/,
                    /"bitrix_sessid"\s*:\s*"([^"]+)"/,
                    /'bitrix_sessid'\s*:\s*'([^']+)'/
                ];
                
                for (let pattern of patterns) {
                    const match = text.match(pattern);
                    if (match && match[1]) {
                        return match[1];
                    }
                }
            }
            
            const storageKeys = ['bitrix_sessid', 'BX_CSRF', 'csrf_token'];
            for (let key of storageKeys) {
                const value = localStorage.getItem(key) || sessionStorage.getItem(key);
                if (value) return value;
            }
            
            const cookies = document.cookie.split(';');
            for (let cookie of cookies) {
                const [name, value] = cookie.trim().split('=');
                if (name.includes('csrf') || name.includes('sessid')) {
                    return value;
                }
            }
            
            return null;
            """
            
            token = self.driver.execute_script(csrf_js)
            if token:
                self.csrf_tokens['bitrix_sessid'] = token
            return token
            
        except Exception as e:
            return None
    
    def close(self):
        """Close browser"""
        self.driver.quit()