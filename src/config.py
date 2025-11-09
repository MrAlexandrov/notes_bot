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

# Notes directory - must be specified in environment variable
NOTES_DIR_STR = os.getenv("NOTES_DIR")
if not NOTES_DIR_STR:
    raise ValueError("NOTES_DIR environment variable must be set")

NOTES_DIR = Path(NOTES_DIR_STR)
if not NOTES_DIR.exists():
    raise ValueError(f"NOTES_DIR path does not exist: {NOTES_DIR}")

# Daily notes subdirectory
DAILY_NOTES_DIR = NOTES_DIR / "Daily"
DAILY_NOTES_DIR.mkdir(exist_ok=True)

# Template directory and file - must be specified in environment variable
TEMPLATE_DIR_STR = os.getenv("TEMPLATE_DIR")
if not TEMPLATE_DIR_STR:
    raise ValueError("TEMPLATE_DIR environment variable must be set")

TEMPLATE_DIR = Path(TEMPLATE_DIR_STR)
if not TEMPLATE_DIR.exists():
    raise ValueError(f"TEMPLATE_DIR path does not exist: {TEMPLATE_DIR}")

DAILY_TEMPLATE_PATH = TEMPLATE_DIR / "Daily.md"
if not DAILY_TEMPLATE_PATH.exists():
    raise ValueError(f"Daily template not found at: {DAILY_TEMPLATE_PATH}")

# Timezone settings
TIMEZONE_OFFSET_HOURS = 3  # Moscow time (UTC+3)
DAY_START_HOUR = 7  # Consider day starts at 7 AM
