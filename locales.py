"""
Localization - bot texts on different languages
Loads from database, with fallback to defaults
"""
from typing import Dict

# Default texts - used as fallback and for initialization
DEFAULT_TEXTS = {
    "pt": {
        "welcome": "👋 Bem-vindo! Escolha o seu idioma:",
        "hello": "Olá, {name}!",
        "subscribe_channel": "Inscreva-se no nosso canal para obter seu bônus 🤑",
        "join_now": "Junte-se agora 👇 Clique no link abaixo para seguir",
        "subscribe_button": "Inscrever-se",
        "subscribed_button": "Já me inscrevi",
        "thank_you_subscription": "🧡 Obrigado pela inscrição! 🧡",
        "promo_code_message": "➡️  Sua promoção FS sem depósito - {promo_code}\n\nAtive-a na página da sua conta!",
        "activate_button": "USAR BÔNUS FS AGORA",
        "not_subscribed": "❌ Você ainda não se inscreveu no canal!\n\nPor favor, inscreva-se e clique no botão novamente.",
        "language_selected": "✅ Idioma alterado com sucesso para Português",
        "language_prompt": "🌐 Escolha o idioma:",
        "offer_expired": "😔 Infelizmente, esta oferta não está mais disponível",
        "offer_already_activated": "ℹ️ Você já ativou este bônus",
    },
    "en": {
        "welcome": "👋 Welcome! Choose your language:",
        "hello": "Hello, {name}!",
        "subscribe_channel": "Subscribe to our channel to get your bonus 🤑",
        "join_now": "Join now 👇 Click link below to follow",
        "subscribe_button": "Subscribe",
        "subscribed_button": "I have subscribed",
        "thank_you_subscription": "🧡 Thank you for the subscription 🧡",
        "promo_code_message": "➡️  Your no-deposit FS promo - {promo_code}\n\nActivate it in your account page!",
        "activate_button": "USE BONUS FS NOW",
        "not_subscribed": "❌ You haven't subscribed to the channel yet!\n\nPlease subscribe and click the button again.",
        "language_selected": "✅ Language successfully changed to English",
        "language_prompt": "🌐 Choose language:",
        "offer_expired": "😔 Unfortunately, this offer is no longer available",
        "offer_already_activated": "ℹ️ You have already activated this bonus",
    },
    "hu": {
        "welcome": "👋 Üdvözöljük! Válassza ki a nyelvét:",
        "hello": "Helló, {name}!",
        "subscribe_channel": "Iratkozzon fel csatornánkra a bónuszért 🤑",
        "join_now": "Csatlakozzon most 👇 Kattintson az alábbi linkre",
        "subscribe_button": "Feliratkozás",
        "subscribed_button": "Már feliratkoztam",
        "thank_you_subscription": "🧡 Köszönjük a feliratkozást! 🧡",
        "promo_code_message": "➡️  Az Ön befizetés nélküli FS promóciója - {promo_code}\n\nAktiválja a fiók oldalán!",
        "activate_button": "BÓNUSZ FS HASZNÁLATA MOST",
        "not_subscribed": "❌ Még nem iratkozott fel a csatornára!\n\nKérjük, iratkozzon fel és kattintson újra a gombra.",
        "language_selected": "✅ A nyelv sikeresen megváltoztatva Magyarra",
        "language_prompt": "🌐 Válasszon nyelvet:",
        "offer_expired": "😔 Sajnos ez az ajánlat már nem elérhető",
        "offer_already_activated": "ℹ️ Ön már aktiválta ezt a bónuszt",
    }
}

# In-memory cache of texts from database
_db_texts_cache: Dict[str, Dict[str, str]] = {}


def set_texts_cache(texts: Dict[str, Dict[str, str]]):
    """Set texts cache (called from main.py after loading from DB)"""
    global _db_texts_cache
    _db_texts_cache = texts


def get_text(language: str, key: str, **kwargs) -> str:
    """
    Get text in the required language with parameter substitution
    First tries database cache, then falls back to defaults
    
    Args:
        language: Language code (en, pt, hu)
        key: Text key
        **kwargs: Parameters for formatting
    
    Returns:
        Formatted text
    """
    # Try database cache first
    if _db_texts_cache:
        if language not in _db_texts_cache:
            language = "en"
        
        text = _db_texts_cache.get(language, {}).get(key)
        if text:
            if kwargs:
                try:
                    return text.format(**kwargs)
                except KeyError:
                    return text
            return text
    
    # Fallback to defaults
    if language not in DEFAULT_TEXTS:
        language = "en"
    
    text = DEFAULT_TEXTS.get(language, {}).get(key, DEFAULT_TEXTS["en"].get(key, key))
    
    if kwargs:
        try:
            return text.format(**kwargs)
        except KeyError:
            return text
    return text
