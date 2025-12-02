import asyncio
import logging
import sys
from typing import Callable, Dict, Any, Awaitable

from aiogram import Bot, Dispatcher, BaseMiddleware
from aiogram.types import Message, TelegramObject, CallbackQuery
from aiogram.fsm.storage.memory import MemoryStorage
from tortoise import Tortoise

from src.config import config
from src.database.config import TORTOISE_ORM
from src.bot.handlers import start, onboarding, goal_setting, checkin, crisis

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class WhitelistMiddleware(BaseMiddleware):
    """Middleware to restrict access to allowed users only."""
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user = data.get("event_from_user")
        if user and config.ALLOWED_USER_IDS:
            if user.id not in config.ALLOWED_USER_IDS:
                logger.warning(f"Unauthorized access attempt from user {user.id} (@{user.username})")
                # We can silently ignore or send a message. 
                # For messages, we can reply.
                if isinstance(event, Message):
                    await event.answer("🔒 Access denied. This bot is in closed Alpha.")
                elif isinstance(event, CallbackQuery):
                    await event.answer("🔒 Access denied.", show_alert=True)
                return
        
        return await handler(event, data)


async def init_db():
    """Initialize database connection."""
    await Tortoise.init(config=TORTOISE_ORM)
    # Safe to run, but usually handled by Aerich
    await Tortoise.generate_schemas(safe=True)


async def main():
    """Entry point for the bot."""
    # Initialize Bot and Dispatcher
    bot = Bot(token=config.BOT_TOKEN.get_secret_value())
    dp = Dispatcher(storage=MemoryStorage())

    # Middleware setup
    if config.ALLOWED_USER_IDS:
        logger.info(f"Whitelist enabled: {config.ALLOWED_USER_IDS}")
        dp.message.outer_middleware(WhitelistMiddleware())
        dp.callback_query.outer_middleware(WhitelistMiddleware())

    # Include routers
    dp.include_router(start.router)
    dp.include_router(onboarding.router)
    dp.include_router(goal_setting.router)
    dp.include_router(checkin.router)
    dp.include_router(crisis.router)

    # Database setup
    await init_db()

    logger.info("Starting bot...")
    try:
        await dp.start_polling(bot)
    finally:
        await Tortoise.close_connections()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped!")
