"""
Data models for Bitrix24 Chat
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime

@dataclass
class User:
    id: int
    name: str = ""
    last_name: str = ""
    email: str = ""
    is_manager: bool = False
    is_moderator: bool = False
    
    @property
    def full_name(self) -> str:
        return f"{self.name} {self.last_name}".strip()
    
    @property
    def display_name(self) -> str:
        if self.full_name:
            return self.full_name
        return self.email or f"User {self.id}"

@dataclass
class Customer:
    id: int
    xml_id: str
    name: str
    last_name: str
    
    @property
    def full_name(self) -> str:
        return f"{self.name} {self.last_name}".strip()

@dataclass
class Group:
    id: int
    title: str
    participants: List[int] = field(default_factory=list)
    participant_names: List[str] = field(default_factory=list)
    unread_count: int = 0
    last_message: Optional[str] = None
    last_message_time: Optional[str] = None
    author: Optional[int] = None
    date: Optional[str] = None
    pinned: bool = False
    type: str = "messageGroup"
    site: str = ""
    
    def display_title(self, current_user, customers) -> str:
        if self.title and self.title.strip():
            return self.title
        
        other_participants = []
        other_participant_names = []
        
        for i, participant_id in enumerate(self.participants):
            if participant_id != current_user.id:
                other_participants.append(participant_id)
                if i < len(self.participant_names):
                    other_participant_names.append(self.participant_names[i])
        
        if not other_participants:
            return "Saved Messages"
        
        if other_participant_names:
            return ", ".join(other_participant_names[:3]) + ("" if len(other_participant_names) <= 3 else "...")
        
        participant_names = []
        for customer in customers:
            if customer.id in other_participants:
                participant_names.append(customer.full_name)
        
        if participant_names:
            return ", ".join(participant_names[:3]) + ("" if len(participant_names) <= 3 else "...")
        
        return f"Chat with {len(other_participants)} participants"

@dataclass
class Message:
    id: int
    text: str
    sender_id: int
    sender_name: str
    timestamp: str
    files: List[Dict] = field(default_factory=list)
    is_own: bool = False
    read: bool = True
    
    @property
    def time_display(self) -> str:
        try:
            dt = datetime.fromisoformat(self.timestamp.replace('Z', '+00:00'))
            return dt.strftime("%H:%M")
        except:
            return self.timestamp