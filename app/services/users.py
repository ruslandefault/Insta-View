"""User bilan bog'liq umumiy DB yordamchilari."""
from __future__ import annotations

from sqlalchemy import select

from app.db.models import User, UserSettings


async def get_user_by_tg(session, telegram_id: int) -> User | None:
    return (
        await session.execute(select(User).where(User.telegram_id == telegram_id))
    ).scalar_one_or_none()


async def ensure_settings(session, user_id: int) -> UserSettings:
    us = (
        await session.execute(select(UserSettings).where(UserSettings.user_id == user_id))
    ).scalar_one_or_none()
    if us is None:
        us = UserSettings(user_id=user_id)
        session.add(us)
        await session.flush()
    return us
