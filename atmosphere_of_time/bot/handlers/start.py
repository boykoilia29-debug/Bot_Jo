"""/start, /help и главное меню."""
from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message

from bot.database import db
from bot.keyboards.common import main_menu_kb

router = Router(name="start")

WELCOME = (
    "<b>Добро пожаловать в Atmosphere of Time 🕰️</b>\n"
    "────────────\n"
    "Парфюмерия, в которой живёт время.\n"
    "Мы собираем ароматы, которые остаются с вами — как часы на запястье.\n\n"
    "Выберите, с чего начать:"
)


@router.message(CommandStart())
async def cmd_start(message: Message, user: dict) -> None:
    count = await db.cart_count(user["id"])
    await message.answer(WELCOME, reply_markup=main_menu_kb(count))


@router.message(Command("help"))
async def cmd_help(message: Message, user: dict) -> None:
    await message.answer(
        "<b>Что я умею?</b>\n"
        "────────────\n"
        "🛍 <b>Каталог</b> — разделы ароматов и карточки товаров.\n"
        "🛒 <b>Корзина</b> — количество, оформление, оплата.\n"
        "👤 <b>Профиль</b> — данные и история заказов.\n"
        "🔍 <b>Поиск</b> — по названию или бренду.\n\n"
        "По вопросам — в разделе 📞 Поддержка.",
        reply_markup=main_menu_kb(await db.cart_count(user["id"])),
    )


@router.callback_query(F.data == "main_menu")
async def back_to_main(callback: CallbackQuery, user: dict) -> None:
    count = await db.cart_count(user["id"])
    # если висит фото — удаляем и отправляем заново, иначе редактируем
    if callback.message.photo:
        await callback.message.delete()
        await callback.message.answer(WELCOME, reply_markup=main_menu_kb(count))
    else:
        try:
            await callback.message.edit_text(WELCOME, reply_markup=main_menu_kb(count))
        except Exception:
            await callback.message.answer(WELCOME, reply_markup=main_menu_kb(count))
    await callback.answer()


@router.callback_query(F.data == "noop")
async def noop(callback: CallbackQuery) -> None:
    await callback.answer()