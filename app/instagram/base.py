"""Instagram fetcher abstraktsiyasi (SOLID / Protocol).

Kelajakda `instagrapi` ni boshqa implementatsiya bilan almashtirish uchun
barcha kod aynan shu interfeys va DTO'larga bog'lanadi.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol, runtime_checkable


class LoginResult(str, enum.Enum):
    ok = "ok"
    needs_2fa = "needs_2fa"
    needs_challenge = "needs_challenge"
    bad_password = "bad_password"
    error = "error"


class FetchErrorKind(str, enum.Enum):
    """Prompt 3.8 — fetch/login xatolar turlari."""
    challenge = "challenge"          # ChallengeRequired
    login_required = "login_required"
    rate_limit = "rate_limit"        # PleaseWaitFewMinutes / RateLimitError
    feedback = "feedback"            # FeedbackRequired
    forbidden = "forbidden"          # ClientForbiddenError
    private = "private"              # yopiq akkaunt
    not_found = "not_found"
    unknown = "unknown"


class FetchError(Exception):
    def __init__(self, kind: FetchErrorKind, message: str = ""):
        self.kind = kind
        self.message = message or kind.value
        super().__init__(self.message)


@dataclass(slots=True)
class LoginOutcome:
    result: LoginResult
    session_json: str | None = None      # dump_settings natijasi (shifrlanadi)
    message: str = ""


@dataclass(slots=True)
class IgUserInfo:
    pk: str
    username: str
    full_name: str | None = None
    is_private: bool = False


@dataclass(slots=True)
class FetchedMedia:
    ig_media_id: str
    shortcode: str | None
    media_type: str                       # "reel" | "story" | "post"
    author_username: str
    caption: str | None
    posted_at: datetime | None
    media_url: str | None                 # yuklab olinadigan to'g'ridan-to'g'ri URL
    permalink: str | None
    thumbnail_url: str | None = None
    is_video: bool = False
    extra: dict = field(default_factory=dict)


@runtime_checkable
class InstagramFetcher(Protocol):
    """Har foydalanuvchi akkaunti uchun alohida instance/sessiya bilan ishlaydi."""

    async def login(self, username: str, password: str) -> LoginOutcome: ...

    async def submit_2fa(self, code: str) -> LoginOutcome: ...

    async def submit_challenge(self, code: str) -> LoginOutcome: ...

    async def resume(self, session_json: str) -> bool:
        """Shifrlangan sessiyadan tiklaydi. True — sessiya yaroqli."""
        ...

    async def get_user_info(self, username: str) -> IgUserInfo: ...

    async def author_from_media_url(self, url: str) -> IgUserInfo:
        """Post/reel linkidan muallifni aniqlaydi."""
        ...

    async def fetch_medias(self, ig_user_id: str, amount: int = 10) -> list[FetchedMedia]: ...

    async def fetch_stories(self, ig_user_id: str) -> list[FetchedMedia]: ...

    async def download(self, media: FetchedMedia, dest_dir: str) -> str | None:
        """Media faylni yuklab oladi, lokal yo'lni qaytaradi."""
        ...
