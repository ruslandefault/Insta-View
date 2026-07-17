"""Per-user fetcher menejeri.

- `pending_logins`: login FSM davomida (2FA/challenge) instance'ni ushlab turadi
  (telegram_id bo'yicha).
- `_active`: aktiv akkaunt sessiyalarini xotirada keshlaydi (user_id bo'yicha),
  qayta login'ni minimallashtirish uchun (prompt 5).
"""
from __future__ import annotations

import logging

from app.crypto import decrypt
from app.db.models import IgAccount
from app.instagram.instagrapi_fetcher import InstagrapiFetcher

logger = logging.getLogger(__name__)

# Login jarayonidagi (hali saqlanmagan) fetcher'lar — telegram_id bo'yicha
pending_logins: dict[int, InstagrapiFetcher] = {}

# Aktiv sessiyalar keshi — user_id (DB) bo'yicha
_active: dict[int, InstagrapiFetcher] = {}


async def get_active_fetcher(account: IgAccount) -> InstagrapiFetcher | None:
    """Aktiv akkaunt uchun tayyor (resume qilingan) fetcher qaytaradi."""
    cached = _active.get(account.user_id)
    if cached is not None:
        return cached

    if not account.enc_session:
        return None

    fetcher = InstagrapiFetcher()
    ok = await fetcher.resume(decrypt(account.enc_session))
    if not ok:
        # sessiya eskirgan — parol bilan qayta login urinamiz
        if not account.enc_password:
            return None
        outcome = await fetcher.login(account.ig_username, decrypt(account.enc_password))
        from app.instagram.base import LoginResult

        if outcome.result is not LoginResult.ok:
            logger.info("qayta login muvaffaqiyatsiz: @%s", account.ig_username)
            return None

    _active[account.user_id] = fetcher
    return fetcher


def get_cached(user_id: int) -> InstagrapiFetcher | None:
    return _active.get(user_id)


def set_active(user_id: int, fetcher: InstagrapiFetcher) -> None:
    _active[user_id] = fetcher


def drop_active(user_id: int) -> None:
    _active.pop(user_id, None)
