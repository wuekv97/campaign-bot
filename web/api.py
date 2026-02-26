"""
API endpoints для веб-админпанели
"""
import json
import logging
import os
import aiofiles
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from database import async_session_maker
from models import User, Campaign, Tag, Settings, AutoMessage, user_campaigns
from services.campaign_service import create_campaign, get_all_campaigns, get_campaign_by_code
from services.user_service import get_users_count, get_users_by_language, get_users_by_source
from services.campaign_service import get_campaign_stats
from web.auth import verify_admin
from config import BOT_TOKEN

logger = logging.getLogger(__name__)
router = APIRouter()


# ========== PYDANTIC MODELS ==========

class StatsResponse(BaseModel):
    total_users: int
    by_language: dict
    by_source: dict
    by_campaign: dict


class CampaignCreate(BaseModel):
    code: str
    title: str
    description: Optional[str] = None
    active_days: int
    message_pt: Optional[str] = None
    message_hu: Optional[str] = None
    message_en: Optional[str] = None
    media_type: Optional[str] = None
    media_file_id: Optional[str] = None
    buttons_json: Optional[str] = None


class CampaignUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    message_pt: Optional[str] = None
    message_hu: Optional[str] = None
    message_en: Optional[str] = None
    is_active: Optional[bool] = None
    media_type: Optional[str] = None
    media_file_id: Optional[str] = None
    buttons_json: Optional[str] = None


class CampaignResponse(BaseModel):
    id: int
    code: str
    title: str
    description: Optional[str]
    message_pt: Optional[str]
    message_hu: Optional[str]
    message_en: Optional[str]
    media_type: Optional[str]
    media_file_id: Optional[str]
    buttons_json: Optional[str]
    active_from: datetime
    active_to: Optional[datetime]
    is_active: bool
    activations: int
    
    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    id: int
    telegram_id: int
    username: Optional[str]
    full_name: Optional[str]
    language: str
    source: Optional[str]
    created_at: datetime
    last_active: datetime
    
    class Config:
        from_attributes = True


class BroadcastCreate(BaseModel):
    text: str
    language: Optional[str] = None
    source: Optional[str] = None
    tags: Optional[List[str]] = None
    media_type: Optional[str] = None
    media_file_id: Optional[str] = None
    buttons_json: Optional[str] = None


class SettingsUpdate(BaseModel):
    key: str
    value: str


# ========== СТАТИСТИКА ==========

@router.get("/stats", response_model=StatsResponse)
async def get_stats(username: str = Depends(verify_admin)):
    """Получить статистику бота"""
    async with async_session_maker() as session:
        total_users = await get_users_count(session)
        by_language = await get_users_by_language(session)
        by_source = await get_users_by_source(session)
        by_campaign = await get_campaign_stats(session)
        
        return StatsResponse(
            total_users=total_users,
            by_language=by_language,
            by_source=by_source,
            by_campaign=by_campaign
        )


@router.get("/stats/today")
async def get_stats_today(username: str = Depends(verify_admin)):
    """Получить статистику за сегодня"""
    async with async_session_maker() as session:
        # Получаем начало сегодняшнего дня
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Подсчитываем новых пользователей за сегодня
        result = await session.execute(
            select(func.count(User.id)).where(User.created_at >= today_start)
        )
        new_today = result.scalar()
        
        # Активные кампании
        result = await session.execute(
            select(func.count(Campaign.id)).where(Campaign.is_active == True)
        )
        active_campaigns = result.scalar()
        
        # Общее количество активаций
        result = await session.execute(
            select(func.count()).select_from(user_campaigns)
        )
        total_activations = result.scalar()
        
        return {
            "new_today": new_today,
            "active_campaigns": active_campaigns,
            "total_activations": total_activations
        }


# ========== КАМПАНИИ ==========

@router.get("/campaigns", response_model=List[CampaignResponse])
async def list_campaigns(username: str = Depends(verify_admin)):
    """Получить список всех кампаний"""
    async with async_session_maker() as session:
        result = await session.execute(
            select(Campaign).options(selectinload(Campaign.users))
        )
        campaigns = result.scalars().all()
        
        return [
            CampaignResponse(
                id=c.id,
                code=c.code,
                title=c.title,
                description=c.description,
                message_pt=c.message_pt,
                message_hu=c.message_hu,
                message_en=c.message_en,
                media_type=c.media_type,
                media_file_id=c.media_file_id,
                buttons_json=c.buttons_json,
                active_from=c.active_from,
                active_to=c.active_to,
                is_active=c.is_active,
                activations=len(c.users)
            )
            for c in campaigns
        ]


