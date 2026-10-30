"""Точка входа бота Atmosphere of Time."""
from __future__ import annotations

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from bot.config import load_config
from bot.database import db
from bot.handlers import admin, cart, catalog, profile, search, start, static
from bot.middlewares.user import UserMiddleware

log = logging.getLogger(__name__)


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    )
    cfg = load_config()
    log.info("Запуск бота. Admin ID: %s", cfg.admin_id)

    await db.init_db(cfg.db_path)

    bot = Bot(token=cfg.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())

    # middlewares
    mw = UserMiddleware(admin_id=cfg.admin_id)
    dp.message.middleware(mw)
    dp.callback_query.middleware(mw)

    # routers (admin первым, чтобы /admin отрабатывал раньше general)
    dp.include_router(admin.router)
    dp.include_router(start.router)
    dp.include_router(catalog.router)
    dp.include_router(search.router)
    dp.include_router(cart.router)
    dp.include_router(profile.router)
    dp.include_router(static.router)

    await bot.set_my_commands([
        BotCommand(command="start", description="🕰 Главное меню"),
        BotCommand(command="help",  description="ℹ️ Помощь"),
        BotCommand(command="admin", description="🛠 Админ-панель"),
    ])

    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        log.info("Завершение работы…")
        await db.close_db()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен")
        sys.exit(0)