"""
Handler для режима кризиса.

Философия режима:
- Без давления — никаких "ты не выполнил план"
- Дыхание первично — сначала выдохнуть, потом думать
- Микро-действие — одно дело на 5-15 минут
- Признание состояния — "тебе тяжело, и это нормально"

AICODE-NOTE: Режим кризиса — не замена профессиональной помощи.
В будущем добавить ресурсы (горячие линии) для тяжёлых случаев.
"""

import asyncio
import logging
from datetime import datetime

from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.bot.states import CrisisStates
from src.bot.callbacks import CrisisCallback
from src.database.models import User, Goal
from src.data.mantras import get_random_mantra
from src.services.gif_service import gif_service

router = Router()
logger = logging.getLogger(__name__)


# ============== Вспомогательные функции ==============


async def send_gif_if_available(
    message: types.Message, category: str, caption: str = None
):
    """
    Отправляет GIF из категории, если он доступен.
    Если GIF нет — просто пропускает (graceful fallback).
    """
    file_id = gif_service.get_random(category)
    if file_id:
        try:
            await message.answer_animation(animation=file_id, caption=caption)
            return True
        except Exception as e:
            logger.warning(f"Failed to send GIF from {category}: {e}")
    return False


def get_crisis_menu_keyboard():
    """Клавиатура главного меню кризис-режима."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🌬 Подышать", callback_data=CrisisCallback(action="breathe"))
    builder.button(text="💬 Написать", callback_data=CrisisCallback(action="talk"))
    builder.button(
        text="🤫 Просто побыть", callback_data=CrisisCallback(action="just_be")
    )
    builder.adjust(3)
    return builder.as_markup()


def get_post_breathing_keyboard():
    """Клавиатура после дыхательной паузы — с опцией микро-действия."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🎯 Микро-действие", callback_data=CrisisCallback(action="micro")
    )
    builder.button(
        text="🤫 Просто побыть", callback_data=CrisisCallback(action="just_be")
    )
    builder.adjust(2)
    return builder.as_markup()


def get_breathing_choice_keyboard():
    """Выбор дыхательной техники."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🌬 4-7-8 (глубокое)", callback_data=CrisisCallback(action="b478")
    )
    builder.button(
        text="⬜ Box 4-4-4-4 (простое)", callback_data=CrisisCallback(action="bbox")
    )
    builder.adjust(1)
    return builder.as_markup()


def get_breathing_repeat_keyboard():
    """Кнопки после дыхательной паузы."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Повторить", callback_data=CrisisCallback(action="brep"))
    builder.button(text="✅ Достаточно", callback_data=CrisisCallback(action="bdone"))
    builder.adjust(2)
    return builder.as_markup()


def get_micro_action_keyboard():
    """Кнопки предложения микро-действия."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🎯 Хочу попробовать", callback_data=CrisisCallback(action="mtry")
    )
    builder.button(text="🛋 Не сейчас", callback_data=CrisisCallback(action="mskip"))
    builder.adjust(2)
    return builder.as_markup()


def get_exit_crisis_keyboard():
    """Кнопки для выхода из режима кризиса."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="✅ Да, переключить", callback_data=CrisisCallback(action="exit_y")
    )
    builder.button(
        text="🔴 Нет, пока в кризисе", callback_data=CrisisCallback(action="exit_n")
    )
    builder.adjust(2)
    return builder.as_markup()


# ============== Команда /crisis ==============


@router.message(Command("crisis"))
async def cmd_crisis(message: types.Message, state: FSMContext):
    """
    Вход в режим кризиса.
    Переключает пользователя в режим поддержки.
    """
    user = await User.get_or_none(telegram_id=message.from_user.id)

    if not user:
        await message.answer("Сначала нужно познакомиться! Нажми /start")
        return

    # Переключаем режим
    user.current_mode = "crisis"
    user.mode_updated_at = datetime.now()
    await user.save()

    # Отправляем GIF поддержки (если есть)
    await send_gif_if_available(message, "support")

    await message.answer(
        "Я рядом. Ничего не нужно делать прямо сейчас.\n\n" "Как ты хочешь?",
        reply_markup=get_crisis_menu_keyboard(),
    )

    await state.set_state(CrisisStates.waiting_for_feeling)


# ============== Главное меню кризиса ==============


async def _verify_crisis_mode(callback: types.CallbackQuery) -> bool:
    """Проверяет, что пользователь в режиме кризиса."""
    user = await User.get_or_none(telegram_id=callback.from_user.id)
    if not user or user.current_mode != "crisis":
        await callback.answer(
            "Режим кризиса не активен. Используй /crisis чтобы войти.", show_alert=True
        )
        return False
    return True


