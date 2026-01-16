"""
Environment variable handler
"""

import os
import json
from typing import Dict, List, Optional

def load_env_file(filename='.env') -> Dict[str, str]:
    """Load environment variables from .env file"""
    if not os.path.exists(filename):
        return {}
    
    env_vars = {}
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()
    
    return env_vars

def save_env_file(env_vars: Dict[str, str], filename='.env') -> List[str]:
    """Save environment variables to .env file"""
    lines = []
    for key, value in env_vars.items():
        lines.append(f"{key}={value}")
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    return lines

def get_env_var(key: str, default: str = None) -> Optional[str]:
    """Get environment variable with fallback"""
    return os.environ.get(key, default)

def set_env_var(key: str, value: str):
    """Set environment variable"""
    os.environ[key] = value

def create_env_file_from_auth(auth_data: Dict) -> List[str]:
    """Create .env file from authentication data"""
    env_lines = []
    
    # Add cookies
    cookies = auth_data.get('cookies', {})
    for cookie_name, cookie_value in cookies.items():
        env_lines.append(f"COOKIE_{cookie_name.upper()}={cookie_value}")
    
    # Add user ID
    user_id = auth_data.get('user_id')
    if user_id:
        env_lines.append(f"USER_ID={user_id}")
    
    # Add important tokens
    env_lines.append("CSRF_BITRIX_SESSID=placeholder")  # Will be extracted dynamically
    
    # Add Pull config if available
    pull_config = auth_data.get('pull_config', {})
    if pull_config:
        # Add channel IDs
        channels = pull_config.get('channels', {})
        if 'private' in channels:
            channel_id = channels['private'].get('id')
            if channel_id:
                env_lines.append(f"PULL_CHANNEL_PRIVATE={channel_id}")
        
        if 'shared' in channels:
            channel_id = channels['shared'].get('id')
            if channel_id:
                env_lines.append(f"PULL_CHANNEL_SHARED={channel_id}")
        
        # Add server config
        server = pull_config.get('server', {})
        websocket_url = server.get('websocket_secure') or server.get('websocket')
        if websocket_url:
            env_lines.append(f"PULL_WEBSOCKET_URL={websocket_url}")
    
    # Write to .env file
    with open('.env', 'w', encoding='utf-8') as f:
        f.write('\n'.join(env_lines))
    
    print(f"✓ Created .env file with {len(env_lines)} entries")
    return env_lines