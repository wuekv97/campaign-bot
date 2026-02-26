"""
Background task for sending automatic messages
"""
import json
import asyncio
import logging
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database import async_session_maker
from services.auto_message_service import (
    get_all_auto_messages,
    get_users_for_auto_message,
    mark_as_sent
)

logger = logging.getLogger(__name__)


async def send_auto_message(bot: Bot, chat_id: int, auto_msg, user_language: str):
    """Send auto message with media and buttons"""
    text = auto_msg.get_message(user_language)
    if not text:
        return
    
    # Build keyboard from buttons_json
    keyboard = None
    if auto_msg.buttons_json:
        try:
            buttons_data = json.loads(auto_msg.buttons_json)
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=btn['text'], url=btn['url'])]
                for btn in buttons_data
            ])
        except:
            pass
    
    # Send with media if exists
    if auto_msg.media_type and auto_msg.media_file_id:
        if auto_msg.media_type == 'photo':
            await bot.send_photo(
                chat_id=chat_id,
                photo=auto_msg.media_file_id,
                caption=text,
                parse_mode='HTML',
                reply_markup=keyboard
            )
        elif auto_msg.media_type == 'video':
            await bot.send_video(
                chat_id=chat_id,
                video=auto_msg.media_file_id,
                caption=text,
                parse_mode='HTML',
                reply_markup=keyboard
            )
    else:
        await bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode='HTML',
            reply_markup=keyboard
        )


async def send_auto_messages(bot: Bot):
    """
    Background task for sending auto messages
    Runs every 5 minutes
    """
    while True:
        try:
            async with async_session_maker() as session:
                auto_messages = await get_all_auto_messages(session)
                active_messages = [msg for msg in auto_messages if msg.is_active]
                
                for auto_msg in active_messages:
                    users = await get_users_for_auto_message(session, auto_msg)
                    
                    if users:
                        logger.info(f"Sending auto message '{auto_msg.name}' to {len(users)} users")
                    
                    for user in users:
                        try:
                            await send_auto_message(bot, user.telegram_id, auto_msg, user.language)
                            await mark_as_sent(session, user.id, auto_msg.id)
                            logger.info(f"Auto message sent to {user.telegram_id}")
                            await asyncio.sleep(0.1)
                                
                        except Exception as e:
                            logger.error(f"Error sending auto message to {user.telegram_id}: {e}")
            
            await asyncio.sleep(300)  # 5 minutes
            
        except Exception as e:
            logger.error(f"Error in auto_sender: {e}")
            await asyncio.sleep(60)
