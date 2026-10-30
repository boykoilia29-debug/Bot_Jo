"""Клавиатуры админ-панели."""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


ORDER_STATUSES = ["новый", "в обработке", "оплачен", "отправлен", "доставлен", "отменён"]


def admin_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить товар", callback_data="admin:add_product")],
        [InlineKeyboardButton(text="🗑 Удалить товар", callback_data="admin:del_product")],
        [InlineKeyboardButton(text="💲 Изменить цены", callback_data="admin:edit_prices")],
        [InlineKeyboardButton(text="📦 Заказы", callback_data="admin:orders")],
        [InlineKeyboardButton(text="🏠 В меню", callback_data="main_menu")],
    ])


def admin_categories_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Унисекс", callback_data="admin:cat:1")],
        [InlineKeyboardButton(text="Женские", callback_data="admin:cat:2")],
        [InlineKeyboardButton(text="Мужские", callback_data="admin:cat:3")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="admin:cancel")],
    ])


def admin_products_kb(products: list[dict], action: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for p in products:
        b.button(text=f"{p['name']} · {p['brand']}", callback_data=f"admin:{action}:{p['id']}")
    b.adjust(1)
    b.row(InlineKeyboardButton(text="◀️ Назад", callback_data="admin"))
    return b.as_markup()


def admin_orders_kb(orders: list[dict]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for o in orders:
        b.button(
            text=f"№ {o['id']:06d} · {o['status']} · {int(o['total'])} ₽",
            callback_data=f"admin:order:{o['id']}",
        )
    b.adjust(1)
    b.row(InlineKeyboardButton(text="◀️ Назад", callback_data="admin"))
    return b.as_markup()


def admin_order_status_kb(order_id: int, current: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for s in ORDER_STATUSES:
        mark = "● " if s == current else ""
        b.button(text=f"{mark}{s}", callback_data=f"admin:setstatus:{order_id}:{s}")
    b.adjust(2)
    b.row(InlineKeyboardButton(text="◀️ К заказам", callback_data="admin:orders"))
    return b.as_markup()