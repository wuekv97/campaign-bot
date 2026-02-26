"""
Handlers for /start command and onboarding
"""
import json
import logging
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from database import async_session_maker
from services.user_service import get_or_create_user, update_user_language, add_tag_to_user, get_user
from services.campaign_service import get_campaign_by_code, activate_campaign_for_user, user_has_campaign
from services.settings_service import get_setting
from keyboards.inline import get_language_keyboard, get_main_menu_keyboard, get_subscribe_keyboard
from locales import get_text
from config import DEFAULT_LANGUAGE, REQUIRED_CHANNEL, CHANNEL_LINK, PROMO_CODE, ACTIVATION_LINK

logger = logging.getLogger(__name__)
router = Router()


class OnboardingStates(StatesGroup):
    """States for offer onboarding"""
    waiting_for_subscription = State()


async def check_subscription(user_id: int, bot) -> bool:
    """Check if user is subscribed to channel"""
    if not REQUIRED_CHANNEL:
        return True
    
    try:
        member = await bot.get_chat_member(chat_id=REQUIRED_CHANNEL, user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        logger.error(f"Subscription check error: {e}")
        return False


async def send_campaign_message(message: Message, campaign, user_language: str):
    """Send campaign message with media and buttons"""
    text = campaign.get_message(user_language)
    if not text:
        return
    
    # Build keyboard from buttons_json
    keyboard = None
    if campaign.buttons_json:
        try:
            buttons_data = json.loads(campaign.buttons_json)
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=btn['text'], url=btn['url'])]
                for btn in buttons_data
            ])
        except:
            pass
    
    # Send with media if exists
    if campaign.media_type and campaign.media_file_id:
        if campaign.media_type == 'photo':
            await message.answer_photo(
                photo=campaign.media_file_id,
                caption=text,
                parse_mode='HTML',
                reply_markup=keyboard
            )
        elif campaign.media_type == 'video':
            await message.answer_video(
                video=campaign.media_file_id,
                caption=text,
                parse_mode='HTML',
                reply_markup=keyboard
            )
    else:
        await message.answer(
            text,
            parse_mode='HTML',
            reply_markup=keyboard
        )


@router.message(CommandStart())
async def cmd_start(message: Message, bot, state: FSMContext):
    """Handler for /start command"""
    async with async_session_maker() as session:
        # Get payload if exists
        args = message.text.split(maxsplit=1)
        payload = args[1] if len(args) > 1 else None
        
        # Determine source and campaign from payload
        source = None
        campaign_code = None
        
        if payload:
            if payload.startswith("offer_"):
                campaign_code = payload
                source = payload  # Use offer code as source for tracking
            else:
                source = payload
        
        logger.info(f"Start command: user={message.from_user.id}, payload={payload}, campaign_code={campaign_code}, source={source}")
        
        # Check if user exists
        existing_user = await get_user(session, message.from_user.id)
        
        # New user - language selection first
        if not existing_user:
            await state.update_data(campaign_code=campaign_code, source=source)
            await message.answer(
                get_text(DEFAULT_LANGUAGE, "welcome"),
                reply_markup=get_language_keyboard()
            )
            return
        
        # Existing user - update data
        user, is_new = await get_or_create_user(
            session=session,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            full_name=message.from_user.full_name,
            source=source,
            language=existing_user.language
        )
        
        if source and not is_new:
            await add_tag_to_user(session, user, source)
        
        if campaign_code:
            await state.update_data(campaign_code=campaign_code)
        
        # Show subscription check
        user_name = message.from_user.first_name or "friend"
        
        text = (
            f"{get_text(user.language, 'hello', name=user_name)}\n\n"
            f"{get_text(user.language, 'subscribe_channel')}\n\n"
            f"{get_text(user.language, 'join_now')}"
        )
        
        await message.answer(
            text,
            reply_markup=get_subscribe_keyboard(CHANNEL_LINK, user.language)
        )


async def handle_campaign(
    message: Message,
    session: AsyncSession,
    user,
    campaign_code: str
):
    """Handle campaign activation"""
    campaign = await get_campaign_by_code(session, campaign_code)
    
    if not campaign:
        logger.warning(f"Campaign {campaign_code} not found")
        await message.answer(get_text(user.language, "offer_expired"))
        return
    
    if not campaign.is_currently_active():
        await message.answer(get_text(user.language, "offer_expired"))
        return
    
    already_activated = await user_has_campaign(session, user, campaign)
    
    if already_activated:
        await message.answer(get_text(user.language, "offer_already_activated"))
        return
    
    # Activate campaign
    await activate_campaign_for_user(session, user, campaign)
    await add_tag_to_user(session, user, campaign_code)
    
    # Send bonus message
    await send_campaign_message(message, campaign, user.language)


