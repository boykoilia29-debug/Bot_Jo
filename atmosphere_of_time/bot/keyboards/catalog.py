"""Клавиатуры каталога."""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


CATEGORIES = [
    ("unisex",     "Унисекс"),
    ("female",     "Женские"),
    ("male",       "Мужские"),
    ("new",        "Новинки"),
    ("bestseller", "Бестселлеры"),
]
CATEGORY_MAP = dict(CATEGORIES)


def catalog_menu_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for slug, name in CATEGORIES:
        b.button(text=name, callback_data=f"cat:{slug}:0")
    b.adjust(2)
    b.row(InlineKeyboardButton(text="🔍 Поиск", callback_data="search"))
    b.row(InlineKeyboardButton(text="🏠 В меню", callback_data="main_menu"))
    return b.as_markup()


def products_list_kb(
    products: list[dict], slug: str, page: int, total: int, per_page: int
) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for p in products:
        b.button(text=f"{p['name']} · {p['brand']}", callback_data=f"prod:{p['id']}")
    b.adjust(1)

    pages = max(1, (total + per_page - 1) // per_page)
    nav: list[InlineKeyboardButton] = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"cat:{slug}:{page - 1}"))
    nav.append(InlineKeyboardButton(text=f"{page + 1}/{pages}", callback_data="noop"))
    if (page + 1) * per_page < total:
        nav.append(InlineKeyboardButton(text="➡️", callback_data=f"cat:{slug}:{page + 1}"))
    if nav:
        b.row(*nav)

    b.row(InlineKeyboardButton(text="🔍 Поиск", callback_data="search"))
    b.row(InlineKeyboardButton(text="◀️ Назад", callback_data="catalog"))
    return b.as_markup()


def product_card_kb(
    product_id: int, volumes: list[dict], is_fav: bool
) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for v in volumes:
        b.button(
            text=f"➕ {v['volume_ml']} мл — {int(v['price'])} ₽",
            callback_data=f"cart:add:{product_id}:{v['volume_ml']}",
        )
    b.adjust(1)
    fav_label = "💔 Убрать из избранного" if is_fav else "❤️ В избранное"
    fav_cb = f"fav:del:{product_id}" if is_fav else f"fav:add:{product_id}"
    b.row(InlineKeyboardButton(text=fav_label, callback_data=fav_cb))
    b.row(InlineKeyboardButton(text="◀️ Назад", callback_data="catalog"))
    return b.as_markup()


def search_results_kb(products: list[dict]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for p in products:
        b.button(text=f"{p['name']} · {p['brand']}", callback_data=f"prod:{p['id']}")
    b.adjust(1)
    b.row(InlineKeyboardButton(text="◀️ Назад в каталог", callback_data="catalog"))
    return b.as_markup()