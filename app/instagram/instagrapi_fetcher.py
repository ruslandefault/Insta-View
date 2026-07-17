"""`instagrapi` asosidagi InstagramFetcher implementatsiyasi.

instagrapi sinxron (blocking) — barcha chaqiruvlar `asyncio.to_thread`
orqali thread pool'da ishlatiladi, event loop bloklanmasin.

Har foydalanuvchi akkaunti uchun ALOHIDA instance (o'z sessiyasi bilan).
Login FSM davomida instance xotirada saqlanadi (2FA/challenge kodini kutish uchun).
"""
from __future__ import annotations

import asyncio
import json
import logging

from instagrapi import Client
from instagrapi.exceptions import (
    BadPassword,
    ChallengeRequired,
    ClientForbiddenError,
    ClientError,
    FeedbackRequired,
    LoginRequired,
    PleaseWaitFewMinutes,
    PrivateError,
    RateLimitError,
    TwoFactorRequired,
    UserNotFound,
)

from app.config import settings
from app.instagram.base import (
    FetchedMedia,
    FetchError,
    FetchErrorKind,
    IgUserInfo,
    LoginOutcome,
    LoginResult,
)

logger = logging.getLogger(__name__)


def _map_error(exc: Exception) -> FetchError:
    """instagrapi xatosini domen FetchError'iga o'giradi (prompt 3.8)."""
    if isinstance(exc, ChallengeRequired):
        return FetchError(FetchErrorKind.challenge, "Instagram tekshiruv talab qilmoqda")
    if isinstance(exc, LoginRequired):
        return FetchError(FetchErrorKind.login_required, "Qayta login talab qilinadi")
    if isinstance(exc, (PleaseWaitFewMinutes, RateLimitError)):
        return FetchError(FetchErrorKind.rate_limit, "So'rovlar chegarasi — biroz kuting")
    if isinstance(exc, FeedbackRequired):
        return FetchError(FetchErrorKind.feedback, "Instagram harakatni cheklab qo'ydi")
    if isinstance(exc, ClientForbiddenError):
        return FetchError(FetchErrorKind.forbidden, "Kirish taqiqlandi")
    if isinstance(exc, (PrivateError,)):
        return FetchError(FetchErrorKind.private, "Yopiq akkaunt")
    if isinstance(exc, UserNotFound):
        return FetchError(FetchErrorKind.not_found, "Akkaunt topilmadi")
    # 467 — Instagram soft rate-limit/throttle (generic ClientError sifatida keladi)
    text = str(exc)
    if "467" in text or "wait a few minutes" in text.lower():
        return FetchError(
            FetchErrorKind.rate_limit,
            "Instagram bu akkauntni vaqtincha cheklab qo'ydi (ko'p so'rov). "
            "10–30 daqiqa kutib qayta urinib ko'ring.",
        )
    return FetchError(FetchErrorKind.unknown, text or "Noma'lum xato")


