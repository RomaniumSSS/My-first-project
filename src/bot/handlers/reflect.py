"""
Handler для глубокого поддерживающего диалога /reflect.

Философия режима:
- Серия осознанных вопросов (7 шт в MVP)
- Накопление ответов → LLM анализ
- Персонализированные рекомендации
- Интеграция с практиками (дыхание)

AICODE-NOTE: Режим /reflect — stateless в MVP (не сохраняем сессии в БД).
В будущем можно добавить ReflectSession для истории.
"""

import logging
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.bot.states import ReflectStates, CrisisStates
from src.database.models import User
from src.services.ai import ai_service
from src.data.mantras import get_random_mantra

router = Router()
logger = logging.getLogger(__name__)


# ============== Вопросы ==============

QUESTIONS = {
    "q1_feeling": "💭 Как ты сейчас себя чувствуешь?\n\nОпиши одним-двумя словами или фразой.",
    "q2_scale": "📊 Оцени своё состояние от 1 до 10.\n\n(1 — совсем плохо, 10 — отлично)",
    "q3_change": "🔄 Что бы тебе хотелось изменить прямо сейчас?",
    "q4_obstacle": "🧱 Что сейчас мешает тебе двигаться вперёд?",
    "q5_last_success": "✨ Когда последний раз ты чувствовал, что у тебя получается?",
    "q6_what_helped": "🔑 Что тебе помогло тогда?",
    "q7_one_step": "👣 Какой один маленький шаг ты можешь сделать сегодня?",
}

# Порядок состояний
STATE_ORDER = [
    ReflectStates.q1_feeling,
    ReflectStates.q2_scale,
    ReflectStates.q3_change,
    ReflectStates.q4_obstacle,
    ReflectStates.q5_last_success,
    ReflectStates.q6_what_helped,
    ReflectStates.q7_one_step,
]

STATE_KEYS = [
    "q1_feeling",
    "q2_scale",
    "q3_change",
    "q4_obstacle",
    "q5_last_success",
    "q6_what_helped",
    "q7_one_step",
]


# ============== Клавиатуры ==============


def get_skip_keyboard():
    """Кнопка пропуска вопроса."""
    builder = InlineKeyboardBuilder()
    builder.button(text="⏭ Пропустить", callback_data="reflect_skip")
    return builder.as_markup()


def get_cancel_keyboard():
    """Кнопка отмены сессии."""
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Прервать", callback_data="reflect_cancel")
    return builder.as_markup()


def get_post_reflect_keyboard():
    """Кнопки после рекомендаций."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🌬 Подышать", callback_data="reflect_breathe")
    builder.button(text="🎯 Записать шаг", callback_data="reflect_save_step")
    builder.button(text="✅ Готово", callback_data="reflect_done")
    builder.adjust(3)
    return builder.as_markup()


def get_back_to_menu_keyboard():
    """Кнопка возврата в меню."""
    builder = InlineKeyboardBuilder()
    builder.button(text="📋 Меню", callback_data="back_to_menu")
    return builder.as_markup()


def get_breathing_choice_keyboard():
    """Выбор дыхательной техники (реюз из crisis)."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🌬 4-7-8 (глубокое)", callback_data="reflect_breathe_478")
    builder.button(text="⬜ Box 4-4-4-4 (простое)", callback_data="reflect_breathe_box")
    builder.adjust(1)
    return builder.as_markup()


# ============== LLM Промпт ==============


REFLECT_SYSTEM_PROMPT = """Ты — эмпатичный коуч и психолог. Пользователь только что прошёл сессию саморефлексии и ответил на вопросы о своём состоянии.

Твоя задача:
1. Проанализировать ответы и понять эмоциональное состояние человека
2. Выявить ключевой паттерн или блок, который мешает двигаться
3. Дать 2-3 персонализированные рекомендации

Правила:
- Используй тёплый, поддерживающий тон
- Не читай мораль, не давай банальных советов
- Опирайся на конкретные слова пользователя
- Рекомендации должны быть практичными и выполнимыми сегодня
- Длина ответа: 3-5 абзацев максимум
- Используй эмодзи умеренно

Формат ответа:
[Краткий анализ состояния — 1-2 предложения]

[Что я заметил/паттерн — 1-2 предложения]

Мои рекомендации:
1. [Конкретное действие]
2. [Конкретное действие]
3. [Опционально: третья рекомендация]

[Тёплое завершение — 1 предложение]"""


