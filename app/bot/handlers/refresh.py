"""Qo'lda "Yangilash" — cooldown bilan (prompt 3.6)."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from aiogram import F, Router
from aiogram.types import Message

from app.bot import keyboards, texts
from app.bot.notify import notify_admin_issue
from app.config import settings
from app.db.base import session_scope
from app.services.delivery import deliver
from app.services.fetch_service import poll_user
from app.services.users import get_user_by_tg

logger = logging.getLogger(__name__)
router = Router()

# 5 daqiqalik cooldown — telegram_id bo'yicha (xotirada)
_last_refresh: dict[int, datetime] = {}


@router.message(F.text == keyboards.BTN_REFRESH)
async def manual_refresh(message: Message) -> None:
    tg_id = message.from_user.id
    now = datetime.now(timezone.utc)
    cooldown = timedelta(minutes=settings.refresh_cooldown_minutes)

    last = _last_refresh.get(tg_id)
    if last and now - last < cooldown:
        left = int((cooldown - (now - last)).total_seconds() // 60) + 1
        await message.answer(
            texts.REFRESH_COOLDOWN.format(minutes=settings.refresh_cooldown_minutes, left=left)
        )
        return

    async with session_scope() as session:
        user = await get_user_by_tg(session, tg_id)
        if user is None:
            await message.answer("❗ Avval /start bosing.")
            return
        user_id, tz = user.id, user.tz

    _last_refresh[tg_id] = now
    await message.answer(texts.REFRESH_START)

    result = await poll_user(user_id)
    if result.no_account:
        await message.answer(texts.SERVICE_UNAVAILABLE)
        return

    count = await deliver(message.bot, user_id, tg_id, tz, result.pending)

    if result.error is not None:
        await notify_admin_issue(message.bot, result)

    if count:
        await message.answer(texts.REFRESH_DONE.format(count=count))
    elif result.error is not None:
        await message.answer(texts.REFRESH_TEMPORARY_FAIL)
    else:
        await message.answer(texts.REFRESH_NOTHING)
