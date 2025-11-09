"""Utility functions for the Notes Bot."""

import re
from datetime import datetime, timedelta, timezone
from .config import TIMEZONE_OFFSET_HOURS, DAY_START_HOUR


def get_today_filename() -> str:
    """Generate filename in format dd-Mmm-yyyy (e.g., 11-Oct-2025)"""
    # Get current UTC time
    now_utc = datetime.now(timezone.utc)
    
    # Convert to Moscow time (UTC+3)
    moscow_time = now_utc + timedelta(hours=TIMEZONE_OFFSET_HOURS)
    
    # If time is before 7 AM in Moscow, consider it previous day
    if moscow_time.hour < DAY_START_HOUR:
        # Subtract one day
        adjusted_time = moscow_time - timedelta(days=1)
    else:
        adjusted_time = moscow_time
    
    return adjusted_time.strftime('%d-%b-%Y') + '.md'


def escape_markdown_v2(text: str) -> str:
    """Escape special characters for MarkdownV2"""
    # Characters that need to be escaped in MarkdownV2
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)