"""Kanal qo'shish / ro'yxat / obunani bekor qilish (prompt 3.4, 3.5)."""
from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import delete, select

from app.bot import keyboards, texts
from app.bot.states import AddChannel
from app.db.base import session_scope
from app.db.models import Channel, Subscription
from app.instagram import shared
from app.instagram.base import FetchError, IgUserInfo
from app.services.links import parse_ig_link
from app.services.users import get_user_by_tg

logger = logging.getLogger(__name__)
router = Router()


@router.message(F.text == keyboards.BTN_ADD)
async def add_channel_start(message: Message, state: FSMContext) -> None:
    await state.set_state(AddChannel.waiting_link)
    await message.answer(texts.ADD_CHANNEL_ASK, parse_mode="HTML")


@router.message(AddChannel.waiting_link, F.text)
async def add_channel_link(message: Message, state: FSMContext) -> None:
    kind, value = parse_ig_link(message.text)
    if kind is None:
        await message.answer(texts.CHANNEL_PARSE_FAIL)
        return

    fetcher = await shared.get_shared()
    if fetcher is None:
        await state.clear()
        await message.answer(texts.SERVICE_UNAVAILABLE)
        return

    async with session_scope() as session:
        user = await get_user_by_tg(session, message.from_user.id)
        if user is None:
            await state.clear()
            await message.answer("❗ Avval /start bosing.")
            return

        await message.answer("🔎 Tekshirilmoqda...")
        try:
            if kind == "media":
                info: IgUserInfo = await fetcher.author_from_media_url(value)
            else:
                info = await fetcher.get_user_info(value)
        except FetchError as exc:
            await message.answer(f"❌ {exc.message}")
            return

        # kanalni get-or-create
        channel = (
            await session.execute(select(Channel).where(Channel.ig_username == info.username))
        ).scalar_one_or_none()
        if channel is None:
            channel = Channel(
                ig_username=info.username,
                ig_user_id=info.pk,
                display_name=info.full_name,
                is_private=info.is_private,
            )
            session.add(channel)
            await session.flush()
        else:
            channel.ig_user_id = info.pk  # yangilaymiz

        # obuna dedup
        exists = (
            await session.execute(
                select(Subscription).where(
                    Subscription.user_id == user.id, Subscription.channel_id == channel.id
                )
            )
        ).scalar_one_or_none()
        if exists is not None:
            await state.clear()
            await message.answer(texts.CHANNEL_EXISTS.format(username=info.username))
            return

        session.add(Subscription(user_id=user.id, channel_id=channel.id))

    await state.clear()
    msg = texts.CHANNEL_ADDED.format(username=info.username)
    if info.is_private:
        msg += "\n\n⚠️ Bu yopiq akkaunt — kontent olib kelish uchun IG akkauntingiz unga obuna bo'lgan bo'lishi kerak."
    await message.answer(msg, reply_markup=keyboards.main_menu())


@router.message(F.text == keyboards.BTN_LIST)
async def list_channels(message: Message) -> None:
    async with session_scope() as session:
        user = await get_user_by_tg(session, message.from_user.id)
        if user is None:
            await message.answer(texts.CHANNELS_EMPTY)
            return
        rows = (
            await session.execute(
                select(Channel.id, Channel.ig_username)
                .join(Subscription, Subscription.channel_id == Channel.id)
                .where(Subscription.user_id == user.id)
                .order_by(Channel.ig_username)
            )
        ).all()

    if not rows:
        await message.answer(texts.CHANNELS_EMPTY)
        return

    channels = [(cid, username) for cid, username in rows]
    await message.answer(
        texts.CHANNELS_HEADER, parse_mode="HTML", reply_markup=keyboards.channels_kb(channels)
    )


@router.callback_query(F.data.startswith("unsub:"))
async def unsubscribe(cb: CallbackQuery) -> None:
    channel_id = int(cb.data.split(":", 1)[1])
    async with session_scope() as session:
        user = await get_user_by_tg(session, cb.from_user.id)
        if user is None:
            await cb.answer("Xato", show_alert=True)
            return
        await session.execute(
            delete(Subscription).where(
                Subscription.user_id == user.id, Subscription.channel_id == channel_id
            )
        )
        rows = (
            await session.execute(
                select(Channel.id, Channel.ig_username)
                .join(Subscription, Subscription.channel_id == Channel.id)
                .where(Subscription.user_id == user.id)
                .order_by(Channel.ig_username)
            )
        ).all()

    await cb.answer(texts.CHANNEL_REMOVED)
    if rows:
        channels = [(cid, username) for cid, username in rows]
        await cb.message.edit_reply_markup(reply_markup=keyboards.channels_kb(channels))
    else:
        await cb.message.edit_text(texts.CHANNELS_EMPTY)
