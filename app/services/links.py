"""Instagram linklarini parse qilish (prompt 3.4)."""
from __future__ import annotations

import re

_RESERVED = {"p", "reel", "reels", "stories", "tv", "explore", "accounts"}

_MEDIA_RE = re.compile(r"instagram\.com/(?:[^/]+/)?(?:p|reel|reels|tv)/([A-Za-z0-9_-]+)", re.I)
_PROFILE_RE = re.compile(r"instagram\.com/([A-Za-z0-9_.]+)", re.I)


def parse_ig_link(text: str) -> tuple[str | None, str | None]:
    """Qaytaradi: ("media", url) | ("profile", username) | (None, None)."""
    text = text.strip()

    m = _MEDIA_RE.search(text)
    if m:
        return "media", text

    p = _PROFILE_RE.search(text)
    if p:
        username = p.group(1).strip("/").lower()
        if username and username not in _RESERVED:
            return "profile", username

    # sof username ("@nasa" yoki "nasa")
    bare = text.lstrip("@").strip()
    if re.fullmatch(r"[A-Za-z0-9_.]+", bare) and bare.lower() not in _RESERVED:
        return "profile", bare.lower()

    return None, None
