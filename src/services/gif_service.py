"""
Сервис для работы с GIF.

AICODE-NOTE: GIF хранятся как file_id Telegram — это быстро и не требует внешних API.
file_id уникальны для каждого бота, поэтому при смене бота нужно перезагрузить GIF.
"""

import json
import random
import logging
from pathlib import Path
from typing import Optional

from aiogram import types

logger = logging.getLogger(__name__)


class GifService:
    def __init__(self):
        self.gifs = self._load_gifs()
    
    def _load_gifs(self) -> dict:
        """Загружает GIF из JSON-файла."""
        path = Path(__file__).parent.parent / "data" / "gifs.json"
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"GIF file not found at {path}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in gifs.json: {e}")
            return {}
    
    def get_random(self, category: str) -> Optional[str]:
        """
        Возвращает случайный file_id из указанной категории.

        Args:
            category: Категория GIF (support, breathe,
                celebration_small, you_got_this, rest)

        Returns:
            file_id GIF или None если категория пуста/не найдена
        """
        if category not in self.gifs:
            return None
        
        gifs = self.gifs[category].get("gifs", [])
        if not gifs:
            return None
        
        gif = random.choice(gifs)
        return gif.get("file_id")
    
    def has_gifs(self, category: str) -> bool:
        """Проверяет, есть ли GIF в указанной категории."""
        if category not in self.gifs:
            return False
        return bool(self.gifs[category].get("gifs"))

    async def send_mood_gif(
        self, 
        message: types.Message, 
        context: str, 
        mood_text: str = None,
        caption: str = None
    ) -> bool:
        """
        Отправляет GIF на основе контекста и настроения пользователя.
        LLM выбирает категорию, затем отправляется случайный GIF из неё.
        
        Args:
            message: Telegram message для ответа
            context: Контекст завершённой функции (reflect/crisis/checkin)
            mood_text: Текст ответов/настроения пользователя (опционально)
            caption: Подпись к GIF (опционально)
        
        Returns:
            True если GIF отправлен, False если нет доступных GIF
        """
        # Ленивый импорт чтобы избежать циклической зависимости
        from src.services.ai import ai_service
        
        try:
            category = await ai_service.choose_gif_category(context, mood_text)
            file_id = self.get_random(category)
            
            if file_id:
                await message.answer_animation(animation=file_id, caption=caption)
                logger.info(f"Sent mood GIF from category: {category}")
                return True
            else:
                logger.debug(f"No GIFs available in category: {category}")
                return False
                
        except Exception as e:
            logger.warning(f"Failed to send mood GIF: {e}")
            return False


# Singleton instance
gif_service = GifService()

