"""
Themes and colors for the UI - Dark and Light themes
"""

# Light theme colors
COLORS_LIGHT = {
    'PRIMARY': '#3390ec',
    'PRIMARY_DARK': '#2b7bc2',
    'BACKGROUND': '#f5f5f7',
    'SURFACE': '#ffffff',
    'SURFACE_VARIANT': '#f0f0f3',
    'ON_SURFACE': '#000000',
    'ON_SURFACE_VARIANT': '#65676b',
    'BORDER': '#e0e0e0',
    'DIVIDER': '#e5e5e5',
    'SUCCESS': '#31a24c',
    'ERROR': '#f44336',
    'WARNING': '#ff9800',
    'INFO': '#2196f3',
    # Backward compatibility
    'TELEGRAM_BLUE': '#3390ec',
    'TELEGRAM_BLUE_DARK': '#2b7bc2',
    'TEXT_LIGHT': '#000000',
    'TEXT_SECONDARY_LIGHT': '#65676b',
}

# Dark theme colors
COLORS_DARK = {
    'PRIMARY': '#4fa3f5',
    'PRIMARY_DARK': '#2b7bc2',
    'BACKGROUND': '#0a0e27',
    'SURFACE': '#1a1f3a',
    'SURFACE_VARIANT': '#2a3054',
    'ON_SURFACE': '#e8eaed',
    'ON_SURFACE_VARIANT': '#9aa0a6',
    'BORDER': '#3f4555',
    'DIVIDER': '#424d63',
    'SUCCESS': '#4caf50',
    'ERROR': '#f44336',
    'WARNING': '#ff9800',
    'INFO': '#2196f3',
    # Backward compatibility
    'TELEGRAM_BLUE': '#4fa3f5',
    'TELEGRAM_BLUE_DARK': '#2b7bc2',
    'TEXT_LIGHT': '#e8eaed',
    'TEXT_SECONDARY_LIGHT': '#9aa0a6',
}

# Default to light theme
COLORS = COLORS_LIGHT

def get_theme_colors(is_dark_mode: bool):
    """Get colors for the specified theme"""
    return COLORS_DARK if is_dark_mode else COLORS_LIGHT

def apply_theme(widget, is_dark_mode=False):
    """Apply theme to widget with modern design"""
    colors = get_theme_colors(is_dark_mode)
    
    stylesheet = f"""
        QMainWindow {{
            background-color: {colors['BACKGROUND']};
            color: {colors['ON_SURFACE']};
        }}
        
        QWidget#sidebar {{
            background-color: {colors['SURFACE']};
            border-right: 1px solid {colors['BORDER']};
        }}
        
        QWidget#chatArea {{
            background-color: {colors['BACKGROUND']};
        }}
        
        QScrollArea {{
            background-color: {colors['BACKGROUND']};
            border: none;
        }}
        
        QScrollBar:vertical {{
            background-color: {colors['BACKGROUND']};
            width: 8px;
            border-radius: 4px;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: {colors['ON_SURFACE_VARIANT']};
            border-radius: 4px;
            min-height: 30px;
            margin: 2px 2px 2px 2px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background-color: {colors['BORDER']};
        }}
        
        QMessageBox {{
            background-color: {colors['SURFACE']};
        }}
        
        QMessageBox QLabel {{
            color: {colors['ON_SURFACE']};
        }}
        
        QDialog {{
            background-color: {colors['SURFACE']};
        }}
    """
    
    widget.setStyleSheet(stylesheet)

def toggle_dark_mode(widget, current_mode):
    """Toggle dark mode and return new mode"""
    new_mode = not current_mode
    apply_theme(widget, new_mode)
    return new_mode