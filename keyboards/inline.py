"""
Inline keyboards for bot
"""
from typing import List, Dict
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import SUPPORTED_LANGUAGES
from locales import get_text

# Languages cache (set from main.py after loading from DB)
_languages_cache: List[Dict] = []


def set_languages_cache(languages: List[Dict]):
    """Set languages cache (called from main.py)"""
    global _languages_cache
    _languages_cache = languages


def get_languages_for_keyboard() -> Dict[str, str]:
    """Get languages for keyboard - from cache or fallback to config"""
    if _languages_cache:
        return {l['code']: f"{l['flag']} {l['name']}" for l in _languages_cache if l.get('is_active', True)}
    return SUPPORTED_LANGUAGES


def get_language_keyboard() -> InlineKeyboardMarkup:
    """Language selection keyboard"""
    buttons = []
    languages = get_languages_for_keyboard()
    
    for code, name in languages.items():
        buttons.append([InlineKeyboardButton(
            text=name,
            callback_data=f"lang_{code}"
        )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_main_menu_keyboard(language: str) -> InlineKeyboardMarkup:
    """Главное меню"""
    buttons = [
        [InlineKeyboardButton(
            text=get_text(language, "settings"),
            callback_data="settings"
        )]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_settings_keyboard(language: str) -> InlineKeyboardMarkup:
    """Меню настроек"""
    buttons = [
        [InlineKeyboardButton(
            text=get_text(language, "change_language"),
            callback_data="change_language"
        )]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_broadcast_language_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора языка для рассылки"""
    buttons = []
    
    # Кнопка "Все языки"
    buttons.append([InlineKeyboardButton(
        text="🌐 Все языки",
        callback_data="broadcast_lang_all"
    )])
    
    # Кнопки для каждого языка
    for code, name in SUPPORTED_LANGUAGES.items():
        buttons.append([InlineKeyboardButton(
            text=name,
            callback_data=f"broadcast_lang_{code}"
        )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_broadcast_source_keyboard(sources: List[str]) -> InlineKeyboardMarkup:
    """Клавиатура выбора источника для рассылки"""
    buttons = []
    
    # Кнопка "Все источники"
    buttons.append([InlineKeyboardButton(
        text="📱 Все источники",
        callback_data="broadcast_source_all"
    )])
    
    # Кнопки для каждого источника
    for source in sources:
        if source:  # Игнорируем пустые источники
            buttons.append([InlineKeyboardButton(
                text=f"📍 {source}",
                callback_data=f"broadcast_source_{source}"
            )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_broadcast_tags_keyboard(tags: List[str]) -> InlineKeyboardMarkup:
    """Клавиатура выбора тегов для рассылки"""
    buttons = []
    
    # Кнопка "Без фильтра по тегам"
    buttons.append([InlineKeyboardButton(
        text="⏩ Пропустить",
        callback_data="broadcast_tags_skip"
    )])
    
    # Кнопки для каждого тега
    for tag in tags:
        buttons.append([InlineKeyboardButton(
            text=f"🏷 {tag}",
            callback_data=f"broadcast_tag_{tag}"
        )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_broadcast_confirm_keyboard(language: str = "en") -> InlineKeyboardMarkup:
    """Клавиатура подтверждения рассылки"""
    buttons = [
        [
            InlineKeyboardButton(
                text=get_text(language, "broadcast_yes"),
                callback_data="broadcast_confirm_yes"
            ),
            InlineKeyboardButton(
                text=get_text(language, "broadcast_no"),
                callback_data="broadcast_confirm_no"
            )
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_campaign_confirm_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура подтверждения создания кампании"""
    buttons = [
        [
            InlineKeyboardButton(
                text="✅ Создать кампанию",
                callback_data="campaign_confirm_yes"
            )
        ],
        [
            InlineKeyboardButton(
                text="❌ Отменить",
                callback_data="campaign_confirm_no"
            )
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_campaign_edit_keyboard(campaign_code: str, has_media: bool = False) -> InlineKeyboardMarkup:
    """Клавиатура редактирования кампании"""
    buttons = [
        [
            InlineKeyboardButton(
                text="📝 Изменить название",
                callback_data=f"edit_camp_title_{campaign_code}"
            )
        ],
        [
            InlineKeyboardButton(
                text="⏱ Продлить срок",
                callback_data=f"edit_camp_extend_{campaign_code}"
            )
        ],
        [
            InlineKeyboardButton(
                text="🇵🇹 Изменить сообщение (PT)",
                callback_data=f"edit_camp_msg_pt_{campaign_code}"
            )
        ],
        [
            InlineKeyboardButton(
                text="🇭🇺 Изменить сообщение (HU)",
                callback_data=f"edit_camp_msg_hu_{campaign_code}"
            )
        ],
        [
            InlineKeyboardButton(
                text="🇬🇧 Изменить сообщение (EN)",
                callback_data=f"edit_camp_msg_en_{campaign_code}"
            )
        ],
        [
            InlineKeyboardButton(
                text="🖼 Изменить медиа" if has_media else "📷 Добавить медиа",
                callback_data=f"edit_camp_media_{campaign_code}"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔘 Управление кнопками",
                callback_data=f"edit_camp_buttons_{campaign_code}"
            )
        ],
        [
            InlineKeyboardButton(
                text="✅ Активировать" if False else "❌ Деактивировать",
                callback_data=f"edit_camp_toggle_{campaign_code}"
            )
        ],
        [
            InlineKeyboardButton(
                text="◀️ Назад",
                callback_data=f"camp_back_{campaign_code}"
            )
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_campaign_list_keyboard(campaigns: list, show_edit: bool = True) -> InlineKeyboardMarkup:
    """Клавиатура со списком кампаний"""
    buttons = []
    
    for campaign in campaigns:
        status = "✅" if campaign.is_currently_active() else "❌"
        button_text = f"{status} {campaign.title[:30]}"
        
        if show_edit:
            buttons.append([
                InlineKeyboardButton(
                    text=button_text,
                    callback_data=f"view_campaign_{campaign.code}"
                )
            ])
        else:
            buttons.append([
                InlineKeyboardButton(
                    text=button_text,
                    callback_data=f"select_campaign_{campaign.code}"
                )
            ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_subscribe_keyboard(channel_link: str, language: str = "en") -> InlineKeyboardMarkup:
    """Клавиатура для проверки подписки на канал"""
    from locales import get_text
    
    buttons = [
        [InlineKeyboardButton(
            text=get_text(language, "subscribe_button"),
            url=channel_link
        )],
        [InlineKeyboardButton(
            text=get_text(language, "subscribed_button"),
            callback_data="check_subscription"
        )]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

