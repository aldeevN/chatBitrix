"""
Bitrix24 API client with token management
"""

import json
import requests
from typing import Dict, List, Optional
from datetime import datetime

class BitrixAPI:
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'Python-Bitrix-Chat-Client/1.0'
        })
        
        # Set longer timeout for debugging
        self.session.timeout = 60
        
        print(f"Initialized API with base URL: {self.webhook_url}")
    
    def call_method(self, method: str, params: Dict = None) -> Dict:
        url = f"{self.webhook_url}/{method}"
        
        try:
            start_time = datetime.now()
            response = self.session.post(url, json=params or {}, timeout=60)
            elapsed = (datetime.now() - start_time).total_seconds()
            
            try:
                result = response.json()
                return result
            except json.JSONDecodeError as e:
                text = response.text[:1000]
                return {"error": f"JSON decode error: {e}", "text": text}
                
        except requests.Timeout:
            return {"error": "Request timeout", "result": None}
        except requests.RequestException as e:
            return {"error": str(e), "result": None}
        except Exception as e:
            return {"error": str(e), "result": None}
    
    # User profile methods
    def get_current_profile(self) -> Dict:
        return self.call_method("profile")
    
    def list_managers(self) -> Dict:
        return self.call_method("uad.shop.api.profile.listManagers")
    
    # Chat methods
    def get_groups(self) -> Dict:
        return self.call_method("uad.shop.api.chat.getGroups")
    
    def get_messages(self, group_id: int) -> Dict:
        return self.call_method("uad.shop.api.chat.getMessages", {"group": group_id})
    
    def get_user_news_content(self) -> Dict:
        return self.call_method("uad.shop.api.chat.getUserNewsContent")
    
    def clear_notifications(self, group_id: int) -> Dict:
        return self.call_method("uad.shop.api.chat.clearNotifications", {"group": group_id})
    
    def get_notifications(self) -> Dict:
        return self.call_method("uad.shop.api.chat.getNotifications")
    
    def create_group(self, title: str, message: str, user_ids: List[int], 
                    document_id: str = "") -> Dict:
        params = {
            "title": title,
            "message": message,
            "userIds": user_ids
        }
        
        if document_id:
            params["documentId"] = document_id
            
        return self.call_method("uad.shop.api.chat.createGroup", params)
    
    def add_message(self, group, message: str) -> Dict:
        group_data = {
            "id": group.id,
            "title": group.title or "",
            "participants": group.participants,
            "participant_names": group.participant_names,
            "unread_count": group.unread_count,
            "type": group.type,
            "site": group.site,
            "author": group.author or 0,
            "date": group.date or "",
            "pinned": group.pinned
        }
        
        group_json = json.dumps(group_data, ensure_ascii=False)
        
        return self.call_method("uad.shop.api.chat.addMessage", {
            "group": group_json,
            "message": message
        })
    
    def get_attachment(self, msg_id: int, att_id: int) -> Dict:
        return self.call_method("uad.shop.api.chat.getAttachment", {
            "msgId": msg_id,
            "attId": att_id
        })
    
    def add_group_participants(self, chat_id: int, user_ids: List[int]) -> Dict:
        return self.call_method("uad.shop.api.chat.addGroupParticipants", {
            "chatId": chat_id,
            "userIds": user_ids
        })
    
    def remove_group_participants(self, chat_id: int, user_ids: List[int]) -> Dict:
        return self.call_method("uad.shop.api.chat.removeGroupParticipants", {
            "chatId": chat_id,
            "userIds": user_ids
        })
    
    def activate_subscriptions(self) -> Dict:
        """Activate WebSocket subscriptions"""
        try:
            # First try the chat-specific method
            result = self.call_method("uad.shop.api.chat.activateSubscriptions")
            
            if result and not result.get("error"):
                return result
            
            # Fallback to generic pull method
            result = self.call_method("pull.config.get")
            
            if result and not result.get("error"):
                return result
            
            # If both fail, return empty result
            return {"result": {}}
                
        except Exception as e:
            return {"error": str(e)}
    
    # Customer methods
    def get_customers(self) -> Dict:
        """Get all customers/contacts - using proper chat API"""
        # Try different API endpoints
        endpoints = [
            "uad.shop.api.profile.listCustomers",
            "uad.shop.api.chat.getCustomers", 
            "crm.contact.list"
        ]
        
        for endpoint in endpoints:
            data = self.call_method(endpoint)
            
            if data and not data.get("error"):
                return data
        
        # If all fail, return empty result
        return {"result": []}
    
    def search_customer(self, query: str) -> Dict:
        """Search customers/contractors"""
        return self.call_method("crm.contact.list", {
            "filter": {"%NAME": query, "%LAST_NAME": query},
            "select": ["ID", "NAME", "LAST_NAME", "EMAIL", "PHONE"],
            "start": 0,
            "limit": 50
        })
    
    # Document methods
    def get_documents(self, doc_type: str, contractor_id: str = "", document_id: str = "") -> Dict:
        """Get documents - simplified version"""
        return self.call_method("uad.shop.api.docview.getDocuments", {
            "page": 0,
            "filter": {"type": doc_type}
        })
    
    # API Token Management Methods
    def get_token_api(self) -> Dict:
        """Get existing API token"""
        return self.call_method("base.api.user.getTokenApi")
    
    def create_token_api(self, name: str = "Python Chat Client", 
                        expires_in_days: int = 365) -> Dict:
        """
        Create new API token
        
        Args:
            name: Token name for identification
            expires_in_days: Token expiration in days (default: 365)
        """
        params = {
            "name": name,
            "expires_in_days": expires_in_days
        }
        return self.call_method("base.api.user.createTokenApi", params)
    
    def revoke_token_api(self, token_id: str) -> Dict:
        """Revoke/delete API token"""
        return self.call_method("base.api.user.revokeTokenApi", {"token_id": token_id})
    
    def list_tokens_api(self) -> Dict:
        """List all API tokens"""
        return self.call_method("base.api.user.listTokensApi")
    
    def get_current_token_info(self) -> Dict:
        """Get information about current API token"""
        return self.call_method("base.api.user.getCurrentTokenInfo")