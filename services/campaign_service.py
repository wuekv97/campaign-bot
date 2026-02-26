"""
Сервис для работы с кампаниями/офферами
"""
from datetime import datetime, timedelta
from typing import List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from models import Campaign, User


async def create_campaign(
    session: AsyncSession,
    code: str,
    title: str,
    message_pt: str | None = None,
    message_hu: str | None = None,
    message_en: str | None = None,
    description: str | None = None,
    active_days: int = 7,
    language: str | None = None,
    is_active: bool = True
) -> Campaign:
    """
    Создать новую кампанию
    
    Args:
        code: Уникальный код кампании (для payload)
        title: Название кампании
        message_pt/hu/en: Сообщения на разных языках
        description: Описание кампании
        active_days: Сколько дней кампания будет активна (по умолчанию 7)
        language: Если кампания только для одного языка
        is_active: Активна ли кампания
    """
    campaign = Campaign(
        code=code,
        title=title,
        description=description,
        message_pt=message_pt,
        message_hu=message_hu,
        message_en=message_en,
        active_from=datetime.utcnow(),
        active_to=datetime.utcnow() + timedelta(days=active_days),
        language=language,
        is_active=is_active
    )
    
    session.add(campaign)
    await session.commit()
    await session.refresh(campaign)
    
    return campaign


async def get_campaign_by_code(
    session: AsyncSession,
    code: str
) -> Campaign | None:
    """Получить кампанию по коду"""
    result = await session.execute(
        select(Campaign).where(Campaign.code == code)
    )
    return result.scalar_one_or_none()


async def activate_campaign_for_user(
    session: AsyncSession,
    user: User,
    campaign: Campaign
) -> bool:
    """
    Активировать кампанию для пользователя
    
    Returns:
        True если кампания была активирована, False если уже была активирована ранее
    """
    # Загружаем кампании пользователя явно
    result = await session.execute(
        select(User)
        .options(selectinload(User.campaigns))
        .where(User.id == user.id)
    )
    user_with_campaigns = result.scalar_one()
    
    # Проверяем, не активировал ли пользователь уже эту кампанию
    if campaign in user_with_campaigns.campaigns:
        return False
    
    # Добавляем кампанию пользователю
    user_with_campaigns.campaigns.append(campaign)
    await session.commit()
    
    return True


async def user_has_campaign(
    session: AsyncSession,
    user: User,
    campaign: Campaign
) -> bool:
    """Проверить, активировал ли пользователь кампанию"""
    # Явная загрузка кампаний пользователя
    result = await session.execute(
        select(User)
        .options(selectinload(User.campaigns))
        .where(User.id == user.id)
    )
    user_with_campaigns = result.scalar_one()
    return campaign in user_with_campaigns.campaigns


async def get_all_campaigns(session: AsyncSession) -> List[Campaign]:
    """Получить все кампании"""
    result = await session.execute(select(Campaign))
    return list(result.scalars().all())


async def get_active_campaigns(session: AsyncSession) -> List[Campaign]:
    """Получить активные кампании"""
    now = datetime.utcnow()
    result = await session.execute(
        select(Campaign)
        .where(Campaign.is_active == True)
        .where(Campaign.active_from <= now)
        .where((Campaign.active_to.is_(None)) | (Campaign.active_to >= now))
    )
    return list(result.scalars().all())


async def get_campaign_stats(session: AsyncSession) -> dict:
    """Получить статистику по кампаниям"""
    result = await session.execute(
        select(Campaign.code, func.count(User.id))
        .select_from(Campaign)
        .outerjoin(Campaign.users)
        .group_by(Campaign.code)
    )
    return {row[0]: row[1] for row in result.all()}

