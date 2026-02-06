"""
Telegram-inspired themes and colors for UI
"""

from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QApplication

# Telegram Light Mode (Official)
TELEGRAM_LIGHT = {
    # Core colors
    'PRIMARY': '#3390ec',
    'PRIMARY_DARK': '#2b7bc2',
    'BACKGROUND': '#ffffff',
    'SURFACE': '#f8f9fa',
    'SURFACE_VARIANT': '#e9ecef',
    'ON_PRIMARY': '#ffffff',
    'ON_BACKGROUND': '#000000',
    'ON_SURFACE': '#212529',
    'ON_SURFACE_VARIANT': '#6c757d',
    'BORDER': '#dee2e6',
    
    # Message bubbles
    'INCOMING_BUBBLE': '#ffffff',
    'OUTGOING_BUBBLE': '#3390ec',
    'INCOMING_TEXT': '#000000',
    'OUTGOING_TEXT': '#ffffff',
    'BUBBLE_BORDER': '#e0e0e0',
    
    # Status indicators
    'ONLINE': '#4caf50',
    'OFFLINE': '#9e9e9e',
    'RECENTLY_ONLINE': '#ff9800',
    
    # Additional
    'LINK': '#3390ec',
    'HIGHLIGHT': 'rgba(51, 144, 236, 0.1)',
    'SELECTION': 'rgba(51, 144, 236, 0.3)',
    'PINNED_BG': 'rgba(255, 193, 7, 0.1)',
    
    # Backward compatibility
    'TELEGRAM_BLUE': '#3390ec',
    'TELEGRAM_BLUE_DARK': '#2b7bc2',
    'TEXT_LIGHT': '#000000',
    'TEXT_SECONDARY_LIGHT': '#6c757d',
}

# Telegram Dark Mode (Official)
TELEGRAM_DARK = {
    # Core colors
    'PRIMARY': '#3390ec',
    'PRIMARY_DARK': '#2b7bc2',
    'BACKGROUND': '#0e1621',
    'SURFACE': '#17212b',
    'SURFACE_VARIANT': '#242f3d',
    'ON_PRIMARY': '#ffffff',
    'ON_BACKGROUND': '#e1e3e6',
    'ON_SURFACE': '#ffffff',
    'ON_SURFACE_VARIANT': '#8a9aa9',
    'BORDER': '#2b5278',
    
    # Message bubbles
    'INCOMING_BUBBLE': '#182533',
    'OUTGOING_BUBBLE': '#2b5278',
    'INCOMING_TEXT': '#ffffff',
    'OUTGOING_TEXT': '#ffffff',
    'BUBBLE_BORDER': '#2b5278',
    
    # Status indicators
    'ONLINE': '#34c759',
    'OFFLINE': '#8e8e93',
    'RECENTLY_ONLINE': '#ff9500',
    
    # Additional
    'LINK': '#3390ec',
    'HIGHLIGHT': 'rgba(51, 144, 236, 0.2)',
    'SELECTION': 'rgba(51, 144, 236, 0.4)',
    'PINNED_BG': 'rgba(255, 149, 0, 0.1)',
    
    # Backward compatibility
    'TELEGRAM_BLUE': '#3390ec',
    'TELEGRAM_BLUE_DARK': '#2b7bc2',
    'TEXT_LIGHT': '#e1e3e6',
    'TEXT_SECONDARY_LIGHT': '#8a9aa9',
}

def get_theme_colors(is_dark_mode: bool):
    """Get colors for the specified theme"""
    return TELEGRAM_DARK if is_dark_mode else TELEGRAM_LIGHT

