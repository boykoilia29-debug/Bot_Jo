"""Профиль: данные, история заказов, избранное, редактирование."""
from __future__ import annotations

import re

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.database import db
from bot.keyboards.profile import (
    edit_profile_kb,
    favorites_list_kb,
    order_back_kb,
    orders_list_kb,
    profile_kb,
)
from bot.states import ProfileStates

router = Router(name="profile")

PHONE_RE = re.compile(r"^\+?7?\d{10,11}$")


def _profile_text(u: dict) -> str:
    return (
        "<b>👤 Профиль</b>\n"
        "────────────\n"
        f"<b>TG ID:</b> <code>{u['tg_id']}</code>\n"
        f"<b>Имя:</b> {u.get('full_name') or '—'}\n"
        f"<b>Телефон:</b> {u.get('phone') or '—'}\n"
        f"<b>@username:</b> @{u['username'] if u.get('username') else '—'}"
    )


@router.callback_query(F.data == "profile")
async def show_profile(callback: CallbackQuery, user: dict) -> None:
    try:
        await callback.message.edit_text(_profile_text(user), reply_markup=profile_kb())
    except Exception:
        await callback.message.delete()
        await callback.message.answer(_profile_text(user), reply_markup=profile_kb())
    await callback.answer()


@router.callback_query(F.data == "profile:edit")
async def edit_menu(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "<b>✏️ Изменение данных</b>\n────────────\nЧто меняем?",
        reply_markup=edit_profile_kb(),
    )
    await callback.answer()


@router.callback_query(F.data == "profile:edit_name")
async def edit_name_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(ProfileStates.edit_name)
    await callback.message.edit_text("Введите новое имя:")
    await callback.answer()


@router.message(ProfileStates.edit_name, F.text)
async def edit_name_apply(message: Message, state: FSMContext, user: dict) -> None:
    name = (message.text or "").strip()
    if len(name) < 2:
        await message.answer("Имя слишком короткое.")
        return
    await db.update_user(user["id"], full_name=name)
    await state.clear()
    user = await db.get_user_by_tg(user["tg_id"])
    await message.answer("Имя обновлено ✅")
    await message.answer(_profile_text(user), reply_markup=profile_kb())


@router.callback_query(F.data == "profile:edit_phone")
async def edit_phone_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(ProfileStates.edit_phone)
    await callback.message.edit_text("Введите телефон (например, <code>+79991234567</code>):")
    await callback.answer()


@router.message(ProfileStates.edit_phone, F.text)
async def edit_phone_apply(message: Message, state: FSMContext, user: dict) -> None:
    raw = (message.text or "").replace(" ", "").replace("-", "").strip()
    if not PHONE_RE.match(raw):
        await message.answer("Неверный формат. Пример: <code>+79991234567</code>")
        return
    await db.update_user(user["id"], phone=raw)
    await state.clear()
    user = await db.get_user_by_tg(user["tg_id"])
    await message.answer("Телефон обновлён ✅")
    await message.answer(_profile_text(user), reply_markup=profile_kb())


@router.callback_query(F.data == "profile:orders")
async def show_orders(callback: CallbackQuery, user: dict) -> None:
    orders = await db.get_user_orders(user["id"], limit=10)
    if not orders:
        await callback.message.edit_text(
            "<b>📦 Мои заказы</b>\n────────────\nПока пусто.",
            reply_markup=order_back_kb(),
        )
        await callback.answer()
        return

    lines = ["<b>📦 Последние заказы</b>", "────────────"]
    for o in orders:
        lines.append(
            f"№ {o['id']:06d} · {o['created_at'][:10]} · "
            f"{int(o['total'])} ₽ · <i>{o['status']}</i>"
        )
    await callback.message.edit_text(
        "\n".join(lines), reply_markup=orders_list_kb(orders)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("profile:order:"))
async def show_order_details(callback: CallbackQuery, user: dict) -> None:
    order_id = int(callback.data.split(":")[2])
    order = await db.get_order(order_id)
    if not order or order["user_id"] != user["id"]:
        await callback.answer("Заказ не найден", show_alert=True)
        return
    items = await db.get_order_items(order_id)

    lines = [
        f"<b>Заказ № {order_id:06d}</b>",
        "────────────",
        f"<b>Дата:</b> {order['created_at']}",
        f"<b>Статус:</b> {order['status']}",
        f"<b>Оплата:</b> {order['payment_method']}",
        "────────────",
    ]
    for it in items:
        lines.append(
            f"• {it.get('name', '—')} · {it['volume_ml']} мл × {it['qty']} — {int(it['price'] * it['qty'])} ₽"
        )
    lines.append("────────────")
    lines.append(f"<b>Итого:</b> {int(order['total'])} ₽")

    await callback.message.edit_text(
        "\n".join(lines), reply_markup=order_back_kb()
    )
    await callback.answer()


@router.callback_query(F.data == "profile:favorites")
async def show_favorites(callback: CallbackQuery, user: dict) -> None:
    products = await db.favorites_get(user["id"])
    if not products:
        await callback.message.edit_text(
            "<b>❤️ Избранное</b>\n────────────\nПока пусто.",
            reply_markup=order_back_kb(),
        )
        await callback.answer()
        return
    await callback.message.edit_text(
        "<b>❤️ Избранное</b>\n────────────\nВыберите аромат:",
        reply_markup=favorites_list_kb(products),
    )
    await callback.answer()