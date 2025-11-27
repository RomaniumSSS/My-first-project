from aiogram import Router, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from src.database.models import User
from src.bot.states import OnboardingStates

router = Router()

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
        # Create new user
        user = await User.create(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name
        )
        await message.answer(
            f"Привет, {first_name}! Я твой AI-коуч.\n"
            "Давай познакомимся. Как мне тебя называть?"
        )
        await state.set_state(OnboardingStates.waiting_for_name)
    else:
        await message.answer(
            f"С возвращением, {user.first_name}!\n"
            "Используй /new_goal чтобы поставить новую цель, или /checkin для отчета."
        )

