"""Админ-панель: товары, цены, заказы."""
from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.database import db
from bot.keyboards.admin import (
    admin_categories_kb,
    admin_menu_kb,
    admin_order_status_kb,
    admin_orders_kb,
    admin_products_kb,
)
from bot.states import AdminPriceStates, AdminProductStates

router = Router(name="admin")
log = logging.getLogger(__name__)


def _is_admin_guard(is_admin: bool) -> bool:
    return bool(is_admin)


@router.message(Command("admin"))
async def admin_entry(message: Message, is_admin: bool) -> None:
    if not is_admin:
        await message.answer("⛔ Команда доступна только администратору.")
        return
    await message.answer(
        "<b>🛠 Админ-панель</b>\n────────────\nЧто делаем?",
        reply_markup=admin_menu_kb(),
    )


@router.callback_query(F.data == "admin")
async def admin_menu(callback: CallbackQuery, is_admin: bool) -> None:
    if not _is_admin_guard(is_admin):
        await callback.answer("Нет доступа", show_alert=True)
        return
    await callback.message.edit_text(
        "<b>🛠 Админ-панель</b>\n────────────\nЧто делаем?",
        reply_markup=admin_menu_kb(),
    )
    await callback.answer()


# ---------------------------------------------------------
# Добавление товара (FSM)
# ---------------------------------------------------------
@router.callback_query(F.data == "admin:add_product")
async def add_product_start(callback: CallbackQuery, state: FSMContext, is_admin: bool) -> None:
    if not _is_admin_guard(is_admin):
        await callback.answer("Нет доступа", show_alert=True)
        return
    await state.clear()
    await state.set_state(AdminProductStates.name)
    await callback.message.edit_text("Шаг 1/9. Введите <b>название</b> аромата:")
    await callback.answer()


@router.message(AdminProductStates.name, F.text)
async def add_name(message: Message, state: FSMContext) -> None:
    await state.update_data(name=message.text.strip())
    await state.set_state(AdminProductStates.brand)
    await message.answer("Шаг 2/9. Введите <b>бренд</b>:")


@router.message(AdminProductStates.brand, F.text)
async def add_brand(message: Message, state: FSMContext) -> None:
    await state.update_data(brand=message.text.strip())
    await state.set_state(AdminProductStates.category)
    await message.answer("Шаг 3/9. Выберите <b>категорию</b>:", reply_markup=admin_categories_kb())


@router.callback_query(AdminProductStates.category, F.data.startswith("admin:cat:"))
async def add_category(callback: CallbackQuery, state: FSMContext) -> None:
    category_id = int(callback.data.split(":")[2])
    await state.update_data(category_id=category_id)
    await state.set_state(AdminProductStates.description)
    await callback.message.edit_text("Шаг 4/9. Введите <b>описание</b>:")
    await callback.answer()


@router.message(AdminProductStates.description, F.text)
async def add_description(message: Message, state: FSMContext) -> None:
    await state.update_data(description=message.text.strip())
    await state.set_state(AdminProductStates.top_notes)
    await message.answer("Шаг 5/9. <b>Верхние ноты</b> (через запятую):")


@router.message(AdminProductStates.top_notes, F.text)
async def add_top(message: Message, state: FSMContext) -> None:
    await state.update_data(top_notes=message.text.strip())
    await state.set_state(AdminProductStates.heart_notes)
    await message.answer("Шаг 6/9. <b>Сердечные ноты</b>:")


@router.message(AdminProductStates.heart_notes, F.text)
async def add_heart(message: Message, state: FSMContext) -> None:
    await state.update_data(heart_notes=message.text.strip())
    await state.set_state(AdminProductStates.base_notes)
    await message.answer("Шаг 7/9. <b>Базовые ноты</b>:")


@router.message(AdminProductStates.base_notes, F.text)
async def add_base(message: Message, state: FSMContext) -> None:
    await state.update_data(base_notes=message.text.strip())
    await state.set_state(AdminProductStates.volumes)
    await message.answer(
        "Шаг 8/9. Введите <b>объёмы и цены</b> в формате:\n"
        "<code>30:2500,50:3500,100:5500</code>"
    )


