#!/usr/bin/env python3
"""
Скрипт запуска веб-админпанели
"""
import sys
import os

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    import uvicorn
    from web.config import HOST, PORT
    
    print("""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║            🎰 BOT WEB ADMIN PANEL STARTING...                ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝

📍 Server: http://{host}:{port}
🔐 Login with your credentials (from .env or web/config.py)
📖 API Docs: http://{host}:{port}/docs

Press CTRL+C to stop
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """.format(host=HOST if HOST != "0.0.0.0" else "localhost", port=PORT))
    
    uvicorn.run(
        "web.app:app",
        host=HOST,
        port=PORT,
        reload=True,  # Auto-reload при изменении файлов
        log_level="info"
    )

