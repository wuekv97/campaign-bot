# campaign-bot

Telegram bot with a **FastAPI-based web admin panel** for managing users, campaigns, broadcasts, and settings. Demonstrates a split architecture: user-facing bot (Aiogram) and internal admin UI (REST API + Jinja2 templates) sharing the same SQLite database.

---

## Architecture overview

- **Bot process:** `main.py` / `run.py bot` — Aiogram dispatcher, start handler, background task for auto-messages. Texts and languages loaded from DB into cache at startup.
- **Web process:** `run_web.py` / `run.py web` — FastAPI app with static files, Jinja2 templates, JWT-based admin auth, and `/api/*` routes for campaigns, users, broadcast, settings.
- **Database:** SQLAlchemy async (aiosqlite) with models for users, tags, campaigns, broadcasts, settings, texts, languages. Single DB for both bot and web.
- **Services:** `services/` — user, campaign, broadcast, text, settings, auto-message logic. Keeps handlers thin and testable.

---

## Tech stack

| Layer    | Technology           |
|----------|----------------------|
| Bot      | Aiogram 3.x          |
| Web      | FastAPI, Jinja2, Uvicorn |
| DB       | SQLAlchemy 2 (async), aiosqlite |
| Auth     | python-jose (JWT), passlib (bcrypt) |
| Config   | python-dotenv, .env  |

---

## Installation

1. **Clone and install:**
   ```bash
   git clone <repo-url>
   cd campaign-bot
   pip install -r requirements.txt
   ```

2. **Environment:** Copy `.env.example` to `.env`. Set at least:
   - `BOT_TOKEN`, `ADMIN_IDS`
   - `DATABASE_URL` (default: `sqlite+aiosqlite:///data/bot.db`)
   - `WEB_ADMIN_USERNAME`, `WEB_ADMIN_PASSWORD`

3. **Run both:**
   ```bash
   python run.py all
   ```
   Or separately: `python run.py bot` and `python run.py web`. Web panel: http://localhost:8000

---

## Example usage

- **User:** `/start` → language selection → main menu; optional subscription gate and promo deep link.
- **Admin (web):** Login → dashboard (stats), manage campaigns, users, broadcast messages, edit settings and localized texts.

---

## Folder structure

```
campaign-bot/
├── main.py, run.py, run_web.py
├── config.py, database.py, models.py
├── docs/
├── handlers/
├── keyboards/
├── services/
├── tasks/
├── web/
├── scripts/
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## Key engineering decisions

- **Single async DB for bot and web:** One source of truth; services layer used by both.
- **Texts and languages in DB:** Admin can change copy and add languages without code deploy.
- **JWT for web admin:** Stateless auth; password hashed with bcrypt.
- **Unified runner:** `run.py all` starts bot and web together for local/dev.

---

## Lessons learned

- Caching texts/languages at bot startup avoids DB hit on every message and keeps response time low.
- FastAPI + Jinja2 is enough for an internal admin UI without a separate front-end framework.
- Clear separation between handlers (Telegram) and services (business logic) simplifies adding new features and tests.

---

## License

Private / Internal use.