def format_user_answers(answers: dict) -> str:
    """Форматирует ответы пользователя для LLM."""
    lines = []
    question_labels = {
        "q1_feeling": "Как себя чувствует",
        "q2_scale": "Оценка состояния (1-10)",
        "q3_change": "Что хочет изменить",
        "q4_obstacle": "Что мешает двигаться",
        "q5_last_success": "Когда последний раз получалось",
        "q6_what_helped": "Что помогло тогда",
        "q7_one_step": "Маленький шаг на сегодня",
    }
    
    for key, label in question_labels.items():
        value = answers.get(key, "(пропущено)")
        lines.append(f"- {label}: {value}")
    
    return "\n".join(lines)


# ============== Команда /reflect ==============


@router.message(Command("reflect"))
async def cmd_reflect(message: types.Message, state: FSMContext):
    """Запуск сессии рефлексии."""
    user = await User.get_or_none(telegram_id=message.from_user.id)
    
    if not user:
        await message.answer("Сначала нужно познакомиться! Нажми /start")
        return
    
    # Очищаем предыдущее состояние и начинаем
    await state.clear()
    await state.update_data(reflect_answers={})
    
    await message.answer(
        "🧘 *Сессия рефлексии*\n\n"
        "Сейчас я задам тебе несколько вопросов, чтобы лучше понять, "
        "как ты себя чувствуешь и что тебе нужно.\n\n"
        "Отвечай честно — это только для тебя.\n\n"
        "_Можешь пропустить любой вопрос, если не хочешь отвечать._",
        parse_mode="Markdown"
    )
    
    # Первый вопрос
    await message.answer(
        QUESTIONS["q1_feeling"],
        reply_markup=get_skip_keyboard()
    )
    await state.set_state(ReflectStates.q1_feeling)


# ============== Обработка ответов ==============


async def process_answer_and_next(
    message_or_callback: types.Message | types.CallbackQuery,
    state: FSMContext,
    current_key: str,
    answer: str | None
):
    """
    Сохраняет ответ и переходит к следующему вопросу.
    Если это последний вопрос — запускает LLM анализ.
    """
    # Определяем message для отправки
    if isinstance(message_or_callback, types.CallbackQuery):
        message = message_or_callback.message
    else:
        message = message_or_callback
    
    # Сохраняем ответ
    data = await state.get_data()
    answers = data.get("reflect_answers", {})
    if answer:
        answers[current_key] = answer
    else:
        answers[current_key] = "(пропущено)"
    await state.update_data(reflect_answers=answers)
    
    # Находим индекс текущего вопроса
    current_idx = STATE_KEYS.index(current_key)
    
    # Если это последний вопрос — анализ
    if current_idx >= len(STATE_KEYS) - 1:
        await state.set_state(ReflectStates.processing)
        await run_llm_analysis(message, state)
        return
    
    # Следующий вопрос
    next_key = STATE_KEYS[current_idx + 1]
    next_state = STATE_ORDER[current_idx + 1]
    
    await message.answer(
        QUESTIONS[next_key],
        reply_markup=get_skip_keyboard()
    )
    await state.set_state(next_state)


# Обработчики для каждого состояния

@router.message(ReflectStates.q1_feeling)
async def handle_q1(message: types.Message, state: FSMContext):
    await process_answer_and_next(message, state, "q1_feeling", message.text)


@router.message(ReflectStates.q2_scale)
async def handle_q2(message: types.Message, state: FSMContext):
    await process_answer_and_next(message, state, "q2_scale", message.text)


@router.message(ReflectStates.q3_change)
async def handle_q3(message: types.Message, state: FSMContext):
    await process_answer_and_next(message, state, "q3_change", message.text)


@router.message(ReflectStates.q4_obstacle)
async def handle_q4(message: types.Message, state: FSMContext):
    await process_answer_and_next(message, state, "q4_obstacle", message.text)


