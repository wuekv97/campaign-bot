"""
Bot configuration - environment variables
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Project root
PROJECT_ROOT = Path(__file__).parent

# Bot token from BotFather
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not found in environment!")

# Admin IDs (comma separated)
ADMIN_IDS_STR = os.getenv("ADMIN_IDS", "")
if not ADMIN_IDS_STR:
    raise ValueError("ADMIN_IDS not found in environment!")
ADMIN_IDS = [int(id.strip()) for id in ADMIN_IDS_STR.split(",") if id.strip()]

# Database URL (stored in data/ folder)
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite+aiosqlite:///{PROJECT_ROOT}/data/bot.db")

# Supported languages
SUPPORTED_LANGUAGES = {
    "pt": "🇵🇹 Português",
    "hu": "🇭🇺 Magyar",
    "en": "🇬🇧 English"
}

# Default language
DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "en")

# Broadcast delay (seconds)
BROADCAST_DELAY = 0.05

# Max retry attempts
MAX_RETRY_ATTEMPTS = 3

# Required channel for subscription (e.g. @your_channel or -1001234567890)
REQUIRED_CHANNEL = os.getenv("REQUIRED_CHANNEL", "")

# Channel link for subscription
CHANNEL_LINK = os.getenv("CHANNEL_LINK", "https://t.me/yourchannel")

# Promo code for no-deposit free spins
PROMO_CODE = os.getenv("PROMO_CODE", "WELCOME30")

# Promo code activation link
ACTIVATION_LINK = os.getenv("ACTIVATION_LINK", "https://example.com/account")
