"""
Service for managing bot texts and languages
"""
from typing import Dict, List, Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from models import BotText, Language

# Text categories for organizing in admin panel
TEXT_CATEGORIES = {
    "start_command": {
        "name": "/start Command",
        "icon": "play",
        "description": "Messages when user first starts the bot",
        "keys": ["welcome", "hello", "language_prompt", "language_selected"]
    },
    "subscription_check": {
        "name": "Subscription Check",
        "icon": "bell",
        "description": "Channel subscription verification",
        "keys": ["subscribe_channel", "join_now", "subscribe_button", "subscribed_button", "not_subscribed"]
    },
    "after_subscription": {
        "name": "After Subscription",
        "icon": "gift",
        "description": "Messages after successful subscription",
        "keys": ["thank_you_subscription", "promo_code_message", "activate_button"]
    },
    "offers": {
        "name": "Offers / Campaigns",
        "icon": "tag",
        "description": "Campaign and offer related messages",
        "keys": ["offer_expired", "offer_already_activated"]
    }
}

# Default texts - used for initialization
DEFAULT_TEXTS = {
    "welcome": {
        "category": "start_command",
        "description": "First message - language selection",
        "en": "👋 Welcome! Choose your language:",
        "pt": "👋 Bem-vindo! Escolha o seu idioma:",
        "hu": "👋 Üdvözöljük! Válassza ki a nyelvét:"
    },
    "hello": {
        "category": "start_command",
        "description": "Greeting with user name. Use {name}",
        "en": "Hello, {name}!",
        "pt": "Olá, {name}!",
        "hu": "Helló, {name}!"
    },
    "language_prompt": {
        "category": "start_command",
        "description": "Prompt to choose language",
        "en": "🌐 Choose language:",
        "pt": "🌐 Escolha o idioma:",
        "hu": "🌐 Válasszon nyelvet:"
    },
    "language_selected": {
        "category": "start_command",
        "description": "Confirmation after language selection",
        "en": "✅ Language successfully changed to English",
        "pt": "✅ Idioma alterado com sucesso para Português",
        "hu": "✅ A nyelv sikeresen megváltoztatva Magyarra"
    },
    "subscribe_channel": {
        "category": "subscription_check",
        "description": "Message asking to subscribe to channel",
        "en": "Subscribe to our channel to get your bonus 🤑",
        "pt": "Inscreva-se no nosso canal para obter seu bônus 🤑",
        "hu": "Iratkozzon fel csatornánkra a bónuszért 🤑"
    },
    "join_now": {
        "category": "subscription_check",
        "description": "Call to action for subscription",
        "en": "Join Now 👇 Click link below to follow",
        "pt": "Junte-se agora 👇 Clique no link abaixo para seguir",
        "hu": "Csatlakozzon most 👇 Kattintson az alábbi linkre"
    },
    "subscribe_button": {
        "category": "subscription_check",
        "description": "Button text for channel subscription",
        "en": "Subscribe",
        "pt": "Inscrever-se",
        "hu": "Feliratkozás"
    },
    "subscribed_button": {
        "category": "subscription_check",
        "description": "Button 'I have subscribed'",
        "en": "I have subscribed",
        "pt": "Já me inscrevi",
        "hu": "Már feliratkoztam"
    },
    "not_subscribed": {
        "category": "subscription_check",
        "description": "Error - user not subscribed",
        "en": "❌ You haven't subscribed to the channel yet!\n\nPlease subscribe and click the button again.",
        "pt": "❌ Você ainda não se inscreveu no canal!\n\nPor favor, inscreva-se e clique no botão novamente.",
        "hu": "❌ Még nem iratkozott fel a csatornára!\n\nKérjük, iratkozzon fel és kattintson újra a gombra."
    },
    "thank_you_subscription": {
        "category": "after_subscription",
        "description": "Thank you message after subscription",
        "en": "🧡 Thank you for the subscription 🧡",
        "pt": "🧡 Obrigado pela inscrição! 🧡",
        "hu": "🧡 Köszönjük a feliratkozást! 🧡"
    },
    "promo_code_message": {
        "category": "after_subscription",
        "description": "Promo code message. Use {promo_code}",
        "en": "➡️  Your no-deposit FS promo - {promo_code}\n\nActivate it in your account page!",
        "pt": "➡️  Sua promoção FS sem depósito - {promo_code}\n\nAtive-a na página da sua conta!",
        "hu": "➡️  Az Ön befizetés nélküli FS promóciója - {promo_code}\n\nAktiválja a fiók oldalán!"
    },
    "activate_button": {
        "category": "after_subscription",
        "description": "Button to activate promo code",
        "en": "USE BONUS FS NOW",
        "pt": "USAR BÔNUS FS AGORA",
        "hu": "BÓNUSZ FS HASZNÁLATA MOST"
    },
    "offer_expired": {
        "category": "offers",
        "description": "Offer expired or unavailable",
        "en": "😔 Unfortunately, this offer is no longer available",
        "pt": "😔 Infelizmente, esta oferta não está mais disponível",
        "hu": "😔 Sajnos ez az ajánlat már nem elérhető"
    },
    "offer_already_activated": {
        "category": "offers",
        "description": "User already activated this offer",
        "en": "ℹ️ You have already activated this bonus",
        "pt": "ℹ️ Você já ativou este bônus",
        "hu": "ℹ️ Ön már aktiválta ezt a bónuszt"
    }
}

DEFAULT_LANGUAGES = [
    {"code": "en", "name": "English", "flag": "🇬🇧", "is_default": True, "sort_order": 1},
    {"code": "pt", "name": "Português", "flag": "🇵🇹", "is_default": False, "sort_order": 2},
    {"code": "hu", "name": "Magyar", "flag": "🇭🇺", "is_default": False, "sort_order": 3},
]


