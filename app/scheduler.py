"""Rejalashtirilgan avtomatik fetch (prompt 7).

AsyncIOScheduler har ~30 daqiqada tick qiladi. Har aktiv foydalanuvchi uchun
`now - last_poll_at >= 24h / polls_per_day` bo'lsa — fetch → deliver → last_poll_at yangilanadi.
Yuk kun bo'yi tabiiy taqsimlanadi (har kim o'z chastotasi bo'yicha).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select, update

from app.bot.notify import notify_admin_issue
from app.config import settings
from app.db.base import session_scope
from app.db.models import User, UserSettings
from app.services.delivery import deliver
from app.services.fetch_service import poll_user

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class DueUser:
    user_id: int
    telegram_id: int
    tz: str


async def _collect_due() -> list[DueUser]:
    now = datetime.now(timezone.utc)
    due: list[DueUser] = []
    async with session_scope() as session:
        rows = (
            await session.execute(
                select(
                    User.id, User.telegram_id, User.tz,
                    UserSettings.polls_per_day, UserSettings.last_poll_at,
                )
                .join(UserSettings, UserSettings.user_id == User.id)
            )
        ).all()

    for user_id, tg_id, tz, polls_per_day, last_poll_at in rows:
        interval = timedelta(hours=24 / max(1, polls_per_day))
        if last_poll_at is None or (now - last_poll_at) >= interval:
            due.append(DueUser(user_id, tg_id, tz))
    return due


async def _mark_polled(user_id: int) -> None:
    now = datetime.now(timezone.utc)
    async with session_scope() as session:
        await session.execute(
            update(UserSettings).where(UserSettings.user_id == user_id).values(last_poll_at=now)
        )


async def tick(bot: Bot) -> None:
    due = await _collect_due()
    if not due:
        return
    logger.info("scheduler tick: %d foydalanuvchi navbatda", len(due))

    # ketma-ket (burst emas) — IG yukini tabiiy taqsimlash
    for du in due:
        try:
            result = await poll_user(du.user_id)
            await deliver(bot, du.user_id, du.telegram_id, du.tz, result.pending)
            if result.error is not None:
                await notify_admin_issue(bot, result)
        except Exception:  # noqa: BLE001
            logger.exception("scheduler: user %s uchun xato", du.user_id)
        finally:
            await _mark_polled(du.user_id)


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(
        tick,
        "interval",
        minutes=settings.scheduler_interval_minutes,
        args=[bot],
        id="poll_tick",
        max_instances=1,
        coalesce=True,
    )
    return scheduler
