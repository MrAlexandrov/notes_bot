"""Notes management module."""

import logging
from .config import NOTES_DIR
from .utils import get_today_filename

logger = logging.getLogger(__name__)


def save_message(text: str) -> None:
    """Save message to today's note file"""
    filename = get_today_filename()
    filepath = NOTES_DIR / filename
    
    # Check if file exists to determine if we need to add a newline
    file_exists = filepath.exists()
    
    with open(filepath, 'a', encoding='utf-8') as f:
        if file_exists:
            # Add empty line before new message
            f.write('\n\n')
        f.write(f"```\n{text}\n```")
    
    logger.info(f"Message saved to {filename}")


def read_note(filename: str) -> str | None:
    """Read note file and return its content"""
    filepath = NOTES_DIR / filename
    
    if not filepath.exists():
        return None
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error reading file {filename}: {e}")
        return None