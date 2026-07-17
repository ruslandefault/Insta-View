"""Fetch orkestratsiyasi: foydalanuvchi akkaunti orqali kanallardan
yangi kontentni olib kelish, DB'ga dedup bilan yozish va yetkazilmagan
elementlar ro'yxatini qaytarish (prompt 3.6, 3.9, 5, 7)."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

from sqlalchemy import select

from app.db.base import session_scope
from app.db.models import (
    AccountStatus,
    Channel,
    ContentItem,
    Delivery,
    IgAccount,
    MediaType,
    Subscription,
    UserSettings,
)
from app.instagram import manager
from app.instagram.base import FetchedMedia, FetchError, FetchErrorKind
from app.instagram.instagrapi_fetcher import InstagrapiFetcher

logger = logging.getLogger(__name__)

MEDIAS_PER_CHANNEL = 5  # cycle'da har kanaldan tekshiriladigan oxirgi postlar soni


@dataclass(slots=True)
class Pending:
    content_item_id: int
    media: FetchedMedia


@dataclass(slots=True)
class PollResult:
    pending: list[Pending] = field(default_factory=list)
    error: FetchError | None = None
    account_username: str | None = None
    no_account: bool = False


def _account_status_for(kind: FetchErrorKind) -> AccountStatus | None:
    if kind is FetchErrorKind.challenge:
        return AccountStatus.challenge_required
    if kind in (FetchErrorKind.feedback, FetchErrorKind.forbidden, FetchErrorKind.login_required):
        return AccountStatus.banned
    return None  # rate_limit va boshqalar — vaqtinchalik, statusni o'zgartirmaymiz


async def poll_user(user_id: int) -> PollResult:
    """Bitta foydalanuvchi uchun to'liq fetch cycle."""
    async with session_scope() as session:
        account = (
            await session.execute(
                select(IgAccount).where(
                    IgAccount.user_id == user_id, IgAccount.is_current.is_(True)
                )
            )
        ).scalar_one_or_none()

        if account is None or account.status is not AccountStatus.active:
            return PollResult(no_account=account is None,
                              account_username=account.ig_username if account else None)

        us = (
            await session.execute(select(UserSettings).where(UserSettings.user_id == user_id))
        ).scalar_one_or_none()
        if us is None:
            us = UserSettings(user_id=user_id)
            session.add(us)
            await session.flush()

        channels = (
            await session.execute(
                select(Channel)
                .join(Subscription, Subscription.channel_id == Channel.id)
                .where(Subscription.user_id == user_id)
            )
        ).scalars().all()

        if not channels:
            return PollResult(account_username=account.ig_username)

        fetcher = await manager.get_active_fetcher(account)
        if fetcher is None:
            account.status = AccountStatus.invalid
            account.last_error = "sessiya tiklab bo'lmadi"
            return PollResult(error=FetchError(FetchErrorKind.login_required),
                              account_username=account.ig_username)

        pending: list[Pending] = []
        try:
            for channel in channels:
                await _poll_channel(session, fetcher, channel, us, pending, user_id)
        except FetchError as exc:
            new_status = _account_status_for(exc.kind)
            if new_status is not None:
                account.status = new_status
                account.last_error = exc.message
                manager.drop_active(user_id)
            logger.warning("fetch to'xtadi (@%s): %s", account.ig_username, exc.kind.value)
            return PollResult(pending=pending, error=exc, account_username=account.ig_username)

        return PollResult(pending=pending, account_username=account.ig_username)


async def _poll_channel(
    session,
    fetcher: InstagrapiFetcher,
    channel: Channel,
    us: UserSettings,
    pending: list[Pending],
    user_id: int,
) -> None:
    if not channel.ig_user_id:
        return

    collected: list[FetchedMedia] = []

    if us.fetch_reels or us.fetch_posts:
        medias = await fetcher.fetch_medias(channel.ig_user_id, MEDIAS_PER_CHANNEL)
        for m in medias:
            if m.media_type == "reel" and not us.fetch_reels:
                continue
            if m.media_type == "post" and not us.fetch_posts:
                continue
            collected.append(m)

    if us.fetch_stories:
        stories = await fetcher.fetch_stories(channel.ig_user_id)
        collected.extend(stories)

    for media in collected:
        item = await _get_or_create_item(session, channel.id, media)
        # allaqachon yetkazilganmi?
        already = (
            await session.execute(
                select(Delivery.id).where(
                    Delivery.user_id == user_id, Delivery.content_item_id == item.id
                )
            )
        ).scalar_one_or_none()
        if already is None:
            pending.append(Pending(content_item_id=item.id, media=media))


async def _get_or_create_item(session, channel_id: int, media: FetchedMedia) -> ContentItem:
    existing = (
        await session.execute(
            select(ContentItem).where(
                ContentItem.channel_id == channel_id,
                ContentItem.ig_media_id == media.ig_media_id,
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        return existing

    item = ContentItem(
        channel_id=channel_id,
        ig_media_id=media.ig_media_id,
        shortcode=media.shortcode,
        media_type=MediaType(media.media_type),
        caption=media.caption,
        author_username=media.author_username,
        posted_at=media.posted_at,
        media_url=media.media_url,
        permalink=media.permalink,
        thumbnail_url=media.thumbnail_url,
    )
    session.add(item)
    await session.flush()  # id kerak
    return item
