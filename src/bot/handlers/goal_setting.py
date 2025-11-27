import logging
from aiogram import Router, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext

from src.database.models import User, Goal
from src.bot.states import GoalSettingStates
from src.services.ai import ai_service
from src.services.vision import (
    download_telegram_photo,
    encode_image_to_base64,
    prepare_vision_payload,
)

router = Router()
logger = logging.getLogger(__name__)


@router.message(Command("new_goal"))
async def cmd_new_goal(message: types.Message, state: FSMContext):
    """Start the goal setting flow."""
    # Clear any existing state to start fresh
    await state.clear()
    await message.answer("Давай поставим новую цель! Как она звучит? (Заголовок)")
    await state.set_state(GoalSettingStates.waiting_for_title)


@router.message(StateFilter(GoalSettingStates.waiting_for_title), F.text)
async def process_title(message: types.Message, state: FSMContext):
    """Save title and ask for description."""
    await state.update_data(title=message.text.strip())
    await message.answer(
        "Хорошо. Теперь опиши подробнее: почему это важно? "
        "Как ты поймешь, что цель достигнута?"
    )
    await state.set_state(GoalSettingStates.waiting_for_description)


@router.message(StateFilter(GoalSettingStates.waiting_for_description), F.text)
async def process_description(message: types.Message, state: FSMContext):
    """Save description and ask for photo."""
    await state.update_data(description=message.text.strip())
    await message.answer(
        "Есть ли картинка, которая тебя вдохновляет на эту цель? (Мудборд)\n"
        "Пришли фото или нажми /skip, если нет."
    )
    await state.set_state(GoalSettingStates.waiting_for_photo)


@router.message(StateFilter(GoalSettingStates.waiting_for_photo), Command("skip"))
async def process_photo_skip(message: types.Message, state: FSMContext):
    """Handle skip photo."""
    await finalize_goal(message, state, photo_base64=None)


@router.message(StateFilter(GoalSettingStates.waiting_for_photo), F.photo)
async def process_photo(message: types.Message, state: FSMContext):
    """Handle photo upload."""
    # Get the largest photo
    photo = message.photo[-1]

    try:
        # Download and convert
        image_data = await download_telegram_photo(message.bot, photo.file_id)
        base64_img = encode_image_to_base64(image_data)

        await finalize_goal(message, state, photo_base64=base64_img)
    except Exception as e:
        logger.error(f"Error processing photo: {e}")
        await message.answer(f"Ошибка при обработке фото: {e}. Попробуем без него.")
        await finalize_goal(message, state, photo_base64=None)


async def finalize_goal(
    message: types.Message, state: FSMContext, photo_base64: str | None
):
    """
    Finalize goal creation: save to DB and get AI feedback.
    """
    data = await state.get_data()
    title = data.get("title")
    description = data.get("description")
    telegram_id = message.from_user.id

    # Validate data integrity
    if not title:
        await message.answer(
            "Произошла ошибка: заголовок цели не найден. "
            "Попробуй создать цель заново через /new_goal"
        )
        await state.clear()
        return

    # Safely get user
    user = await User.get_or_none(telegram_id=telegram_id)
    if not user:
        await message.answer("Пользователь не найден. Нажми /start")
        await state.clear()
        return

    # Notify user that we are thinking
    processing_msg = await message.answer(
        "Анализирую твою цель и готовлю план действий..."
    )

    # Prepare AI Prompt
    system_prompt = (
        "Ты — опытный и эмпатичный коуч. Твоя задача — вдохновить пользователя "
        "и дать 3 первых шага к цели."
    )
    user_text = (
        f"Моя цель: {title}\n"
        f"Описание: {description or 'Без описания'}\n\n"
        "Дай мне мотивирующий пинок и 3 простых шага для начала."
    )

    messages = [{"role": "system", "content": system_prompt}]

    if photo_base64:
        # Use Vision
        vision_payload = prepare_vision_payload(user_text, [photo_base64])
        messages.extend(vision_payload)
    else:
        messages.append({"role": "user", "content": user_text})

    # Save to DB
    await Goal.create(
        user=user,
        title=title,
        description=description,
        image_base64=photo_base64,
        status="active",
    )

    try:
        ai_response = await ai_service.get_chat_response(messages)
    except Exception as e:
        logger.error(f"Error getting AI response: {e}")
        ai_response = (
            "Цель сохранена! К сожалению, мой AI-модуль сейчас недоступен, "
            "но я верю в тебя! Начни с малого."
        )

    # Delete processing message and send result
    try:
        await processing_msg.delete()
    except Exception:
        pass  # Ignore deletion errors

    await message.answer(ai_response)
    await message.answer(f"Цель '{title}' успешно сохранена!")

    await state.clear()