@router.get("/campaigns/{code}", response_model=CampaignResponse)
async def get_campaign(code: str, username: str = Depends(verify_admin)):
    """Получить кампанию по коду"""
    async with async_session_maker() as session:
        result = await session.execute(
            select(Campaign)
            .options(selectinload(Campaign.users))
            .where(Campaign.code == code)
        )
        campaign = result.scalar_one_or_none()
        
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        return CampaignResponse(
            id=campaign.id,
            code=campaign.code,
            title=campaign.title,
            description=campaign.description,
            message_pt=campaign.message_pt,
            message_hu=campaign.message_hu,
            message_en=campaign.message_en,
            media_type=campaign.media_type,
            media_file_id=campaign.media_file_id,
            buttons_json=campaign.buttons_json,
            active_from=campaign.active_from,
            active_to=campaign.active_to,
            is_active=campaign.is_active,
            activations=len(campaign.users)
        )


@router.post("/campaigns", response_model=CampaignResponse)
async def create_new_campaign(campaign_data: CampaignCreate, username: str = Depends(verify_admin)):
    """Создать новую кампанию"""
    async with async_session_maker() as session:
        # Проверяем существование
        existing = await get_campaign_by_code(session, campaign_data.code)
        if existing:
            raise HTTPException(status_code=400, detail="Campaign with this code already exists")
        
        # Convert temp file path to Telegram file_id if needed
        media_file_id = campaign_data.media_file_id
        if campaign_data.media_type and media_file_id and media_file_id.startswith('/tmp/'):
            from aiogram import Bot
            from aiogram.types import FSInputFile
            from config import ADMIN_IDS
            
            bot = Bot(token=BOT_TOKEN)
            admin_id = ADMIN_IDS[0] if ADMIN_IDS else None
            
            if admin_id:
                try:
                    if campaign_data.media_type == 'photo':
                        photo = FSInputFile(media_file_id)
                        msg = await bot.send_photo(chat_id=admin_id, photo=photo)
                        media_file_id = msg.photo[-1].file_id
                        await bot.delete_message(chat_id=admin_id, message_id=msg.message_id)
                    elif campaign_data.media_type == 'video':
                        video = FSInputFile(media_file_id)
                        msg = await bot.send_video(chat_id=admin_id, video=video)
                        media_file_id = msg.video.file_id
                        await bot.delete_message(chat_id=admin_id, message_id=msg.message_id)
                    logger.info(f"Converted temp file to file_id: {media_file_id}")
                except Exception as e:
                    logger.error(f"Error converting media: {e}")
                    media_file_id = None
                finally:
                    await bot.session.close()
        
        # Создаем кампанию
        campaign = Campaign(
            code=campaign_data.code,
            title=campaign_data.title,
            description=campaign_data.description,
            message_pt=campaign_data.message_pt,
            message_hu=campaign_data.message_hu,
            message_en=campaign_data.message_en,
            media_type=campaign_data.media_type if media_file_id else None,
            media_file_id=media_file_id,
            buttons_json=campaign_data.buttons_json,
            active_from=datetime.utcnow(),
            active_to=datetime.utcnow() + timedelta(days=campaign_data.active_days),
            is_active=True
        )
        
        session.add(campaign)
        await session.commit()
        await session.refresh(campaign, ["users"])
        
        return CampaignResponse(
            id=campaign.id,
            code=campaign.code,
            title=campaign.title,
            description=campaign.description,
            message_pt=campaign.message_pt,
            message_hu=campaign.message_hu,
            message_en=campaign.message_en,
            media_type=campaign.media_type,
            media_file_id=campaign.media_file_id,
            buttons_json=campaign.buttons_json,
            active_from=campaign.active_from,
            active_to=campaign.active_to,
            is_active=campaign.is_active,
            activations=0
        )


