#!/usr/bin/env python3
"""
Unified entry point for bot and web panel
Usage:
    python run.py bot      - Start bot only
    python run.py web      - Start web panel only
    python run.py all      - Start both (default)
"""
import asyncio
import subprocess
import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))


def run_bot():
    """Run the Telegram bot"""
    print("🤖 Starting bot...")
    os.system(f"{sys.executable} main.py")


def run_web():
    """Run the web admin panel"""
    print("🌐 Starting web panel on http://localhost:8000")
    os.system(f"{sys.executable} run_web.py")


async def run_all():
    """Run both bot and web panel"""
    import signal
    
    print("🚀 Starting Campaign Bot & Web Panel")
    print("=" * 40)
    
    # Start both processes
    bot_process = subprocess.Popen(
        [sys.executable, "main.py"],
        cwd=PROJECT_ROOT
    )
    
    web_process = subprocess.Popen(
        [sys.executable, "run_web.py"],
        cwd=PROJECT_ROOT
    )
    
    print("✅ Bot started (PID: {})".format(bot_process.pid))
    print("✅ Web panel started (PID: {})".format(web_process.pid))
    print("=" * 40)
    print("🌐 Web panel: http://localhost:8000")
    print("Press Ctrl+C to stop all services")
    
    def cleanup(signum, frame):
        print("\n🛑 Stopping services...")
        bot_process.terminate()
        web_process.terminate()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    
    # Wait for processes
    bot_process.wait()
    web_process.wait()


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    
    if mode == "bot":
        run_bot()
    elif mode == "web":
        run_web()
    elif mode == "all":
        asyncio.run(run_all())
    else:
        print("Usage: python run.py [bot|web|all]")
        print("  bot  - Start bot only")
        print("  web  - Start web panel only")
        print("  all  - Start both (default)")





