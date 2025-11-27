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