@router.callback_query(CrisisCallback.filter(F.action == "breathe"))
async def handle_breathe_choice(callback: types.CallbackQuery, state: FSMContext):
    """Пользователь хочет подышать — показываем выбор техники."""
    if not await _verify_crisis_mode(callback):
        return

    try:
        await callback.message.edit_text(
            "🌬 Выбери технику дыхания:", reply_markup=get_breathing_choice_keyboard()
        )
    except Exception:
        await callback.message.answer(
            "🌬 Выбери технику дыхания:", reply_markup=get_breathing_choice_keyboard()
        )
    await state.set_state(CrisisStates.breathing)
    await callback.answer()


@router.callback_query(CrisisCallback.filter(F.action == "talk"))
async def handle_talk(callback: types.CallbackQuery, state: FSMContext):
    """Пользователь хочет написать что чувствует."""
    if not await _verify_crisis_mode(callback):
        return

    try:
        await callback.message.edit_text(
            "💬 Напиши, что чувствуешь. Я просто послушаю.\n\n"
            "Не нужно объяснять или оправдываться. Просто выпусти это наружу.",
            reply_markup=None,
        )
    except Exception:
        await callback.message.answer(
            "💬 Напиши, что чувствуешь. Я просто послушаю.\n\n"
            "Не нужно объяснять или оправдываться. Просто выпусти это наружу."
        )
    await state.set_state(CrisisStates.waiting_for_feeling)
    await callback.answer()


@router.callback_query(CrisisCallback.filter(F.action == "just_be"))
async def handle_just_be(callback: types.CallbackQuery, state: FSMContext):
    """Пользователь хочет просто побыть."""
    if not await _verify_crisis_mode(callback):
        return

    # Отправляем GIF отдыха если есть
    await send_gif_if_available(callback.message, "rest")

    try:
        await callback.message.edit_text(
            "🤫 Я тут. Напиши, когда будешь готов.\n\n"
            f"_{get_random_mantra('crisis')}_",
            parse_mode="Markdown",
            reply_markup=None,
        )
    except Exception:
        await callback.message.answer(
            f"🤫 Я тут. Напиши, когда будешь готов.\n\n"
            f"_{get_random_mantra('crisis')}_",
            parse_mode="Markdown",
        )
    await state.set_state(CrisisStates.just_being)
    await callback.answer()


# ============== Обработка текста в режиме "просто побыть" или "написать" ==============


@router.message(CrisisStates.waiting_for_feeling)
async def handle_feeling_message(message: types.Message, state: FSMContext):
    """
    Пользователь написал что чувствует.
    Принимаем без анализа, просто поддерживаем.
    """
    mantra = get_random_mantra("crisis")

    await message.answer(
        f"Спасибо, что поделился. 💙\n\n"
        f"_{mantra}_\n\n"
        "Хочешь подышать или сделать что-то маленькое?",
        parse_mode="Markdown",
        reply_markup=get_crisis_menu_keyboard(),
    )


@router.message(CrisisStates.just_being)
async def handle_just_being_message(message: types.Message, state: FSMContext):
    """
    Пользователь написал, находясь в режиме "просто побыть".
    Мягко отвечаем и предлагаем варианты.
    """
    mantra = get_random_mantra("crisis")

    await message.answer(
        f"Я тут. 💙\n\n" f"_{mantra}_\n\n" "Готов к чему-то или ещё побудем?",
        parse_mode="Markdown",
        reply_markup=get_crisis_menu_keyboard(),
    )


# ============== Дыхательные техники ==============


@router.callback_query(
    CrisisStates.breathing, CrisisCallback.filter(F.action == "b478")
)
async def start_breathing_478(callback: types.CallbackQuery, state: FSMContext):
    """Запуск техники 4-7-8."""
    await state.update_data(breathing_technique="478")
    await callback.message.edit_text("🌬 Давай подышим вместе.\n\nТехника 4-7-8:")
    await callback.answer()
    await run_breathing_478(callback.message, state)


@router.callback_query(
    CrisisStates.breathing, CrisisCallback.filter(F.action == "bbox")
)
async def start_breathing_box(callback: types.CallbackQuery, state: FSMContext):
    """Запуск Box Breathing 4-4-4-4."""
    await state.update_data(breathing_technique="box")
    await callback.message.edit_text(
        "⬜ Давай подышим вместе.\n\nBox Breathing 4-4-4-4:"
    )
    await callback.answer()
    await run_breathing_box(callback.message, state)