@router.message(AdminProductStates.volumes, F.text)
async def add_volumes(message: Message, state: FSMContext) -> None:
    try:
        parts = message.text.replace(" ", "").split(",")
        volumes = []
        for p in parts:
            v, pr = p.split(":")
            volumes.append((int(v), float(pr)))
        if not volumes:
            raise ValueError
    except Exception:
        await message.answer("Неверный формат. Пример: <code>30:2500,50:3500,100:5500</code>")
        return
    await state.update_data(volumes=volumes)
    await state.set_state(AdminProductStates.stock)
    await message.answer("Шаг 9/9. <b>Остаток</b> на складе (целое число):")


@router.message(AdminProductStates.stock, F.text)
async def add_stock(message: Message, state: FSMContext) -> None:
    try:
        stock = int(message.text.strip())
        if stock < 0:
            raise ValueError
    except ValueError:
        await message.answer("Нужно целое неотрицательное число.")
        return
    await state.update_data(stock=stock)
    await state.set_state(AdminProductStates.photo)
    await message.answer(
        "И последнее: отправьте <b>ссылку на фото</b> или photo-файл."
    )


@router.message(AdminProductStates.photo)
async def add_photo(message: Message, state: FSMContext) -> None:
    if message.photo:
        photo_id = message.photo[-1].file_id
    elif message.text and message.text.startswith("http"):
        photo_id = message.text.strip()
    else:
        await message.answer("Нужна ссылка (http...) или изображение.")
        return

    data = await state.get_data()
    product_id = await db.admin_add_product(
        category_id=data["category_id"],
        name=data["name"],
        brand=data["brand"],
        description=data["description"],
        top_notes=data["top_notes"],
        heart_notes=data["heart_notes"],
        base_notes=data["base_notes"],
        photo_id=photo_id,
        stock=data["stock"],
        volumes=data["volumes"],
    )
    await state.clear()
    await message.answer(
        f"✅ Товар <b>{data['name']}</b> добавлен (ID {product_id})",
        reply_markup=admin_menu_kb(),
    )


@router.callback_query(F.data == "admin:cancel")
async def admin_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text(
        "<b>🛠 Админ-панель</b>", reply_markup=admin_menu_kb()
    )
    await callback.answer("Отменено")


