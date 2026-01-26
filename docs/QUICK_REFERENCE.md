# Quick Reference Guide

A concise reference for commonly used functions and patterns in the chatBitrix project.

## Table of Contents
1. [API Methods](#api-methods)
2. [Data Models](#data-models)
3. [UI Components](#ui-components)
4. [Utility Functions](#utility-functions)
5. [Common Patterns](#common-patterns)
6. [Error Codes](#error-codes)

---

## API Methods

### BitrixAPI

#### User Methods
```python
api.get_current_profile()          # Get current user info
api.list_managers()                # Get all managers
```

#### Chat Methods
```python
api.get_groups()                   # Get all chats
api.get_messages(group_id)         # Get messages from chat
api.get_user_news_content()        # Get activity feed
api.clear_notifications(group_id)  # Mark group as read
api.get_notifications()            # Get unread counts
api.create_group(title, message, user_ids)  # Create chat
```

#### Generic
```python
api.call_method(method, params)    # Call any API method
```

**Response Format**:
```python
result = api.get_groups()
if "error" in result:
    error = result["error"]
else:
    groups = result.get("result", [])
```

---

## Data Models

### User
```python
user = User(
    id=2611,
    name="John",
    last_name="Doe",
    email="john@example.com",
    is_manager=False,
    is_moderator=False
)
print(user.full_name)        # "John Doe"
print(user.display_name)     # "John Doe"
```

### Customer
```python
customer = Customer(
    id=1,
    xml_id="CRM_123",
    name="Jane",
    last_name="Smith"
)
print(customer.full_name)    # "Jane Smith"
```

### Group
```python
group = Group(
    id=133,
    title="Support Team",
    participants=[2611, 2612],
    participant_names=["John", "Jane"],
    unread_count=0,
    last_message="Hello"
)
display = group.display_title(current_user, customers)
```

### Message
```python
msg = Message(
    id=1,
    text="Hello World",
    sender_id=2611,
    sender_name="John",
    timestamp="2025-01-26T09:30:00Z",
    is_own=True,
    files=[]
)
print(msg.time_display)      # "09:30"
```

---

## UI Components

### Main Window
```python
from ui.main_window import TelegramChatWindow

window = TelegramChatWindow(api=api, auth_data=auth_data)
window.show()

# Methods
window.select_chat(group_id)
window.send_message()
window.apply_current_theme()
```

### Message Bubble
```python
from ui.message_bubble import MessageBubble

bubble = MessageBubble(
    message=msg,
    current_user=user,
    is_own=True,
    is_dark=False,
    is_group_chat=True
)
```

### Chat List Item
```python
from ui.chat_list_item import ChatListItem

item = ChatListItem(
    group=group,
    current_user=user,
    is_dark=False
)
item.clicked.connect(on_chat_selected)
```

### Custom Widgets
```python
from ui.widgets import TelegramButton, TelegramInput, TelegramSearchBar

button = TelegramButton("Click me", is_dark=False)
input_field = TelegramInput(placeholder="Type...", is_dark=False)
search = TelegramSearchBar(is_dark=False)
```

### New Message Dialog
```python
from ui.new_message_dialog import NewMessageDialog

dialog = NewMessageDialog(
    groups=groups,
    current_user=user,
    customers=customers,
    is_dark=False
)

if dialog.exec_() == QDialog.Accepted:
    text = dialog.message_text
    group_id = dialog.selected_group_id
```

### Theme System
```python
from ui.themes import get_theme_colors, apply_theme

# Get colors
colors = get_theme_colors(is_dark_mode=False)
primary_color = colors['PRIMARY']

# Apply theme
apply_theme(widget, is_dark_mode=False)
```

---

## Utility Functions

### Timestamp Handling
```python
from utils.helpers import format_timestamp, parse_bitrix_date

# Format
time_str = format_timestamp("2025-01-26T09:30:00Z")  # "09:30"
time_str = format_timestamp("2025-01-26T09:30:00Z", "%d.%m.%Y %H:%M")

# Parse
dt = parse_bitrix_date("26.01.2025 09:30")
dt = parse_bitrix_date("2025-01-26T09:30:00Z")
```

### Text Manipulation
```python
from utils.helpers import truncate_text, get_user_display_name

# Truncate
preview = truncate_text(message, max_length=100)

# Get name
name = get_user_display_name({"name": "John", "last_name": "Doe"})
```

### Validation
```python
from utils.helpers import validate_url, extract_user_id_from_cookie

if validate_url(user_input):
    open_link(user_input)

user_id = extract_user_id_from_cookie("2611_data")
```

### Time Calculations
```python
from utils.helpers import get_elapsed_time

elapsed = get_elapsed_time("2025-01-26T09:30:00Z")
# Output: "Just now" or "5 minutes ago" or "1 day ago"
```

### File Operations
```python
from utils.file_handlers import save_file, load_file, get_file_size

# Save
save_file("data.txt", "content")

# Load
content = load_file("data.txt")

# Size
size = get_file_size("document.pdf")

# Validate
if is_valid_file_type("doc.pdf", ["pdf", "doc"]):
    upload()
```

---

## Common Patterns

### Load and Display All Chats
```python
from api.bitrix_api import BitrixAPI
from api.models import Group
from ui.chat_list_item import ChatListItem

api = BitrixAPI(user_id=2611, token="token")
response = api.get_groups()
groups = [Group(**g) for g in response.get("result", [])]

for group in groups:
    item = ChatListItem(group=group, current_user=user, is_dark=False)
    chat_list_widget.addWidget(item)
```

### Load Messages in Chat
```python
response = api.get_messages(group_id=133)
messages = [Message(**m) for m in response.get("result", [])]

for msg in messages:
    bubble = MessageBubble(
        message=msg,
        current_user=user,
        is_own=(msg.sender_id == user.id),
        is_dark=False,
        is_group_chat=True
    )
    messages_layout.addWidget(bubble)
```

### Listen for Real-time Messages
```python
from pull.bitrix_pull import BitrixPullClient

pull = BitrixPullClient(api=api, user_id=2611)
pull.message_received.connect(on_new_message)
pull.connection_status.connect(on_status_changed)
pull.start()

def on_new_message(message):
    group_id = message.get('group_id')
    # Update UI
    
def on_status_changed(connected, message):
    if connected:
        status_bar.setText("Connected")
```

### Handle Authentication
```python
from auth.auth_manager import authenticate_from_captured_data
import os
from dotenv import load_dotenv

# Load saved credentials
load_dotenv()
user_id = int(os.getenv('BITRIX_USER_ID'))
token = os.getenv('BITRIX_REST_TOKEN')

# Or authenticate interactively
auth_data = authenticate_from_captured_data()
user_id = auth_data['user_id']
```

### Switch Themes
```python
# In main window
self.is_dark_mode = not self.is_dark_mode
self.apply_current_theme()  # Refreshes all components
```

### Format Display Text
```python
from utils.helpers import format_timestamp, truncate_text

# Message timestamp
time = format_timestamp(msg.timestamp)

# Message preview
preview = truncate_text(msg.text, max_length=100)

# Sender name
from utils.helpers import get_user_display_name
name = get_user_display_name(msg.sender_data)
```

---

## Error Codes

### API Errors

| Error | Meaning | Solution |
|-------|---------|----------|
| `"Invalid token"` | Token expired or invalid | Run `python3 main.py` to refresh |
| `"Request timeout"` | Server took too long | Retry request, check network |
| `"User not found"` | Wrong user_id | Check BITRIX_USER_ID in .env |
| `"JSON decode error"` | Invalid response | Check server response format |

### Authentication Errors

| Error | Meaning | Solution |
|-------|---------|----------|
| `"Token cannot be empty"` | No token provided | Run `python3 main.py` first |
| `"User ID cannot be empty"` | No user_id | Check .env file |
| `"FileNotFoundError"` | Auth files missing | Run `python3 main.py` |

### WebSocket Errors

| Error | Meaning | Solution |
|-------|---------|----------|
| `"Connection refused"` | Can't reach server | Check network, server status |
| `"SSL error"` | Certificate issue | Check server certificate |
| `"Timeout"` | No response from server | Increase timeout, retry |

---

## Status Constants

### PullStatus
```python
from pull.pull_constants import PullStatus

PullStatus.Online      # Connected
PullStatus.Offline     # Disconnected
PullStatus.Connecting  # In progress
```

### ConnectionType
```python
from pull.pull_constants import ConnectionType

ConnectionType.WebSocket   # WebSocket connection
ConnectionType.LongPoll    # Long polling (fallback)
```

---

## Configuration

### Environment Variables
```
BITRIX_REST_TOKEN=your_api_token
BITRIX_USER_ID=2611
BITRIX_API_URL=https://ugautodetal.ru
BITRIX_SITE_ID=ap
```

### Files Generated
- `.env` - Configuration
- `auth_data_full.json` - Complete auth data
- `cookies.pkl` - Session cookies
- `bitrix_token.json` - Token information

---

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Ctrl+N` | New message |
| `Ctrl+Q` | Quit application |
| `Enter` | Send message |
| `Escape` | Close dialog |
| `Tab` | Next component |
| `Shift+Tab` | Previous component |

---

## Color Reference

### Light Theme
```
Primary Blue: #3390ec
Primary Dark: #2b7bc2
Background: #f5f5f7
Surface: #ffffff
Text: #000000
Secondary Text: #65676b
Border: #e0e0e0
```

### Dark Theme
```
Primary Blue: #4fa3f5
Primary Dark: #2b7bc2
Background: #0a0e27
Surface: #1a1f3a
Text: #e8eaed
Secondary Text: #9aa0a6
Border: #3f4555
```

---

## Useful Commands

```bash
# Start application
python3 main.py

# Run chat
python3 run_chat.py

# Authenticate
python3 start.py

# Check syntax
python3 -m py_compile src/ui/main_window.py

# List all groups (test API)
python3 -c "from api.bitrix_api import BitrixAPI; import os; from dotenv import load_dotenv; load_dotenv(); api = BitrixAPI(int(os.getenv('BITRIX_USER_ID')), os.getenv('BITRIX_REST_TOKEN')); print(api.get_groups())"

# Clear authentication
rm .env auth_data_full.json cookies.pkl
```

---

## Tips & Tricks

1. **Debugging messages**: Check `debug_info` signal from Pull client
2. **Performance**: Cache groups and users, don't reload repeatedly
3. **UI responsiveness**: API calls run in main thread; consider moving to background
4. **Message display**: Limit to last 100 messages for better performance
5. **Token refresh**: Run `python3 main.py` monthly to refresh token

---

## Additional Resources

- [Project Documentation](PROJECT_DOCUMENTATION.md) - Complete docs
- [Bitrix API Documentation](BITRIX_API_CLIENT.md)
- [Authentication Guide](AUTHENTICATION_SYSTEM.md)
- [Pull Client Guide](BITRIX_PULL_CLIENT.md)
- [UI Components](UI_COMPONENTS.md)
- [Utility Functions](UTILITY_FUNCTIONS.md)

---

**Last Updated**: January 26, 2025  
**Quick Ref Version**: 1.0
