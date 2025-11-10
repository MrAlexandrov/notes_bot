"""Callback query handlers for the Notes Bot."""

import logging
from datetime import datetime
from pathlib import Path
from telegram import Update
from telegram.ext import ContextTypes

from ..config import ROOT_ID, DAILY_NOTES_DIR, NOTES_DIR
from ..states.manager import StateManager
from ..states.context import UserState
from ..keyboards.main_menu import get_main_menu_keyboard
from ..keyboards.tasks import get_tasks_keyboard, get_task_add_keyboard
from ..keyboards.calendar import get_calendar_keyboard
from ..features.rating import get_rating
from ..features.tasks import parse_tasks, toggle_task
from ..features.calendar_ops import get_existing_dates
from ..notes import read_note, _create_daily_note_from_template
from ..utils import escape_markdown_v2

logger = logging.getLogger(__name__)

# Global state manager instance
state_manager = StateManager()


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Main callback query router.
    
    Parses callback_data and routes to appropriate handler based on action prefix.
    Format: "action:param1:param2:..."
    
    Args:
        update: Telegram update object
        context: Bot context
    """
    query = update.callback_query
    if not query or not query.data or not update.effective_user:
        return
    
    await query.answer()
    
    user_id = update.effective_user.id
    
    # Check authorization
    if ROOT_ID and user_id != ROOT_ID:
        await query.edit_message_text("⛔ Unauthorized access.")
        logger.warning(f"Unauthorized callback from user {user_id}")
        return
    
    callback_data = query.data
    parts = callback_data.split(":")
    
    if len(parts) == 0:
        logger.error(f"Invalid callback_data: {callback_data}")
        return
    
    action = parts[0]
    
    try:
        # Route to appropriate handler
        if action == "menu":
            if len(parts) < 2:
                logger.error(f"Invalid menu callback: {callback_data}")
                return
            
            menu_action = parts[1]
            
            if menu_action == "rating":
                await handle_menu_rating(query, user_id, state_manager)
            elif menu_action == "tasks":
                await handle_menu_tasks(query, user_id, state_manager)
            elif menu_action == "note":
                await handle_menu_note(query, user_id, state_manager)
            elif menu_action == "calendar":
                await handle_menu_calendar(query, user_id, state_manager)
        
        elif action == "task":
            if len(parts) < 2:
                logger.error(f"Invalid task callback: {callback_data}")
                return
            
            task_action = parts[1]
            
            if task_action == "toggle" and len(parts) >= 3:
                task_index = int(parts[2])
                await handle_task_toggle(query, user_id, task_index, state_manager)
            elif task_action == "add":
                await handle_task_add(query, user_id, state_manager)
            elif task_action == "page" and len(parts) >= 3:
                page = int(parts[2])
                await handle_task_page(query, user_id, page, state_manager)
            elif task_action == "back":
                await handle_task_back(query, user_id, state_manager)
            elif task_action == "cancel":
                await handle_task_cancel(query, user_id, state_manager)
            elif task_action == "noop":
                pass  # No operation for pagination display
        
        elif action == "cal":
            if len(parts) < 2:
                logger.error(f"Invalid calendar callback: {callback_data}")
                return
            
            cal_action = parts[1]
            
            if cal_action == "prev":
                await handle_cal_prev(query, user_id, state_manager)
            elif cal_action == "next":
                await handle_cal_next(query, user_id, state_manager)
            elif cal_action == "select" and len(parts) >= 3:
                date = parts[2]
                await handle_cal_select(query, user_id, date, state_manager)
            elif cal_action == "today":
                await handle_cal_today(query, user_id, state_manager)
            elif cal_action == "back":
                await handle_cal_back(query, user_id, state_manager)
            elif cal_action == "noop":
                pass  # No operation for header/weekday display
        
        else:
            logger.warning(f"Unknown callback action: {action}")
    
    except Exception as e:
        logger.error(f"Error handling callback {callback_data}: {e}")
        await query.edit_message_text(
            "❌ Произошла ошибка при обработке действия\\.",
            parse_mode="MarkdownV2"
        )


# Menu handlers

async def handle_menu_rating(query, user_id: int, state_manager: StateManager) -> None:
    """Handle rating menu button - request rating input."""
    user_context = state_manager.get_context(user_id)
    
    # Update state to waiting for rating
    state_manager.update_context(user_id, state=UserState.WAITING_RATING)
    
    # Send rating request
    text = "📊 Введите оценку дня \\(0\\-10\\):"
    
    await query.edit_message_text(
        text,
        parse_mode="MarkdownV2"
    )
    
    logger.info(f"User {user_id} requested rating input")


async def handle_menu_tasks(query, user_id: int, state_manager: StateManager) -> None:
    """Handle tasks menu button - show tasks list."""
    user_context = state_manager.get_context(user_id)
    active_date = user_context.active_date
    
    # Update state
    state_manager.update_context(user_id, state=UserState.TASKS_VIEW, task_page=0)
    
    # Get filepath
    filepath = DAILY_NOTES_DIR / f"{active_date}.md"
    
    # Ensure note exists
    if not filepath.exists():
        _create_daily_note_from_template(filepath, active_date)
    
    # Read and parse tasks
    content = read_note(f"{active_date}.md")
    if not content:
        await query.edit_message_text(
            "❌ Не удалось прочитать заметку\\.",
            parse_mode="MarkdownV2"
        )
        return
    
    tasks = parse_tasks(content)
    
    # Generate tasks keyboard
    keyboard = get_tasks_keyboard(tasks, current_page=0)
    
    # Prepare message
    if tasks:
        text = f"✅ Задачи на {escape_markdown_v2(active_date)}:\n\nВсего задач: {len(tasks)}"
    else:
        text = f"✅ Задачи на {escape_markdown_v2(active_date)}:\n\nЗадач пока нет\\."
    
    await query.edit_message_text(
        text,
        reply_markup=keyboard,
        parse_mode="MarkdownV2"
    )
    
    logger.info(f"User {user_id} opened tasks view")


async def handle_menu_note(query, user_id: int, state_manager: StateManager) -> None:
    """Handle note menu button - display current note."""
    user_context = state_manager.get_context(user_id)
    active_date = user_context.active_date
    
    # Get filepath
    filepath = DAILY_NOTES_DIR / f"{active_date}.md"
    
    # Ensure note exists
    if not filepath.exists():
        _create_daily_note_from_template(filepath, active_date)
    
    # Read note
    content = read_note(f"{active_date}.md")
    if not content:
        await query.edit_message_text(
            "❌ Не удалось прочитать заметку\\.",
            parse_mode="MarkdownV2"
        )
        return
    
    # Get rating if exists
    rating = get_rating(filepath)
    rating_text = f"Оценка: {rating}" if rating is not None else "Оценка: не установлена"
    
    # Prepare note preview (first 3800 chars)
    preview = content[:3800]
    if len(content) > 3800:
        preview += "..."
    
    # Escape for MarkdownV2
    preview_escaped = escape_markdown_v2(preview)
    rating_escaped = escape_markdown_v2(rating_text)
    
    text = (
        f"📝 Заметка {escape_markdown_v2(active_date)}\n\n"
        f"{rating_escaped}\n\n"
        f"```\n{preview_escaped}\n```"
    )
    
    # Get main menu keyboard
    keyboard = get_main_menu_keyboard(active_date)
    
    await query.edit_message_text(
        text,
        reply_markup=keyboard,
        parse_mode="MarkdownV2"
    )
    
    logger.info(f"User {user_id} viewed note for {active_date}")


async def handle_menu_calendar(query, user_id: int, state_manager: StateManager) -> None:
    """Handle calendar menu button - show calendar."""
    user_context = state_manager.get_context(user_id)
    active_date = user_context.active_date
    
    # Update state
    state_manager.update_context(user_id, state=UserState.CALENDAR_VIEW)
    
    # Get existing dates
    existing_dates = get_existing_dates(NOTES_DIR)
    
    # Generate calendar keyboard
    keyboard = get_calendar_keyboard(
        user_context.calendar_year,
        user_context.calendar_month,
        active_date,
        existing_dates
    )
    
    text = f"📅 Календарь\n\nАктивная дата: {escape_markdown_v2(active_date)}"
    
    await query.edit_message_text(
        text,
        reply_markup=keyboard,
        parse_mode="MarkdownV2"
    )
    
    logger.info(f"User {user_id} opened calendar")


# Task handlers

async def handle_task_toggle(query, user_id: int, task_index: int, state_manager: StateManager) -> None:
    """Handle task toggle button - switch task completion status."""
    user_context = state_manager.get_context(user_id)
    active_date = user_context.active_date
    
    # Get filepath
    filepath = DAILY_NOTES_DIR / f"{active_date}.md"
    
    # Toggle task
    if toggle_task(filepath, task_index):
        # Re-read and display updated tasks
        content = read_note(f"{active_date}.md")
        if content:
            tasks = parse_tasks(content)
            keyboard = get_tasks_keyboard(tasks, current_page=user_context.task_page)
            
            text = f"✅ Задачи на {escape_markdown_v2(active_date)}:\n\nВсего задач: {len(tasks)}"
            
            await query.edit_message_text(
                text,
                reply_markup=keyboard,
                parse_mode="MarkdownV2"
            )
            
            logger.info(f"User {user_id} toggled task {task_index}")
    else:
        await query.answer("❌ Ошибка при переключении задачи", show_alert=True)


async def handle_task_add(query, user_id: int, state_manager: StateManager) -> None:
    """Handle add task button - request new task text."""
    # Update state
    state_manager.update_context(user_id, state=UserState.WAITING_NEW_TASK)
    
    # Request task text
    text = "➕ Введите текст новой задачи:"
    keyboard = get_task_add_keyboard()
    
    await query.edit_message_text(
        text,
        reply_markup=keyboard,
        parse_mode="MarkdownV2"
    )
    
    logger.info(f"User {user_id} started adding new task")


async def handle_task_page(query, user_id: int, page: int, state_manager: StateManager) -> None:
    """Handle task pagination - change page."""
    user_context = state_manager.get_context(user_id)
    active_date = user_context.active_date
    
    # Update page
    state_manager.update_context(user_id, task_page=page)
    
    # Get filepath
    filepath = DAILY_NOTES_DIR / f"{active_date}.md"
    
    # Read and parse tasks
    content = read_note(f"{active_date}.md")
    if content:
        tasks = parse_tasks(content)
        keyboard = get_tasks_keyboard(tasks, current_page=page)
        
        text = f"✅ Задачи на {escape_markdown_v2(active_date)}:\n\nВсего задач: {len(tasks)}"
        
        await query.edit_message_text(
            text,
            reply_markup=keyboard,
            parse_mode="MarkdownV2"
        )
        
        logger.info(f"User {user_id} changed to task page {page}")


async def handle_task_back(query, user_id: int, state_manager: StateManager) -> None:
    """Handle task back button - return to main menu."""
    user_context = state_manager.get_context(user_id)
    active_date = user_context.active_date
    
    # Reset state
    state_manager.update_context(user_id, state=UserState.IDLE)
    
    # Show main menu
    text = f"📅 Активная дата: {escape_markdown_v2(active_date)}\n\nВыберите действие:"
    keyboard = get_main_menu_keyboard(active_date)
    
    await query.edit_message_text(
        text,
        reply_markup=keyboard,
        parse_mode="MarkdownV2"
    )
    
    logger.info(f"User {user_id} returned to main menu from tasks")


async def handle_task_cancel(query, user_id: int, state_manager: StateManager) -> None:
    """Handle task cancel button - cancel adding new task."""
    user_context = state_manager.get_context(user_id)
    active_date = user_context.active_date
    
    # Return to tasks view
    state_manager.update_context(user_id, state=UserState.TASKS_VIEW)
    
    # Get filepath
    filepath = DAILY_NOTES_DIR / f"{active_date}.md"
    
    # Read and parse tasks
    content = read_note(f"{active_date}.md")
    if content:
        tasks = parse_tasks(content)
        keyboard = get_tasks_keyboard(tasks, current_page=user_context.task_page)
        
        text = f"✅ Задачи на {escape_markdown_v2(active_date)}:\n\nВсего задач: {len(tasks)}"
        
        await query.edit_message_text(
            text,
            reply_markup=keyboard,
            parse_mode="MarkdownV2"
        )
        
        logger.info(f"User {user_id} cancelled adding task")


# Calendar handlers

async def handle_cal_prev(query, user_id: int, state_manager: StateManager) -> None:
    """Handle calendar previous month button."""
    user_context = state_manager.get_context(user_id)
    
    # Calculate previous month
    month = user_context.calendar_month
    year = user_context.calendar_year
    
    if month == 1:
        month = 12
        year -= 1
    else:
        month -= 1
    
    # Update context
    state_manager.update_context(user_id, calendar_month=month, calendar_year=year)
    
    # Get existing dates
    existing_dates = get_existing_dates(NOTES_DIR)
    
    # Generate calendar
    keyboard = get_calendar_keyboard(year, month, user_context.active_date, existing_dates)
    
    text = f"📅 Календарь\n\nАктивная дата: {escape_markdown_v2(user_context.active_date)}"
    
    await query.edit_message_text(
        text,
        reply_markup=keyboard,
        parse_mode="MarkdownV2"
    )
    
    logger.info(f"User {user_id} navigated to {month}/{year}")


async def handle_cal_next(query, user_id: int, state_manager: StateManager) -> None:
    """Handle calendar next month button."""
    user_context = state_manager.get_context(user_id)
    
    # Calculate next month
    month = user_context.calendar_month
    year = user_context.calendar_year
    
    if month == 12:
        month = 1
        year += 1
    else:
        month += 1
    
    # Update context
    state_manager.update_context(user_id, calendar_month=month, calendar_year=year)
    
    # Get existing dates
    existing_dates = get_existing_dates(NOTES_DIR)
    
    # Generate calendar
    keyboard = get_calendar_keyboard(year, month, user_context.active_date, existing_dates)
    
    text = f"📅 Календарь\n\nАктивная дата: {escape_markdown_v2(user_context.active_date)}"
    
    await query.edit_message_text(
        text,
        reply_markup=keyboard,
        parse_mode="MarkdownV2"
    )
    
    logger.info(f"User {user_id} navigated to {month}/{year}")


async def handle_cal_select(query, user_id: int, date: str, state_manager: StateManager) -> None:
    """Handle calendar date selection."""
    # Set as active date
    state_manager.set_active_date(user_id, date)
    
    # Get filepath
    filepath = DAILY_NOTES_DIR / f"{date}.md"
    
    # Create note if doesn't exist
    if not filepath.exists():
        _create_daily_note_from_template(filepath, date)
        logger.info(f"Created new note for {date}")
    
    # Reset to IDLE state
    state_manager.update_context(user_id, state=UserState.IDLE)
    
    # Show main menu with new active date
    text = (
        f"✅ Выбрана дата: {escape_markdown_v2(date)}\n\n"
        f"📅 Активная дата: {escape_markdown_v2(date)}\n\n"
        f"Выберите действие:"
    )
    keyboard = get_main_menu_keyboard(date)
    
    await query.edit_message_text(
        text,
        reply_markup=keyboard,
        parse_mode="MarkdownV2"
    )
    
    logger.info(f"User {user_id} selected date {date}")


async def handle_cal_today(query, user_id: int, state_manager: StateManager) -> None:
    """Handle calendar today button - return to current date."""
    from ..utils import get_today_filename
    
    # Get today's date
    today_filename = get_today_filename()
    today_date = today_filename.replace(".md", "")
    
    # Set as active date
    state_manager.set_active_date(user_id, today_date)
    
    # Update calendar to current month
    now = datetime.now()
    state_manager.update_context(
        user_id,
        calendar_month=now.month,
        calendar_year=now.year
    )
    
    # Get existing dates
    existing_dates = get_existing_dates(NOTES_DIR)
    
    # Generate calendar
    keyboard = get_calendar_keyboard(now.year, now.month, today_date, existing_dates)
    
    text = f"📅 Календарь\n\nАктивная дата: {escape_markdown_v2(today_date)}"
    
    await query.edit_message_text(
        text,
        reply_markup=keyboard,
        parse_mode="MarkdownV2"
    )
    
    logger.info(f"User {user_id} returned to today: {today_date}")


async def handle_cal_back(query, user_id: int, state_manager: StateManager) -> None:
    """Handle calendar back button - return to main menu."""
    user_context = state_manager.get_context(user_id)
    active_date = user_context.active_date
    
    # Reset state
    state_manager.update_context(user_id, state=UserState.IDLE)
    
    # Show main menu
    text = f"📅 Активная дата: {escape_markdown_v2(active_date)}\n\nВыберите действие:"
    keyboard = get_main_menu_keyboard(active_date)
    
    await query.edit_message_text(
        text,
        reply_markup=keyboard,
        parse_mode="MarkdownV2"
    )
    
    logger.info(f"User {user_id} returned to main menu from calendar")