"""Клавиатуры профиля."""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def profile_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Изменить данные", callback_data="profile:edit")],
        [InlineKeyboardButton(text="📦 Мои заказы", callback_data="profile:orders")],
        [InlineKeyboardButton(text="❤️ Избранное", callback_data="profile:favorites")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")],
    ])


def edit_profile_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Имя", callback_data="profile:edit_name")],
        [InlineKeyboardButton(text="Телефон", callback_data="profile:edit_phone")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="profile")],
    ])


def orders_list_kb(orders: list[dict]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for o in orders:
        b.button(
            text=f"№ {o['id']:06d} · {int(o['total'])} ₽ · {o['status']}",
            callback_data=f"profile:order:{o['id']}",
        )
    b.adjust(1)
    b.row(InlineKeyboardButton(text="◀️ Назад", callback_data="profile"))
    return b.as_markup()


def favorites_list_kb(products: list[dict]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for p in products:
        b.button(text=f"{p['name']} · {p['brand']}", callback_data=f"prod:{p['id']}")
    b.adjust(1)
    b.row(InlineKeyboardButton(text="◀️ Назад", callback_data="profile"))
    return b.as_markup()


def order_back_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ К заказам", callback_data="profile:orders")],
    ])