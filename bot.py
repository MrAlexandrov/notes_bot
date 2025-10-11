import os
import logging
import re
from datetime import datetime
from pathlib import Path
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes
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
        f.write(f"```\n{text}\n```")
    
    logger.info(f"Message saved to {filename}")


def escape_markdown_v2(text: str) -> str:
    """Escape special characters for MarkdownV2"""
    # Characters that need to be escaped in MarkdownV2
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)


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


async def cmd_today(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /today command - get today's note"""
    # Check if message is from authorized user
    if update.effective_user.id != ROOT_ID:
        logger.warning(f"Unauthorized access attempt from user {update.effective_user.id}")
        return
    
    filename = get_today_filename()
    content = read_note(filename)
    
    if content:
        date_escaped = escape_markdown_v2(filename[:-3])
        await update.message.reply_text(
            f"📝 *Заметка за {date_escaped}:*\n\n{content}",
            parse_mode='MarkdownV2'
        )
    else:
        date_escaped = escape_markdown_v2(filename[:-3])
        await update.message.reply_text(
            f"📭 Заметка за сегодня \\({date_escaped}\\) пока пуста",
            parse_mode='MarkdownV2'
        )


async def cmd_get(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /get command - get note for specific date"""
    # Check if message is from authorized user
    if update.effective_user.id != ROOT_ID:
        logger.warning(f"Unauthorized access attempt from user {update.effective_user.id}")
        return
    
    # Check if date argument is provided
    if not context.args or len(context.args) == 0:
        await update.message.reply_text(
            "❌ Укажите дату в формате dd\\-Mmm\\-yyyy\n"
            "Например: `/get 11-Oct-2025`",
            parse_mode='MarkdownV2'
        )
        return
    
    # Get the date argument
    date_str = context.args[0]
    filename = date_str if date_str.endswith('.md') else date_str + '.md'
    
    # Validate filename format (basic check)
    if not filename.endswith('.md') or len(filename) < 15:
        await update.message.reply_text(
            "❌ Неверный формат даты\\. Используйте формат dd\\-Mmm\\-yyyy\n"
            "Например: `/get 11-Oct-2025`",
            parse_mode='MarkdownV2'
        )
        return
    
    content = read_note(filename)
    
    if content:
        date_escaped = escape_markdown_v2(filename[:-3])
        await update.message.reply_text(
            f"📝 *Заметка за {date_escaped}:*\n\n{content}",
            parse_mode='MarkdownV2'
        )
    else:
        date_escaped = escape_markdown_v2(filename[:-3])
        await update.message.reply_text(
            f"📭 Заметка за {date_escaped} не найдена",
            parse_mode='MarkdownV2'
        )


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
    
    # Add command handlers
    application.add_handler(CommandHandler("today", cmd_today))
    application.add_handler(CommandHandler("get", cmd_get))
    
    # Add message handler for text messages
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )
    
    logger.info("Bot started successfully")
    
    # Run the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()