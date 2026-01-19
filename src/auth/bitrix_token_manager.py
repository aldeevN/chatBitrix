"""
Bitrix24 API Token Manager
Handles token persistence and validation
Note: Token creation is done in chrome_auth.py via browser
"""

import json
from typing import Optional, Tuple
from datetime import datetime


class BitrixTokenManager:
    """Manages API token persistence and validation"""
    
    def __init__(self, user_id: int):
        """
        Initialize token manager
        
        Args:
            user_id: User ID for API calls
        """
        self.user_id = user_id
        self.token = None
        self.token_created_at = None
    
    def _save_token_info(self, token: str, token_data: dict = None):
        """Save token information to file"""
        try:
            token_info = {
                "token": token,
                "created_at": self.token_created_at.isoformat() if self.token_created_at else datetime.now().isoformat(),
                "name": token_data.get("name") if token_data else "API Token",
                "expires": token_data.get("expires") if token_data else "N/A",
                "user_id": self.user_id
            }
            
            with open("token_info.json", "w", encoding="utf-8") as f:
                json.dump(token_info, f, indent=2, ensure_ascii=False)
            
            print(f"   ✓ Token info saved to token_info.json")
        except Exception as e:
            print(f"   ⚠ Failed to save token info: {e}")
    
    def load_saved_token(self) -> Optional[str]:
        """Load token from saved file"""
        try:
            with open("token_info.json", "r", encoding="utf-8") as f:
                token_data = json.load(f)
            
            token = token_data.get("token")
            if token:
                self.token = token
                try:
                    self.token_created_at = datetime.fromisoformat(token_data.get("created_at", ""))
                except:
                    self.token_created_at = datetime.now()
                print(f"✓ Loaded saved token (first 30 chars): {token[:30]}...")
                return token
        except Exception as e:
            print(f"⚠ Could not load saved token: {e}")
        
        return None
    
    def test_token(self) -> Tuple[bool, str]:
        """
        Test if token is valid (basic check - token must be set)
        
        Returns:
            Tuple of (is_valid, message)
        """
        if not self.token:
            return False, "No token set"
        
        if len(self.token) < 20:
            return False, "Token appears invalid (too short)"
        
        print(f"✓ Token is valid (first 30 chars): {self.token[:30]}...")
        return True, "Token is valid"
    
    def set_token(self, token: str, token_data: dict = None):
        """
        Set the token (called by chrome_auth after obtaining from browser)
        
        Args:
            token: The API token obtained from browser
            token_data: Optional additional token data
        """
        if token:
            self.token = token
            self.token_created_at = datetime.now()
            self._save_token_info(token, token_data)
            print(f"✓ Token set and saved: {token[:30]}...")
