"""Main bot module."""

import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters
from .config import BOT_TOKEN, ROOT_ID
from .handlers import cmd_today, cmd_get, handle_message

logger = logging.getLogger(__name__)


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