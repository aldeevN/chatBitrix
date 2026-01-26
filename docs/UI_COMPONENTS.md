# UI Components Documentation

## Overview
The UI module provides PyQt5-based GUI components for the Telegram-style chat application. Components include the main window, message bubbles, chat lists, and custom widgets.

## Core Components

### 1. main_window.py
**Purpose**: Main application window and chat interface

**Class**: `TelegramChatWindow(QMainWindow)`

**Key Features**:
- Two-panel layout: sidebar (chats) + main area (messages)
- Real-time message display
- Theme system (dark/light modes)
- Chat selection and navigation
- Message input with file attachment

**Main Methods**:

#### Window Setup
```python
def setup_ui(self):
    """Initialize UI components"""
    # Creates layout with sidebar + chat area
    # Initializes all subcomponents
    # Applies theme styling
```

#### Sidebar Creation
```python
def create_sidebar(self) -> QWidget:
    """Create left sidebar with chat list"""
    # Search bar
    # Chat list (scrollable)
    # "New Chat" button
```

**Sidebar Features**:
- Modern search bar (🔍)
- Chat list with avatars and unread counts
- Scroll area with refined scrollbar
- Bottom button for creating new chats

**Styling**:
- Search bar: 40px height, rounded (20px), surface variant background
- Chat list: 4px spacing and margins
- Scrollbar: 6px width, subtle handle color

#### Header Creation
```python
def create_sidebar_header(self) -> QWidget:
    """Create top header for sidebar"""
    # Title: "Чаты"
    # Profile button (👤)
    # Menu button (⋯)
    # Filter button: "Все чаты"
```

**Header Features**:
- Height: 56px (compact)
- Modern title with Material Design 3 styling
- Action buttons with hover effects
- No bottom border (cleaner look)

#### Chat Area
```python
def create_chat_area(self) -> QWidget:
    """Create main chat display area"""
    # Chat header (with title + subtitle)
    # Message scroll area
    # Message input area
```

**Chat Area Features**:
- Dynamic title updates
- Subtitle shows participant count or status
- Scrollable message area
- Modern input field with rounded borders

#### Chat Header
```python
def create_chat_header(self) -> QWidget:
    """Create header for chat area"""
    # Back button (←) - hidden by default
    # Chat title (2-line)
    # Search and menu buttons
```

**Header Details**:
- Height: 56px
- Title line 1: Chat name (15px, bold)
- Title line 2: Status/participants (12px, secondary)
- No bottom border

#### Input Area
```python
def create_input_area(self) -> QWidget:
    """Create message input interface"""
    # Attachment button (➕)
    # Message input field
    # Send button (↗)
```

**Input Features**:
- Height: 68px (compact)
- Input field: rounded (20px), surface variant background
- Placeholder: "Сообщение..."
- Attachment button: transparent with hover
- Send button: primary color, circular

**Styling**:
- Input focus: 2px primary border
- Send button: hover with opacity change
- All elements aligned vertically

#### Message Handling
```python
def load_messages(self, group_id: int):
    """Load and display messages for group"""
    # Fetch from API
    # Convert to Message objects
    # Display in scroll area
```

```python
def send_message(self):
    """Send message from input field"""
    # Get text from input
    # Clear field
    # Send via API (future enhancement)
```

#### Chat Selection
```python
def select_chat(self, group_id: int):
    """Select and display a chat"""
    # Find group by ID
    # Update title with display name
    # Update subtitle with participant count
    # Load messages
    # Show back button
```

**Subtitle Logic**:
```python
member_count = len(group.members)
if member_count == 1:
    subtitle = "1 участник"
else:
    subtitle = f"{member_count} участников"
```

#### Theme Application
```python
def apply_current_theme(self):
    """Apply current theme to all components"""
    # Get theme colors
    # Update all widgets
    # Update stylesheets
    # Refresh display
```

### 2. themes.py
**Purpose**: Color system and theme management

**Color Palettes**:

#### Light Theme (COLORS_LIGHT)
```python
PRIMARY = '#3390ec'           # Main blue
PRIMARY_DARK = '#2b7bc2'      # Dark blue
BACKGROUND = '#f5f5f7'        # Light gray bg
SURFACE = '#ffffff'           # White panels
SURFACE_VARIANT = '#f0f0f3'   # Light variant
ON_SURFACE = '#000000'        # Black text
ON_SURFACE_VARIANT = '#65676b' # Gray text
BORDER = '#e0e0e0'            # Light borders
```

#### Dark Theme (COLORS_DARK)
```python
PRIMARY = '#4fa3f5'           # Bright blue
PRIMARY_DARK = '#2b7bc2'      # Dark blue
BACKGROUND = '#0a0e27'        # Very dark bg
SURFACE = '#1a1f3a'           # Dark panels
SURFACE_VARIANT = '#2a3054'   # Darker variant
ON_SURFACE = '#e8eaed'        # Light text
ON_SURFACE_VARIANT = '#9aa0a6' # Gray text
BORDER = '#3f4555'            # Dark borders
```

