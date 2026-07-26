import os
import logging
import sqlite3

from config import DB_PATH

logger = logging.getLogger(__name__)


def init_db() -> None:
    """Create the users table if it doesn't exist yet."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id     INTEGER PRIMARY KEY,
                username        TEXT,
                full_name       TEXT,
                language        TEXT,
                joined_at       TEXT DEFAULT (datetime('now')),
                last_active     TEXT DEFAULT (datetime('now')),
                downloads_count INTEGER DEFAULT 0,
                is_active       INTEGER DEFAULT 1
            )
        """)
    logger.info("Database ready at %s", DB_PATH)


def upsert_user(
        telegram_id: int,
        username: str | None,
        full_name: str | None,
        language: str | None,
) -> None:
    """Insert a new user, or update an existing one's details and activity."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            INSERT INTO users (telegram_id, username, full_name, language)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(telegram_id) DO UPDATE SET
                username    = excluded.username,
                full_name   = excluded.full_name,
                language    = excluded.language,
                last_active = datetime('now'),
                is_active   = 1
        """, (telegram_id, username, full_name, language))
