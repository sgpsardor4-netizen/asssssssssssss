import aiosqlite
from datetime import datetime
from config import DB_PATH, DEFAULT_PRICE_PER_STAR, DEFAULT_CARD_NUMBER, DEFAULT_CARD_OWNER


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                created_at TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                stars_amount INTEGER,
                price_uzs INTEGER,
                status TEXT DEFAULT 'pending',   -- pending / paid / rejected / sent
                receipt_file_id TEXT,
                stars_target TEXT,               -- foydalanuvchi @username (stars kimga yuboriladi)
                created_at TEXT,
                updated_at TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        # boshlang'ich sozlamalar
        defaults = {
            "price_per_star": str(DEFAULT_PRICE_PER_STAR),
            "card_number": DEFAULT_CARD_NUMBER,
            "card_owner": DEFAULT_CARD_OWNER,
        }
        for k, v in defaults.items():
            await db.execute(
                "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v)
            )
        await db.commit()


async def get_setting(key: str) -> str:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = await cur.fetchone()
        return row[0] if row else ""


async def set_setting(key: str, value: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )
        await db.commit()


async def upsert_user(user_id: int, username: str, full_name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, username, full_name, created_at) "
            "VALUES (?, ?, ?, ?)",
            (user_id, username, full_name, datetime.utcnow().isoformat()),
        )
        await db.commit()


async def create_order(user_id: int, stars_amount: int, price_uzs: int, stars_target: str) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "INSERT INTO orders (user_id, stars_amount, price_uzs, stars_target, status, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, 'pending', ?, ?)",
            (user_id, stars_amount, price_uzs, stars_target,
             datetime.utcnow().isoformat(), datetime.utcnow().isoformat()),
        )
        await db.commit()
        return cur.lastrowid


async def attach_receipt(order_id: int, file_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE orders SET receipt_file_id = ?, updated_at = ? WHERE order_id = ?",
            (file_id, datetime.utcnow().isoformat(), order_id),
        )
        await db.commit()


async def update_order_status(order_id: int, status: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE orders SET status = ?, updated_at = ? WHERE order_id = ?",
            (status, datetime.utcnow().isoformat(), order_id),
        )
        await db.commit()


async def get_order(order_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,))
        return await cur.fetchone()


async def get_pending_orders():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM orders WHERE status = 'pending' ORDER BY order_id DESC")
        return await cur.fetchall()


async def get_user_orders(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM orders WHERE user_id = ? ORDER BY order_id DESC LIMIT 10", (user_id,)
        )
        return await cur.fetchall()
