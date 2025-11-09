"""Command and message handlers for the bot."""

import logging
from telegram import Update
from telegram.ext import ContextTypes
from .config import ROOT_ID
from .notes import save_message, read_note
from .utils import get_today_filename, escape_markdown_v2

logger = logging.getLogger(__name__)


async def cmd_today(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /today command - get today's note"""
    # Check if message is from authorized user
    if update.effective_user.id != ROOT_ID:
        logger.warning(
            f"Unauthorized access attempt from user {update.effective_user.id}"
        )
        return

    filename = get_today_filename()
    content = read_note(filename)

    if content:
        date_escaped = escape_markdown_v2(filename[:-3])
        await update.message.reply_text(
            f"📝 *Заметка за {date_escaped}:*\n\n{content}", parse_mode="MarkdownV2"
        )
    else:
        date_escaped = escape_markdown_v2(filename[:-3])
        await update.message.reply_text(
            f"📭 Заметка за сегодня \\({date_escaped}\\) пока пуста",
            parse_mode="MarkdownV2",
        )


async def cmd_get(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /get command - get note for specific date"""
    # Check if message is from authorized user
    if update.effective_user.id != ROOT_ID:
        logger.warning(
            f"Unauthorized access attempt from user {update.effective_user.id}"
        )
        return

    # Check if date argument is provided
    if not context.args or len(context.args) == 0:
        await update.message.reply_text(
            "❌ Укажите дату в формате dd\\-Mmm\\-yyyy\nНапример: `/get 11-Oct-2025`",
            parse_mode="MarkdownV2",
        )
        return

    # Get the date argument
    date_str = context.args[0]
    filename = date_str if date_str.endswith(".md") else date_str + ".md"

    # Validate filename format (basic check)
    if not filename.endswith(".md") or len(filename) < 15:
        await update.message.reply_text(
            "❌ Неверный формат даты\\. Используйте формат dd\\-Mmm\\-yyyy\n"
            "Например: `/get 11-Oct-2025`",
            parse_mode="MarkdownV2",
        )
        return

    content = read_note(filename)

    if content:
        date_escaped = escape_markdown_v2(filename[:-3])
        await update.message.reply_text(
            f"📝 *Заметка за {date_escaped}:*\n\n{content}", parse_mode="MarkdownV2"
        )
    else:
        date_escaped = escape_markdown_v2(filename[:-3])
        await update.message.reply_text(
            f"📭 Заметка за {date_escaped} не найдена", parse_mode="MarkdownV2"
        )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming text messages"""
    # Check if message is from authorized user
    if update.effective_user.id != ROOT_ID:
        logger.warning(
            f"Unauthorized access attempt from user {update.effective_user.id}"
        )
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
