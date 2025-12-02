"""
Сервис для работы с GIF в режиме кризиса.

AICODE-NOTE: GIF хранятся как file_id Telegram — это быстро и не требует внешних API.
file_id уникальны для каждого бота, поэтому при смене бота нужно перезагрузить GIF.
"""

import json
import random
import logging
from pathlib import Path
from typing import Optional

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
            category: Категория GIF (support, breathe, celebration_small, you_got_this, rest)
        
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
    
    def get_for_context(self, context: str) -> tuple[str, Optional[str]]:
        """
        Определяет категорию по контексту и возвращает file_id.
        
        AICODE-NOTE: Простая логика для MVP, в будущем можно использовать LLM
        для более точного определения категории.
        
        Args:
            context: Текстовый контекст ситуации
        
        Returns:
            (category, file_id) — категория и file_id GIF
        """
        context_lower = context.lower()
        
        if "дыхан" in context_lower or "выдох" in context_lower:
            category = "breathe"
        elif "сделал" in context_lower or "получилось" in context_lower:
            category = "celebration_small"
        elif "тяжело" in context_lower or "плохо" in context_lower:
            category = "support"
        elif "отдых" in context_lower or "не сейчас" in context_lower:
            category = "rest"
        else:
            category = "you_got_this"
        
        return category, self.get_random(category)
    
    def has_gifs(self, category: str) -> bool:
        """Проверяет, есть ли GIF в указанной категории."""
        if category not in self.gifs:
            return False
        return bool(self.gifs[category].get("gifs"))


# Singleton instance
gif_service = GifService()

