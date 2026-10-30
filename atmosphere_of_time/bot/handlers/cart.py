"""Корзина + оформление заказа (FSM)."""
from __future__ import annotations

import logging
import re

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.database import db
from bot.keyboards.cart import (
    cart_kb,
    order_confirm_kb,
    payment_kb,
    skip_comment_kb,
)
from bot.keyboards.common import back_to_menu_kb, main_menu_kb
from bot.states import OrderStates

router = Router(name="cart")
log = logging.getLogger(__name__)

PHONE_RE = re.compile(r"^\+?7?\d{10,11}$")
PAYMENT_LABELS = {
    "cash": "💵 Наличными при получении",
    "card": "💳 Картой онлайн",
    "sbp":  "📱 СБП",
}


async def _render_cart(user_id: int) -> tuple[str, object]:
    items = await db.cart_get(user_id)
    if not items:
        text = (
            "<b>🛒 Корзина</b>\n────────────\n"
            "Пока пусто. Загляните в каталог — там живут ароматы."
        )
        return text, back_to_menu_kb()

    total = await db.cart_total(user_id)
    lines = ["<b>🛒 Корзина</b>", "────────────"]
    for it in items:
        line_sum = int(it["price"] * it["qty"])
        lines.append(
            f"• {it['name']} · {it['volume_ml']} мл × {it['qty']} = <b>{line_sum} ₽</b>"
        )
    lines.append("────────────")
    lines.append(f"<b>Итого:</b> {int(total)} ₽")
    return "\n".join(lines), cart_kb(items)


@router.callback_query(F.data == "cart")
async def show_cart(callback: CallbackQuery, user: dict) -> None:
    text, kb = await _render_cart(user["id"])
    try:
        await callback.message.edit_text(text, reply_markup=kb)
    except Exception:
        await callback.message.delete()
        await callback.message.answer(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("cart:add:"))
async def cart_add(callback: CallbackQuery, user: dict) -> None:
    _, _, pid_s, vol_s = callback.data.split(":")
    product_id, volume_ml = int(pid_s), int(vol_s)

    product = await db.get_product(product_id)
    if not product:
        await callback.answer("Товар не найден", show_alert=True)
        return
    if product["stock"] <= 0:
        await callback.answer("Этого аромата нет в наличии", show_alert=True)
        return

    # проверка остатка
    existing = await db.cart_get(user["id"])
    current_qty = sum(
        it["qty"] for it in existing
        if it["product_id"] == product_id and it["volume_ml"] == volume_ml
    )
    if current_qty + 1 > product["stock"]:
        await callback.answer(
            f"Доступно максимум {product['stock']} шт.", show_alert=True
        )
        return

    await db.cart_add(user["id"], product_id, volume_ml, 1)
    await callback.answer("Добавлено в корзину 🛒")


@router.callback_query(F.data.startswith("cart:inc:"))
async def cart_inc(callback: CallbackQuery, user: dict) -> None:
    cart_id = int(callback.data.split(":")[2])
    await db.cart_inc(cart_id)
    text, kb = await _render_cart(user["id"])
    try:
        await callback.message.edit_text(text, reply_markup=kb)
    except Exception:
        pass
    await callback.answer()


@router.callback_query(F.data.startswith("cart:dec:"))
async def cart_dec(callback: CallbackQuery, user: dict) -> None:
    cart_id = int(callback.data.split(":")[2])
    await db.cart_dec(cart_id)
    text, kb = await _render_cart(user["id"])
    try:
        await callback.message.edit_text(text, reply_markup=kb)
    except Exception:
        pass
    await callback.answer()


@router.callback_query(F.data.startswith("cart:del:"))
async def cart_del(callback: CallbackQuery, user: dict) -> None:
    cart_id = int(callback.data.split(":")[2])
    await db.cart_remove(cart_id)
    text, kb = await _render_cart(user["id"])
    try:
        await callback.message.edit_text(text, reply_markup=kb)
    except Exception:
        pass
    await callback.answer("Удалено")


@router.callback_query(F.data == "cart:clear")
async def cart_clear(callback: CallbackQuery, user: dict) -> None:
    await db.cart_clear(user["id"])
    text, kb = await _render_cart(user["id"])
    try:
        await callback.message.edit_text(text, reply_markup=kb)
    except Exception:
        pass
    await callback.answer("Корзина очищена")


# ---------------------------------------------------------
# Оформление заказа
# ---------------------------------------------------------
@router.callback_query(F.data == "order:start")
async def order_start(callback: CallbackQuery, user: dict, state: FSMContext) -> None:
    items = await db.cart_get(user["id"])
    if not items:
        await callback.answer("Корзина пуста", show_alert=True)
        return

    await state.clear()
    await state.set_state(OrderStates.name)
    await state.update_data(order_items=items, user_id=user["id"])

    await callback.message.answer(
        "<b>Оформление заказа · 1/5</b>\n────────────\n"
        "Как вас зовут?"
    )
    await callback.answer()


@router.message(OrderStates.name, F.text)
async def order_name(message: Message, state: FSMContext) -> None:
    name = (message.text or "").strip()
    if len(name) < 2:
        await message.answer("Имя слишком короткое. Попробуйте ещё раз.")
        return
    await state.update_data(name=name)
    await state.set_state(OrderStates.phone)
    await message.answer(
        "<b>Оформление заказа · 2/5</b>\n────────────\n"
        "Телефон для связи (например: <code>+79991234567</code>):"
    )


