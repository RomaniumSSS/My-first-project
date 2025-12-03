import logging
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.bot.states import CheckInStates
from src.database.models import Goal, CheckIn, User
from src.services.ai import ai_service
from src.services.vision import (
    download_telegram_photo,
    encode_image_to_base64,
    prepare_vision_payload,
)

router = Router()
logger = logging.getLogger(__name__)


def get_back_to_menu_keyboard():
    """Кнопка возврата в меню."""
    builder = InlineKeyboardBuilder()
    builder.button(text="📋 Меню", callback_data="back_to_menu")
    return builder.as_markup()


@router.message(Command("checkin"))
async def cmd_checkin(message: types.Message, state: FSMContext):
    """Start check-in process by listing active goals."""
    user_id = message.from_user.id

    # Fetch active goals for the user
    # We need to join with User to filter by telegram_id
    # Assuming User exists since they are using the bot (onboarding should ensure this)
    user = await User.get_or_none(telegram_id=user_id)
    if not user:
        await message.answer("Сначала нужно познакомиться! Нажми /start")
        return

    goals = await Goal.filter(user=user, status="active").all()

    if not goals:
        await message.answer(
            "У тебя пока нет активных целей. Создай новую через /new_goal"
        )
        return

    builder = InlineKeyboardBuilder()
    for goal in goals:
        # callback_data limit is 64 bytes. goal_id is int, should be fine.
        builder.button(text=goal.title, callback_data=f"checkin_goal_{goal.id}")

    builder.adjust(1)

    await message.answer("Выбери цель для отчета:", reply_markup=builder.as_markup())
    await state.set_state(CheckInStates.waiting_for_goal_selection)


@router.callback_query(
    CheckInStates.waiting_for_goal_selection, F.data.startswith("checkin_goal_")
)
async def process_goal_selection(callback: types.CallbackQuery, state: FSMContext):
    """Handle goal selection."""
    try:
        goal_id = int(callback.data.split("_")[-1])
    except ValueError:
        await callback.message.answer("Некорректный ID цели.")
        await state.clear()
        return

    # AICODE-NOTE: Prevent IDOR by filtering by user__telegram_id
    # Verify goal exists and belongs to user (security check)
    goal = await Goal.get_or_none(id=goal_id, user__telegram_id=callback.from_user.id)

    if not goal:
        await callback.message.answer("Цель не найдена или у вас нет прав.")
        await state.clear()
        await callback.answer()
        return

    await state.update_data(goal_id=goal_id)

    # Try to edit the message, but if it's too old or deleted, send a new one
    try:
        await callback.message.edit_text(
            f"Отлично! Как успехи с целью **{goal.title}**?\n\n"
            "Напиши отчет текстом или пришли фото (можно с подписью).",
            reply_markup=None,
        )
    except Exception:
        await callback.message.answer(
            f"Отлично! Как успехи с целью **{goal.title}**?\n\n"
            "Напиши отчет текстом или пришли фото (можно с подписью)."
        )
        # Try to remove buttons from the old message if possible
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass

    await state.set_state(CheckInStates.waiting_for_report)
    await callback.answer()


@router.message(CheckInStates.waiting_for_report)
async def process_report(message: types.Message, state: FSMContext):
    """Handle the report (text or photo)."""
    data = await state.get_data()
    goal_id = data.get("goal_id")

    # Validate goal_id exists
    if not goal_id:
        await message.answer("Что-то пошло не так. Начни чек-ин заново через /checkin")
        await state.clear()
        return

    goal = await Goal.get_or_none(id=goal_id, user__telegram_id=message.from_user.id)
    if not goal:
        await message.answer(
            "Цель не найдена или у вас нет прав. "
            "Попробуй выбрать заново через /checkin"
        )
        await state.clear()
        return

    report_text = ""
    image_base64 = None

    # Handle Photo
    if message.photo:
        # Get the largest photo
        photo = message.photo[-1]
        try:
            image_data = await download_telegram_photo(message.bot, photo.file_id)
            image_base64 = encode_image_to_base64(image_data)
            report_text = message.caption or "[Фото отчет]"
        except Exception as e:
            logger.error(f"Failed to download photo: {e}")
            await message.answer(
                "Не удалось загрузить фото. Пожалуйста, отправь отчет текстом."
            )
            return

    # Handle Text
    elif message.text:
        report_text = message.text
    else:
        await message.answer("Пожалуйста, пришли текст или фото.")
        return

    wait_msg = await message.answer("Анализирую твой отчет... 🧠")

    # AI Analysis
    try:
        # Prepare prompt
        system_prompt = (
            "Ты - опытный коуч по достижению целей. Твоя задача - поддержать "
            "пользователя и дать конструктивный совет на основе его отчета."
        )

        user_content = (
            f"Цель: {goal.title}\n"
            f"Описание цели: {goal.description}\n\n"
            f"Отчет пользователя: {report_text}"
        )

        messages = [{"role": "system", "content": system_prompt}]

        if image_base64:
            # Use vision payload
            vision_messages = prepare_vision_payload(user_content, [image_base64])
            # Need to merge properly. prepare_vision_payload returns a list
            messages.extend(vision_messages)
        else:
            messages.append({"role": "user", "content": user_content})

        # Add instruction for output format
        messages.append(
            {
                "role": "user",
                "content": (
                    "Проанализируй прогресс. Дай краткую обратную связь: "
                    "1. Похвали за сделанное.\n"
                    "2. Дай 1 конкретный совет, что можно улучшить или сделать "
                    "следующим шагом.\n"
                    "Ответ должен быть мотивирующим, но кратким (до 100 слов)."
                ),
            }
        )

        ai_feedback = await ai_service.get_chat_response(messages)

    except Exception as e:
        logger.error(f"Error in AI analysis: {e}")
        ai_feedback = (
            "Отличная работа! Продолжай в том же духе. "
            "(AI временно недоступен для детального анализа)"
        )

    # Save to DB
    await CheckIn.create(
        goal=goal,
        report_text=report_text,
        image_base64=image_base64,
        ai_feedback=ai_feedback,
    )

    try:
        await wait_msg.delete()
    except Exception:
        pass  # Ignore deletion errors to ensure state is cleared

    await message.answer(
        f"✅ Записано!\n\n{ai_feedback}",
        reply_markup=get_back_to_menu_keyboard()
    )

    await state.clear()
