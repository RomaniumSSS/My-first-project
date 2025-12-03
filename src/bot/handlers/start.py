from aiogram import Router, F, types
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from src.database.models import User, Goal
from src.bot.states import (
    OnboardingStates,
    GoalSettingStates,
    CheckInStates,
    CrisisStates,
    ReflectStates,
)
from src.bot.callbacks import MenuCallback, CheckinCallback

router = Router()


# ============== Клавиатуры ==============


def get_persistent_menu():
    """Постоянная Reply клавиатура с меню."""
    builder = ReplyKeyboardBuilder()
    builder.button(text="📋 Меню")
    builder.button(text="🎯 Новая цель")
    builder.button(text="✅ Чек-ин")
    builder.button(text="🧘 Рефлексия")
    builder.button(text="🆘 Кризис")
    builder.adjust(1, 4)  # Меню на первой строке, остальные на второй
    return builder.as_markup(resize_keyboard=True, is_persistent=True)


def get_main_menu_keyboard(has_goals: bool = False):
    """Inline меню бота."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🎯 Новая цель", callback_data=MenuCallback(action="new_goal"))
    if has_goals:
        builder.button(text="✅ Чек-ин", callback_data=MenuCallback(action="checkin"))
    builder.button(text="🧘 Рефлексия", callback_data=MenuCallback(action="reflect"))
    builder.button(text="🆘 Кризис", callback_data=MenuCallback(action="crisis"))
    builder.adjust(2)
    return builder.as_markup()


# ============== Команды ==============


@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    """
    Handle /start command.
    Checks if user exists. If not, starts onboarding.
    """
    telegram_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name

    # Check if user exists
    user = await User.get_or_none(telegram_id=telegram_id)

    if not user:
        # Create new user immediately to store basic info
        user = await User.create(
            telegram_id=telegram_id, username=username, first_name=first_name
        )
        await message.answer(
            f"Привет, {first_name or 'друг'}! Я твой AI-коуч.\n"
            "Давай познакомимся. Как мне тебя называть?",
            reply_markup=get_persistent_menu(),
        )
        await state.set_state(OnboardingStates.waiting_for_name)
    else:
        # Clear any previous state to avoid getting stuck
        await state.clear()

        # Check if user has active goals
        has_goals = await Goal.filter(user=user, status="active").exists()

        display_name = user.first_name or message.from_user.first_name or "друг"
        await message.answer(
            f"С возвращением, {display_name}! 👋\n\n" "Выбери, что хочешь сделать:",
            reply_markup=get_persistent_menu(),
        )
        await message.answer(
            "Или выбери из меню:", reply_markup=get_main_menu_keyboard(has_goals)
        )


@router.message(Command("menu"))
async def cmd_menu(message: types.Message, state: FSMContext):
    """
    Показать главное меню.
    """
    user = await User.get_or_none(telegram_id=message.from_user.id)

    if not user:
        await message.answer("Сначала нужно познакомиться! Нажми /start")
        return

    # Clear any previous state
    await state.clear()

    # Check if user has active goals
    has_goals = await Goal.filter(user=user, status="active").exists()

    display_name = user.first_name or message.from_user.first_name or "друг"
    await message.answer(
        f"📋 *Главное меню*\n\n" f"Привет, {display_name}! Выбери действие:",
        parse_mode="Markdown",
        reply_markup=get_main_menu_keyboard(has_goals),
    )


# ============== Обработка текстовых кнопок меню ==============


@router.message(F.text == "📋 Меню")
async def handle_menu_button(message: types.Message, state: FSMContext):
    """Обработка нажатия кнопки Меню."""
    await cmd_menu(message, state)


@router.message(F.text == "🎯 Новая цель")
async def handle_new_goal_button(message: types.Message, state: FSMContext):
    """Обработка кнопки Новая цель."""
    user = await User.get_or_none(telegram_id=message.from_user.id)
    if not user:
        await message.answer("Сначала нужно познакомиться! Нажми /start")
        return

    await state.clear()
    await message.answer("Давай поставим новую цель! Как она звучит? (Заголовок)")
    await state.set_state(GoalSettingStates.waiting_for_title)


@router.message(F.text == "✅ Чек-ин")
async def handle_checkin_button(message: types.Message, state: FSMContext):
    """Обработка кнопки Чек-ин."""
    from src.bot.handlers.checkin import cmd_checkin

    await cmd_checkin(message, state)


@router.message(F.text == "🧘 Рефлексия")
async def handle_reflect_button(message: types.Message, state: FSMContext):
    """Обработка кнопки Рефлексия."""
    from src.bot.handlers.reflect import cmd_reflect

    await cmd_reflect(message, state)


@router.message(F.text == "🆘 Кризис")
async def handle_crisis_button(message: types.Message, state: FSMContext):
    """Обработка кнопки Кризис."""
    from src.bot.handlers.crisis import cmd_crisis

    await cmd_crisis(message, state)


# ============== Обработка inline-кнопок меню ==============

# AICODE-NOTE: callback.message.from_user — это бот, не пользователь!
# Используем callback.from_user.id для получения реального user_id.


@router.callback_query(MenuCallback.filter(F.action == "new_goal"))
async def handle_menu_new_goal(callback: types.CallbackQuery, state: FSMContext):
    """Переход к созданию новой цели."""
    user = await User.get_or_none(telegram_id=callback.from_user.id)
    if not user:
        await callback.answer(
            "Сначала нужно познакомиться! Нажми /start", show_alert=True
        )
        return

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer()

    # Очищаем состояние и запускаем флоу новой цели
    await state.clear()
    await callback.message.answer(
        "Давай поставим новую цель! Как она звучит? (Заголовок)"
    )
    await state.set_state(GoalSettingStates.waiting_for_title)


@router.callback_query(MenuCallback.filter(F.action == "checkin"))
async def handle_menu_checkin(callback: types.CallbackQuery, state: FSMContext):
    """Переход к чек-ину."""
    user = await User.get_or_none(telegram_id=callback.from_user.id)
    if not user:
        await callback.answer(
            "Сначала нужно познакомиться! Нажми /start", show_alert=True
        )
        return

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer()

    # Получаем цели пользователя
    goals = await Goal.filter(user=user, status="active").all()

    if not goals:
        await callback.message.answer(
            "У тебя пока нет активных целей. Создай новую через /new_goal или кнопку 🎯"
        )
        return

    builder = InlineKeyboardBuilder()
    for goal in goals:
        builder.button(text=goal.title, callback_data=CheckinCallback(goal_id=goal.id))
    builder.adjust(1)

    await callback.message.answer(
        "Выбери цель для отчета:", reply_markup=builder.as_markup()
    )
    await state.set_state(CheckInStates.waiting_for_goal_selection)


@router.callback_query(MenuCallback.filter(F.action == "reflect"))
async def handle_menu_reflect(callback: types.CallbackQuery, state: FSMContext):
    """Переход к рефлексии."""
    user = await User.get_or_none(telegram_id=callback.from_user.id)
    if not user:
        await callback.answer(
            "Сначала нужно познакомиться! Нажми /start", show_alert=True
        )
        return

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer()  # Исправлено: добавлен answer()

    # Очищаем состояние и начинаем рефлексию
    await state.clear()
    await state.update_data(reflect_answers={})

    from src.bot.handlers.reflect import QUESTIONS, get_skip_keyboard

    await callback.message.answer(
        "🧘 *Сессия рефлексии*\n\n"
        "Сейчас я задам тебе несколько вопросов, чтобы лучше понять, "
        "как ты себя чувствуешь и что тебе нужно.\n\n"
        "Отвечай честно — это только для тебя.\n\n"
        "_Можешь пропустить любой вопрос, если не хочешь отвечать._",
        parse_mode="Markdown",
    )

    await callback.message.answer(
        QUESTIONS["q1_feeling"], reply_markup=get_skip_keyboard()
    )
    await state.set_state(ReflectStates.q1_feeling)


@router.callback_query(MenuCallback.filter(F.action == "crisis"))
async def handle_menu_crisis(callback: types.CallbackQuery, state: FSMContext):
    """Переход в режим кризиса."""
    from datetime import datetime
    from src.bot.handlers.crisis import get_crisis_menu_keyboard, send_gif_if_available

    user = await User.get_or_none(telegram_id=callback.from_user.id)
    if not user:
        await callback.answer(
            "Сначала нужно познакомиться! Нажми /start", show_alert=True
        )
        return

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer()

    # Переключаем режим пользователя
    user.current_mode = "crisis"
    user.mode_updated_at = datetime.now()
    await user.save()

    # Отправляем GIF поддержки (если есть)
    await send_gif_if_available(callback.message, "support")

    await callback.message.answer(
        "Я рядом. Ничего не нужно делать прямо сейчас.\n\n" "Как ты хочешь?",
        reply_markup=get_crisis_menu_keyboard(),
    )

    await state.set_state(CrisisStates.waiting_for_feeling)


@router.callback_query(MenuCallback.filter(F.action == "back"))
async def handle_back_to_menu(callback: types.CallbackQuery, state: FSMContext):
    """Возврат в главное меню."""
    # AICODE-NOTE: Используем callback.from_user.id, не callback.message.from_user.id
    user = await User.get_or_none(telegram_id=callback.from_user.id)

    if not user:
        await callback.answer(
            "Сначала нужно познакомиться! Нажми /start", show_alert=True
        )
        return

    # Clear state
    await state.clear()

    # Check if user has active goals
    has_goals = await Goal.filter(user=user, status="active").exists()

    display_name = user.first_name or callback.from_user.first_name or "друг"

    try:
        await callback.message.edit_text(
            f"📋 *Главное меню*\n\n" f"Привет, {display_name}! Выбери действие:",
            parse_mode="Markdown",
            reply_markup=get_main_menu_keyboard(has_goals),
        )
    except Exception:
        await callback.message.answer(
            f"📋 *Главное меню*\n\n" f"Привет, {display_name}! Выбери действие:",
            parse_mode="Markdown",
            reply_markup=get_main_menu_keyboard(has_goals),
        )

    await callback.answer()
