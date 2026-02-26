"""
Сервис для работы с пользователями
"""
from datetime import datetime
from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from models import User, Tag


async def get_or_create_user(
    session: AsyncSession,
    telegram_id: int,
    username: str | None = None,
    full_name: str | None = None,
    source: str | None = None,
    language: str = "en"
) -> tuple[User, bool]:
    """
    Получить существующего пользователя или создать нового
    
    Returns:
        Tuple (пользователь, создан ли новый)
    """
    # Пытаемся найти существующего пользователя
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = result.scalar_one_or_none()
    
    if user:
        # Обновляем last_active
        user.last_active = datetime.utcnow()
        if username:
            user.username = username
        if full_name:
            user.full_name = full_name
        await session.commit()
        return user, False
    
    # Создаём нового пользователя
    user = User(
        telegram_id=telegram_id,
        username=username,
        full_name=full_name,
        source=source,
        language=language
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    
    # Автоматически добавляем тег с датой регистрации
    reg_date = user.created_at.strftime('%Y-%m-%d')
    await add_tag_to_user(session, user, f"registered_{reg_date}")
    
    return user, True


async def get_user(session: AsyncSession, telegram_id: int) -> User | None:
    """Получить пользователя по telegram_id"""
    result = await session.execute(
        select(User)
        .options(selectinload(User.tags), selectinload(User.campaigns))
        .where(User.telegram_id == telegram_id)
    )
    return result.scalar_one_or_none()


async def update_user_language(
    session: AsyncSession,
    telegram_id: int,
    language: str
) -> User | None:
    """Обновить язык пользователя"""
    user = await get_user(session, telegram_id)
    if user:
        user.language = language
        await session.commit()
        await session.refresh(user)
    return user


async def add_tag_to_user(
    session: AsyncSession,
    user: User,
    tag_name: str
) -> None:
    """Добавить тег пользователю"""
    # Загружаем теги пользователя явно
    await session.refresh(user, ['tags'])
    
    # Найти или создать тег
    result = await session.execute(
        select(Tag).where(Tag.name == tag_name)
    )
    tag = result.scalar_one_or_none()
    
    if not tag:
        tag = Tag(name=tag_name)
        session.add(tag)
        await session.flush()
    
    # Добавить тег, если его ещё нет
    if tag not in user.tags:
        user.tags.append(tag)
        await session.commit()


async def get_users(
    session: AsyncSession,
    language: str | None = None,
    source: str | None = None,
    tags: List[str] | None = None,
    registered_from: datetime | None = None,
    registered_to: datetime | None = None,
) -> List[User]:
    """
    Получить список пользователей по фильтрам для сегментации
    
    Args:
        language: Фильтр по языку
        source: Фильтр по источнику
        tags: Список тегов (пользователь должен иметь хотя бы один из них)
        registered_from: Дата регистрации от
        registered_to: Дата регистрации до
    
    Returns:
        Список пользователей
    """
    query = select(User).options(selectinload(User.tags))
    
    # Фильтр по языку
    if language:
        query = query.where(User.language == language)
    
    # Фильтр по источнику
    if source:
        query = query.where(User.source == source)
    
    # Фильтр по датам регистрации
    if registered_from:
        query = query.where(User.created_at >= registered_from)
    if registered_to:
        query = query.where(User.created_at <= registered_to)
    
    # Фильтр по тегам
    if tags:
        query = query.join(User.tags).where(Tag.name.in_(tags)).distinct()
    
    result = await session.execute(query)
    return list(result.scalars().all())


async def get_users_count(session: AsyncSession) -> int:
    """Получить общее количество пользователей"""
    result = await session.execute(select(func.count(User.id)))
    return result.scalar() or 0


async def get_users_by_language(session: AsyncSession) -> dict:
    """Получить количество пользователей по языкам"""
    result = await session.execute(
        select(User.language, func.count(User.id))
        .group_by(User.language)
    )
    return {row[0]: row[1] for row in result.all()}


async def get_users_by_source(session: AsyncSession) -> dict:
    """Получить количество пользователей по источникам"""
    result = await session.execute(
        select(User.source, func.count(User.id))
        .where(User.source.isnot(None))
        .group_by(User.source)
    )
    return {row[0]: row[1] for row in result.all()}


async def get_all_sources(session: AsyncSession) -> List[str]:
    """Получить список всех уникальных источников"""
    result = await session.execute(
        select(User.source)
        .where(User.source.isnot(None))
        .distinct()
    )
    return [row[0] for row in result.scalars().all()]


async def get_all_tags(session: AsyncSession) -> List[Tag]:
    """Получить список всех тегов"""
    result = await session.execute(select(Tag))
    return list(result.scalars().all())

