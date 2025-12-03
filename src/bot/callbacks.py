"""
Типизированные CallbackData для aiogram 3.x.

Преимущества:
- Типобезопасность (IDE подсказки, автодополнение)
- Автоматическая валидация данных
- Удобная фильтрация по полям
- Нет ручного парсинга строк

AICODE-NOTE: Все callback_data должны быть короче 64 байт (ограничение Telegram).
Используем короткие префиксы.
"""

from aiogram.filters.callback_data import CallbackData


class MenuCallback(CallbackData, prefix="m"):
    """
    Callback для действий в главном меню.
    
    Действия:
    - new_goal: создание новой цели
    - checkin: переход к чек-ину
    - reflect: сессия рефлексии
    - crisis: режим кризиса
    - back: возврат в меню
    """
    action: str


class CheckinCallback(CallbackData, prefix="ci"):
    """
    Callback для выбора цели при чек-ине.
    
    Пример: ci:123 (выбор цели с id=123)
    """
    goal_id: int


class CrisisCallback(CallbackData, prefix="cr"):
    """
    Callback для режима кризиса.
    
    Действия:
    - breathe: выбор дыхания
    - talk: написать
    - just_be: просто побыть
    - b478: техника 4-7-8
    - bbox: box breathing
    - brep: повторить дыхание
    - bdone: дыхание завершено
    - micro: микро-действие
    - mtry: попробовать
    - mskip: пропустить
    - exit_y: подтвердить выход
    - exit_n: отменить выход
    """
    action: str


class ReflectCallback(CallbackData, prefix="rf"):
    """
    Callback для сессии рефлексии.
    
    Действия:
    - skip: пропустить вопрос
    - cancel: отменить сессию
    - breathe: показать выбор дыхания
    - b478: техника 4-7-8
    - bbox: box breathing
    - save: записать шаг
    - done: завершить
    """
    action: str

