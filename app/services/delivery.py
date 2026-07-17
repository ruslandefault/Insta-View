"""Kontentni Telegram'da yetkazib berish (prompt 3.9).

Har element alohida xabar: muallif, joylangan vaqti (user tz), tur,
caption, media (yoki permalink fallback), originalga havola.
Yetkazish idempotent — `deliveries` jadvali orqali (prompt 8).
"""
from __future__ import annotations

import html
import logging
import os
import shutil
import tempfile
from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import FSInputFile
from sqlalchemy import insert
from sqlalchemy.exc import IntegrityError

from app.db.base import session_scope
from app.db.models import Delivery
from app.instagram import shared
from app.instagram.base import FetchedMedia
from app.services.video import ensure_under_limit

logger = logging.getLogger(__name__)

_TYPE_LABEL = {"reel": "🎬 Reel", "story": "📸 Story", "post": "🖼 Post"}
_CAPTION_LIMIT = 700  # Telegram media caption ~1024, zaxira qoldiramiz


def _format_caption(media: FetchedMedia, tz: str) -> str:
    author = media.author_username or "?"
    lines = [
        f"👤 <b>Muallif:</b> <a href=\"https://instagram.com/{author}\">@{author}</a>",
    ]
    if media.posted_at:
        try:
            local = media.posted_at.astimezone(ZoneInfo(tz))
            lines.append(f"🕐 <b>Joylangan:</b> {local.strftime('%Y-%m-%d %H:%M')}")
        except Exception:  # noqa: BLE001
            pass
    lines.append(f"🏷 <b>Turi:</b> {_TYPE_LABEL.get(media.media_type, media.media_type)}")

    if media.caption:
        cap = media.caption.strip()
        if len(cap) > _CAPTION_LIMIT:
            cap = cap[:_CAPTION_LIMIT] + "…"
        lines.append("")
        lines.append(f"📝 {html.escape(cap)}")

    if media.permalink:
        lines.append("")
        lines.append(f"🔗 <a href=\"{media.permalink}\">Originalga o'tish</a>")

    return "\n".join(lines)


async def _mark_delivered(user_id: int, content_item_id: int) -> None:
    try:
        async with session_scope() as session:
            await session.execute(
                insert(Delivery).values(user_id=user_id, content_item_id=content_item_id)
            )
    except IntegrityError:
        pass  # allaqachon yozilgan (parallel cycle) — idempotent


async def deliver(bot: Bot, user_id: int, telegram_id: int, tz: str, pending: list) -> int:
    """Pending elementlarni yuboradi, yuborilganlar sonini qaytaradi."""
    if not pending:
        return 0

    fetcher = await shared.get_shared()
    # eng eski birinchi
    pending.sort(key=lambda p: p.media.posted_at or datetime.min.replace(tzinfo=ZoneInfo("UTC")))

    work_dir = tempfile.mkdtemp(prefix="iv_")
    sent = 0
    try:
        for p in pending:
            media: FetchedMedia = p.media
            caption = _format_caption(media, tz)
            ok = await _send_one(bot, telegram_id, media, caption, fetcher, work_dir)
            if ok:
                await _mark_delivered(user_id, p.content_item_id)
                sent += 1
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)
    return sent


async def _send_one(bot, telegram_id, media, caption, fetcher, work_dir) -> bool:
    path = None
    if fetcher is not None:
        path = await fetcher.download(media, work_dir)

    if path and os.path.exists(path):
        sendable, _compressed = await ensure_under_limit(path)
        if sendable:
            try:
                file = FSInputFile(sendable)
                if media.is_video:
                    await bot.send_video(telegram_id, file, caption=caption, parse_mode="HTML")
                else:
                    await bot.send_photo(telegram_id, file, caption=caption, parse_mode="HTML")
                return True
            except TelegramBadRequest as exc:
                logger.warning("media yuborilmadi, fallback: %s", exc)

    # Fallback — matn + permalink
    text = caption
    if media.permalink is None and media.media_url:
        text += f"\n\n🔗 {media.media_url}"
    try:
        await bot.send_message(telegram_id, text, parse_mode="HTML", disable_web_page_preview=False)
        return True
    except TelegramBadRequest as exc:
        logger.warning("xabar yuborilmadi: %s", exc)
        return False