async def run_breathing_478(message: types.Message, state: FSMContext):
    """
    Выполнение дыхательной техники 4-7-8.
    Вдох 4с → Задержка 7с → Выдох 8с
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

    # Отправляем GIF дыхания (если есть)
    await send_gif_if_available(message, "breathe")

    mantra = get_random_mantra("breathing")
    await message.answer(
        f"✨ Отлично.\n\n_{mantra}_\n\nЕщё раз?",
        parse_mode="Markdown",
        reply_markup=get_breathing_repeat_keyboard(),
    )


async def run_breathing_box(message: types.Message, state: FSMContext):
    """
    Выполнение Box Breathing 4-4-4-4.
    Более простой вариант для тех, кому 4-7-8 сложно.
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

    # Отправляем GIF дыхания (если есть)
    await send_gif_if_available(message, "breathe")

    mantra = get_random_mantra("breathing")
    await message.answer(
        f"✨ Отлично.\n\n_{mantra}_\n\nЕщё раз?",
        parse_mode="Markdown",
        reply_markup=get_breathing_repeat_keyboard(),
    )


@router.callback_query(
    CrisisStates.breathing, CrisisCallback.filter(F.action == "brep")
)
async def repeat_breathing(callback: types.CallbackQuery, state: FSMContext):
    """Повторение дыхательной техники."""
    data = await state.get_data()
    technique = data.get("breathing_technique", "478")

    await callback.message.edit_text("🌬 Ещё один цикл...")
    await callback.answer()

    if technique == "box":
        await run_breathing_box(callback.message, state)
    else:
        await run_breathing_478(callback.message, state)


@router.callback_query(
    CrisisStates.breathing, CrisisCallback.filter(F.action == "bdone")
)
async def breathing_done(callback: types.CallbackQuery, state: FSMContext):
    """Пользователь закончил дышать — предлагаем микро-действие."""
    mantra = get_random_mantra("breathing")

    await callback.message.edit_text(
        f"💙 Как теперь?\n\n_{mantra}_\n\n"
        "Хочешь сделать одно маленькое действие или просто побыть?",
        parse_mode="Markdown",
        reply_markup=get_post_breathing_keyboard(),
    )
    await state.set_state(CrisisStates.waiting_for_feeling)
    await callback.answer()


# ============== Микро-действие ==============


@router.callback_query(CrisisCallback.filter(F.action == "micro"))
async def offer_micro_action(callback: types.CallbackQuery, state: FSMContext):
    """Предложение микро-действия."""
    user = await User.get_or_none(telegram_id=callback.from_user.id)
    if not user:
        await callback.answer("Ошибка", show_alert=True)
        return

    # Проверяем что пользователь в режиме кризиса
    if user.current_mode != "crisis":
        await callback.answer(
            "Эта функция доступна только в режиме кризиса", show_alert=True
        )
        return

    # Ищем активную цель
    goal = await Goal.filter(user=user, status="active").first()

    if goal:
        text = (
            "Если есть силы — можешь сделать одно маленькое действие.\n"
            "Буквально 5-15 минут. Что угодно в сторону цели.\n\n"
            f"Твоя цель: **{goal.title}**\n\n"
            "Примеры:\n"
            "• Написать одну идею\n"
            "• Задать один вопрос\n"
            "• Сделать один маленький шаг"
        )
        await state.update_data(micro_goal_id=goal.id)
    else:
        text = (
            "Если есть силы — можешь сделать одно маленькое действие.\n"
            "Буквально 5-15 минут. Что угодно полезное для себя.\n\n"
            "Примеры:\n"
            "• Выпить воды\n"
            "• Открыть окно\n"
            "• Записать одну мысль"
        )

    try:
        await callback.message.edit_text(
            text, parse_mode="Markdown", reply_markup=get_micro_action_keyboard()
        )
    except Exception:
        await callback.message.answer(
            text, parse_mode="Markdown", reply_markup=get_micro_action_keyboard()
        )
    await state.set_state(CrisisStates.micro_action)
    await callback.answer()


# Обработчики кнопок микро-действия (доступны только в состоянии micro_action)
@router.callback_query(
    CrisisStates.micro_action, CrisisCallback.filter(F.action == "mtry")
)
async def micro_action_try(callback: types.CallbackQuery, state: FSMContext):
    """Пользователь хочет попробовать микро-действие."""
    try:
        await callback.message.edit_text(
            "🎯 Отлично! Сделай что-нибудь маленькое и напиши мне, когда закончишь.\n\n"
            "Не торопись. Хоть 5 минут, хоть 15. Любой прогресс важен.",
            reply_markup=None,
        )
    except Exception:
        await callback.message.answer(
            "🎯 Отлично! Сделай что-нибудь маленькое и напиши мне, когда закончишь.\n\n"
            "Не торопись. Хоть 5 минут, хоть 15. Любой прогресс важен."
        )
    await state.set_state(CrisisStates.waiting_for_micro_report)
    await callback.answer()


