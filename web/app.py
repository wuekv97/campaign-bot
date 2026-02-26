"""
Главный файл веб-админпанели
"""
import logging
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from web.config import CORS_ORIGINS
from web.api import router as api_router
from web.auth import verify_admin

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создание приложения
app = FastAPI(
    title="Bot Admin Panel",
    description="Веб-админпанель для управления Telegram ботом",
    version="1.0.0"
)

# Exception handler для 401 ошибок
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    # Если 401 и это HTML запрос (не API), редирект на логин
    if exc.status_code == 401:
        accept = request.headers.get("accept", "")
        if "text/html" in accept and not request.url.path.startswith("/api"):
            return RedirectResponse(url="/login", status_code=303)
    
    # Иначе возвращаем стандартный JSON ответ
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение статических файлов и шаблонов
app.mount("/static", StaticFiles(directory="web/static"), name="static")
templates = Jinja2Templates(directory="web/templates")

# Подключение API роутера
app.include_router(api_router, prefix="/api", tags=["API"])


# ========== СТРАНИЦЫ ==========

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Страница логина"""
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/", response_class=HTMLResponse)
async def index(request: Request, username: str = Depends(verify_admin)):
    """Главная страница - Dashboard"""
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "username": username}
    )


@app.get("/campaigns", response_class=HTMLResponse)
async def campaigns_page(request: Request, username: str = Depends(verify_admin)):
    """Страница управления кампаниями"""
    return templates.TemplateResponse(
        "campaigns.html",
        {"request": request, "username": username}
    )


@app.get("/campaigns/create", response_class=HTMLResponse)
async def create_campaign_page(request: Request, username: str = Depends(verify_admin)):
    """Страница создания кампании"""
    return templates.TemplateResponse(
        "campaign_create.html",
        {"request": request, "username": username}
    )


@app.get("/campaigns/edit/{code}", response_class=HTMLResponse)
async def edit_campaign_page(request: Request, code: str, username: str = Depends(verify_admin)):
    """Страница редактирования кампании"""
    return templates.TemplateResponse(
        "campaign_edit.html",
        {"request": request, "username": username, "code": code}
    )


@app.get("/users", response_class=HTMLResponse)
async def users_page(request: Request, username: str = Depends(verify_admin)):
    """Страница пользователей"""
    return templates.TemplateResponse(
        "users.html",
        {"request": request, "username": username}
    )


@app.get("/broadcast", response_class=HTMLResponse)
async def broadcast_page(request: Request, username: str = Depends(verify_admin)):
    """Страница broadcast"""
    return templates.TemplateResponse(
        "broadcast.html",
        {"request": request, "username": username}
    )


@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request, username: str = Depends(verify_admin)):
    """Страница настроек"""
    return templates.TemplateResponse(
        "settings.html",
        {"request": request, "username": username}
    )


@app.get("/texts", response_class=HTMLResponse)
async def texts_page(request: Request, username: str = Depends(verify_admin)):
    """Bot texts editor page"""
    return templates.TemplateResponse(
        "texts.html",
        {"request": request, "username": username}
    )


@app.get("/languages", response_class=HTMLResponse)
async def languages_page(request: Request, username: str = Depends(verify_admin)):
    """Languages management page"""
    return templates.TemplateResponse(
        "languages.html",
        {"request": request, "username": username}
    )


# ========== HEALTH CHECK ==========

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    from web.config import HOST, PORT
    
    logger.info(f"Starting web admin panel on {HOST}:{PORT}")
    uvicorn.run(app, host=HOST, port=PORT)

