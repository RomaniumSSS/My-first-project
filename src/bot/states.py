from aiogram.fsm.state import State, StatesGroup


class OnboardingStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_main_goal = State()


class GoalSettingStates(StatesGroup):
    waiting_for_title = State()
    waiting_for_description = State()
    waiting_for_photo = State()


class CheckInStates(StatesGroup):
    waiting_for_goal_selection = State()
    waiting_for_report = State()


class CrisisStates(StatesGroup):
    """FSM состояния для режима кризиса."""
    waiting_for_feeling = State()   # Ожидание ответа "как ты?"
    breathing = State()              # Режим дыхательной паузы
    micro_action = State()           # Предложение микро-действия
    just_being = State()             # Просто рядом, без действий
    waiting_for_micro_report = State()  # Ожидание отчёта о микро-действии
