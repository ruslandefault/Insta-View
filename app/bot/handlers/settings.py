"""Sozlamalar: kunlik so'rovlar, kontent turlari, akkaunt (prompt 3.7)."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from app.bot import keyboards, texts
from app.config import settings as app_settings
from app.db.base import session_scope
from app.services.users import current_account, ensure_settings, get_user_by_tg, account_status_label

router = Router()


def _settings_text(status_label: str) -> str:
    return f"{texts.SETTINGS_HEADER}\n\n📱 Instagram akkaunt: {status_label}"


@router.message(F.text == keyboards.BTN_SETTINGS)
async def open_settings(message: Message) -> None:
    async with session_scope() as session:
        user = await get_user_by_tg(session, message.from_user.id)
        if user is None:
            await message.answer(texts.NEED_IG_FIRST)
            return
        us = await ensure_settings(session, user.id)
        account = await current_account(session, user.id)
        label = account_status_label(account)
        kb = keyboards.settings_kb(us.polls_per_day, us.fetch_reels, us.fetch_stories, us.fetch_posts)

    await message.answer(_settings_text(label), parse_mode="HTML", reply_markup=kb)


@router.callback_query(F.data == "noop")
async def noop(cb: CallbackQuery) -> None:
    await cb.answer()


@router.callback_query(F.data.startswith("set_polls:"))
async def set_polls(cb: CallbackQuery) -> None:
    n = int(cb.data.split(":", 1)[1])
    n = max(1, min(n, app_settings.max_polls_per_day))
    await _update_and_refresh(cb, polls=n)
    await cb.answer(f"Kunlik so'rovlar: {n}")


@router.callback_query(F.data.startswith("toggle:"))
async def toggle(cb: CallbackQuery) -> None:
    field = cb.data.split(":", 1)[1]
    await _update_and_refresh(cb, toggle_field=field)
    await cb.answer("Yangilandi")


async def _update_and_refresh(cb: CallbackQuery, polls: int | None = None, toggle_field: str | None = None) -> None:
    async with session_scope() as session:
        user = await get_user_by_tg(session, cb.from_user.id)
        if user is None:
            return
        us = await ensure_settings(session, user.id)
        if polls is not None:
            us.polls_per_day = polls
        if toggle_field == "reels":
            us.fetch_reels = not us.fetch_reels
        elif toggle_field == "stories":
            us.fetch_stories = not us.fetch_stories
        elif toggle_field == "posts":
            us.fetch_posts = not us.fetch_posts
        account = await current_account(session, user.id)
        label = account_status_label(account)
        kb = keyboards.settings_kb(us.polls_per_day, us.fetch_reels, us.fetch_stories, us.fetch_posts)

    try:
        await cb.message.edit_text(_settings_text(label), parse_mode="HTML", reply_markup=kb)
    except Exception:  # noqa: BLE001
        pass
