import aiosqlite
from datetime import datetime
from config import DB_PATH, DEFAULT_BANNED_WORDS

CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS users (
    telegram_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    joined_at TEXT
);

CREATE TABLE IF NOT EXISTS group_members (
    chat_id INTEGER,
    telegram_id INTEGER,
    warn_count INTEGER DEFAULT 0,
    is_muted INTEGER DEFAULT 0,
    is_banned INTEGER DEFAULT 0,
    joined_at TEXT,
    PRIMARY KEY (chat_id, telegram_id)
);

CREATE TABLE IF NOT EXISTS group_settings (
    chat_id INTEGER PRIMARY KEY,
    rules_text TEXT DEFAULT '',
    captcha_enabled INTEGER DEFAULT 1,
    link_filter_enabled INTEGER DEFAULT 1,
    flood_filter_enabled INTEGER DEFAULT 1,
    welcome_message TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS banned_words (
    chat_id INTEGER,
    word TEXT,
    PRIMARY KEY (chat_id, word)
);

CREATE TABLE IF NOT EXISTS message_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER,
    telegram_id INTEGER,
    text TEXT,
    timestamp TEXT
);
"""


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(CREATE_TABLES_SQL)
        await db.commit()


async def ensure_group_settings(chat_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO group_settings (chat_id) VALUES (?)", (chat_id,)
        )
        await db.commit()
        # Standart so'zlarni birinchi marta qo'shish
        cur = await db.execute(
            "SELECT COUNT(*) FROM banned_words WHERE chat_id=?", (chat_id,)
        )
        count = (await cur.fetchone())[0]
        if count == 0:
            for word in DEFAULT_BANNED_WORDS:
                await db.execute(
                    "INSERT OR IGNORE INTO banned_words (chat_id, word) VALUES (?, ?)",
                    (chat_id, word.lower()),
                )
            await db.commit()


async def upsert_user(telegram_id: int, username: str, first_name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO users (telegram_id, username, first_name, joined_at)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(telegram_id) DO UPDATE SET username=excluded.username, first_name=excluded.first_name""",
            (telegram_id, username, first_name, datetime.utcnow().isoformat()),
        )
        await db.commit()


async def ensure_group_member(chat_id: int, telegram_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT OR IGNORE INTO group_members (chat_id, telegram_id, joined_at)
               VALUES (?, ?, ?)""",
            (chat_id, telegram_id, datetime.utcnow().isoformat()),
        )
        await db.commit()


async def add_warn(chat_id: int, telegram_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """UPDATE group_members SET warn_count = warn_count + 1
               WHERE chat_id=? AND telegram_id=?""",
            (chat_id, telegram_id),
        )
        await db.commit()
        cur = await db.execute(
            "SELECT warn_count FROM group_members WHERE chat_id=? AND telegram_id=?",
            (chat_id, telegram_id),
        )
        row = await cur.fetchone()
        return row[0] if row else 0


async def reset_warns(chat_id: int, telegram_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE group_members SET warn_count=0 WHERE chat_id=? AND telegram_id=?",
            (chat_id, telegram_id),
        )
        await db.commit()


async def set_banned(chat_id: int, telegram_id: int, banned: bool):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE group_members SET is_banned=? WHERE chat_id=? AND telegram_id=?",
            (int(banned), chat_id, telegram_id),
        )
        await db.commit()


async def get_banned_words(chat_id: int) -> list[str]:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT word FROM banned_words WHERE chat_id=?", (chat_id,)
        )
        rows = await cur.fetchall()
        return [r[0] for r in rows]


async def add_banned_word(chat_id: int, word: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO banned_words (chat_id, word) VALUES (?, ?)",
            (chat_id, word.lower()),
        )
        await db.commit()


async def remove_banned_word(chat_id: int, word: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "DELETE FROM banned_words WHERE chat_id=? AND word=?",
            (chat_id, word.lower()),
        )
        await db.commit()


async def set_rules(chat_id: int, text: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE group_settings SET rules_text=? WHERE chat_id=?", (text, chat_id)
        )
        await db.commit()


async def get_rules(chat_id: int) -> str:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT rules_text FROM group_settings WHERE chat_id=?", (chat_id,)
        )
        row = await cur.fetchone()
        return row[0] if row else ""


async def toggle_setting(chat_id: int, field: str, value: bool):
    """field: 'captcha_enabled' | 'link_filter_enabled' | 'flood_filter_enabled'"""
    allowed = {"captcha_enabled", "link_filter_enabled", "flood_filter_enabled"}
    if field not in allowed:
        raise ValueError("Noto'g'ri sozlama nomi")
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            f"UPDATE group_settings SET {field}=? WHERE chat_id=?",
            (int(value), chat_id),
        )
        await db.commit()


async def get_settings(chat_id: int) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """SELECT captcha_enabled, link_filter_enabled, flood_filter_enabled, rules_text, welcome_message
               FROM group_settings WHERE chat_id=?""",
            (chat_id,),
        )
        row = await cur.fetchone()
        if not row:
            return {
                "captcha_enabled": True,
                "link_filter_enabled": True,
                "flood_filter_enabled": True,
                "rules_text": "",
                "welcome_message": "",
            }
        return {
            "captcha_enabled": bool(row[0]),
            "link_filter_enabled": bool(row[1]),
            "flood_filter_enabled": bool(row[2]),
            "rules_text": row[3],
            "welcome_message": row[4],
        }