def apply_telegram_theme(app, is_dark_mode=False):
    """Apply complete Telegram theme to application"""
    colors = get_theme_colors(is_dark_mode)
    
    # Create comprehensive stylesheet
    stylesheet = f"""
        /* Main Window */
        QMainWindow {{
            background-color: {colors['BACKGROUND']};
            color: {colors['ON_BACKGROUND']};
        }}
        
        /* Sidebar */
        QWidget#sidebar {{
            background-color: {colors['SURFACE']};
            border-right: 1px solid {colors['BORDER']};
        }}
        
        /* Chat Area */
        QWidget#chatArea {{
            background-color: {colors['BACKGROUND']};
        }}
        
        /* Scroll Areas */
        QScrollArea {{
            background-color: {colors['BACKGROUND']};
            border: none;
        }}
        
        /* Scroll Bars */
        QScrollBar:vertical {{
            background-color: transparent;
            width: 6px;
            border-radius: 3px;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: {colors['ON_SURFACE_VARIANT']};
            border-radius: 3px;
            min-height: 30px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background-color: {colors['BORDER']};
        }}
        
        QScrollBar:horizontal {{
            background-color: transparent;
            height: 6px;
            border-radius: 3px;
        }}
        
        QScrollBar::handle:horizontal {{
            background-color: {colors['ON_SURFACE_VARIANT']};
            border-radius: 3px;
            min-width: 30px;
        }}
        
        /* Buttons */
        QPushButton {{
            border: none;
            border-radius: 8px;
            padding: 8px 16px;
            font-size: 14px;
            font-weight: 500;
            color: {colors['ON_SURFACE']};
            background-color: transparent;
        }}
        
        QPushButton:hover {{
            background-color: {colors['HIGHLIGHT']};
        }}
        
        QPushButton:pressed {{
            background-color: {colors['SELECTION']};
        }}
        
        QPushButton[primary="true"] {{
            background-color: {colors['PRIMARY']};
            color: {colors['ON_PRIMARY']};
        }}
        
        /* Inputs */
        QLineEdit, QTextEdit {{
            background-color: {colors['SURFACE_VARIANT']};
            border: 1px solid {colors['BORDER']};
            border-radius: 8px;
            padding: 8px 12px;
            font-size: 14px;
            color: {colors['ON_SURFACE']};
            selection-background-color: {colors['PRIMARY']};
            selection-color: {colors['ON_PRIMARY']};
        }}
        
        QLineEdit:focus, QTextEdit:focus {{
            border: 2px solid {colors['PRIMARY']};
            background-color: {colors['SURFACE']};
        }}
        
        /* Labels */
        QLabel {{
            color: {colors['ON_SURFACE']};
            font-size: 14px;
        }}
        
        /* Dialogs */
        QDialog {{
            background-color: {colors['SURFACE']};
            border: 1px solid {colors['BORDER']};
            border-radius: 12px;
        }}
        
        /* Menus */
        QMenu {{
            background-color: {colors['SURFACE']};
            border: 1px solid {colors['BORDER']};
            border-radius: 8px;
            padding: 4px;
        }}
        
        QMenu::item {{
            padding: 8px 24px 8px 16px;
            border-radius: 4px;
            color: {colors['ON_SURFACE']};
        }}
        
        QMenu::item:selected {{
            background-color: {colors['HIGHLIGHT']};
        }}
        
        QMenu::separator {{
            height: 1px;
            background-color: {colors['BORDER']};
            margin: 4px 8px;
        }}
        
        /* Tool Tips */
        QToolTip {{
            background-color: {colors['SURFACE']};
            color: {colors['ON_SURFACE']};
            border: 1px solid {colors['BORDER']};
            border-radius: 4px;
            padding: 4px 8px;
        }}
    """
    
    app.setStyleSheet(stylesheet)
    
    # Also set palette for native widgets
    palette = app.palette()
    if is_dark_mode:
        palette.setColor(palette.Window, QColor(colors['BACKGROUND']))
        palette.setColor(palette.WindowText, QColor(colors['ON_BACKGROUND']))
        palette.setColor(palette.Base, QColor(colors['SURFACE']))
        palette.setColor(palette.AlternateBase, QColor(colors['SURFACE_VARIANT']))
        palette.setColor(palette.Text, QColor(colors['ON_SURFACE']))
        palette.setColor(palette.Button, QColor(colors['SURFACE']))
        palette.setColor(palette.ButtonText, QColor(colors['ON_SURFACE']))
        palette.setColor(palette.Highlight, QColor(colors['SELECTION']))
        palette.setColor(palette.HighlightedText, QColor(colors['ON_PRIMARY']))
    app.setPalette(palette)

# Backward compatibility functions
def apply_theme(widget, is_dark_mode=False):
    """Backward compatibility alias for apply_telegram_theme"""
    apply_telegram_theme(widget, is_dark_mode)

def toggle_dark_mode(widget, current_mode):
    """Toggle dark mode and return new mode"""
    new_mode = not current_mode
    apply_telegram_theme(widget, new_mode)
    return new_mode

# Backward compatibility constants
COLORS_LIGHT = TELEGRAM_LIGHT
COLORS_DARK = TELEGRAM_DARK
COLORS = TELEGRAM_LIGHT

# Export all constants for backward compatibility
__all__ = [
    'TELEGRAM_LIGHT',
    'TELEGRAM_DARK',
    'COLORS_LIGHT',
    'COLORS_DARK',
    'COLORS',
    'get_theme_colors',
    'apply_telegram_theme',
    'apply_theme',
    'toggle_dark_mode'
]