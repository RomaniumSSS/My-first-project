import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from tortoise import Tortoise

from src.config import config
from src.database.config import TORTOISE_ORM
from src.bot.handlers import start, onboarding, goal_setting, checkin

# Configure logging
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)


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

    # Include routers
    dp.include_router(start.router)
    dp.include_router(onboarding.router)
    dp.include_router(goal_setting.router)
    dp.include_router(checkin.router)

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
