"""
Main bot entry point
All admin functions are managed via web panel
"""
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from database import init_db
from handlers import start
from tasks.auto_sender import send_auto_messages

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


async def load_texts_to_cache():
    """Load texts and languages from database to cache"""
    from database import async_session_maker
    from services.text_service import (
        init_default_languages, 
        init_default_texts, 
        get_all_languages,
        get_texts_for_language
    )
    from locales import set_texts_cache
    from keyboards.inline import set_languages_cache
    
    async with async_session_maker() as session:
        # Initialize defaults if needed
        await init_default_languages(session)
        await init_default_texts(session)
        
        # Load all languages
        languages = await get_all_languages(session, active_only=False)
        
        # Set languages cache for keyboards
        languages_data = [
            {"code": l.code, "name": l.name, "flag": l.flag, "is_active": l.is_active}
            for l in languages
        ]
        set_languages_cache(languages_data)
        
        # Load all texts to cache
        cache = {}
        for lang in languages:
            cache[lang.code] = await get_texts_for_language(session, lang.code)
        
        set_texts_cache(cache)
        logger.info(f"Loaded texts for {len(languages)} languages")


async def main():
    """Main bot function"""
    logger.info("Starting bot...")
    
    # Initialize database
    await init_db()
    logger.info("Database initialized")
    
    # Load texts from database
    await load_texts_to_cache()
    
    # Create bot and dispatcher
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Register routers (only user-facing handlers)
    dp.include_router(start.router)
    
    # Start background task for auto messages
    asyncio.create_task(send_auto_messages(bot))
    
    logger.info("Bot started and ready!")
    
    # Start polling
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped")