**Functions**:

```python
def get_theme_colors(is_dark_mode: bool) -> Dict:
    """Get color palette for theme"""
    return COLORS_DARK if is_dark_mode else COLORS_LIGHT
```

```python
def apply_theme(widget, is_dark_mode=False) -> None:
    """Apply comprehensive stylesheet to widget"""
    # Generates Qt stylesheet
    # Covers all component types
    # Updates colors dynamically
```

### 3. widgets.py
**Purpose**: Custom reusable UI components

#### TelegramButton
**Features**:
- Rounded button with primary color
- Hover effects
- Text or icon support
- Theme-aware styling

**Usage**:
```python
button = TelegramButton(
    text="New Chat",
    is_dark=False
)
button.clicked.connect(on_click)
```

**Styling**:
```css
/* Normal state */
background-color: #3390ec;
border: none;
border-radius: 8px;
color: white;
font-weight: bold;

/* Hover state */
background-color: #2b7bc2;

/* Pressed state */
background-color: #1f5a96;
```

#### TelegramInput
**Features**:
- Rounded input field
- Placeholder text
- Focus state styling
- Theme support

**Usage**:
```python
input_field = TelegramInput(
    placeholder="Type message...",
    is_dark=False
)
```

**Styling**:
```css
/* Normal state */
background-color: #f0f0f3;
border: 1px solid #e0e0e0;
border-radius: 20px;
padding: 8px 16px;

/* Focus state */
border: 2px solid #3390ec;
padding: 8px 15px;
```

#### TelegramSearchBar
**Features**:
- Search field with icon
- Clear button
- Theme colors
- Focus effects

**Usage**:
```python
search = TelegramSearchBar(
    placeholder="Search chats...",
    is_dark=False
)
search.text_changed.connect(on_search)
```

### 4. message_bubble.py
**Purpose**: Display individual messages

**Class**: `MessageBubble(QWidget)`

**Features**:
- Styled message containers
- Sender name display (for groups)
- Timestamp
- File attachments
- Read status indicator
- Different styling for own vs received messages

**Layout**:
```
┌─────────────────────────────┐
│ Sender Name (groups only)   │
├─────────────────────────────┤
│ Message text                │
│ (can wrap to multiple lines)│
├─────────────────────────────┤
│ [Attachment] [✓ 09:30]      │
└─────────────────────────────┘
```

**Own Messages** (right-aligned, primary color):
```
                    ┌──────────────┐
                    │ My message   │
                    │ ✓ 09:30      │
                    └──────────────┘
```

**Received Messages** (left-aligned, surface color):
```
┌──────────────┐
│ John Doe     │
├──────────────┤
│ Their msg    │
│ 09:30        │
└──────────────┘
```

**Constructor**:
```python
bubble = MessageBubble(
    message=message_obj,
    current_user=user,
    is_own=True,
    is_dark=False,
    is_group_chat=True
)
```

**Methods**:
```python
def set_message(self, message):
    """Update message display"""
    
def apply_style(self):
    """Apply theme colors"""
    
def show_attachment(self, file_data):
    """Display file attachment"""
```

**Styling Logic**:
- Own messages: Primary color background, white text
- Received: Surface color background, on-surface text
- Sender name: Secondary color, smaller font
- Timestamp: On-surface-variant color
- Attachment: Icon + filename, clickable

### 5. chat_list_item.py
**Purpose**: Display chat entries in sidebar

**Class**: `ChatListItem(QWidget)`

**Features**:
- Avatar with user initials
- Chat title
- Last message preview
- Timestamp of last message
- Unread count badge
- Hover effects

**Layout**:
```
┌─────────────────────────────────┐
│ [👤] Title           [9] 09:30  │
│      Last message preview...    │
└─────────────────────────────────┘
```

**Components**:
- Avatar: 44x44px circle with initials
- Title: 14px bold, on-surface color
- Message preview: 13px secondary, truncated
- Timestamp: 12px secondary, right-aligned
- Badge: Unread count in circle (primary color)

**Hover Effects**:
```css
/* Normal */
background-color: white;

/* Hover */
background-color: #f0f0f3;
```

**Constructor**:
```python
item = ChatListItem(
    group=group_obj,
    current_user=user,
    is_dark=False
)
item.clicked.connect(on_chat_selected)
```

**Methods**:
```python
def update_unread_count(self, count):
    """Update badge with new count"""
    
def update_last_message(self, message):
    """Update message preview"""
    
def set_selected(self, selected):
    """Highlight selected state"""
```

