"""Shared akkaunt muammolari haqida ADMINni ogohlantirish (prompt 3.8).

Foydalanuvchilar shaxsiy akkaunt kiritmagani uchun ban/challenge xabari
markaziy akkaunt egasiga (admin) boradi, oddiy foydalanuvchiga emas."""
from __future__ import annotations

import logging

from aiogram import Bot

from app.config import settings
from app.instagram.base import FetchErrorKind
from app.services.fetch_service import PollResult

logger = logging.getLogger(__name__)

_BLOCK_KINDS = {
    FetchErrorKind.challenge,
    FetchErrorKind.feedback,
    FetchErrorKind.forbidden,
    FetchErrorKind.login_required,
}


async def notify_admin_issue(bot: Bot, result: PollResult) -> None:
    if result.error is None:
        return
    kind = result.error.kind

    if kind in _BLOCK_KINDS:
        logger.error("SHARED AKKAUNT MUAMMOSI: %s — fetch to'xtatildi", kind.value)
        if settings.admin_telegram_id:
            await bot.send_message(
                settings.admin_telegram_id,
                f"⚠️ Markaziy Instagram akkauntda muammo: <b>{kind.value}</b>.\n"
                f"Fetch to'xtatildi. .env dagi IG_SESSIONID/parolni yangilang.",
                parse_mode="HTML",
            )
    elif kind is FetchErrorKind.rate_limit:
        logger.warning("shared akkaunt rate-limit — keyingi cycle'da qayta urinamiz")
