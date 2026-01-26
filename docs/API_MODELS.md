# API Models Documentation

## Overview
The `models.py` file defines data classes for representing Bitrix24 entities: Users, Customers, Groups, and Messages. These models provide structured access to API data and helper methods for display.

## Classes

### 1. User
**Purpose**: Represents a Bitrix24 user/employee

**Attributes**:
- `id` (int): Unique user identifier
- `name` (str): First name
- `last_name` (str): Last name
- `email` (str): Email address
- `is_manager` (bool): Whether user has manager role
- `is_moderator` (bool): Whether user can moderate chats

**Properties**:
- `full_name`: Returns formatted full name ("FirstName LastName")
- `display_name`: Returns best available name, fallback to email or ID

**Example**:
```python
user = User(id=2611, name="John", last_name="Doe", email="john@example.com")
print(user.full_name)        # "John Doe"
print(user.display_name)     # "John Doe"
```

### 2. Customer
**Purpose**: Represents a customer/contact in the system

**Attributes**:
- `id` (int): Customer ID
- `xml_id` (str): External system ID
- `name` (str): First name
- `last_name` (str): Last name

**Properties**:
- `full_name`: Returns formatted full name

**Example**:
```python
customer = Customer(id=1, xml_id="CRM_123", name="Jane", last_name="Smith")
print(customer.full_name)  # "Jane Smith"
```

### 3. Group
**Purpose**: Represents a chat group or direct message thread

**Attributes**:
- `id` (int): Group/chat ID
- `title` (str): Chat title
- `participants` (List[int]): List of participant user IDs
- `participant_names` (List[str]): List of participant names
- `unread_count` (int): Number of unread messages
- `last_message` (str): Last message text
- `last_message_time` (str): Last message timestamp
- `author` (int): Creator user ID
- `date` (str): Creation date
- `pinned` (bool): Whether chat is pinned
- `type` (str): Chat type (default: "messageGroup")
- `site` (str): Site identifier

**Methods**:
- `display_title(current_user, customers)`: Returns appropriate display title
  - If title is set, returns it
  - For direct messages, returns participant names
  - Falls back to participant count

**Example**:
```python
group = Group(
    id=133,
    title="Support Team",
    participants=[2611, 2612, 2613],
    participant_names=["John", "Jane", "Bob"]
)
print(group.display_title(current_user, []))  # "Support Team"
```

### 4. Message
**Purpose**: Represents a chat message

**Attributes**:
- `id` (int): Message ID
- `text` (str): Message content
- `sender_id` (int): Sender user ID
- `sender_name` (str): Sender display name
- `timestamp` (str): Message timestamp (ISO format)
- `files` (List[Dict]): Attached file information
- `is_own` (bool): Whether message was sent by current user
- `read` (bool): Whether message has been read

**Properties**:
- `time_display`: Returns formatted time ("HH:MM")

**Example**:
```python
msg = Message(
    id=1,
    text="Hello World",
    sender_id=2611,
    sender_name="John",
    timestamp="2025-01-26T09:30:00Z",
    is_own=True
)
print(msg.time_display)  # "09:30"
```

## Usage in Application

### Loading Data from API
```python
from api.models import User, Group, Message
from api.bitrix_api import BitrixAPI

api = BitrixAPI(user_id=2611, token="your_token")

# Create User
current_user = User(id=2611, name="John", last_name="Doe")

# Create Groups from API response
groups = [
    Group(id=133, title="Sales Team", participants=[2611, 2612])
]

# Create Messages from API response
messages = [
    Message(
        id=1,
        text="Hi there",
        sender_id=2611,
        sender_name="John",
        timestamp="2025-01-26T09:30:00Z"
    )
]
```

### Display Logic
The `display_title()` method handles complex naming logic:
1. Use chat title if set
2. For direct messages, show participant names
3. For groups without names, show first 3 participant names + "..."
4. Fallback to participant count

## Design Patterns

### Dataclass Usage
All models use Python's `@dataclass` decorator for:
- Automatic `__init__` generation
- Default value support
- Clean, readable code

### Optional Fields
Fields with defaults can be omitted when creating instances:
```python
user = User(id=2611, name="John")  # Other fields use defaults
```

### Factory-like Properties
Display properties compute values on-demand:
```python
# Efficiently computed at access time
user.display_name  # Only computed when accessed
```

## Integration Points

### With BitrixAPI
Models receive data from API responses:
- `api.get_groups()` returns data structured into `Group` objects
- `api.get_messages()` returns data for `Message` objects
- `api.get_current_profile()` returns data for `User` object

### With UI Components
Models are passed to UI classes:
- `ChatListItem` displays `Group` information
- `MessageBubble` displays `Message` content
- Header shows `User` information

## Type Hints
All attributes include type hints for IDE support and type checking:
```python
id: int
name: str
is_manager: bool
participants: List[int]
files: List[Dict]
```

## Notes
- All timestamp fields use ISO format (2025-01-26T09:30:00Z)
- Field lists are mutable but should be treated as immutable after creation
- Display methods provide safe fallbacks for missing data