### 6. new_message_dialog.py
**Purpose**: Compose and send new messages

**Class**: `NewMessageDialog(QDialog)`

**Features**:
- Group/recipient selector dropdown
- Message text area
- Character counter (limit: 4000)
- Send/cancel buttons
- Theme support
- Validation

**Layout**:
```
┌─────────────────────────────┐
│ New Message                 │
├─────────────────────────────┤
│ Group: [Dropdown ▼]         │
│                             │
│ ┌─────────────────────────┐ │
│ │ Type your message...    │ │
│ │                         │ │
│ │                    1200 │ │
│ └─────────────────────────┘ │
├─────────────────────────────┤
│ [Cancel]            [Send]  │
└─────────────────────────────┘
```

**Components**:
- Group selector: QComboBox with all groups
- Text area: QPlainTextEdit, wrapping enabled
- Counter: Live character count
- Buttons: Cancel (secondary), Send (primary)

**Constructor**:
```python
dialog = NewMessageDialog(
    groups=groups_list,
    current_user=user,
    customers=customers_list,
    is_dark=False
)

if dialog.exec_() == QDialog.Accepted:
    text = dialog.message_text
    group_id = dialog.selected_group_id
```

**Signals**:
```python
# Emitted when message sent
message_sent = pyqtSignal(str, int)  # (text, group_id)
```

**Validation**:
```python
def validate(self) -> bool:
    """Check if message is valid"""
    # Text not empty
    # Text length <= 4000
    # Group selected
    return True
```

## Layout System

### Main Window Layout
```
┌────────────────────────────────────┐
│ Sidebar         │ Chat Area        │
├─────────────────┼──────────────────┤
│ Header          │ Chat Header      │
│ (56px)          │ (56px)           │
├─────────────────┼──────────────────┤
│ Search          │                  │
│ (40px)          │                  │
├─────────────────┤ Messages         │
│                 │ (scrollable)     │
│ Chat List       │                  │
│ (scrollable)    │                  │
│ 4px spacing     │                  │
│                 │                  │
├─────────────────┼──────────────────┤
│ [New Chat]      │ Input Area       │
│ (48px)          │ (68px)           │
└─────────────────┴──────────────────┘
```

**Responsive Sizing**:
- Sidebar: 300px minimum width
- Chat area: Remaining space
- Messages: Flexible height
- Input: Fixed 68px

## Styling System

### Stylesheet Generation
All themes generated via `apply_theme()`:
```python
stylesheet = f"""
    QWidget#chatArea {{
        background-color: {colors['BACKGROUND']};
    }}
    QLabel {{
        color: {colors['ON_SURFACE']};
    }}
    ... (comprehensive stylesheet)
"""
widget.setStyleSheet(stylesheet)
```

### Dynamic Theme Updates
```python
# Change theme at runtime
self.is_dark_mode = not self.is_dark_mode
self.apply_current_theme()  # Refreshes all components
```

## Event Handling

### Chat Selection
```
User clicks ChatListItem
    ↓
chatListItem.clicked signal
    ↓
Main window: select_chat(group_id)
    ↓
Load messages
    ↓
Display in message area
```

### Message Input
```
User types in input field
    ↓
User presses Enter or clicks Send
    ↓
send_message() method
    ↓
Extract text and group ID
    ↓
API call (future)
    ↓
Display in message list
```

### Real-time Updates
```
Pull client: message_received signal
    ↓
Main window: handle_pull_message()
    ↓
Check if group is active
    ↓
Add to message display
    ↓
Scroll to bottom
```

## Integration with Data Models

### Chat Data Flow
```
BitrixAPI.get_groups()
    ↓
[Group objects]
    ↓
ChatListItem widgets (one per group)
    ↓
Display in sidebar
```

### Message Data Flow
```
BitrixAPI.get_messages(group_id)
    ↓
[Message objects]
    ↓
MessageBubble widgets (one per message)
    ↓
Display in scroll area
```

## Performance Optimizations

### Lazy Loading
- Messages loaded on demand
- Chat list cached
- Avatars rendered at low resolution

### Efficient Updates
- Partial UI updates
- Signals/slots for threading
- Stylesheet caching

### Memory Management
- MessageBubbles reused when scrolling
- Old messages removed from display
- Images cached with size limits

## Accessibility

### Keyboard Navigation
- Tab through components
- Enter to send message
- Escape to close dialogs

### Screen Reader Support
- Alt text for icons
- Descriptive labels
- Proper tab order

### Color Contrast
- WCAG AA compliant
- Light/dark themes for different needs
- No color-only information

## See Also
- `themes.py` - Complete theme system
- `main_window.py` - Main window implementation
- `TELEGRAM_DESIGN_UPDATE.md` - Design specifications
