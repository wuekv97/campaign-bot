"""
Инициализация и управление базой данных
"""
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from models import Base
from config import DATABASE_URL
import logging

logger = logging.getLogger(__name__)

# Создание async движка
engine = create_async_engine(
    DATABASE_URL,
    echo=False  # Установите True для отладки SQL-запросов
)

# Фабрика сессий
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def init_db():
    """Создание всех таблиц в базе данных"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("База данных инициализирована")


async def get_session() -> AsyncSession:
    """Получить сессию базы данных"""
    async with async_session_maker() as session:
        yield session

