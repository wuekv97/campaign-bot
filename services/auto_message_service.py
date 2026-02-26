"""
Сервис для автоматических отложенных сообщений
"""
import logging
from datetime import datetime, timedelta
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models import User, AutoMessage, SentAutoMessage

logger = logging.getLogger(__name__)


async def create_auto_message(
    session: AsyncSession,
    name: str,
    delay_minutes: int,
    message_pt: str | None = None,
    message_hu: str | None = None,
    message_en: str | None = None,
    target_language: str | None = None,
    target_source: str | None = None
) -> AutoMessage:
    """Создать автоматическое сообщение"""
    auto_msg = AutoMessage(
        name=name,
        delay_minutes=delay_minutes,
        message_pt=message_pt,
        message_hu=message_hu,
        message_en=message_en,
        target_language=target_language,
        target_source=target_source
    )
    
    session.add(auto_msg)
    await session.commit()
    await session.refresh(auto_msg)
    
    return auto_msg


async def get_all_auto_messages(session: AsyncSession) -> list[AutoMessage]:
    """Получить все автоматические сообщения"""
    result = await session.execute(
        select(AutoMessage).order_by(AutoMessage.delay_minutes)
    )
    return list(result.scalars().all())


async def get_auto_message_by_id(session: AsyncSession, msg_id: int) -> AutoMessage | None:
    """Получить автосообщение по ID"""
    result = await session.execute(
        select(AutoMessage).where(AutoMessage.id == msg_id)
    )
    return result.scalar_one_or_none()


async def get_users_for_auto_message(
    session: AsyncSession,
    auto_message: AutoMessage
) -> list[User]:
    """
    Получить пользователей, которым нужно отправить автосообщение
    
    Логика:
    - Пользователь зарегистрирован X минут назад (где X = delay_minutes)
    - Ему еще не отправляли это сообщение
    - Подходит по фильтрам (язык, источник)
    """
    now = datetime.utcnow()
    target_time = now - timedelta(minutes=auto_message.delay_minutes)
    
    # Диапазон: +/- 5 минут от целевого времени
    time_from = target_time - timedelta(minutes=5)
    time_to = target_time + timedelta(minutes=5)
    
    # Базовый запрос
    query = select(User).where(
        and_(
            User.created_at >= time_from,
            User.created_at <= time_to
        )
    )
    
    # Фильтр по языку
    if auto_message.target_language:
        query = query.where(User.language == auto_message.target_language)
    
    # Фильтр по источнику
    if auto_message.target_source:
        query = query.where(User.source == auto_message.target_source)
    
    result = await session.execute(query)
    all_users = list(result.scalars().all())
    
    # Фильтруем тех, кому уже отправляли
    users_to_send = []
    for user in all_users:
        # Проверяем, не отправляли ли уже
        check = await session.execute(
            select(SentAutoMessage).where(
                and_(
                    SentAutoMessage.user_id == user.id,
                    SentAutoMessage.auto_message_id == auto_message.id
                )
            )
        )
        if not check.scalar_one_or_none():
            users_to_send.append(user)
    
    return users_to_send


async def mark_as_sent(
    session: AsyncSession,
    user_id: int,
    auto_message_id: int
):
    """Отметить что сообщение отправлено пользователю"""
    sent_log = SentAutoMessage(
        user_id=user_id,
        auto_message_id=auto_message_id
    )
    session.add(sent_log)
    await session.commit()


async def toggle_auto_message(session: AsyncSession, msg_id: int) -> AutoMessage | None:
    """Включить/выключить автосообщение"""
    auto_msg = await get_auto_message_by_id(session, msg_id)
    if auto_msg:
        auto_msg.is_active = not auto_msg.is_active
        await session.commit()
        await session.refresh(auto_msg)
    return auto_msg


async def delete_auto_message(session: AsyncSession, msg_id: int) -> bool:
    """Удалить автосообщение"""
    auto_msg = await get_auto_message_by_id(session, msg_id)
    if auto_msg:
        await session.delete(auto_msg)
        await session.commit()
        return True
    return False

