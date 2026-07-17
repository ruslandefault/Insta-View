"""Shared (markaziy) Instagram akkaunt menejeri.

Foydalanuvchilar Instagram akkaunt kiritmaydi — barcha fetch `.env` dagi
bitta akkaunt orqali amalga oshadi. Sessiya diskka saqlanadi, shuning uchun
qayta login (throttle sababi) minimallashtiriladi.

Autentifikatsiya tartibi:
  1) saqlangan sessiya fayli (mavjud bo'lsa)
  2) IG_SESSIONID (brauzer cookie — eng barqaror)
  3) IG_USERNAME + IG_PASSWORD
"""
from __future__ import annotations

import asyncio
import logging
import os

from app.config import settings
from app.instagram.base import LoginResult
from app.instagram.instagrapi_fetcher import InstagrapiFetcher

logger = logging.getLogger(__name__)

_lock = asyncio.Lock()
_shared: InstagrapiFetcher | None = None


def _save_session(session_json: str) -> None:
    try:
        with open(settings.shared_session_file, "w", encoding="utf-8") as f:
            f.write(session_json)
    except OSError as exc:
        logger.warning("sessiyani saqlab bo'lmadi: %s", exc)


def _load_session() -> str | None:
    if not os.path.exists(settings.shared_session_file):
        return None
    try:
        with open(settings.shared_session_file, encoding="utf-8") as f:
            return f.read()
    except OSError:
        return None


async def get_shared() -> InstagrapiFetcher | None:
    """Tayyor shared fetcher qaytaradi (yoki None — sozlanmagan/yaroqsiz)."""
    global _shared
    if _shared is not None:
        return _shared

    async with _lock:
        if _shared is not None:
            return _shared

        fetcher = InstagrapiFetcher()

        # 1) saqlangan sessiya
        saved = _load_session()
        if saved and await fetcher.resume(saved):
            logger.info("shared akkaunt: saqlangan sessiyadan tiklandi")
            _shared = fetcher
            return _shared

        # 2) sessionid
        if settings.ig_sessionid:
            if await fetcher.login_by_sessionid(settings.ig_sessionid):
                logger.info("shared akkaunt: sessionid bilan kirildi")
                _save_session(fetcher._dump_session())  # noqa: SLF001
                _shared = fetcher
                return _shared
            logger.error("shared akkaunt: sessionid yaroqsiz")

        # 3) username/parol
        if settings.ig_username and settings.ig_password:
            outcome = await fetcher.login(settings.ig_username, settings.ig_password)
            if outcome.result is LoginResult.ok:
                logger.info("shared akkaunt: parol bilan kirildi (@%s)", settings.ig_username)
                if outcome.session_json:
                    _save_session(outcome.session_json)
                _shared = fetcher
                return _shared
            logger.error(
                "shared akkaunt login muvaffaqiyatsiz: %s (%s). "
                "2FA/challenge bo'lsa IG_SESSIONID dan foydalaning.",
                outcome.result.value, outcome.message,
            )

        logger.error("shared akkaunt sozlanmagan — .env da IG_USERNAME/IG_PASSWORD yoki IG_SESSIONID kerak")
        return None


def reset() -> None:
    """Sessiya yaroqsiz bo'lganda keshni tozalaydi (keyingi urinishda qayta login)."""
    global _shared
    _shared = None
    try:
        if os.path.exists(settings.shared_session_file):
            os.remove(settings.shared_session_file)
    except OSError:
        pass
