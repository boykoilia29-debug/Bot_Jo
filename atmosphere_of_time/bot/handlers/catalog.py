"""Каталог, карточки товаров, избранное."""
from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery, InputMediaPhoto

from bot.database import db
from bot.keyboards.catalog import (
    CATEGORY_MAP,
    catalog_menu_kb,
    product_card_kb,
    products_list_kb,
)

router = Router(name="catalog")
log = logging.getLogger(__name__)

PER_PAGE = 5


@router.callback_query(F.data == "catalog")
async def show_catalog(callback: CallbackQuery) -> None:
    text = "<b>🛍 Каталог</b>\n────────────\nВыберите раздел:"
    try:
        await callback.message.edit_text(text, reply_markup=catalog_menu_kb())
    except Exception:
        await callback.message.delete()
        await callback.message.answer(text, reply_markup=catalog_menu_kb())
    await callback.answer()


@router.callback_query(F.data.startswith("cat:"))
async def show_category(callback: CallbackQuery) -> None:
    _, slug, page_s = callback.data.split(":")
    page = int(page_s)

    products, total = await db.list_products_by_category(slug, page * PER_PAGE, PER_PAGE)
    if total == 0:
        await callback.answer("В этом разделе пока пусто", show_alert=True)
        return

    label = CATEGORY_MAP.get(slug, "Раздел")
    text = f"<b>{label}</b>\n────────────\nВыберите аромат:"
    kb = products_list_kb(products, slug, page, total, PER_PAGE)
    try:
        await callback.message.edit_text(text, reply_markup=kb)
    except Exception:
        await callback.message.delete()
        await callback.message.answer(text, reply_markup=kb)
    await callback.answer()


def _format_card(p: dict) -> str:
    return (
        f"<b>{p['name']}</b>\n"
        f"<i>{p['brand']}</i>\n"
        f"────────────\n"
        f"<b>Верхние ноты:</b> {p['top_notes'] or '—'}\n"
        f"<b>Сердечные:</b> {p['heart_notes'] or '—'}\n"
        f"<b>Базовые:</b> {p['base_notes'] or '—'}\n"
        f"────────────\n"
        f"{p['description'] or ''}"
    )


@router.callback_query(F.data.startswith("prod:"))
async def show_product(callback: CallbackQuery, user: dict) -> None:
    product_id = int(callback.data.split(":")[1])
    product = await db.get_product(product_id)
    if not product:
        await callback.answer("Аромат не найден", show_alert=True)
        return

    volumes = await db.get_product_volumes(product_id)
    is_fav = await db.is_favorite(user["id"], product_id)

    caption = _format_card(product)
    if product["stock"] <= 0:
        caption += "\n\n<i>❌ Нет в наличии</i>"

    kb = product_card_kb(product_id, volumes, is_fav)
    photo = product["photo_id"]

    # Если у текущего сообщения уже фото — редактируем media
    if callback.message.photo:
        try:
            await callback.message.edit_media(
                InputMediaPhoto(media=photo, caption=caption),
                reply_markup=kb,
            )
            await callback.answer()
            return
        except Exception as e:
            log.warning("edit_media failed: %s", e)

    try:
        await callback.message.delete()
    except Exception:
        pass
    try:
        await callback.message.answer_photo(photo=photo, caption=caption, reply_markup=kb)
    except Exception as e:
        log.warning("send_photo failed: %s", e)
        # фолбэк — отправляем как текст
        await callback.message.answer(caption, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("fav:"))
async def toggle_favorite(callback: CallbackQuery, user: dict) -> None:
    _, action, pid_s = callback.data.split(":")
    product_id = int(pid_s)

    if action == "add":
        await db.favorites_add(user["id"], product_id)
        await callback.answer("Добавлено в избранное ❤️")
    else:
        await db.favorites_remove(user["id"], product_id)
        await callback.answer("Удалено из избранного 💔")

    # перерисовываем карточку
    product = await db.get_product(product_id)
    if not product:
        return
    volumes = await db.get_product_volumes(product_id)
    is_fav = await db.is_favorite(user["id"], product_id)
    caption = _format_card(product)
    if product["stock"] <= 0:
        caption += "\n\n<i>❌ Нет в наличии</i>"
    kb = product_card_kb(product_id, volumes, is_fav)
    if callback.message.photo:
        try:
            await callback.message.edit_caption(caption=caption, reply_markup=kb)
        except Exception:
            pass
    else:
        try:
            await callback.message.edit_text(caption, reply_markup=kb)
        except Exception:
            pass