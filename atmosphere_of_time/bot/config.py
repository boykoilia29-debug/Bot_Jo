"""Конфигурация бота — читается из .env рядом с корнем проекта."""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Явно указываем путь: bot/config.py → parent.parent = корень проекта
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / ".env"

# Загружаем с явным путём, принудительно перезаписывая системные переменные,
# и с encoding="utf-8" (на Windows это критично — иначе utf-16/cyrillic ломается)
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH, override=True, encoding="utf-8")
else:
    load_dotenv(override=True, encoding="utf-8")  # fallback на CWD
    print(
        f"[config] ВНИМАНИЕ: файл {ENV_PATH} не найден.\n"
        f"[config] Скопируйте .env.example → .env и заполните токены.",
        file=sys.stderr,
    )


@dataclass(frozen=True)
class Config:
    bot_token: str
    admin_id: int
    db_path: str


_PLACEHOLDER_TOKEN = "1234567890:AAEEexample-token-replace-me"


def load_config() -> Config:
    """Загружает и валидирует переменные окружения с понятными ошибками."""
    token = os.getenv("BOT_TOKEN", "").strip()
    admin_raw = os.getenv("ADMIN_ID", "").strip()

    errors: list[str] = []
    if not token:
        errors.append("BOT_TOKEN пуст или не задан")
    elif token == _PLACEHOLDER_TOKEN or not token.count(":") == 1:
        errors.append(
            "BOT_TOKEN — это плейсхолдер из .env.example. "
            "Вставьте реальный токен от @BotFather"
        )
    if not admin_raw.isdigit():
        errors.append("ADMIN_ID должен быть числом (ваш Telegram ID)")

    if errors:
        raise RuntimeError(
            "\n" + "=" * 60 + "\n"
            "❌ ОШИБКА КОНФИГУРАЦИИ\n"
            f"Искали файл: {ENV_PATH}\n"
            f"Файл существует: {'ДА' if ENV_PATH.exists() else 'НЕТ'}\n"
            "Проблемы:\n  - " + "\n  - ".join(errors) + "\n\n"
            "Как исправить:\n"
            "  1) Откройте PowerShell в корне проекта\n"
            "  2) copy .env.example .env\n"
            "  3) Откройте .env в VS Code / Notepad++\n"
            "  4) Вставьте реальный BOT_TOKEN и ADMIN_ID\n"
            "  5) Сохраните в кодировке UTF-8\n"
            "  6) Запустите снова\n"
            + "=" * 60
        )

    return Config(
        bot_token=token,
        admin_id=int(admin_raw),
        db_path=os.getenv("DB_PATH", "atmosphere.db"),
    )