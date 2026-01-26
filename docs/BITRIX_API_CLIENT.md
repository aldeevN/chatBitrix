# Bitrix API Client Documentation

## Overview
The `BitrixAPI` class provides a REST API client for Bitrix24 with token-based authentication. It handles API method calls, error management, and response parsing.

## Authentication

### How to Get API Credentials

#### Step 1: Get Token and User ID
```bash
python3 main.py
```
This launches a Chromium browser that:
1. Auto-logs in using saved cookies
2. Extracts API token from browser (via /me: endpoint)
3. Saves credentials to `.env` file

#### Step 2: Load Credentials
```python
import os
from dotenv import load_dotenv
load_dotenv()

user_id = int(os.getenv('API_USER_ID'))
token = os.getenv('API_TOKEN')
```

### Required Environment Variables
```
BITRIX_REST_TOKEN=your_api_token
BITRIX_USER_ID=your_user_id
BITRIX_API_URL=https://ugautodetal.ru
```

## REST API URL Format

### Structure
```
https://ugautodetal.ru/rest/{user_id}/{token}/{method}
```

### Example Requests

#### Get Current User
```python
api = BitrixAPI(user_id=2611, token="pkc4eycs2shrl0ko")
profile = api.get_current_profile()
```

HTTP Request:
```
POST /rest/2611/pkc4eycs2shrl0ko/profile HTTP/1.1
Host: ugautodetal.ru
Content-Type: application/json
```

#### Get Chat Groups
```python
groups = api.get_groups()
```

HTTP Request:
```
POST /rest/2611/pkc4eycs2shrl0ko/uad.shop.api.chat.getGroups HTTP/1.1
Host: ugautodetal.ru
Content-Type: application/json
```

## Class Reference

### Constructor: `__init__(user_id, token, base_domain)`

**Parameters**:
- `user_id` (int): User ID for authentication
  - Must match the user who generated the token
  - Example: `2611`
  - Source: `.env` as `API_USER_ID` or browser response

- `token` (str): API token from browser authentication
  - Obtained via `python3 main.py`
  - Saved to `.env` as `API_TOKEN`
  - Format: alphanumeric string (e.g., `pkc4eycs2shrl0ko`)
  - Used in API URL: `/rest/{user_id}/{token}/{method}`

- `base_domain` (str, optional): Base Bitrix instance URL
  - Default: `https://ugautodetal.ru`
  - Example: `https://company.bitrix24.com`

**Raises**:
- `ValueError`: If token is empty
- `ValueError`: If user_id is empty
- `TypeError`: If user_id cannot be converted to int

**Example**:
```python
from api.bitrix_api import BitrixAPI

api = BitrixAPI(
    user_id=2611,
    token="pkc4eycs2shrl0ko",
    base_domain="https://ugautodetal.ru"
)
```

## API Methods

### User Methods

#### `get_current_profile()`
Get current user profile information

**Returns**: `Dict`
```python
{
    "result": {
        "ID": "2611",
        "NAME": "John",
        "LAST_NAME": "Doe",
        "EMAIL": "john@example.com"
    }
}
```

#### `list_managers()`
Get list of managers

**Returns**: `Dict` with managers list

### Chat Methods

#### `get_groups()`
Get all chat groups and direct messages

**Returns**: `Dict` with groups
```python
{
    "result": [
        {
            "ID": "133",
            "TITLE": "Support Team",
            "PARTICIPANTS": [2611, 2612],
            "UNREAD": 0
        }
    ]
}
```

#### `get_messages(group_id)`
Get messages for a specific group

**Parameters**:
- `group_id` (int): Chat group ID

**Returns**: `Dict` with messages
```python
{
    "result": [
        {
            "ID": "1",
            "AUTHOR": 2611,
            "AUTHOR_NAME": "John",
            "MESSAGE": "Hello",
            "DATE": "2025-01-26T09:30:00"
        }
    ]
}
```

#### `get_user_news_content()`
Get user news/activity feed

**Returns**: `Dict` with news items

#### `clear_notifications(group_id)`
Mark all messages in group as read

**Parameters**:
- `group_id` (int): Chat group ID

**Returns**: `Dict` with result status

#### `get_notifications()`
Get active notifications

**Returns**: `Dict` with unread message counts by group

#### `create_group(title, message, user_ids, document_id)`
Create a new group chat

