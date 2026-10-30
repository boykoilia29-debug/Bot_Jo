"""Статичные экраны: О магазине, Поддержка."""
from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot.keyboards.common import back_to_menu_kb

router = Router(name="static")

ABOUT_TEXT = (
    "<b>ℹ️ О магазине</b>\n"
    "────────────\n"
    "<b>Atmosphere of Time</b> — с 2024 года мы ищем ароматы, в которых "
    "время ощущается физически: как тепло амбры, как прохлада кедра, как "
    "тишина после дождя.\n\n"
    "Мы работаем только с нишевой парфюмерией и небольшими ателье. "
    "Каждый флакон — отдельная история.\n\n"
    "📍 Доставка по всей России\n"
    "🚚 2–7 дней\n"
    "💎 Оригинальная продукция\n\n"
    "🕰️ <i>Atmosphere of Time — время, которое можно носить.</i>"
)

SUPPORT_TEXT = (
    "<b>📞 Поддержка</b>\n"
    "────────────\n"
    "Возникли вопросы по заказу или аромату? Мы рядом.\n\n"
    "✉️ Email: <code>care@atmosphere-of-time.ru</code>\n"
    "💬 Telegram: @Normai0\n"
    "🕒 Ежедневно с 10:00 до 21:00 (МСК)"
)


@router.callback_query(F.data == "about")
async def about(callback: CallbackQuery) -> None:
    try:
        await callback.message.edit_text(ABOUT_TEXT, reply_markup=back_to_menu_kb())
    except Exception:
        await callback.message.delete()
        await callback.message.answer(ABOUT_TEXT, reply_markup=back_to_menu_kb())
    await callback.answer()


@router.callback_query(F.data == "support")
async def support(callback: CallbackQuery) -> None:
    try:
        await callback.message.edit_text(SUPPORT_TEXT, reply_markup=back_to_menu_kb())
    except Exception:
        await callback.message.delete()
        await callback.message.answer(SUPPORT_TEXT, reply_markup=back_to_menu_kb())
    await callback.answer()