@router.patch("/campaigns/{code}", response_model=CampaignResponse)
async def update_campaign(code: str, update_data: CampaignUpdate, username: str = Depends(verify_admin)):
    """Обновить кампанию"""
    async with async_session_maker() as session:
        result = await session.execute(
            select(Campaign)
            .options(selectinload(Campaign.users))
            .where(Campaign.code == code)
        )
        campaign = result.scalar_one_or_none()
        
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        # Обновляем поля
        if update_data.title is not None:
            campaign.title = update_data.title
        if update_data.description is not None:
            campaign.description = update_data.description
        if update_data.message_pt is not None:
            campaign.message_pt = update_data.message_pt
        if update_data.message_hu is not None:
            campaign.message_hu = update_data.message_hu
        if update_data.message_en is not None:
            campaign.message_en = update_data.message_en
        if update_data.is_active is not None:
            campaign.is_active = update_data.is_active
        if update_data.media_type is not None:
            campaign.media_type = update_data.media_type
        if update_data.media_file_id is not None:
            # Convert temp file path to Telegram file_id if needed
            media_file_id = update_data.media_file_id
            if media_file_id and media_file_id.startswith('/tmp/'):
                from aiogram import Bot
                from aiogram.types import FSInputFile
                from config import ADMIN_IDS
                
                bot = Bot(token=BOT_TOKEN)
                admin_id = ADMIN_IDS[0] if ADMIN_IDS else None
                
                if admin_id:
                    try:
                        if update_data.media_type == 'photo':
                            photo = FSInputFile(media_file_id)
                            msg = await bot.send_photo(chat_id=admin_id, photo=photo)
                            media_file_id = msg.photo[-1].file_id
                            await bot.delete_message(chat_id=admin_id, message_id=msg.message_id)
                        elif update_data.media_type == 'video':
                            video = FSInputFile(media_file_id)
                            msg = await bot.send_video(chat_id=admin_id, video=video)
                            media_file_id = msg.video.file_id
                            await bot.delete_message(chat_id=admin_id, message_id=msg.message_id)
                        logger.info(f"Converted temp file to file_id: {media_file_id}")
                    except Exception as e:
                        logger.error(f"Error converting media: {e}")
                        media_file_id = None
                    finally:
                        await bot.session.close()
            
            campaign.media_file_id = media_file_id
            if not media_file_id:
                campaign.media_type = None
        if update_data.buttons_json is not None:
            campaign.buttons_json = update_data.buttons_json
        
        await session.commit()
        await session.refresh(campaign, ["users"])
        
        return CampaignResponse(
            id=campaign.id,
            code=campaign.code,
            title=campaign.title,
            description=campaign.description,
            message_pt=campaign.message_pt,
            message_hu=campaign.message_hu,
            message_en=campaign.message_en,
            media_type=campaign.media_type,
            media_file_id=campaign.media_file_id,
            buttons_json=campaign.buttons_json,
            active_from=campaign.active_from,
            active_to=campaign.active_to,
            is_active=campaign.is_active,
            activations=len(campaign.users)
        )


@router.delete("/campaigns/{code}")
async def delete_campaign(code: str, username: str = Depends(verify_admin)):
    """Удалить кампанию"""
    async with async_session_maker() as session:
        campaign = await get_campaign_by_code(session, code)
        
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        await session.delete(campaign)
        await session.commit()
        
        return {"message": "Campaign deleted successfully"}


# ========== ПОЛЬЗОВАТЕЛИ ==========

@router.get("/users", response_model=List[UserResponse])
async def list_users(
    limit: int = 100,
    offset: int = 0,
    language: Optional[str] = None,
    source: Optional[str] = None,
    sort: Optional[str] = None,
    username: str = Depends(verify_admin)
):
    """Get list of users with filters and sorting"""
    async with async_session_maker() as session:
        query = select(User)
        
        if language:
            query = query.where(User.language == language)
        if source:
            query = query.where(User.source == source)
        
        # Sorting
        if sort == 'created_desc':
            query = query.order_by(User.created_at.desc())
        elif sort == 'created_asc':
            query = query.order_by(User.created_at.asc())
        elif sort == 'source':
            query = query.order_by(User.source.asc())
        else:
            query = query.order_by(User.created_at.desc())
        
        query = query.limit(limit).offset(offset)
        
        result = await session.execute(query)
        users = result.scalars().all()
        
        return [
            UserResponse(
                id=u.id,
                telegram_id=u.telegram_id,
                username=u.username,
                full_name=u.full_name,
                language=u.language,
                source=u.source,
                created_at=u.created_at,
                last_active=u.last_active
            )
            for u in users
        ]


