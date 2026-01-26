# Utility Functions Documentation

## Overview
The `utils` module provides helper functions for formatting, validation, and common operations used throughout the application.

## Module: helpers.py

### Timestamp Formatting

#### `format_timestamp(timestamp, format_str)`
Convert ISO timestamp string to formatted display string

**Parameters**:
- `timestamp` (str): ISO format timestamp (e.g., "2025-01-26T09:30:00Z")
- `format_str` (str, default: "%H:%M"): Python strftime format

**Returns**: `str` - Formatted timestamp

**Examples**:
```python
# Default (time only)
format_timestamp("2025-01-26T09:30:00Z")
# Output: "09:30"

# Custom format
format_timestamp("2025-01-26T09:30:00Z", "%d.%m.%Y %H:%M")
# Output: "26.01.2025 09:30"

# ISO format
format_timestamp("2025-01-26T09:30:00Z", "%Y-%m-%d")
# Output: "2025-01-26"
```

**Handles**:
- Timezone markers (Z suffix)
- ISO format with timezone
- Invalid formats (returns original string)

### User Information

#### `get_user_display_name(user_data)`
Extract best available display name from user data

**Parameters**:
- `user_data` (dict): User information dictionary

**Returns**: `str` - Display name

**Lookup Order**:
1. `name` + `last_name` (if both present)
2. `first_name` + `last_name`
3. `email`
4. `id` (formatted as "User {id}")
5. "Unknown User"

**Examples**:
```python
# Full name available
get_user_display_name({"name": "John", "last_name": "Doe"})
# Output: "John Doe"

# Only email
get_user_display_name({"email": "john@example.com"})
# Output: "john@example.com"

# Minimal data
get_user_display_name({"id": 2611})
# Output: "User 2611"
```

### URL Validation

#### `validate_url(url)`
Check if string is a valid URL

**Parameters**:
- `url` (str): URL to validate

**Returns**: `bool` - True if valid URL

**Examples**:
```python
validate_url("https://example.com")           # True
validate_url("http://localhost:8000")         # True
validate_url("not a url")                     # False
validate_url("")                              # False
```

### Cookie Parsing

#### `extract_user_id_from_cookie(cookie_value)`
Extract numeric user ID from cookie value

**Parameters**:
- `cookie_value` (str): Cookie value string

**Returns**: `int | None` - Extracted user ID or None

**Examples**:
```python
extract_user_id_from_cookie("2611")              # 2611
extract_user_id_from_cookie("USER_2611_DATA")    # 2611
extract_user_id_from_cookie("invalid")           # None
```

**Use Cases**:
- Parse UAD_AVATAR cookie
- Extract ID from BITRIX_SM_UIDH
- Recover user ID from various sources

### Text Manipulation

#### `truncate_text(text, max_length, ellipsis)`
Shorten text to specified length with ellipsis

**Parameters**:
- `text` (str): Text to truncate
- `max_length` (int, default: 100): Maximum length
- `ellipsis` (str, default: "..."): Trailing text

**Returns**: `str` - Truncated text

**Examples**:
```python
truncate_text("This is a very long message", max_length=15)
# Output: "This is a ve..."

truncate_text("Short", max_length=10)
# Output: "Short"

truncate_text("Message", max_length=5, ellipsis="…")
# Output: "Me…"
```

**Use Cases**:
- Last message preview in chat list (100 chars)
- Group titles truncation (50 chars)
- Status text display (200 chars)

### Date Parsing

#### `parse_bitrix_date(date_str)`
Parse various Bitrix24 date formats

**Parameters**:
- `date_str` (str): Date string in any supported format

**Returns**: `datetime | None` - Parsed datetime or None

**Supported Formats**:
1. `2025-01-26T09:30:00+00:00` - ISO with timezone
2. `2025-01-26T09:30:00` - ISO without timezone
3. `26.01.2025 09:30:15` - Russian format with seconds
4. `26.01.2025 09:30` - Russian format without seconds
5. `2025-01-26` - Date only

**Examples**:
```python
# ISO format
dt = parse_bitrix_date("2025-01-26T09:30:00Z")
dt.strftime("%d.%m.%Y")  # "26.01.2025"

# Russian format
dt = parse_bitrix_date("26.01.2025 09:30")
dt.hour  # 9

# Invalid format
dt = parse_bitrix_date("invalid")  # None
```

### Time Calculations

#### `get_elapsed_time(timestamp)`
Convert timestamp to human-readable elapsed time

**Parameters**:
- `timestamp` (str | datetime): Timestamp to calculate from

**Returns**: `str` - Human-readable elapsed time

**Output Examples**:
- "Just now" - 0-30 seconds
- "1 minute ago" - 1-59 seconds
- "5 minutes ago"
- "1 hour ago"
- "Yesterday at 09:30"
- "3 days ago"

**Examples**:
```python
# Recent message
get_elapsed_time("2025-01-26T09:30:00Z")
# Output: "Just now" (if run immediately)

# Older message
get_elapsed_time("2025-01-25T09:30:00Z")
# Output: "1 day ago" (if run on Jan 26)

# String or datetime
current = datetime.now()
get_elapsed_time(current)  # Works with both
```

## Module: file_handlers.py

### File Operations

#### `save_file(file_path, content)`
Save content to file with error handling

**Parameters**:
- `file_path` (str): Destination file path
- `content` (str | bytes): Content to save

**Returns**: `bool` - True if successful

**Examples**:
```python
# Save text
save_file("data.txt", "Hello World")

# Save binary
save_file("image.png", binary_data)
```

