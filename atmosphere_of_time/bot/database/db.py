"""Асинхронный слой доступа к SQLite через aiosqlite."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Optional

import aiosqlite

log = logging.getLogger(__name__)

_DB_PATH: str = "atmosphere.db"


async def init_db(path: str) -> None:
    """Инициализация: создаёт таблицы и наполняет демо-данными (schema.sql)."""
    global _DB_PATH
    _DB_PATH = path

    schema_file = Path(__file__).parent / "schema.sql"
    sql = schema_file.read_text(encoding="utf-8")

    async with aiosqlite.connect(_DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        await conn.executescript(sql)
        await conn.commit()
    log.info("БД инициализирована: %s", _DB_PATH)


@asynccontextmanager
async def get_conn():
    """Контекстный менеджер соединения."""
    conn = await aiosqlite.connect(_DB_PATH)
    conn.row_factory = aiosqlite.Row
    await conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
    finally:
        await conn.close()


async def close_db() -> None:
    """Заглушка graceful shutdown (соединения открываются по требованию)."""
    log.info("Соединение с БД завершено")


# ---------------------------------------------------------
# USERS
# ---------------------------------------------------------
async def get_user_by_tg(tg_id: int) -> Optional[dict]:
    async with get_conn() as conn:
        cur = await conn.execute("SELECT * FROM users WHERE tg_id = ?", (tg_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def create_user(tg_id: int, username: str | None, full_name: str | None) -> int:
    async with get_conn() as conn:
        cur = await conn.execute(
            "INSERT INTO users (tg_id, username, full_name) VALUES (?, ?, ?)",
            (tg_id, username, full_name),
        )
        await conn.commit()
        return cur.lastrowid


async def update_user(user_id: int, **fields: Any) -> None:
    """Универсальное обновление полей пользователя."""
    if not fields:
        return
    keys = ", ".join(f"{k} = ?" for k in fields)
    async with get_conn() as conn:
        await conn.execute(
            f"UPDATE users SET {keys} WHERE id = ?",
            (*fields.values(), user_id),
        )
        await conn.commit()


# ---------------------------------------------------------
# CATEGORIES / PRODUCTS
# ---------------------------------------------------------
async def get_categories() -> list[dict]:
    async with get_conn() as conn:
        cur = await conn.execute("SELECT * FROM categories ORDER BY id")
        return [dict(r) for r in await cur.fetchall()]


async def get_category_by_slug(slug: str) -> Optional[dict]:
    async with get_conn() as conn:
        cur = await conn.execute("SELECT * FROM categories WHERE slug = ?", (slug,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def list_products_by_category(
    slug: str, offset: int = 0, limit: int = 5
) -> tuple[list[dict], int]:
    """Список товаров раздела + общее количество."""
    async with get_conn() as conn:
        if slug == "new":
            where = "p.is_new = 1"
            args: tuple = ()
        elif slug == "bestseller":
            where = "p.is_bestseller = 1"
            args = ()
        else:
            where = "c.slug = ?"
            args = (slug,)

        cur = await conn.execute(
            f"SELECT p.* FROM products p "
            f"LEFT JOIN categories c ON c.id = p.category_id "
            f"WHERE {where} ORDER BY p.id",
            args,
        )
        all_rows = [dict(r) for r in await cur.fetchall()]
        return all_rows[offset : offset + limit], len(all_rows)


async def get_product(product_id: int) -> Optional[dict]:
    async with get_conn() as conn:
        cur = await conn.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def get_product_volumes(product_id: int) -> list[dict]:
    async with get_conn() as conn:
        cur = await conn.execute(
            "SELECT * FROM product_volumes WHERE product_id = ? ORDER BY volume_ml",
            (product_id,),
        )
        return [dict(r) for r in await cur.fetchall()]


async def get_volume_price(product_id: int, volume_ml: int) -> Optional[float]:
    async with get_conn() as conn:
        cur = await conn.execute(
            "SELECT price FROM product_volumes WHERE product_id = ? AND volume_ml = ?",
            (product_id, volume_ml),
        )
        row = await cur.fetchone()
        return float(row["price"]) if row else None


async def search_products(query: str) -> list[dict]:
    """Поиск по названию и бренду без учёта регистра."""
    q = f"%{query.lower()}%"
    async with get_conn() as conn:
        cur = await conn.execute(
            "SELECT * FROM products WHERE LOWER(name) LIKE ? OR LOWER(brand) LIKE ?",
            (q, q),
        )
        return [dict(r) for r in await cur.fetchall()]


# ---------------------------------------------------------
# CART
# ---------------------------------------------------------
async def cart_add(user_id: int, product_id: int, volume_ml: int, qty: int = 1) -> None:
    async with get_conn() as conn:
        cur = await conn.execute(
            "SELECT id, qty FROM cart WHERE user_id = ? AND product_id = ? AND volume_ml = ?",
            (user_id, product_id, volume_ml),
        )
        row = await cur.fetchone()
        if row:
            await conn.execute(
                "UPDATE cart SET qty = qty + ? WHERE id = ?",
                (qty, row["id"]),
            )
        else:
            await conn.execute(
                "INSERT INTO cart (user_id, product_id, volume_ml, qty) VALUES (?, ?, ?, ?)",
                (user_id, product_id, volume_ml, qty),
            )
        await conn.commit()


async def cart_get(user_id: int) -> list[dict]:
    """Позиции корзины с расшифровкой товара."""
    async with get_conn() as conn:
        cur = await conn.execute(
            """
            SELECT cart.id AS cart_id, cart.volume_ml, cart.qty,
                   p.id AS product_id, p.name, p.brand, p.stock,
                   pv.price AS price
              FROM cart
              JOIN products p         ON p.id = cart.product_id
              JOIN product_volumes pv ON pv.product_id = cart.product_id
                                     AND pv.volume_ml = cart.volume_ml
             WHERE cart.user_id = ?
             ORDER BY cart.id
            """,
            (user_id,),
        )
        return [dict(r) for r in await cur.fetchall()]


async def cart_count(user_id: int) -> int:
    async with get_conn() as conn:
        cur = await conn.execute(
            "SELECT COALESCE(SUM(qty), 0) AS c FROM cart WHERE user_id = ?", (user_id,)
        )
        row = await cur.fetchone()
        return int(row["c"])


async def cart_total(user_id: int) -> float:
    async with get_conn() as conn:
        cur = await conn.execute(
            """
            SELECT COALESCE(SUM(cart.qty * pv.price), 0) AS t
              FROM cart
              JOIN product_volumes pv ON pv.product_id = cart.product_id
                                     AND pv.volume_ml = cart.volume_ml
             WHERE cart.user_id = ?
            """,
            (user_id,),
        )
        row = await cur.fetchone()
        return float(row["t"])


async def cart_inc(cart_id: int) -> None:
    async with get_conn() as conn:
        await conn.execute("UPDATE cart SET qty = qty + 1 WHERE id = ?", (cart_id,))
        await conn.commit()


async def cart_dec(cart_id: int) -> None:
    """Уменьшение; удаляет позицию при qty <= 1."""
    async with get_conn() as conn:
        cur = await conn.execute("SELECT qty FROM cart WHERE id = ?", (cart_id,))
        row = await cur.fetchone()
        if not row:
            return
        if row["qty"] <= 1:
            await conn.execute("DELETE FROM cart WHERE id = ?", (cart_id,))
        else:
            await conn.execute("UPDATE cart SET qty = qty - 1 WHERE id = ?", (cart_id,))
        await conn.commit()


async def cart_remove(cart_id: int) -> None:
    async with get_conn() as conn:
        await conn.execute("DELETE FROM cart WHERE id = ?", (cart_id,))
        await conn.commit()


async def cart_clear(user_id: int) -> None:
    async with get_conn() as conn:
        await conn.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
        await conn.commit()


# ---------------------------------------------------------
# FAVORITES
# ---------------------------------------------------------
async def favorites_add(user_id: int, product_id: int) -> None:
    async with get_conn() as conn:
        await conn.execute(
            "INSERT OR IGNORE INTO favorites (user_id, product_id) VALUES (?, ?)",
            (user_id, product_id),
        )
        await conn.commit()


async def favorites_remove(user_id: int, product_id: int) -> None:
    async with get_conn() as conn:
        await conn.execute(
            "DELETE FROM favorites WHERE user_id = ? AND product_id = ?",
            (user_id, product_id),
        )
        await conn.commit()


async def favorites_get(user_id: int) -> list[dict]:
    async with get_conn() as conn:
        cur = await conn.execute(
            """SELECT p.* FROM favorites f
               JOIN products p ON p.id = f.product_id
               WHERE f.user_id = ? ORDER BY f.id DESC""",
            (user_id,),
        )
        return [dict(r) for r in await cur.fetchall()]


async def is_favorite(user_id: int, product_id: int) -> bool:
    async with get_conn() as conn:
        cur = await conn.execute(
            "SELECT 1 FROM favorites WHERE user_id = ? AND product_id = ?",
            (user_id, product_id),
        )
        return await cur.fetchone() is not None


# ---------------------------------------------------------
# ORDERS
# ---------------------------------------------------------
async def create_order(
    user_id: int,
    name: str,
    phone: str,
    address: str,
    comment: str,
    payment: str,
    items: list[dict],
    total: float,
) -> int:
    async with get_conn() as conn:
        cur = await conn.execute(
            """INSERT INTO orders
               (user_id, total, status, name, phone, address, payment_method, comment)
               VALUES (?, ?, 'новый', ?, ?, ?, ?, ?)""",
            (user_id, total, name, phone, address, payment, comment),
        )
        order_id = cur.lastrowid
        for it in items:
            await conn.execute(
                """INSERT INTO order_items
                   (order_id, product_id, volume_ml, qty, price)
                   VALUES (?, ?, ?, ?, ?)""",
                (order_id, it["product_id"], it["volume_ml"], it["qty"], it["price"]),
            )
        await conn.commit()
        return order_id


async def get_order(order_id: int) -> Optional[dict]:
    async with get_conn() as conn:
        cur = await conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def get_order_items(order_id: int) -> list[dict]:
    async with get_conn() as conn:
        cur = await conn.execute(
            """SELECT oi.*, p.name, p.brand FROM order_items oi
               LEFT JOIN products p ON p.id = oi.product_id
               WHERE oi.order_id = ?""",
            (order_id,),
        )
        return [dict(r) for r in await cur.fetchall()]


async def get_user_orders(user_id: int, limit: int = 10) -> list[dict]:
    async with get_conn() as conn:
        cur = await conn.execute(
            "SELECT * FROM orders WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        )
        return [dict(r) for r in await cur.fetchall()]


async def all_orders(limit: int = 20) -> list[dict]:
    async with get_conn() as conn:
        cur = await conn.execute(
            "SELECT * FROM orders ORDER BY id DESC LIMIT ?", (limit,)
        )
        return [dict(r) for r in await cur.fetchall()]


async def update_order_status(order_id: int, status: str) -> None:
    async with get_conn() as conn:
        await conn.execute(
            "UPDATE orders SET status = ? WHERE id = ?", (status, order_id)
        )
        await conn.commit()


# ---------------------------------------------------------
# ADMIN: products
# ---------------------------------------------------------
async def admin_add_product(
    category_id: int,
    name: str,
    brand: str,
    description: str,
    top_notes: str,
    heart_notes: str,
    base_notes: str,
    photo_id: str,
    stock: int,
    volumes: list[tuple[int, float]],
) -> int:
    """volumes: [(volume_ml, price), ...]"""
    base_price = volumes[0][1] if volumes else 0
    async with get_conn() as conn:
        cur = await conn.execute(
            """INSERT INTO products
               (category_id, name, brand, description,
                top_notes, heart_notes, base_notes,
                price, photo_id, stock, is_new, is_bestseller)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0)""",
            (category_id, name, brand, description,
             top_notes, heart_notes, base_notes,
             base_price, photo_id, stock),
        )
        pid = cur.lastrowid
        for vol, price in volumes:
            await conn.execute(
                "INSERT INTO product_volumes (product_id, volume_ml, price) VALUES (?, ?, ?)",
                (pid, vol, price),
            )
        await conn.commit()
        return pid


async def admin_delete_product(product_id: int) -> None:
    async with get_conn() as conn:
        await conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
        await conn.commit()


async def admin_set_volumes(product_id: int, volumes: list[tuple[int, float]]) -> None:
    async with get_conn() as conn:
        await conn.execute("DELETE FROM product_volumes WHERE product_id = ?", (product_id,))
        for vol, price in volumes:
            await conn.execute(
                "INSERT INTO product_volumes (product_id, volume_ml, price) VALUES (?, ?, ?)",
                (product_id, vol, price),
            )
        if volumes:
            await conn.execute(
                "UPDATE products SET price = ? WHERE id = ?",
                (volumes[0][1], product_id),
            )
        await conn.commit()