**Parameters**:
- `title` (str): Group name
- `message` (str): Initial message to post
- `user_ids` (List[int]): User IDs to add
- `document_id` (str, optional): Document to share

**Returns**: `Dict` with new group ID

## Core Methods

### `call_method(method, params)`
Generic API method caller

**Parameters**:
- `method` (str): API method name
  - Examples: `profile`, `uad.shop.api.chat.getGroups`
- `params` (Dict, optional): Request parameters

**Returns**: `Dict` with API response or error

**Example**:
```python
result = api.call_method("uad.shop.api.chat.getGroups", {})
if "error" in result:
    print(f"Error: {result['error']}")
else:
    groups = result.get("result", [])
```

## Error Handling

### API Response Format
All responses follow a standard format:

**Success**:
```python
{
    "result": [...]  # Data
}
```

**Error**:
```python
{
    "error": "Error description",
    "result": None
}
```

### Error Types

| Error Type | Cause | Solution |
|-----------|-------|----------|
| `JSON decode error` | Invalid response format | Retry request |
| `Request timeout` | Server didn't respond | Increase timeout or retry |
| `Invalid token` | Token expired/invalid | Run `python3 main.py` again |
| `User not found` | Wrong user_id | Verify user_id in .env |

### Error Handling Example
```python
result = api.get_groups()

if "error" in result:
    error = result["error"]
    print(f"API Error: {error}")
    # Handle error
else:
    groups = result.get("result", [])
    print(f"Loaded {len(groups)} groups")
```

## Configuration

### Session Configuration
The API client uses `requests.Session` with:
- **Timeout**: 60 seconds (configurable)
- **Headers**: 
  - `Content-Type: application/json`
  - `Accept: application/json`
  - `User-Agent: Python-Bitrix-Chat-Client/1.0`

### Timeout Settings
```python
api.session.timeout = 120  # Change timeout to 120 seconds
```

## Usage Examples

### Basic Setup
```python
from api.bitrix_api import BitrixAPI
import os
from dotenv import load_dotenv

# Load credentials
load_dotenv()
api = BitrixAPI(
    user_id=int(os.getenv('API_USER_ID')),
    token=os.getenv('API_TOKEN')
)
```

### Load All Chats
```python
groups_response = api.get_groups()
groups = groups_response.get("result", [])

for group in groups:
    print(f"Chat: {group['TITLE']} (ID: {group['ID']})")
```

### Load Messages from Chat
```python
messages_response = api.get_messages(group_id=133)
messages = messages_response.get("result", [])

for msg in messages:
    print(f"{msg['AUTHOR_NAME']}: {msg['MESSAGE']}")
```

### Send Message (Create Group with Message)
```python
result = api.create_group(
    title="New Group",
    message="Hello everyone!",
    user_ids=[2611, 2612, 2613]
)

if "error" not in result:
    new_group_id = result["result"]["ID"]
    print(f"Created group: {new_group_id}")
```

## Integration with Application

### In Main Window
```python
from api.bitrix_api import BitrixAPI
from api.models import User, Group, Message

api = BitrixAPI(user_id=2611, token=os.getenv('API_TOKEN'))

# Load current user
user_response = api.get_current_profile()
current_user = User(**user_response["result"])

# Load groups
groups_response = api.get_groups()
groups = [Group(**g) for g in groups_response["result"]]

# Load messages for group
messages_response = api.get_messages(133)
messages = [Message(**m) for m in messages_response["result"]]
```

## API Method Discovery
For a complete list of available methods, check:
- Bitrix24 REST API documentation
- `uad.shop.api.*` methods (custom shop API)
- Standard Bitrix methods: `profile`, `user.get`, etc.

## Performance Notes
- Large message lists may take time to load
- Use pagination for better performance
- Consider caching frequently accessed data
- API calls block while waiting for response

## Troubleshooting

### "Invalid token" Error
```bash
# Get a fresh token
python3 main.py
```

### "Request timeout"
```python
# Increase timeout
api.session.timeout = 120
```

### Connection Issues
```python
# Check network connectivity
import requests
requests.get("https://ugautodetal.ru")
```

## Security Considerations
- Never hardcode tokens in source code
- Always load from `.env` file
- Rotate tokens regularly
- Don't expose token in logs or error messages (API truncates to 20 chars)
