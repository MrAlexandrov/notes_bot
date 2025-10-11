import os
import logging
from datetime import datetime
from pathlib import Path
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# Get configuration from environment
BOT_TOKEN = os.getenv('BOT_TOKEN')
ROOT_ID = int(os.getenv('ROOT_ID'))

# Notes directory
NOTES_DIR = Path('notes')
NOTES_DIR.mkdir(exist_ok=True)


def get_today_filename() -> str:
    """Generate filename in format dd-Mmm-yyyy (e.g., 11-Oct-2025)"""
    now = datetime.now()
    return now.strftime('%d-%b-%Y') + '.md'


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
        f.write(text)
    
    logger.info(f"Message saved to {filename}")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming text messages"""
    # Check if message is from authorized user
    if update.effective_user.id != ROOT_ID:
        logger.warning(f"Unauthorized access attempt from user {update.effective_user.id}")
        return
    
    # Get message text
    text = update.message.text
    
    if not text:
        return
    
    try:
        # Save message to file
        save_message(text)
        
        # Send confirmation
        await update.message.reply_text("✅ Сообщение сохранено в заметку")
        
    except Exception as e:
        logger.error(f"Error saving message: {e}")
        await update.message.reply_text("❌ Ошибка при сохранении сообщения")


def main() -> None:
    """Start the bot"""
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN not found in environment variables")
        return
    
    if not ROOT_ID:
        logger.error("ROOT_ID not found in environment variables")
        return
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add message handler for text messages
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )
    
    logger.info("Bot started successfully")
    
    # Run the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()