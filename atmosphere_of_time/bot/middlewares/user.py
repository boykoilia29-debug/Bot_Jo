"""Middleware: авторегистрация пользователя + инжект объекта user в хендлер."""
from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from bot.database import db

log = logging.getLogger(__name__)


class UserMiddleware(BaseMiddleware):
    def __init__(self, admin_id: int) -> None:
        self.admin_id = admin_id

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        tg_user = getattr(event, "from_user", None)
        if tg_user is None or tg_user.is_bot:
            return await handler(event, data)

        user = await db.get_user_by_tg(tg_user.id)
        if user is None:
            await db.create_user(tg_user.id, tg_user.username, tg_user.full_name)
            user = await db.get_user_by_tg(tg_user.id)
            log.info("Зарегистрирован новый пользователь tg_id=%s", tg_user.id)
        else:
            # Обновим username/full_name если поменялись
            updates: dict[str, Any] = {}
            if user["username"] != tg_user.username:
                updates["username"] = tg_user.username
            if user["full_name"] != tg_user.full_name:
                updates["full_name"] = tg_user.full_name
            if updates:
                await db.update_user(user["id"], **updates)
                user = await db.get_user_by_tg(tg_user.id)

        data["user"] = user
        data["is_admin"] = tg_user.id == self.admin_id
        return await handler(event, data)


class UserMiddlewareShim:  # pragma: no cover
    """Заглушка для type-checker'ов."""
    pass