@router.message(ReflectStates.q5_last_success)
async def handle_q5(message: types.Message, state: FSMContext):
    await process_answer_and_next(message, state, "q5_last_success", message.text)


@router.message(ReflectStates.q6_what_helped)
async def handle_q6(message: types.Message, state: FSMContext):
    await process_answer_and_next(message, state, "q6_what_helped", message.text)


@router.message(ReflectStates.q7_one_step)
async def handle_q7(message: types.Message, state: FSMContext):
    await process_answer_and_next(message, state, "q7_one_step", message.text)


# ============== Пропуск вопроса ==============


@router.callback_query(F.data == "reflect_skip")
async def handle_skip(callback: types.CallbackQuery, state: FSMContext):
    """Пропуск текущего вопроса."""
    current_state = await state.get_state()
    
    # Находим текущий ключ по состоянию
    state_to_key = {
        ReflectStates.q1_feeling.state: "q1_feeling",
        ReflectStates.q2_scale.state: "q2_scale",
        ReflectStates.q3_change.state: "q3_change",
        ReflectStates.q4_obstacle.state: "q4_obstacle",
        ReflectStates.q5_last_success.state: "q5_last_success",
        ReflectStates.q6_what_helped.state: "q6_what_helped",
        ReflectStates.q7_one_step.state: "q7_one_step",
    }
    
    current_key = state_to_key.get(current_state)
    if not current_key:
        await callback.answer("Ошибка состояния", show_alert=True)
        return
    
    await callback.answer("Пропущено ⏭")
    
    # Убираем кнопку
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    
    await process_answer_and_next(callback, state, current_key, None)


# ============== Отмена сессии ==============


@router.callback_query(F.data == "reflect_cancel")
async def handle_cancel(callback: types.CallbackQuery, state: FSMContext):
    """Отмена сессии рефлексии."""
    await state.clear()
    await callback.message.edit_text(
        "❌ Сессия прервана.\n\n"
        "Когда будешь готов — напиши /reflect снова.",
        reply_markup=None
    )
    await callback.answer()


# ============== LLM Анализ ==============


async def run_llm_analysis(message: types.Message, state: FSMContext):
    """Отправляет ответы в LLM и получает рекомендации."""
    data = await state.get_data()
    answers = data.get("reflect_answers", {})
    
    # Показываем typing и мантру
    mantra = get_random_mantra("reflect")
    processing_msg = await message.answer(
        f"🧠 Анализирую твои ответы...\n\n"
        f"_{mantra}_",
        parse_mode="Markdown"
    )
    
    # Формируем промпт
    user_content = f"Ответы пользователя на вопросы рефлексии:\n\n{format_user_answers(answers)}"
    
    messages = [
        {"role": "system", "content": REFLECT_SYSTEM_PROMPT},
        {"role": "user", "content": user_content}
    ]
    
    try:
        response = await ai_service.get_chat_response(messages, temperature=0.7, max_tokens=800)
        
        # Удаляем сообщение "анализирую"
        try:
            await processing_msg.delete()
        except Exception:
            pass
        
        # Отправляем результат
        await message.answer(
            f"🧘 *Результаты рефлексии*\n\n{response}",
            parse_mode="Markdown",
            reply_markup=get_post_reflect_keyboard()
        )
        
        await state.set_state(ReflectStates.post_reflect)
        
    except Exception as e:
        logger.error(f"LLM analysis failed: {e}")
        
        try:
            await processing_msg.delete()
        except Exception:
            pass
        
        await message.answer(
            "😔 Не получилось проанализировать сейчас.\n\n"
            "Но само то, что ты ответил на эти вопросы — уже шаг.\n\n"
            "Хочешь подышать или записать свой шаг?",
            reply_markup=get_post_reflect_keyboard()
        )
        await state.set_state(ReflectStates.post_reflect)


# ============== Post-reflect действия ==============


@router.callback_query(ReflectStates.post_reflect, F.data == "reflect_breathe")
async def handle_breathe_choice(callback: types.CallbackQuery, state: FSMContext):
    """Пользователь хочет подышать — показываем выбор техники."""
    await callback.message.edit_text(
        "🌬 Выбери технику дыхания:",
        reply_markup=get_breathing_choice_keyboard()
    )
    await callback.answer()


