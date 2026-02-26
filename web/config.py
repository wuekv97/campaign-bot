"""
Конфигурация веб-админпанели
"""
import os
from typing import List
from dotenv import load_dotenv

# Загружаем переменные окружения из .env
load_dotenv()

# Секретный ключ для JWT токенов (генерируйте свой!)
SECRET_KEY = os.getenv("WEB_SECRET_KEY", "your-secret-key-change-in-production-please-use-env-file")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 часа

# Учетные данные администраторов
# Формат: {"username": "password"}
ADMINS = {
    os.getenv("WEB_ADMIN_USERNAME", "admin"): os.getenv("WEB_ADMIN_PASSWORD", "change_this_password_123"),
}

# Legacy support
ADMIN_USERNAME = os.getenv("WEB_ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("WEB_ADMIN_PASSWORD", "change_this_password_123")

# Разрешенные IP адреса (оставьте пустым для доступа отовсюду)
# Пример: ALLOWED_IPS = ["127.0.0.1", "192.168.1.100"]
ALLOWED_IPS: List[str] = []

# Хост и порт
HOST = os.getenv("WEB_HOST", "0.0.0.0")
PORT = int(os.getenv("WEB_PORT", "8000"))

# CORS (для разработки)
CORS_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

