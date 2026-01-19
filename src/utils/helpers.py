"""
Helper functions
"""

import re
from datetime import datetime
from typing import Optional, Union
import urllib.parse

def format_timestamp(timestamp: str, format_str: str = "%H:%M") -> str:
    """Format timestamp string"""
    try:
        # Try to parse ISO format
        if 'Z' in timestamp:
            timestamp = timestamp.replace('Z', '+00:00')
        
        dt = datetime.fromisoformat(timestamp)
        return dt.strftime(format_str)
    except:
        # If parsing fails, return original
        return timestamp

def get_user_display_name(user_data: dict) -> str:
    """Get display name from user data"""
    first_name = user_data.get('name') or user_data.get('first_name') or ''
    last_name = user_data.get('last_name') or ''
    
    full_name = f"{first_name} {last_name}".strip()
    if full_name:
        return full_name
    
    # Fallback to email or ID
    email = user_data.get('email')
    if email:
        return email
    
    user_id = user_data.get('id')
    if user_id:
        return f"User {user_id}"
    
    return "Unknown User"

def validate_url(url: str) -> bool:
    """Validate URL format"""
    try:
        result = urllib.parse.urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def extract_user_id_from_cookie(cookie_value: str) -> Optional[int]:
    """Extract user ID from cookie value"""
    try:
        # Try to find numeric ID in cookie
        match = re.search(r'\d+', cookie_value)
        if match:
            return int(match.group())
    except:
        pass
    return None

def truncate_text(text: str, max_length: int = 100, ellipsis: str = "...") -> str:
    """Truncate text to specified length"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(ellipsis)] + ellipsis

def parse_bitrix_date(date_str: str) -> Optional[datetime]:
    """Parse Bitrix24 date string"""
    if not date_str:
        return None
    
    formats = [
        "%Y-%m-%dT%H:%M:%S%z",  # ISO with timezone
        "%Y-%m-%dT%H:%M:%S",     # ISO without timezone
        "%d.%m.%Y %H:%M:%S",     # Russian format
        "%d.%m.%Y %H:%M",        # Russian format without seconds
        "%Y-%m-%d",              # Date only
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    return None

def get_elapsed_time(timestamp: Union[str, datetime]) -> str:
    """Get human-readable elapsed time"""
    if isinstance(timestamp, str):
        dt = parse_bitrix_date(timestamp)
        if not dt:
            return timestamp
    else:
        dt = timestamp
    
    now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
    diff = now - dt
    
    if diff.days > 365:
        years = diff.days // 365
        return f"{years} year{'s' if years > 1 else ''} ago"
    elif diff.days > 30:
        months = diff.days // 30
        return f"{months} month{'s' if months > 1 else ''} ago"
    elif diff.days > 7:
        weeks = diff.days // 7
        return f"{weeks} week{'s' if weeks > 1 else ''} ago"
    elif diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    else:
        return "just now"