@router.delete("/users/{telegram_id}")
async def delete_user(telegram_id: int, username: str = Depends(verify_admin)):
    """Delete user from database"""
    async with async_session_maker() as session:
        from sqlalchemy import delete
        from models import user_tags, user_campaigns, SentAutoMessage
        
        # Get user
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Delete related records
        await session.execute(delete(user_tags).where(user_tags.c.user_id == user.id))
        await session.execute(delete(user_campaigns).where(user_campaigns.c.user_id == user.id))
        await session.execute(delete(SentAutoMessage).where(SentAutoMessage.user_id == user.id))
        
        # Delete user
        await session.delete(user)
        await session.commit()
        
        return {"message": f"User {telegram_id} deleted"}


# ========== НАСТРОЙКИ ==========

@router.get("/settings")
async def get_settings(username: str = Depends(verify_admin)):
    """Получить все настройки"""
    async with async_session_maker() as session:
        result = await session.execute(select(Settings))
        settings = result.scalars().all()
        
        return {s.key: s.value for s in settings}


@router.put("/settings")
async def update_settings(settings_data: SettingsUpdate, username: str = Depends(verify_admin)):
    """Обновить настройку"""
    async with async_session_maker() as session:
        result = await session.execute(
            select(Settings).where(Settings.key == settings_data.key)
        )
        setting = result.scalar_one_or_none()
        
        if setting:
            setting.value = settings_data.value
        else:
            setting = Settings(key=settings_data.key, value=settings_data.value)
            session.add(setting)
        
        await session.commit()
        
        return {"message": "Setting updated successfully"}


# ========== SOURCES ==========

@router.get("/sources")
async def get_sources(username: str = Depends(verify_admin)):
    """Get all unique sources from users and campaigns"""
    async with async_session_maker() as session:
        # Get unique sources from users
        user_sources_result = await session.execute(
            select(User.source).distinct().where(User.source.isnot(None))
        )
        user_sources = [s for s in user_sources_result.scalars().all() if s]
        
        # Get campaign codes
        campaigns_result = await session.execute(
            select(Campaign.code).where(Campaign.is_active == True)
        )
        campaign_codes = [f"offer_{c}" if not c.startswith('offer_') else c 
                         for c in campaigns_result.scalars().all()]
        
        # Combine and deduplicate
        all_sources = list(set(user_sources + campaign_codes + ['direct']))
        all_sources.sort()
        
        return {"sources": all_sources}


# ========== BROADCAST ==========

