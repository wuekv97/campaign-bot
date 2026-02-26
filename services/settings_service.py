"""
Сервис для работы с настройками бота
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models import Settings


async def get_setting(session: AsyncSession, key: str, default: str = "") -> str:
    """
    Получить значение настройки
    
    Args:
        session: Сессия БД
        key: Ключ настройки
        default: Значение по умолчанию
    
    Returns:
        Значение настройки
    """
    result = await session.execute(
        select(Settings).where(Settings.key == key)
    )
    setting = result.scalar_one_or_none()
    
    if setting:
        return setting.value
    return default


async def set_setting(session: AsyncSession, key: str, value: str) -> Settings:
    """
    Установить значение настройки
    
    Args:
        session: Сессия БД
        key: Ключ настройки
        value: Значение
    
    Returns:
        Объект настройки
    """
    result = await session.execute(
        select(Settings).where(Settings.key == key)
    )
    setting = result.scalar_one_or_none()
    
    if setting:
        setting.value = value
    else:
        setting = Settings(key=key, value=value)
        session.add(setting)
    
    await session.commit()
    await session.refresh(setting)
    
    return setting


async def get_all_settings(session: AsyncSession) -> dict:
    """
    Получить все настройки в виде словаря
    
    Returns:
        Словарь настроек
    """
    result = await session.execute(select(Settings))
    settings = result.scalars().all()
    
    return {s.key: s.value for s in settings}

