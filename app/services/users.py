"""User bilan bog'liq umumiy DB yordamchilari."""
from __future__ import annotations

from sqlalchemy import select

from app.db.models import AccountStatus, IgAccount, User, UserSettings


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


async def current_account(session, user_id: int) -> IgAccount | None:
    return (
        await session.execute(
            select(IgAccount).where(IgAccount.user_id == user_id, IgAccount.is_current.is_(True))
        )
    ).scalar_one_or_none()


def account_status_label(account: IgAccount | None) -> str:
    if account is None:
        return "ulanmagan"
    labels = {
        AccountStatus.active: "✅ faol",
        AccountStatus.challenge_required: "🛡 tekshiruv kerak",
        AccountStatus.banned: "⛔ bloklangan",
        AccountStatus.invalid: "❌ yaroqsiz",
    }
    return f"@{account.ig_username} — {labels.get(account.status, account.status.value)}"