class InstagrapiFetcher:
    """InstagramFetcher protokoli implementatsiyasi (bitta akkaunt uchun)."""

    def __init__(self) -> None:
        self.client = Client()
        # So'rovlar orasidagi tasodifiy kutish (throttling) — instagrapi built-in
        self.client.delay_range = [settings.throttle_min_sec, settings.throttle_max_sec]
        self._username: str | None = None
        self._password: str | None = None
        self._challenge_code: str | None = None
        # challenge kodini instagrapi callback'iga uzatish
        self.client.challenge_code_handler = self._challenge_handler

    # ---- login oqimi ----------------------------------------------------

    def _challenge_handler(self, username: str, choice) -> str:  # noqa: ANN001
        """instagrapi challenge kodini shu yerdan so'raydi (sinxron)."""
        if not self._challenge_code:
            raise ChallengeRequired("kod hali kiritilmagan")
        return self._challenge_code

    def _dump_session(self) -> str:
        return json.dumps(self.client.get_settings())

    def _is_authenticated(self) -> bool:
        """accounts/login [200] o'tganini tekshiradi (login_flow'dan oldin ham).

        instagrapi login'dan keyin reels_tray/timeline kabi "warm-up" so'rovlarni
        yuboradi; ular 467 (throttle) bersa ham autentifikatsiya haqiqiy bo'lishi mumkin.
        """
        try:
            if self.client.user_id:
                return True
        except Exception:  # noqa: BLE001
            pass
        return bool(getattr(self.client, "authorization_data", None))

    async def login(self, username: str, password: str) -> LoginOutcome:
        self._username, self._password = username, password
        try:
            await asyncio.to_thread(self.client.login, username, password)
        except TwoFactorRequired:
            return LoginOutcome(LoginResult.needs_2fa, message="2FA kodi kerak")
        except ChallengeRequired:
            # Instagram odatda kodni allaqachon yuborgan bo'ladi
            return LoginOutcome(LoginResult.needs_challenge, message="Tekshiruv kodi kerak")
        except BadPassword:
            return LoginOutcome(LoginResult.bad_password, message="Login yoki parol xato")
        except Exception as exc:  # noqa: BLE001
            # Auth o'tgan-u, faqat login_flow (warm-up) xato bergan bo'lsa — OK deb saqlaymiz
            if self._is_authenticated():
                logger.info("login_flow xatosi e'tiborsiz (auth OK): %s", type(exc).__name__)
                return LoginOutcome(LoginResult.ok, session_json=self._dump_session())
            logger.warning(
                "login xatosi: %s | msg=%s | ig_response=%s",
                type(exc).__name__,
                str(exc)[:300],
                str(getattr(self.client, "last_json", None))[:800],
            )
            return LoginOutcome(LoginResult.error, message=_map_error(exc).message)
        return LoginOutcome(LoginResult.ok, session_json=self._dump_session())

    async def submit_2fa(self, code: str) -> LoginOutcome:
        try:
            await asyncio.to_thread(
                self.client.login, self._username, self._password, False, code
            )
        except ChallengeRequired:
            return LoginOutcome(LoginResult.needs_challenge, message="Tekshiruv kodi kerak")
        except Exception as exc:  # noqa: BLE001
            if self._is_authenticated():
                return LoginOutcome(LoginResult.ok, session_json=self._dump_session())
            return LoginOutcome(LoginResult.error, message="2FA kodi noto'g'ri yoki muddati o'tgan")
        return LoginOutcome(LoginResult.ok, session_json=self._dump_session())

    async def submit_challenge(self, code: str) -> LoginOutcome:
        self._challenge_code = code
        try:
            await asyncio.to_thread(
                self.client.challenge_resolve, self.client.last_json
            )
        except Exception as exc:  # noqa: BLE001
            if self._is_authenticated():
                return LoginOutcome(LoginResult.ok, session_json=self._dump_session())
            self._challenge_code = None
            return LoginOutcome(LoginResult.error, message="Tekshiruv kodi noto'g'ri yoki muddati o'tgan")
        # challenge yakunlandi — sessiya o'rnatilgan bo'lishi kerak
        return LoginOutcome(LoginResult.ok, session_json=self._dump_session())

    async def login_by_sessionid(self, sessionid: str) -> bool:
        """Brauzer sessionid orqali kirish — login challenge/467 bo'lmaydi."""
        try:
            await asyncio.to_thread(self.client.login_by_sessionid, sessionid)
        except Exception as exc:  # noqa: BLE001
            if self._is_authenticated():
                return True
            logger.warning("sessionid login xatosi: %s", type(exc).__name__)
            return False
        return True

    async def resume(self, session_json: str) -> bool:
        try:
            settings_dict = json.loads(session_json)
            await asyncio.to_thread(self.client.set_settings, settings_dict)
            # yengil tekshiruv — sessiya yaroqlimi
            await asyncio.to_thread(self.client.get_timeline_feed)
        except LoginRequired:
            logger.info("sessiya yaroqsiz (LoginRequired)")
            return False
        except Exception as exc:  # noqa: BLE001
            # throttle/467/tarmoq xatosi — sessiya ehtimol yaroqli, keyin qayta urinamiz
            logger.info("resume probe xatosi (sessiya saqlanadi): %s", type(exc).__name__)
        return True

    # ---- fetch ----------------------------------------------------------

    async def get_user_info(self, username: str) -> IgUserInfo:
        try:
            # v1 (private API) — anonim public GraphQL (401) yo'lini o'tkazib yuboramiz
            info = await asyncio.to_thread(self.client.user_info_by_username_v1, username)
        except Exception as exc:  # noqa: BLE001
            raise _map_error(exc) from exc
        return IgUserInfo(
            pk=str(info.pk),
            username=info.username,
            full_name=info.full_name,
            is_private=info.is_private,
        )

    async def author_from_media_url(self, url: str) -> IgUserInfo:
        try:
            pk = await asyncio.to_thread(self.client.media_pk_from_url, url)
            # v1 (private API) — public GraphQL 401 retry'larini o'tkazib yuboramiz
            media = await asyncio.to_thread(self.client.media_info_v1, pk)
        except Exception as exc:  # noqa: BLE001
            raise _map_error(exc) from exc
        return IgUserInfo(
            pk=str(media.user.pk),
            username=media.user.username,
            full_name=media.user.full_name,
            is_private=getattr(media.user, "is_private", False),
        )

    async def fetch_medias(self, ig_user_id: str, amount: int = 10) -> list[FetchedMedia]:
        try:
            # v1 (private API) — public GraphQL 401 yo'lini o'tkazib yuboramiz
            medias = await asyncio.to_thread(self.client.user_medias_v1, int(ig_user_id), amount)
        except Exception as exc:  # noqa: BLE001
            raise _map_error(exc) from exc
        return [self._map_media(m) for m in medias]

    async def fetch_stories(self, ig_user_id: str) -> list[FetchedMedia]:
        try:
            stories = await asyncio.to_thread(self.client.user_stories, int(ig_user_id))
        except Exception as exc:  # noqa: BLE001
            raise _map_error(exc) from exc
        return [self._map_story(s) for s in stories]

    async def download(self, media: FetchedMedia, dest_dir: str) -> str | None:
        pk = media.extra.get("pk")
        if not pk:
            return None
        try:
            path = await asyncio.to_thread(self._download_sync, media, pk, dest_dir)
        except Exception as exc:  # noqa: BLE001
            logger.warning("download xatosi (%s): %s", media.ig_media_id, type(exc).__name__)
            return None
        return str(path) if path else None

    # ---- helpers --------------------------------------------------------

    def _download_sync(self, media: FetchedMedia, pk: str, dest_dir: str):
        if media.media_type == "story":
            return self.client.story_download(int(pk), folder=dest_dir)
        if media.is_video:
            try:
                return self.client.clip_download(int(pk), folder=dest_dir)
            except Exception:  # noqa: BLE001
                return self.client.video_download(int(pk), folder=dest_dir)
        return self.client.photo_download(int(pk), folder=dest_dir)

    @staticmethod
    def _map_media(m) -> FetchedMedia:  # noqa: ANN001
        product = getattr(m, "product_type", "") or ""
        is_reel = product == "clips"
        is_video = m.media_type == 2
        code = getattr(m, "code", None)
        prefix = "reel" if is_reel else "p"
        return FetchedMedia(
            ig_media_id=str(m.pk),
            shortcode=code,
            media_type="reel" if is_reel else "post",
            author_username=m.user.username,
            caption=getattr(m, "caption_text", None),
            posted_at=getattr(m, "taken_at", None),
            media_url=str(m.video_url) if is_video and m.video_url else (str(m.thumbnail_url) if getattr(m, "thumbnail_url", None) else None),
            permalink=f"https://www.instagram.com/{prefix}/{code}/" if code else None,
            thumbnail_url=str(m.thumbnail_url) if getattr(m, "thumbnail_url", None) else None,
            is_video=is_video,
            extra={"pk": str(m.pk)},
        )

    @staticmethod
    def _map_story(s) -> FetchedMedia:  # noqa: ANN001
        is_video = s.media_type == 2
        return FetchedMedia(
            ig_media_id=str(s.pk),
            shortcode=getattr(s, "code", None),
            media_type="story",
            author_username=s.user.username if getattr(s, "user", None) else "",
            caption=getattr(s, "caption_text", None) or None,
            posted_at=getattr(s, "taken_at", None),
            media_url=str(s.video_url) if is_video and s.video_url else (str(s.thumbnail_url) if getattr(s, "thumbnail_url", None) else None),
            permalink=None,
            thumbnail_url=str(s.thumbnail_url) if getattr(s, "thumbnail_url", None) else None,
            is_video=is_video,
            extra={"pk": str(s.pk)},
        )