@router.post("/broadcast")
async def create_broadcast(broadcast_data: BroadcastCreate, username: str = Depends(verify_admin)):
    """Create and send broadcast to users"""
    from aiogram import Bot
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest
    import asyncio
    
    async with async_session_maker() as session:
        # Get recipients
        query = select(User)
        
        if broadcast_data.language:
            query = query.where(User.language == broadcast_data.language)
        if broadcast_data.source:
            query = query.where(User.source == broadcast_data.source)
        if broadcast_data.tags:
            # Filter by tags
            for tag in broadcast_data.tags:
                query = query.join(User.tags).where(Tag.name == tag)
        
        result = await session.execute(query)
        users = result.scalars().all()
        
        if not users:
            return {
                "success": True,
                "total": 0,
                "sent": 0,
                "failed": 0,
                "details": []
            }
        
        # Initialize bot
        bot = Bot(token=BOT_TOKEN)
        
        # Prepare keyboard if buttons exist
        keyboard = None
        if broadcast_data.buttons_json:
            buttons_data = json.loads(broadcast_data.buttons_json)
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=btn['text'], url=btn['url'])]
                for btn in buttons_data
            ])
        
        # Prepare media if exists
        media_file_id = None
        if broadcast_data.media_type and broadcast_data.media_file_id:
            # If file_id is a path, upload it first to get telegram file_id
            if broadcast_data.media_file_id.startswith('/tmp/'):
                from aiogram.types import FSInputFile
                from config import ADMIN_IDS
                admin_id = ADMIN_IDS[0] if ADMIN_IDS else None
                
                if admin_id:
                    try:
                        if broadcast_data.media_type == 'photo':
                            photo = FSInputFile(broadcast_data.media_file_id)
                            msg = await bot.send_photo(chat_id=admin_id, photo=photo)
                            media_file_id = msg.photo[-1].file_id
                            # Delete the message from admin chat
                            await bot.delete_message(chat_id=admin_id, message_id=msg.message_id)
                        elif broadcast_data.media_type == 'video':
                            video = FSInputFile(broadcast_data.media_file_id)
                            msg = await bot.send_video(chat_id=admin_id, video=video)
                            media_file_id = msg.video.file_id
                            # Delete the message from admin chat
                            await bot.delete_message(chat_id=admin_id, message_id=msg.message_id)
                    except Exception as e:
                        logger.error(f"Error getting file_id: {e}")
            else:
                media_file_id = broadcast_data.media_file_id
        
        # Send messages
        sent = 0
        failed = 0
        details = []
        
        for user in users:
            try:
                if broadcast_data.media_type and media_file_id:
                    if broadcast_data.media_type == 'photo':
                        await bot.send_photo(
                            chat_id=user.telegram_id,
                            photo=media_file_id,
                            caption=broadcast_data.text,
                            parse_mode='HTML',
                            reply_markup=keyboard
                        )
                    elif broadcast_data.media_type == 'video':
                        await bot.send_video(
                            chat_id=user.telegram_id,
                            video=media_file_id,
                            caption=broadcast_data.text,
                            parse_mode='HTML',
                            reply_markup=keyboard
                        )
                else:
                    await bot.send_message(
                        chat_id=user.telegram_id,
                        text=broadcast_data.text,
                        parse_mode='HTML',
                        reply_markup=keyboard
                    )
                
                sent += 1
                details.append({
                    "user_id": user.telegram_id,
                    "username": user.username or user.full_name or f"User {user.telegram_id}",
                    "status": "success"
                })
                
                # Sleep to avoid flood limits
                await asyncio.sleep(0.05)
                
            except (TelegramForbiddenError, TelegramBadRequest) as e:
                failed += 1
                details.append({
                    "user_id": user.telegram_id,
                    "username": user.username or user.full_name or f"User {user.telegram_id}",
                    "status": "error",
                    "error": str(e)
                })
            except Exception as e:
                logger.error(f"Error sending broadcast to {user.telegram_id}: {e}")
                failed += 1
                details.append({
                    "user_id": user.telegram_id,
                    "username": user.username or user.full_name or f"User {user.telegram_id}",
                    "status": "error",
                    "error": "Unknown error"
                })
        
        await bot.session.close()
        
        return {
            "success": True,
            "total": len(users),
            "sent": sent,
            "failed": failed,
            "success_rate": round((sent / len(users)) * 100, 1) if users else 0,
            "details": details
        }


# ========== ЗАГРУЗКА МЕДИА ==========

