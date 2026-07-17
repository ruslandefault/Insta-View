"""Katta videolarni ffmpeg bilan siqish (prompt 3.9).

Telegram bot fayl chegarasi ~50MB. Undan katta bo'lsa H.264 two-pass
kodlash bilan ~45MB gacha siqiladi. Baribir katta bo'lsa — fallback (permalink).
"""
from __future__ import annotations

import asyncio
import logging
import os
import tempfile

from app.config import settings

logger = logging.getLogger(__name__)

_MAX_BYTES = settings.max_telegram_file_mb * 1024 * 1024
_TARGET_MB = settings.target_file_mb


async def _run(*args: str) -> tuple[int, str]:
    proc = await asyncio.create_subprocess_exec(
        *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
    )
    out, _ = await proc.communicate()
    return proc.returncode or 0, out.decode(errors="ignore")


async def _duration_seconds(path: str) -> float:
    code, out = await _run(
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", path,
    )
    try:
        return float(out.strip())
    except ValueError:
        return 0.0


async def ensure_under_limit(path: str) -> tuple[str | None, bool]:
    """Faylni Telegram chegarasiga moslashtiradi.

    Qaytaradi: (yuboriladigan_yo'l | None, compressed_bool).
    None — siqib bo'lmadi, permalink fallback ishlatish kerak.
    """
    try:
        size = os.path.getsize(path)
    except OSError:
        return None, False

    if size <= _MAX_BYTES:
        return path, False  # siqish shart emas

    duration = await _duration_seconds(path)
    if duration <= 0:
        logger.warning("duration aniqlanmadi: %s", path)
        return None, False

    # Maqsad bitrate (kbit/s): audio uchun ~128 kbit/s ajratamiz
    target_video_bitrate = int((_TARGET_MB * 8 * 1024) / duration - 128)
    if target_video_bitrate < 100:
        # Video juda uzun/katta — siqib bo'lmaydi
        return None, False

    out_path = os.path.join(tempfile.gettempdir(), f"compressed_{os.path.basename(path)}")
    passlog = os.path.join(tempfile.gettempdir(), f"pass_{os.getpid()}")
    scale = "scale='min(1080,iw)':-2"  # eni 1080px dan katta bo'lsa kichraytiriladi
    vb = f"{target_video_bitrate}k"

    # Pass 1 (video yo'q, statistika)
    code1, _ = await _run(
        "ffmpeg", "-y", "-i", path, "-vf", scale, "-c:v", "libx264",
        "-b:v", vb, "-pass", "1", "-passlogfile", passlog,
        "-an", "-f", "mp4", os.devnull,
    )
    # Pass 2
    code2, _ = await _run(
        "ffmpeg", "-y", "-i", path, "-vf", scale, "-c:v", "libx264",
        "-b:v", vb, "-pass", "2", "-passlogfile", passlog,
        "-c:a", "aac", "-b:a", "128k", out_path,
    )

    # passlog fayllarini tozalash
    for suffix in ("-0.log", "-0.log.mbtree"):
        try:
            os.remove(passlog + suffix)
        except OSError:
            pass

    if code1 != 0 or code2 != 0 or not os.path.exists(out_path):
        logger.warning("ffmpeg siqish muvaffaqiyatsiz (%s)", path)
        return None, False

    if os.path.getsize(out_path) > _MAX_BYTES:
        return None, False  # baribir katta — fallback

    return out_path, True
