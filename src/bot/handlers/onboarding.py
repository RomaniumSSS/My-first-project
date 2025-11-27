from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from src.database.models import User, Goal
from src.bot.states import OnboardingStates

router = Router()


@router.message(StateFilter(OnboardingStates.waiting_for_name), F.text)
async def process_name(message: types.Message, state: FSMContext):
    """
    Process user name input during onboarding.
    """
    name = message.text.strip()
    telegram_id = message.from_user.id

    # Update user's name
    user = await User.get_or_none(telegram_id=telegram_id)
    if not user:
        # Should not happen if flow is correct, but safety first
        user = await User.create(
            telegram_id=telegram_id,
            username=message.from_user.username,
            first_name=name,
        )
    else:
        user.first_name = name
        await user.save()

    await message.answer(
        f"Приятно познакомиться, {name}!\n\n"
        "Какая у тебя сейчас главная цель? "
        "(Напиши кратко, например: 'Выучить английский' или 'Похудеть на 5 кг')"
    )
    await state.set_state(OnboardingStates.waiting_for_main_goal)


@router.message(StateFilter(OnboardingStates.waiting_for_main_goal), F.text)
async def process_main_goal(message: types.Message, state: FSMContext):
    """
    Process main goal input during onboarding.
    """
    goal_title = message.text.strip()
    telegram_id = message.from_user.id

    user = await User.get_or_none(telegram_id=telegram_id)
    if not user:
        await message.answer("Произошла ошибка: пользователь не найден. Нажми /start")
        await state.clear()
        return

    # Create the first goal
    await Goal.create(
        user=user,
        title=goal_title,
        description=f"Главная цель: {goal_title}",
        status="active",
    )

    await message.answer(
        "Отличная цель! Я сохранил её.\n\n"
        "Теперь ты можешь:\n"
        "1. Добавить детали к цели через /new_goal\n"
        "2. Сделать чек-ин через /checkin"
    )
    await state.clear()