#### `load_file(file_path)`
Load file content with error handling

**Parameters**:
- `file_path` (str): Source file path

**Returns**: `str | bytes | None` - File content or None

**Examples**:
```python
# Load text
content = load_file("data.txt")

# Load binary
data = load_file("image.png")
```

#### `ensure_directory(directory)`
Create directory if it doesn't exist

**Parameters**:
- `directory` (str): Directory path

**Returns**: `bool` - True if directory exists or created

**Examples**:
```python
ensure_directory("./data/uploads")
# Creates ./data/ and ./data/uploads/ if needed
```

### File Validation

#### `is_valid_file(file_path)`
Check if file exists and is readable

**Parameters**:
- `file_path` (str): File path to check

**Returns**: `bool` - True if file is valid

#### `get_file_size(file_path)`
Get file size in bytes

**Parameters**:
- `file_path` (str): File path

**Returns**: `int | None` - File size or None if error

**Examples**:
```python
size = get_file_size("document.pdf")
if size and size < 5 * 1024 * 1024:  # < 5MB
    send_file(size)
```

### File Extensions

#### `get_file_extension(file_path)`
Extract file extension

**Parameters**:
- `file_path` (str): File path

**Returns**: `str` - Extension (e.g., "pdf", "doc")

**Examples**:
```python
get_file_extension("document.pdf")  # "pdf"
get_file_extension("archive.tar.gz")  # "gz"
```

#### `is_valid_file_type(file_path, allowed_types)`
Check if file type is allowed

**Parameters**:
- `file_path` (str): File path
- `allowed_types` (list): Allowed extensions (e.g., ["pdf", "doc", "docx"])

**Returns**: `bool` - True if allowed

**Examples**:
```python
allowed = ["pdf", "doc", "docx", "xls", "xlsx"]
if is_valid_file_type("document.pdf", allowed):
    upload_file()
```

## Common Patterns

### Timestamp Display
```python
# In message display
timestamp_str = format_timestamp(message.timestamp)
label.setText(timestamp_str)  # "09:30"
```

### User Name Display
```python
# In sender name
sender_name = get_user_display_name(user_data)
label.setText(sender_name)  # "John Doe" or "john@example.com"
```

### Last Message Preview
```python
# In chat list item
preview = truncate_text(group.last_message, max_length=100)
label.setText(preview)
```

### Date Parsing
```python
# Parse Bitrix response
dt = parse_bitrix_date(response["DATE"])
if dt:
    display_text = dt.strftime("%d.%m.%Y")
```

### File Validation
```python
# Before uploading
if is_valid_file_type(file_path, ["pdf", "doc"]):
    size = get_file_size(file_path)
    if size and size < 10 * 1024 * 1024:  # < 10MB
        upload_file(file_path)
```

## Error Handling

All utility functions include try/except blocks:

```python
def format_timestamp(timestamp: str) -> str:
    try:
        # Parse and format
        return formatted
    except:
        # Return original on error
        return timestamp
```

### Safe Defaults
- `format_timestamp()` - Returns original timestamp if parsing fails
- `parse_bitrix_date()` - Returns None if format not recognized
- `get_user_display_name()` - Falls back to email, then ID, then "Unknown"
- `truncate_text()` - Returns full text if already short

## Type Hints

All functions include proper type hints:

```python
def format_timestamp(timestamp: str, format_str: str = "%H:%M") -> str:
    """..."""
    
def validate_url(url: str) -> bool:
    """..."""
    
def parse_bitrix_date(date_str: str) -> Optional[datetime]:
    """..."""
```

## Integration Examples

### In Main Window
```python
from utils.helpers import format_timestamp, get_user_display_name

# Display message
sender_name = get_user_display_name(message.sender_data)
timestamp = format_timestamp(message.timestamp)
```

### In Chat List Item
```python
from utils.helpers import truncate_text

# Last message preview
preview = truncate_text(group.last_message, max_length=100)
```

### In File Upload
```python
from utils.file_handlers import is_valid_file_type, get_file_size

if is_valid_file_type(filepath, allowed):
    size = get_file_size(filepath)
```

## Performance Notes

### Timestamp Formatting
- Use `format_timestamp()` for display (calls strftime)
- Cache formatted timestamps if using many times
- Avoid repeated parsing of same timestamp

### Text Truncation
- `truncate_text()` is fast for normal lengths
- Acceptable for UI display loops
- Cache truncated text if needed

### File Operations
- Check file size before reading large files
- Use `ensure_directory()` before writing
- Catch exceptions for missing files

## Recommended Usage

### Message Display
```python
# In MessageBubble.apply_style()
sender_name = get_user_display_name(self.message.sender_data)
time_str = format_timestamp(self.message.timestamp)
self.sender_label.setText(sender_name)
self.time_label.setText(time_str)
```

### Chat List Item
```python
# In ChatListItem.__init__()
preview = truncate_text(self.group.last_message, 100)
self.preview_label.setText(preview)
```

### User Input Validation
```python
# Validate URL in link
if validate_url(user_input):
    open_link(user_input)
```

### Date Handling
```python
# Convert API timestamp to display
dt = parse_bitrix_date(api_response["date"])
if dt:
    display_date = dt.strftime("%d.%m.%Y")
```

## See Also
- `API_MODELS.md` - Data structures these utilities work with
- `UI_COMPONENTS.md` - UI components that use these helpers
- `BITRIX_API_CLIENT.md` - API responses that need parsing
