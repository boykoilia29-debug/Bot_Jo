"""FSM-поиск по названию и бренду."""
from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.database import db
from bot.keyboards.catalog import search_results_kb
from bot.keyboards.common import back_kb
from bot.states import SearchStates

router = Router(name="search")


@router.callback_query(F.data == "search")
async def search_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(SearchStates.query)
    text = (
        "<b>🔍 Поиск</b>\n────────────\n"
        "Введите название аромата или бренд.\n"
        "<i>Например: Time, Noir, AoT</i>"
    )
    try:
        await callback.message.edit_text(text, reply_markup=back_kb("catalog", "◀️ Отмена"))
    except Exception:
        await callback.message.answer(text, reply_markup=back_kb("catalog", "◀️ Отмена"))
    await callback.answer()


@router.message(StateFilter(SearchStates.query), F.text)
async def search_process(message: Message, state: FSMContext) -> None:
    query = (message.text or "").strip()
    if len(query) < 2:
        await message.answer("Слишком короткий запрос. Введите хотя бы 2 символа.")
        return

    products = await db.search_products(query)
    await state.clear()

    if not products:
        await message.answer(
            f"<b>По запросу «{query}»</b> ничего не найдено.\n"
            "Попробуйте другое слово.",
            reply_markup=back_kb("catalog", "◀️ В каталог"),
        )
        return

    await message.answer(
        f"<b>Результаты поиска:</b> «{query}»\n"
        f"────────────\nНайдено: {len(products)}",
        reply_markup=search_results_kb(products),
    )