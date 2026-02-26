#!/usr/bin/env python3
"""
Database backup script
Run daily via cron: 0 0 * * * /path/to/python /path/to/backup.py
"""
import shutil
import os
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
BACKUP_DIR = PROJECT_ROOT / "backups"
DB_FILE = DATA_DIR / "bot.db"

# Keep last 7 days of backups
MAX_BACKUPS = 7


def backup_database():
    """Create timestamped backup of database"""
    if not DB_FILE.exists():
        print(f"❌ Database not found: {DB_FILE}")
        return
    
    # Create backup directory
    BACKUP_DIR.mkdir(exist_ok=True)
    
    # Create backup with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = BACKUP_DIR / f"bot_{timestamp}.db"
    
    shutil.copy2(DB_FILE, backup_file)
    print(f"✅ Backup created: {backup_file}")
    
    # Clean old backups
    backups = sorted(BACKUP_DIR.glob("bot_*.db"), reverse=True)
    for old_backup in backups[MAX_BACKUPS:]:
        old_backup.unlink()
        print(f"🗑️ Removed old backup: {old_backup.name}")


def restore_latest():
    """Restore from latest backup"""
    backups = sorted(BACKUP_DIR.glob("bot_*.db"), reverse=True)
    
    if not backups:
        print("❌ No backups found!")
        return
    
    latest = backups[0]
    print(f"📦 Restoring from: {latest.name}")
    
    # Backup current DB first
    if DB_FILE.exists():
        current_backup = DATA_DIR / "bot_before_restore.db"
        shutil.copy2(DB_FILE, current_backup)
        print(f"📋 Current DB backed up to: {current_backup}")
    
    shutil.copy2(latest, DB_FILE)
    print(f"✅ Database restored!")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "restore":
        restore_latest()
    else:
        backup_database()





