"""
Сервис для работы с рассылками
"""
import asyncio
import logging
from typing import List
from aiogram import Bot
from aiogram.types import Message
from aiogram.exceptions import TelegramRetryAfter, TelegramForbiddenError
from models import User
from config import BROADCAST_DELAY, MAX_RETRY_ATTEMPTS

logger = logging.getLogger(__name__)


async def send_broadcast(
    bot: Bot,
    users: List[User],
    message: Message,
    delay: float = BROADCAST_DELAY
) -> tuple[int, int]:
    """
    Отправить рассылку пользователям
    
    Args:
        bot: Экземпляр бота
        users: Список пользователей для рассылки
        message: Сообщение для пересылки (шаблон)
        delay: Задержка между отправками
    
    Returns:
        Tuple (количество успешных отправок, количество ошибок)
    """
    success_count = 0
    failed_count = 0
    
    for user in users:
        try:
            # Отправляем сообщение в зависимости от типа контента
            if message.photo:
                # Если есть фото
                await bot.send_photo(
                    chat_id=user.telegram_id,
                    photo=message.photo[-1].file_id,
                    caption=message.caption or message.text
                )
            elif message.video:
                # Если есть видео
                await bot.send_video(
                    chat_id=user.telegram_id,
                    video=message.video.file_id,
                    caption=message.caption or message.text
                )
            elif message.document:
                # Если есть документ
                await bot.send_document(
                    chat_id=user.telegram_id,
                    document=message.document.file_id,
                    caption=message.caption or message.text
                )
            else:
                # Просто текст
                await bot.send_message(
                    chat_id=user.telegram_id,
                    text=message.text or message.caption or ""
                )
            
            success_count += 1
            logger.info(f"Сообщение отправлено пользователю {user.telegram_id}")
            
        except TelegramRetryAfter as e:
            # Если получили ограничение от Telegram, ждем
            logger.warning(f"Flood control: ожидание {e.retry_after} секунд")
            await asyncio.sleep(e.retry_after)
            # Повторная попытка
            try:
                if message.photo:
                    await bot.send_photo(
                        chat_id=user.telegram_id,
                        photo=message.photo[-1].file_id,
                        caption=message.caption or message.text
                    )
                else:
                    await bot.send_message(
                        chat_id=user.telegram_id,
                        text=message.text or ""
                    )
                success_count += 1
            except Exception as retry_error:
                logger.error(f"Ошибка при повторной отправке пользователю {user.telegram_id}: {retry_error}")
                failed_count += 1
                
        except TelegramForbiddenError:
            # Пользователь заблокировал бота
            logger.warning(f"Пользователь {user.telegram_id} заблокировал бота")
            failed_count += 1
            
        except Exception as e:
            logger.error(f"Ошибка отправки пользователю {user.telegram_id}: {e}")
            failed_count += 1
        
        # Задержка между отправками
        await asyncio.sleep(delay)
    
    return success_count, failed_count

