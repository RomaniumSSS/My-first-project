import logging
import time
from typing import List, Dict, Any

from openai import AsyncOpenAI, APIError, RateLimitError, APIConnectionError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from src.config import config

# Configure logger
logger = logging.getLogger(__name__)


class AIService:
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=config.OPENAI_KEY.get_secret_value(), timeout=60.0
        )
        self.model = config.OPENAI_MODEL

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(
            (APIError, APIConnectionError, RateLimitError, ConnectionError)
        ),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    async def _make_request(self, messages: List[Dict[str, Any]], **kwargs) -> str:
        """Internal method to make the actual API call with retries."""
        start_time = time.time()
        try:
            # AICODE-NOTE: Using chat completions for both text and vision
            response = await self.client.chat.completions.create(
                model=self.model, messages=messages, **kwargs
            )
            latency = time.time() - start_time
            logger.info(f"AI Request successful. Latency: {latency:.2f}s")
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"AI Request failed: {e}")
            raise e

    async def get_chat_response(self, messages: List[Dict[str, Any]], **kwargs) -> str:
        """
        Public method to get chat response with fallback.
        """
        # Log shortened prompt for debugging
        if messages:
            last_msg = messages[-1].get("content", "")
            if isinstance(last_msg, str):
                preview = last_msg[:100] + "..." if len(last_msg) > 100 else last_msg
                logger.info(f"Sending AI request: {preview}")
            elif isinstance(last_msg, list):
                logger.info("Sending AI request with multimodal content")

        try:
            return await self._make_request(messages, **kwargs)
        except Exception:
            logger.error("All AI retries failed. Returning fallback.")
            # Fallback as per plan
            return "Мозг коуча сейчас перезагружается, попробуй позже."


# Singleton instance
ai_service = AIService()