@router.message(OrderStates.phone, F.text)
async def order_phone(message: Message, state: FSMContext) -> None:
    raw = (message.text or "").replace(" ", "").replace("-", "").strip()
    if not PHONE_RE.match(raw):
        await message.answer("Не похоже на телефон. Формат: <code>+79991234567</code>")
        return
    await state.update_data(phone=raw)
    await state.set_state(OrderStates.address)
    await message.answer(
        "<b>Оформление заказа · 3/5</b>\n────────────\n"
        "Адрес доставки (город, улица, дом, квартира):"
    )


@router.message(OrderStates.address, F.text)
async def order_address(message: Message, state: FSMContext) -> None:
    addr = (message.text or "").strip()
    if len(addr) < 5:
        await message.answer("Адрес слишком короткий.")
        return
    await state.update_data(address=addr)
    await state.set_state(OrderStates.comment)
    await message.answer(
        "<b>Оформление заказа · 4/5</b>\n────────────\n"
        "Комментарий к заказу (или нажмите «Пропустить»):",
        reply_markup=skip_comment_kb(),
    )


@router.callback_query(OrderStates.comment, F.data == "order:skip_comment")
async def order_skip_comment(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(comment="")
    await state.set_state(OrderStates.payment)
    await callback.message.edit_text(
        "<b>Оформление заказа · 5/5</b>\n────────────\n"
        "Способ оплаты:",
        reply_markup=payment_kb(),
    )
    await callback.answer()


@router.message(OrderStates.comment, F.text)
async def order_comment(message: Message, state: FSMContext) -> None:
    await state.update_data(comment=(message.text or "").strip())
    await state.set_state(OrderStates.payment)
    await message.answer(
        "<b>Оформление заказа · 5/5</b>\n────────────\n"
        "Способ оплаты:",
        reply_markup=payment_kb(),
    )


@router.callback_query(OrderStates.payment, F.data.startswith("pay:"))
async def order_payment(callback: CallbackQuery, state: FSMContext) -> None:
    method = callback.data.split(":")[1]
    if method not in PAYMENT_LABELS:
        await callback.answer("Неизвестный способ", show_alert=True)
        return
    await state.update_data(payment=PAYMENT_LABELS[method])
    data = await state.get_data()

    total = sum(int(it["price"] * it["qty"]) for it in data["order_items"])
    summary = [
        "<b>Проверьте заказ:</b>",
        "────────────",
        f"<b>Имя:</b> {data['name']}",
        f"<b>Телефон:</b> {data['phone']}",
        f"<b>Адрес:</b> {data['address']}",
        f"<b>Оплата:</b> {PAYMENT_LABELS[method]}",
    ]
    if data.get("comment"):
        summary.append(f"<b>Комментарий:</b> {data['comment']}")
    summary.append("────────────")
    for it in data["order_items"]:
        summary.append(f"• {it['name']} · {it['volume_ml']} мл × {it['qty']}")
    summary.append(f"────────────\n<b>Итого:</b> {total} ₽")

    await callback.message.edit_text(
        "\n".join(summary), reply_markup=order_confirm_kb()
    )
    await callback.answer()


@router.callback_query(OrderStates.payment, F.data == "order:cancel")
async def order_cancel(callback: CallbackQuery, state: FSMContext, user: dict) -> None:
    await state.clear()
    text, kb = await _render_cart(user["id"])
    try:
        await callback.message.edit_text(text, reply_markup=kb)
    except Exception:
        pass
    await callback.answer("Заказ отменён")


@router.callback_query(OrderStates.payment, F.data == "order:confirm")
async def order_confirm(
    callback: CallbackQuery, state: FSMContext, user: dict, bot: Bot, is_admin: bool
) -> None:
    data = await state.get_data()
    items = data["order_items"]
    total = sum(int(it["price"] * it["qty"]) for it in items)

    # проверка остатков ещё раз
    for it in items:
        p = await db.get_product(it["product_id"])
        if not p or p["stock"] < it["qty"]:
            await callback.answer(
                f"Товар «{it['name']}» больше не доступен в нужном количестве",
                show_alert=True,
            )
            await state.clear()
            return

    order_id = await db.create_order(
        user_id=user["id"],
        name=data["name"],
        phone=data["phone"],
        address=data["address"],
        comment=data.get("comment", ""),
        payment=data["payment"],
        items=items,
        total=total,
    )
    await db.cart_clear(user["id"])

    # сохраним телефон в профиле, если ещё нет
    if not user.get("phone"):
        await db.update_user(user["id"], phone=data["phone"])

    await state.clear()

    number = f"AT-{order_id:06d}"
    await callback.message.edit_text(
        f"<b>Заказ {number} оформлен ✅</b>\n"
        "────────────\n"
        "Мы свяжемся с вами в ближайшее время.\n"
        "Спасибо, что выбрали Atmosphere of Time 🕰️",
        reply_markup=main_menu_kb(0),
    )
    await callback.answer("Заказ оформлен")

    # уведомление админу
    from bot.config import load_config
    cfg = load_config()
    admin_text = (
        f"🆕 <b>Новый заказ {number}</b>\n"
        "────────────\n"
        f"👤 {data['name']}\n"
        f"📞 {data['phone']}\n"
        f"📍 {data['address']}\n"
        f"💳 {data['payment']}\n"
        f"💬 {data.get('comment') or '—'}\n"
        "────────────\n"
        + "\n".join(
            f"• {it['name']} · {it['volume_ml']} мл × {it['qty']} — {int(it['price'] * it['qty'])} ₽"
            for it in items
        )
        + f"\n────────────\n<b>Итого: {total} ₽</b>"
    )
    try:
        await bot.send_message(cfg.admin_id, admin_text)
    except Exception as e:
        log.warning("Не удалось отправить уведомление админу: %s", e)