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


class ReflectStates(StatesGroup):
    """
    FSM состояния для глубокого поддерживающего диалога /reflect.
    MVP: 7 вопросов → LLM анализ → рекомендации.
    """
    q1_feeling = State()       # Как ты себя чувствуешь?
    q2_scale = State()         # Оценка 1-10
    q3_change = State()        # Что хочешь изменить?
    q4_obstacle = State()      # Что мешает?
    q5_last_success = State()  # Когда последний раз получалось?
    q6_what_helped = State()   # Что помогло тогда?
    q7_one_step = State()      # Какой маленький шаг можешь сделать?
    processing = State()       # LLM обработка
    post_reflect = State()     # После рекомендаций (дыхание/цель)
