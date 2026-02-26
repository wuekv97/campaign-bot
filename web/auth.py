"""
Аутентификация и авторизация
"""
import logging
import base64
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status, Request, Cookie
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext

from web.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, ADMINS, ALLOWED_IPS

# Logger
logger = logging.getLogger(__name__)

# Контекст для хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Basic Auth схема
security = HTTPBasic()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверить пароль"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Получить хеш пароля"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Создать JWT токен"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[str]:
    """Проверить JWT токен"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        return username
    except JWTError:
        return None


def check_ip_allowed(request: Request) -> bool:
    """Проверить разрешен ли IP адрес"""
    if not ALLOWED_IPS:
        # Если список пуст, разрешаем все IP
        return True
    
    client_ip = request.client.host
    return client_ip in ALLOWED_IPS


async def get_credentials_optional(request: Request) -> Optional[HTTPBasicCredentials]:
    """Получить Basic Auth credentials если есть"""
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Basic "):
        try:
            encoded = auth_header.replace("Basic ", "")
            decoded = base64.b64decode(encoded).decode('utf-8')
            username, password = decoded.split(':', 1)
            return HTTPBasicCredentials(username=username, password=password)
        except:
            pass
    return None


async def verify_admin(
    request: Request, 
    auth_credentials: Optional[str] = Cookie(None),
    credentials: Optional[HTTPBasicCredentials] = Depends(get_credentials_optional)
) -> str:
    """
    Проверить credentials администратора
    Поддерживает HTTP Basic Auth и cookie
    """
    # Проверка IP
    if not check_ip_allowed(request):
        # Редирект на страницу логина для HTML запросов
        if "text/html" in request.headers.get("accept", ""):
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url="/login", status_code=303)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied from your IP address"
        )
    
    username = None
    password = None
    
    # Сначала пробуем получить из cookie
    if auth_credentials:
        try:
            decoded = base64.b64decode(auth_credentials).decode('utf-8')
            username, password = decoded.split(':', 1)
        except Exception as e:
            pass
    
    # Если не из cookie, то из Basic Auth
    if not username and credentials:
        username = credentials.username
        password = credentials.password
    
    # Проверка username и password по словарю админов
    if not username or username not in ADMINS or ADMINS.get(username) != password:
        # Редирект на страницу логина для HTML запросов
        if "text/html" in request.headers.get("accept", ""):
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url="/login", status_code=303)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    return username


# Для более продвинутой защиты можно использовать JWT
class JWTBearer:
    """Bearer token для JWT аутентификации"""
    
    async def __call__(self, request: Request):
        # Проверка IP
        if not check_ip_allowed(request):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied from your IP address"
            )
        
        # Получаем токен из cookie или header
        token = request.cookies.get("access_token")
        
        if not token:
            # Пробуем из Authorization header
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.replace("Bearer ", "")
        
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated"
            )
        
        username = verify_token(token)
        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        return username