@router.callback_query(F.data == "check_subscription")
async def callback_check_subscription(callback: CallbackQuery, bot, state: FSMContext):
    """Subscription check handler"""
    if await check_subscription(callback.from_user.id, bot):
        state_data = await state.get_data()
        campaign_code = state_data.get('campaign_code')
        
        logger.info(f"Subscription confirmed: user={callback.from_user.id}, campaign_code={campaign_code}, state_data={state_data}")
        
        async with async_session_maker() as session:
            user = await get_user(session, callback.from_user.id)
            
            if not user:
                user, is_new = await get_or_create_user(
                    session=session,
                    telegram_id=callback.from_user.id,
                    username=callback.from_user.username,
                    full_name=callback.from_user.full_name,
                    language=DEFAULT_LANGUAGE
                )
            
            user_language = user.language if user else DEFAULT_LANGUAGE
            
            await callback.message.edit_text(
                get_text(user_language, "thank_you_subscription")
            )
            
            if campaign_code:
                await handle_campaign(callback.message, session, user, campaign_code)
                await state.clear()
            else:
                # Show default promo code
                promo_code = await get_setting(session, "PROMO_CODE", PROMO_CODE)
                activation_link = await get_setting(session, "ACTIVATION_LINK", ACTIVATION_LINK)
                
                promo_text = get_text(user_language, "promo_code_message", promo_code=promo_code)
                
                activation_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(
                        text=get_text(user_language, "activate_button"),
                        url=activation_link
                    )]
                ])
                
                await callback.message.answer(
                    promo_text,
                    reply_markup=activation_keyboard
                )
    else:
        async with async_session_maker() as session:
            user = await get_user(session, callback.from_user.id)
            user_language = user.language if user else DEFAULT_LANGUAGE
        
        await callback.answer(
            get_text(user_language, "not_subscribed"),
            show_alert=True
        )


@router.callback_query(F.data.startswith("lang_"))
async def callback_language_select(callback: CallbackQuery, state: FSMContext):
    """Language selection handler"""
    language = callback.data.split("_")[1]
    
    state_data = await state.get_data()
    campaign_code = state_data.get('campaign_code')
    source = state_data.get('source')
    
    logger.info(f"Language selected: user={callback.from_user.id}, lang={language}, campaign_code={campaign_code}, source={source}")
    
    async with async_session_maker() as session:
        existing_user = await get_user(session, callback.from_user.id)
        
        if not existing_user:
            user, is_new = await get_or_create_user(
                session=session,
                telegram_id=callback.from_user.id,
                username=callback.from_user.username,
                full_name=callback.from_user.full_name,
                source=source,
                language=language
            )
            
            if source and is_new:
                await add_tag_to_user(session, user, source)
        else:
            user = await update_user_language(
                session=session,
                telegram_id=callback.from_user.id,
                language=language
            )
        
        if user:
            await callback.message.edit_text(
                get_text(language, "language_selected")
            )
            
            # IMPORTANT: Keep campaign_code in state for subscription check
            if campaign_code:
                await state.update_data(campaign_code=campaign_code)
                logger.info(f"Kept campaign_code in state: {campaign_code}")
            
            # Show subscription check
            user_name = callback.from_user.first_name or "friend"
            
            text = (
                f"{get_text(language, 'hello', name=user_name)}\n\n"
                f"{get_text(language, 'subscribe_channel')}\n\n"
                f"{get_text(language, 'join_now')}"
            )
            
            await callback.message.answer(
                text,
                reply_markup=get_subscribe_keyboard(CHANNEL_LINK, language)
            )
        
    await callback.answer()


@router.message(Command("language"))
async def cmd_language(message: Message):
    """Language change command"""
    async with async_session_maker() as session:
        user = await get_user(session, message.from_user.id)
        
        lang = user.language if user else DEFAULT_LANGUAGE
        await message.answer(
            get_text(lang, "language_prompt"),
            reply_markup=get_language_keyboard()
        )


@router.callback_query(F.data == "settings")
async def callback_settings(callback: CallbackQuery):
    """Settings handler"""
    async with async_session_maker() as session:
        user = await get_user(session, callback.from_user.id)
        
        if user:
            from keyboards.inline import get_settings_keyboard
            await callback.message.edit_text(
                get_text(user.language, "settings"),
                reply_markup=get_settings_keyboard(user.language)
            )
    
    await callback.answer()


@router.callback_query(F.data == "change_language")
async def callback_change_language(callback: CallbackQuery):
    """Language change from settings handler"""
    async with async_session_maker() as session:
        user = await get_user(session, callback.from_user.id)
        
        if user:
            await callback.message.edit_text(
                get_text(user.language, "language_prompt"),
                reply_markup=get_language_keyboard()
            )
    
    await callback.answer()