# ---------------------------------------------------------
# Удаление товара
# ---------------------------------------------------------
@router.callback_query(F.data == "admin:del_product")
async def del_product_list(callback: CallbackQuery, is_admin: bool) -> None:
    if not _is_admin_guard(is_admin):
        await callback.answer("Нет доступа", show_alert=True)
        return
    products, _ = await db.list_products_by_category("unisex", 0, 1000)
    # подтянем все товары (все категории)
    all_products: list[dict] = []
    for slug in ("unisex", "female", "male", "new", "bestseller"):
        items, _ = await db.list_products_by_category(slug, 0, 1000)
        for it in items:
            if it["id"] not in {x["id"] for x in all_products}:
                all_products.append(it)
    if not all_products:
        await callback.answer("Товаров нет", show_alert=True)
        return
    await callback.message.edit_text(
        "Выберите товар для удаления:",
        reply_markup=admin_products_kb(all_products, "del_exec"),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:del_exec:"))
async def del_product_exec(callback: CallbackQuery, is_admin: bool) -> None:
    if not _is_admin_guard(is_admin):
        await callback.answer("Нет доступа", show_alert=True)
        return
    product_id = int(callback.data.split(":")[2])
    product = await db.get_product(product_id)
    if not product:
        await callback.answer("Не найден", show_alert=True)
        return
    await db.admin_delete_product(product_id)
    await callback.message.edit_text(
        f"✅ Удалён товар <b>{product['name']}</b>",
        reply_markup=admin_menu_kb(),
    )
    await callback.answer()


# ---------------------------------------------------------
# Изменение цен
# ---------------------------------------------------------
@router.callback_query(F.data == "admin:edit_prices")
async def edit_prices_list(callback: CallbackQuery, is_admin: bool) -> None:
    if not _is_admin_guard(is_admin):
        await callback.answer("Нет доступа", show_alert=True)
        return
    all_products: list[dict] = []
    for slug in ("unisex", "female", "male"):
        items, _ = await db.list_products_by_category(slug, 0, 1000)
        for it in items:
            if it["id"] not in {x["id"] for x in all_products}:
                all_products.append(it)
    if not all_products:
        await callback.answer("Товаров нет", show_alert=True)
        return
    await callback.message.edit_text(
        "Выберите товар, чтобы изменить цены:",
        reply_markup=admin_products_kb(all_products, "edit_price"),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:edit_price:"))
async def edit_prices_start(callback: CallbackQuery, state: FSMContext, is_admin: bool) -> None:
    if not _is_admin_guard(is_admin):
        await callback.answer("Нет доступа", show_alert=True)
        return
    product_id = int(callback.data.split(":")[2])
    product = await db.get_product(product_id)
    volumes = await db.get_product_volumes(product_id)
    current = ", ".join(f"{v['volume_ml']}:{int(v['price'])}" for v in volumes)
    await state.set_state(AdminPriceStates.volumes)
    await state.update_data(product_id=product_id)
    await callback.message.edit_text(
        f"<b>{product['name']}</b>\nТекущие цены: <code>{current}</code>\n\n"
        "Введите новые цены в формате: <code>30:2500,50:3500,100:5500</code>"
    )
    await callback.answer()


@router.message(AdminPriceStates.volumes, F.text)
async def edit_prices_apply(message: Message, state: FSMContext) -> None:
    try:
        parts = message.text.replace(" ", "").split(",")
        volumes = []
        for p in parts:
            v, pr = p.split(":")
            volumes.append((int(v), float(pr)))
        if not volumes:
            raise ValueError
    except Exception:
        await message.answer("Формат: <code>30:2500,50:3500,100:5500</code>")
        return
    data = await state.get_data()
    await db.admin_set_volumes(data["product_id"], volumes)
    await state.clear()
    await message.answer("✅ Цены обновлены", reply_markup=admin_menu_kb())


# ---------------------------------------------------------
# Заказы
# ---------------------------------------------------------
@router.callback_query(F.data == "admin:orders")
async def admin_orders(callback: CallbackQuery, is_admin: bool) -> None:
    if not _is_admin_guard(is_admin):
        await callback.answer("Нет доступа", show_alert=True)
        return
    orders = await db.all_orders(20)
    if not orders:
        await callback.message.edit_text("Заказов нет", reply_markup=admin_menu_kb())
        await callback.answer()
        return
    await callback.message.edit_text(
        "<b>📦 Последние заказы</b>", reply_markup=admin_orders_kb(orders)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:order:"))
async def admin_order_details(callback: CallbackQuery, is_admin: bool) -> None:
    if not _is_admin_guard(is_admin):
        await callback.answer("Нет доступа", show_alert=True)
        return
    order_id = int(callback.data.split(":")[2])
    order = await db.get_order(order_id)
    if not order:
        await callback.answer("Не найден", show_alert=True)
        return
    items = await db.get_order_items(order_id)
    lines = [
        f"<b>Заказ № {order_id:06d}</b>",
        "────────────",
        f"<b>Имя:</b> {order['name']}",
        f"<b>Телефон:</b> {order['phone']}",
        f"<b>Адрес:</b> {order['address']}",
        f"<b>Оплата:</b> {order['payment_method']}",
        f"<b>Комментарий:</b> {order['comment'] or '—'}",
        f"<b>Статус:</b> {order['status']}",
        "────────────",
    ]
    for it in items:
        lines.append(
            f"• {it.get('name', '—')} · {it['volume_ml']} мл × {it['qty']} — {int(it['price'] * it['qty'])} ₽"
        )
    lines.append(f"────────────\n<b>Итого:</b> {int(order['total'])} ₽")
    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=admin_order_status_kb(order_id, order["status"]),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:setstatus:"))
async def admin_set_status(callback: CallbackQuery, is_admin: bool) -> None:
    if not _is_admin_guard(is_admin):
        await callback.answer("Нет доступа", show_alert=True)
        return
    _, _, order_id_s, status = callback.data.split(":", 3)
    order_id = int(order_id_s)
    await db.update_order_status(order_id, status)
    await callback.answer(f"Статус: {status}")
    # перерисовываем карточку
    order = await db.get_order(order_id)
    if order:
        await callback.message.edit_reply_markup(
            reply_markup=admin_order_status_kb(order_id, order["status"])
        )