async def init_default_texts(session: AsyncSession):
    """Initialize default texts if not exist"""
    # Check if texts exist
    result = await session.execute(select(BotText).limit(1))
    if result.scalar_one_or_none():
        return  # Texts already exist
    
    # Insert default texts
    for key, data in DEFAULT_TEXTS.items():
        description = data.get("description", "")
        for lang_code in ["en", "pt", "hu"]:
            if lang_code in data:
                text = BotText(
                    key=key,
                    language=lang_code,
                    text=data[lang_code],
                    description=description
                )
                session.add(text)
    
    await session.commit()


async def init_default_languages(session: AsyncSession):
    """Initialize default languages if not exist"""
    result = await session.execute(select(Language).limit(1))
    if result.scalar_one_or_none():
        return
    
    for lang_data in DEFAULT_LANGUAGES:
        lang = Language(**lang_data)
        session.add(lang)
    
    await session.commit()


async def get_all_languages(session: AsyncSession, active_only: bool = True) -> List[Language]:
    """Get all languages"""
    query = select(Language)
    if active_only:
        query = query.where(Language.is_active == True)
    query = query.order_by(Language.sort_order)
    result = await session.execute(query)
    return list(result.scalars().all())


async def get_language(session: AsyncSession, code: str) -> Optional[Language]:
    """Get language by code"""
    result = await session.execute(
        select(Language).where(Language.code == code)
    )
    return result.scalar_one_or_none()


async def create_language(session: AsyncSession, code: str, name: str, flag: str) -> Language:
    """Create new language"""
    # Get max sort order
    result = await session.execute(select(Language.sort_order).order_by(Language.sort_order.desc()).limit(1))
    max_order = result.scalar() or 0
    
    lang = Language(
        code=code,
        name=name,
        flag=flag,
        sort_order=max_order + 1
    )
    session.add(lang)
    await session.commit()
    return lang


async def update_language(session: AsyncSession, code: str, **kwargs) -> Optional[Language]:
    """Update language"""
    lang = await get_language(session, code)
    if not lang:
        return None
    
    for key, value in kwargs.items():
        if hasattr(lang, key):
            setattr(lang, key, value)
    
    await session.commit()
    return lang


async def delete_language(session: AsyncSession, code: str) -> bool:
    """Delete language (also deletes all texts for this language)"""
    lang = await get_language(session, code)
    if not lang or lang.is_default:
        return False  # Can't delete default language
    
    # Delete texts for this language
    await session.execute(
        delete(BotText).where(BotText.language == code)
    )
    
    # Delete language
    await session.delete(lang)
    await session.commit()
    return True


async def get_all_text_keys(session: AsyncSession) -> List[str]:
    """Get all unique text keys"""
    result = await session.execute(
        select(BotText.key).distinct()
    )
    return [r for r in result.scalars().all()]


async def get_texts_for_language(session: AsyncSession, language: str) -> Dict[str, str]:
    """Get all texts for a language as dict"""
    result = await session.execute(
        select(BotText).where(BotText.language == language)
    )
    texts = result.scalars().all()
    return {t.key: t.text for t in texts}


async def get_all_texts(session: AsyncSession) -> List[BotText]:
    """Get all texts"""
    result = await session.execute(
        select(BotText).order_by(BotText.key, BotText.language)
    )
    return list(result.scalars().all())


async def get_text_by_key(session: AsyncSession, key: str, language: str) -> Optional[BotText]:
    """Get specific text"""
    result = await session.execute(
        select(BotText).where(BotText.key == key, BotText.language == language)
    )
    return result.scalar_one_or_none()


async def update_text(session: AsyncSession, key: str, language: str, text: str, description: str = None) -> BotText:
    """Update or create text"""
    existing = await get_text_by_key(session, key, language)
    
    if existing:
        existing.text = text
        if description:
            existing.description = description
    else:
        existing = BotText(
            key=key,
            language=language,
            text=text,
            description=description
        )
        session.add(existing)
    
    await session.commit()
    return existing


async def create_text_key(session: AsyncSession, key: str, description: str = None) -> bool:
    """Create new text key for all languages"""
    languages = await get_all_languages(session)
    
    for lang in languages:
        existing = await get_text_by_key(session, key, lang.code)
        if not existing:
            text = BotText(
                key=key,
                language=lang.code,
                text="",  # Empty, to be filled
                description=description
            )
            session.add(text)
    
    await session.commit()
    return True


async def delete_text_key(session: AsyncSession, key: str) -> bool:
    """Delete text key for all languages"""
    await session.execute(
        delete(BotText).where(BotText.key == key)
    )
    await session.commit()
    return True


# Cache for texts (refreshed on updates)
_texts_cache: Dict[str, Dict[str, str]] = {}


async def refresh_texts_cache(session: AsyncSession):
    """Refresh the in-memory cache of texts"""
    global _texts_cache
    _texts_cache = {}
    
    languages = await get_all_languages(session, active_only=False)
    for lang in languages:
        _texts_cache[lang.code] = await get_texts_for_language(session, lang.code)


def get_cached_text(language: str, key: str, **kwargs) -> str:
    """Get text from cache with fallback to English"""
    if language not in _texts_cache:
        language = "en"
    
    text = _texts_cache.get(language, {}).get(key)
    if not text:
        text = _texts_cache.get("en", {}).get(key, key)
    
    if kwargs:
        try:
            return text.format(**kwargs)
        except KeyError:
            return text
    return text