@router.callback_query(ReflectStates.post_reflect, F.data == "reflect_breathe_478")
async def start_breathing_478(callback: types.CallbackQuery, state: FSMContext):
    """Запуск техники 4-7-8."""
    await callback.message.edit_text("🌬 Давай подышим вместе.\n\nТехника 4-7-8:")
    await callback.answer()
    await run_breathing_478(callback.message, state)


@router.callback_query(ReflectStates.post_reflect, F.data == "reflect_breathe_box")
async def start_breathing_box(callback: types.CallbackQuery, state: FSMContext):
    """Запуск Box Breathing 4-4-4-4."""
    await callback.message.edit_text("⬜ Давай подышим вместе.\n\nBox Breathing 4-4-4-4:")
    await callback.answer()
    await run_breathing_box(callback.message, state)


import asyncio


async def run_breathing_478(message: types.Message, state: FSMContext):
    """
    Выполнение дыхательной техники 4-7-8.
    AICODE-NOTE: Реюз логики из crisis.py, но без привязки к crisis mode.
    """
    await asyncio.sleep(1)
    
    # Вдох
    inhale_msg = await message.answer("🌬 Вдох... (4 секунды)")
    await asyncio.sleep(4)
    
    # Задержка
    await inhale_msg.edit_text("⏸ Задержи... (7 секунд)")
    await asyncio.sleep(7)
    
    # Выдох
    await inhale_msg.edit_text("💨 Выдох... (8 секунд)")
    await asyncio.sleep(8)
    
    mantra = get_random_mantra("breathing")
    await message.answer(
        f"✨ Отлично.\n\n_{mantra}_",
        parse_mode="Markdown",
        reply_markup=get_post_reflect_keyboard()
    )


async def run_breathing_box(message: types.Message, state: FSMContext):
    """
    Выполнение Box Breathing 4-4-4-4.
    """
    await asyncio.sleep(1)
    
    # Вдох
    inhale_msg = await message.answer("🌬 Вдох... (4 секунды)")
    await asyncio.sleep(4)
    
    # Задержка 1
    await inhale_msg.edit_text("⏸ Задержи... (4 секунды)")
    await asyncio.sleep(4)
    
    # Выдох
    await inhale_msg.edit_text("💨 Выдох... (4 секунды)")
    await asyncio.sleep(4)
    
    # Задержка 2
    await inhale_msg.edit_text("⏸ Задержи... (4 секунды)")
    await asyncio.sleep(4)
    
    mantra = get_random_mantra("breathing")
    await message.answer(
        f"✨ Отлично.\n\n_{mantra}_",
        parse_mode="Markdown",
        reply_markup=get_post_reflect_keyboard()
    )


@router.callback_query(ReflectStates.post_reflect, F.data == "reflect_save_step")
async def handle_save_step(callback: types.CallbackQuery, state: FSMContext):
    """
    Записать шаг как микро-цель.
    AICODE-TODO: В будущем интегрировать с Goal моделью.
    Пока просто показываем что шаг записан.
    """
    data = await state.get_data()
    answers = data.get("reflect_answers", {})
    step = answers.get("q7_one_step", "")
    
    if step and step != "(пропущено)":
        await callback.message.edit_text(
            f"🎯 *Твой шаг на сегодня:*\n\n"
            f"_{step}_\n\n"
            "Я верю в тебя! 💪",
            parse_mode="Markdown",
            reply_markup=get_back_to_menu_keyboard()
        )
    else:
        await callback.message.edit_text(
            "🎯 Напиши свой шаг — что ты сделаешь сегодня?",
            reply_markup=get_back_to_menu_keyboard()
        )
    
    await state.clear()
    await callback.answer()


@router.callback_query(ReflectStates.post_reflect, F.data == "reflect_done")
async def handle_done(callback: types.CallbackQuery, state: FSMContext):
    """Завершение сессии."""
    mantra = get_random_mantra("exit")
    await callback.message.edit_text(
        f"✅ Сессия завершена.\n\n"
        f"_{mantra}_\n\n"
        "Возвращайся когда захочешь!",
        parse_mode="Markdown",
        reply_markup=get_back_to_menu_keyboard()
    )
    await state.clear()
    await callback.answer()

