"""Akkaunt muammolari haqida foydalanuvchini ogohlantirish (prompt 3.8)."""
from __future__ import annotations

from aiogram import Bot

from app.bot import keyboards, texts
from app.instagram.base import FetchErrorKind
from app.services.fetch_service import PollResult

_BLOCK_KINDS = {
    FetchErrorKind.challenge,
    FetchErrorKind.feedback,
    FetchErrorKind.forbidden,
    FetchErrorKind.login_required,
}


async def notify_account_issue(bot: Bot, telegram_id: int, result: PollResult) -> None:
    if result.error is None:
        return
    kind = result.error.kind
    username = result.account_username or "?"

    if kind in _BLOCK_KINDS:
        await bot.send_message(
            telegram_id,
            texts.ACCOUNT_BLOCKED.format(username=username),
            parse_mode="HTML",
            reply_markup=keyboards.add_account_kb(),
        )
    elif kind is FetchErrorKind.rate_limit:
        await bot.send_message(telegram_id, texts.RATE_LIMITED)
