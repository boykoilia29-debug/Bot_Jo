"""Клавиатуры корзины."""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def cart_kb(items: list[dict]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for it in items:
        row_title = f"{it['name']} · {it['volume_ml']} мл · {it['qty']} шт"
        b.row(
            InlineKeyboardButton(
                text=f"➖ {row_title}",
                callback_data=f"cart:dec:{it['cart_id']}",
            ),
            InlineKeyboardButton(
                text="➕",
                callback_data=f"cart:inc:{it['cart_id']}",
            ),
            InlineKeyboardButton(
                text="❌",
                callback_data=f"cart:del:{it['cart_id']}",
            ),
        )
    b.row(
        InlineKeyboardButton(text="✅ Оформить заказ", callback_data="order:start"),
    )
    b.row(
        InlineKeyboardButton(text="🗑 Очистить", callback_data="cart:clear"),
        InlineKeyboardButton(text="🏠 В меню", callback_data="main_menu"),
    )
    return b.as_markup()


def payment_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💵 Наличными при получении", callback_data="pay:cash")],
        [InlineKeyboardButton(text="💳 Картой онлайн", callback_data="pay:card")],
        [InlineKeyboardButton(text="📱 СБП", callback_data="pay:sbp")],
    ])


def order_confirm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить заказ", callback_data="order:confirm")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data="order:cancel")],
    ])


def skip_comment_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭ Пропустить", callback_data="order:skip_comment")],
    ])