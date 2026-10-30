"""Общие inline-клавиатуры."""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu_kb(cart_count: int = 0) -> InlineKeyboardMarkup:
    cart_label = f"🛒 Корзина ({cart_count})" if cart_count else "🛒 Корзина"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛍 Каталог", callback_data="catalog")],
        [InlineKeyboardButton(text=cart_label, callback_data="cart")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile")],
        [
            InlineKeyboardButton(text="ℹ️ О магазине", callback_data="about"),
            InlineKeyboardButton(text="📞 Поддержка", callback_data="support"),
        ],
    ])


def back_to_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 В меню", callback_data="main_menu")],
    ])


def back_kb(target: str = "main_menu", text: str = "◀️ Назад") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=text, callback_data=target)],
    ])