@router.post("/upload/media")
async def upload_media(file: UploadFile = File(...), username: str = Depends(verify_admin)):
    """
    Upload media and get file_id (stores locally, gets file_id when sending)
    """
    try:
        # Read file contents
        contents = await file.read()
        
        # Determine media type by extension
        file_extension = file.filename.split('.')[-1].lower() if file.filename else ''
        
        if file_extension in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
            media_type = 'photo'
        elif file_extension in ['mp4', 'avi', 'mov', 'mkv']:
            media_type = 'video'
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type. Use images or videos.")
        
        # Save to temp directory
        import hashlib
        file_hash = hashlib.md5(contents).hexdigest()
        temp_path = f"/tmp/media_{file_hash}_{file.filename}"
        
        async with aiofiles.open(temp_path, 'wb') as f:
            await f.write(contents)
        
        # Return path instead of file_id (will get file_id when sending)
        return {
            "media_type": media_type,
            "file_id": temp_path,  # Store path temporarily
            "filename": file.filename,
            "size": len(contents)
        }
        
    except Exception as e:
        logger.error(f"Error uploading media: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== LANGUAGES ==========

class LanguageCreate(BaseModel):
    code: str
    name: str
    flag: str


class LanguageUpdate(BaseModel):
    name: Optional[str] = None
    flag: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


@router.get("/languages")
async def list_languages(username: str = Depends(verify_admin)):
    """Get all languages"""
    from services.text_service import get_all_languages
    
    async with async_session_maker() as session:
        languages = await get_all_languages(session, active_only=False)
        return [
            {
                "code": l.code,
                "name": l.name,
                "flag": l.flag,
                "is_active": l.is_active,
                "is_default": l.is_default,
                "sort_order": l.sort_order
            }
            for l in languages
        ]


@router.post("/languages")
async def create_language(data: LanguageCreate, username: str = Depends(verify_admin)):
    """Create new language"""
    from services.text_service import create_language, get_language, create_text_key, get_all_text_keys
    
    async with async_session_maker() as session:
        # Check if exists
        existing = await get_language(session, data.code)
        if existing:
            raise HTTPException(status_code=400, detail="Language already exists")
        
        lang = await create_language(session, data.code, data.name, data.flag)
        
        # Create empty texts for all existing keys
        keys = await get_all_text_keys(session)
        for key in keys:
            from models import BotText
            text = BotText(key=key, language=data.code, text="")
            session.add(text)
        await session.commit()
        
        return {"code": lang.code, "name": lang.name, "flag": lang.flag}


@router.patch("/languages/{code}")
async def update_language(code: str, data: LanguageUpdate, username: str = Depends(verify_admin)):
    """Update language"""
    from services.text_service import update_language
    
    async with async_session_maker() as session:
        lang = await update_language(
            session, code,
            **{k: v for k, v in data.dict().items() if v is not None}
        )
        if not lang:
            raise HTTPException(status_code=404, detail="Language not found")
        
        return {"code": lang.code, "name": lang.name}


@router.delete("/languages/{code}")
async def delete_language_endpoint(code: str, username: str = Depends(verify_admin)):
    """Delete language"""
    from services.text_service import delete_language
    
    async with async_session_maker() as session:
        success = await delete_language(session, code)
        if not success:
            raise HTTPException(status_code=400, detail="Cannot delete default language")
        return {"message": "Language deleted"}


# ========== BOT TEXTS ==========

class TextUpdate(BaseModel):
    text: str
    description: Optional[str] = None


class TextKeyCreate(BaseModel):
    key: str
    description: Optional[str] = None


@router.get("/texts")
async def list_texts(username: str = Depends(verify_admin)):
    """Get all texts grouped by category"""
    from services.text_service import get_all_texts, get_all_languages, TEXT_CATEGORIES, DEFAULT_TEXTS
    
    async with async_session_maker() as session:
        texts = await get_all_texts(session)
        languages = await get_all_languages(session, active_only=False)
        
        # Group by key first
        texts_by_key = {}
        for t in texts:
            if t.key not in texts_by_key:
                texts_by_key[t.key] = {
                    "key": t.key,
                    "description": t.description,
                    "translations": {}
                }
            texts_by_key[t.key]["translations"][t.language] = t.text
        
        # Now group by category
        categories = []
        for cat_id, cat_data in TEXT_CATEGORIES.items():
            cat_texts = []
            for key in cat_data["keys"]:
                if key in texts_by_key:
                    cat_texts.append(texts_by_key[key])
                elif key in DEFAULT_TEXTS:
                    # Use default description if not in DB
                    cat_texts.append({
                        "key": key,
                        "description": DEFAULT_TEXTS[key].get("description", ""),
                        "translations": {}
                    })
            
            categories.append({
                "id": cat_id,
                "name": cat_data["name"],
                "icon": cat_data["icon"],
                "description": cat_data["description"],
                "texts": cat_texts
            })
        
        # Add uncategorized texts
        categorized_keys = set()
        for cat in TEXT_CATEGORIES.values():
            categorized_keys.update(cat["keys"])
        
        uncategorized = [t for k, t in texts_by_key.items() if k not in categorized_keys]
        if uncategorized:
            categories.append({
                "id": "other",
                "name": "Other",
                "icon": "ellipsis-h",
                "description": "Custom texts",
                "texts": uncategorized
            })
        
        return {
            "categories": categories,
            "languages": [{"code": l.code, "name": l.name, "flag": l.flag} for l in languages]
        }


@router.put("/texts/{key}/{language}")
async def update_text_endpoint(key: str, language: str, data: TextUpdate, username: str = Depends(verify_admin)):
    """Update specific text"""
    from services.text_service import update_text, refresh_texts_cache
    
    async with async_session_maker() as session:
        text = await update_text(session, key, language, data.text, data.description)
        await refresh_texts_cache(session)
        return {"key": text.key, "language": text.language, "text": text.text}


@router.post("/texts/keys")
async def create_text_key_endpoint(data: TextKeyCreate, username: str = Depends(verify_admin)):
    """Create new text key"""
    from services.text_service import create_text_key
    
    async with async_session_maker() as session:
        await create_text_key(session, data.key, data.description)
        return {"key": data.key}


@router.delete("/texts/keys/{key}")
async def delete_text_key_endpoint(key: str, username: str = Depends(verify_admin)):
    """Delete text key"""
    from services.text_service import delete_text_key
    
    async with async_session_maker() as session:
        await delete_text_key(session, key)
        return {"message": "Text key deleted"}

