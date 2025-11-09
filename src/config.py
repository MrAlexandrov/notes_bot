"""Configuration module for the Notes Bot."""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

# Get configuration from environment
BOT_TOKEN = os.getenv("BOT_TOKEN")
_root_id = os.getenv("ROOT_ID")
ROOT_ID = int(_root_id) if _root_id else None

# Notes directory
NOTES_DIR = Path("notes")
NOTES_DIR.mkdir(exist_ok=True)

# Timezone settings
TIMEZONE_OFFSET_HOURS = 3  # Moscow time (UTC+3)
DAY_START_HOUR = 7  # Consider day starts at 7 AM