@router.callback_query(
    CrisisStates.micro_action, CrisisCallback.filter(F.action == "mskip")
)
async def micro_action_skip(callback: types.CallbackQuery, state: FSMContext):
    """Пользователь не хочет делать микро-действие."""
    # Отправляем GIF отдыха
    await send_gif_if_available(callback.message, "rest")

    try:
        await callback.message.edit_text(
            "Это тоже ок. Я тут, если что. 💙\n\n" f"_{get_random_mantra('crisis')}_",
            parse_mode="Markdown",
            reply_markup=None,
        )
    except Exception:
        await callback.message.answer(
            f"Это тоже ок. Я тут, если что. 💙\n\n" f"_{get_random_mantra('crisis')}_",
            parse_mode="Markdown",
        )
    await state.set_state(CrisisStates.just_being)
    await callback.answer()


@router.message(CrisisStates.micro_action)
async def handle_micro_action_message(message: types.Message, state: FSMContext):
    """Пользователь написал в режиме микро-действия."""
    # Направляем на попытку
    user = await User.get_or_none(telegram_id=message.from_user.id)
    goal = await Goal.filter(user=user, status="active").first() if user else None

    if goal:
        text = (
            f"Твоя цель: **{goal.title}**\n\n"
            "Хочешь попробовать сделать что-то маленькое?"
        )
        await state.update_data(micro_goal_id=goal.id)
    else:
        text = "Хочешь попробовать сделать что-то маленькое?"

    await message.answer(
        text, parse_mode="Markdown", reply_markup=get_micro_action_keyboard()
    )


@router.message(CrisisStates.waiting_for_micro_report)
async def handle_micro_report(message: types.Message, state: FSMContext):
    """Пользователь сообщил о выполнении микро-действия."""
    # Отправляем GIF празднования
    await send_gif_if_available(message, "celebration_small")

    mantra = get_random_mantra("micro_action")

    await message.answer(
        f"💙 Ты молодец!\n\n_{mantra}_\n\n"
        "Хочешь ещё что-то сделать или достаточно на сегодня?",
        parse_mode="Markdown",
        reply_markup=get_crisis_menu_keyboard(),
    )

    await state.set_state(CrisisStates.waiting_for_feeling)


# ============== Выход из режима кризиса ==============


@router.message(Command("normal"))
async def cmd_normal(message: types.Message, state: FSMContext):
    """Ручной выход из режима кризиса."""
    user = await User.get_or_none(telegram_id=message.from_user.id)

    if not user:
        await message.answer("Сначала нужно познакомиться! Нажми /start")
        return

    if user.current_mode != "crisis":
        await message.answer("Ты уже в обычном режиме. 👍")
        return

    await message.answer(
        "Переключить на обычный режим?", reply_markup=get_exit_crisis_keyboard()
    )


@router.callback_query(CrisisCallback.filter(F.action == "exit_y"))
async def confirm_exit_crisis(callback: types.CallbackQuery, state: FSMContext):
    """Подтверждение выхода из режима кризиса с GIF."""
    user = await User.get_or_none(telegram_id=callback.from_user.id)

    if user:
        user.current_mode = "normal"
        user.mode_updated_at = datetime.now()
        await user.save()

    mantra = get_random_mantra("exit")

    await callback.message.edit_text(
        f"✅ Переключил на обычный режим.\n\n"
        f"_{mantra}_\n\n"
        "Используй /new_goal или /checkin когда будешь готов.",
        parse_mode="Markdown",
        reply_markup=None,
    )

    # GIF мотивации — пользователь выходит из кризиса
    await gif_service.send_mood_gif(
        callback.message,
        context="Пользователь выходит из режима кризиса, "
        "чувствует себя лучше, мотивация",
    )

    await state.clear()
    await callback.answer()


@router.callback_query(CrisisCallback.filter(F.action == "exit_n"))
async def cancel_exit_crisis(callback: types.CallbackQuery, state: FSMContext):
    """Отмена выхода из режима кризиса."""
    await callback.message.edit_text(
        "Хорошо, остаёмся в режиме поддержки. 💙\n\n" "Я тут, если что.",
        reply_markup=get_crisis_menu_keyboard(),
    )
    await callback.answer()


# ============== Утилита для проверки режима из других handlers ==============


async def is_user_in_crisis(telegram_id: int) -> bool:
    """
    Проверяет, находится ли пользователь в режиме кризиса.
    Используется другими handlers для смягчения тона.
    """
    user = await User.get_or_none(telegram_id=telegram_id)
    if user:
        return user.current_mode == "crisis"
    return False
