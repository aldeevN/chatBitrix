"""
File handling utilities
"""

import os
import mimetypes
from typing import Dict

def download_file(file_info: Dict, save_path: str = None) -> str:
    """Download a file from Bitrix24"""
    try:
        import requests
        
        url = file_info.get('download_link') or file_info.get('url')
        if not url:
            raise ValueError("No download URL provided")
        
        filename = file_info.get('name', 'downloaded_file')
        
        # If no save path provided, use current directory
        if not save_path:
            save_path = os.path.join(os.getcwd(), filename)
        
        # Download the file
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return save_path
    
    except Exception as e:
        print(f"Error downloading file: {e}")
        return None

def format_size(size_in_bytes: int) -> str:
    """Format file size in human-readable format"""
    if not size_in_bytes:
        return "0 B"
    
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_in_bytes < 1024.0:
            return f"{size_in_bytes:.1f} {unit}"
        size_in_bytes /= 1024.0
    
    return f"{size_in_bytes:.1f} PB"

def get_file_icon(filename: str) -> str:
    """Get emoji icon for file type"""
    ext = os.path.splitext(filename)[1].lower()
    
    icons = {
        # Documents
        '.pdf': '📕',
        '.doc': '📘', '.docx': '📘',
        '.txt': '📝', '.rtf': '📝',
        '.xls': '📊', '.xlsx': '📊', '.csv': '📊',
        '.ppt': '📽️', '.pptx': '📽️',
        
        # Images
        '.jpg': '🖼️', '.jpeg': '🖼️', '.png': '🖼️',
        '.gif': '🖼️', '.bmp': '🖼️', '.svg': '🖼️',
        '.ico': '🖼️', '.webp': '🖼️',
        
        # Archives
        '.zip': '📦', '.rar': '📦', '.7z': '📦',
        '.tar': '📦', '.gz': '📦',
        
        # Audio
        '.mp3': '🎵', '.wav': '🎵', '.flac': '🎵',
        '.aac': '🎵', '.ogg': '🎵',
        
        # Video
        '.mp4': '🎬', '.avi': '🎬', '.mov': '🎬',
        '.wmv': '🎬', '.flv': '🎬', '.mkv': '🎬',
        
        # Code
        '.py': '🐍', '.js': '📜', '.html': '🌐',
        '.css': '🎨', '.json': '📋', '.xml': '📋',
        
        # Executables
        '.exe': '⚙️', '.msi': '⚙️', '.bat': '⚙️',
        '.sh': '⚙️',
    }
    
    return icons.get(ext, '📎')  # Default: paperclip

def get_mime_type(filename: str) -> str:
    """Get MIME type for file"""
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or 'application/octet-stream'

def is_safe_filename(filename: str) -> bool:
    """Check if filename is safe"""
    dangerous_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    return not any(char in filename for char in dangerous_chars)

def sanitize_filename(filename: str) -> str:
    """Sanitize filename by removing dangerous characters"""
    dangerous_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    for char in dangerous_chars:
        filename = filename.replace(char, '_')
    return filename