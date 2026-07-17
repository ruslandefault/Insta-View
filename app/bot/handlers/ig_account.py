"""Instagram akkaunt qo'shish: login + 2FA + challenge + shifrlangan session
(prompt 3.3, 6). Parolli xabar darhol o'chiriladi."""
from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import update

from app.bot import keyboards, texts
from app.bot.states import IgLogin
from app.crypto import encrypt
from app.db.base import session_scope
from app.db.models import AccountStatus, IgAccount
from app.instagram import manager
from app.instagram.base import LoginOutcome, LoginResult
from app.instagram.instagrapi_fetcher import InstagrapiFetcher
from app.services.users import get_user_by_tg

logger = logging.getLogger(__name__)
router = Router()


async def start_ig_add(message: Message, state: FSMContext) -> None:
    await state.set_state(IgLogin.waiting_username)
    await message.answer(texts.IG_WARNING, parse_mode="HTML")


@router.callback_query(F.data == "ig_add")
async def cb_ig_add(cb: CallbackQuery, state: FSMContext) -> None:
    await cb.answer()
    await start_ig_add(cb.message, state)


@router.message(IgLogin.waiting_username, F.text)
async def got_username(message: Message, state: FSMContext) -> None:
    username = message.text.strip().lstrip("@").lower()
    await state.update_data(ig_username=username)
    await state.set_state(IgLogin.waiting_password)
    await message.answer(texts.IG_ASK_PASSWORD, parse_mode="HTML")


@router.message(IgLogin.waiting_password, F.text)
async def got_password(message: Message, state: FSMContext) -> None:
    password = message.text
    # ⚠️ parolli xabarni darhol o'chirish (prompt 3.3)
    try:
        await message.delete()
    except Exception:  # noqa: BLE001
        pass

    data = await state.get_data()
    username = data["ig_username"]
    await state.update_data(ig_password=password)

    fetcher = InstagrapiFetcher()
    manager.pending_logins[message.from_user.id] = fetcher

    await message.answer("⏳ Instagram'ga ulanmoqda...")
    outcome = await fetcher.login(username, password)
    await _handle_outcome(message, state, outcome)


@router.message(IgLogin.waiting_2fa, F.text)
async def got_2fa(message: Message, state: FSMContext) -> None:
    code = message.text.strip()
    try:
        await message.delete()
    except Exception:  # noqa: BLE001
        pass
    fetcher = manager.pending_logins.get(message.from_user.id)
    if fetcher is None:
        await _fail(message, state, "Sessiya topilmadi, qaytadan urinib ko'ring.")
        return
    outcome = await fetcher.submit_2fa(code)
    await _handle_outcome(message, state, outcome)


@router.message(IgLogin.waiting_challenge, F.text)
async def got_challenge(message: Message, state: FSMContext) -> None:
    code = message.text.strip()
    try:
        await message.delete()
    except Exception:  # noqa: BLE001
        pass
    fetcher = manager.pending_logins.get(message.from_user.id)
    if fetcher is None:
        await _fail(message, state, "Sessiya topilmadi, qaytadan urinib ko'ring.")
        return
    outcome = await fetcher.submit_challenge(code)
    await _handle_outcome(message, state, outcome)


async def _handle_outcome(message: Message, state: FSMContext, outcome: LoginOutcome) -> None:
    if outcome.result is LoginResult.needs_2fa:
        await state.set_state(IgLogin.waiting_2fa)
        await message.answer(texts.IG_ASK_2FA, parse_mode="HTML")
        return
    if outcome.result is LoginResult.needs_challenge:
        await state.set_state(IgLogin.waiting_challenge)
        await message.answer(texts.IG_ASK_CHALLENGE, parse_mode="HTML")
        return
    if outcome.result is LoginResult.bad_password:
        await _fail(message, state, None, texts.IG_BAD_PASSWORD)
        return
    if outcome.result is LoginResult.error:
        await _fail(message, state, None, texts.IG_LOGIN_ERROR.format(reason=outcome.message))
        return

    # === Muvaffaqiyat ===
    data = await state.get_data()
    username = data["ig_username"]
    password = data.get("ig_password", "")
    await _save_account(message.from_user.id, username, password, outcome.session_json)

    fetcher = manager.pending_logins.pop(message.from_user.id, None)
    await state.clear()
    await message.answer(
        texts.IG_LOGIN_OK.format(username=username),
        reply_markup=keyboards.main_menu(),
    )


async def _save_account(tg_id: int, username: str, password: str, session_json: str | None) -> None:
    async with session_scope() as session:
        user = await get_user_by_tg(session, tg_id)
        if user is None:
            return
        # eski joriy akkauntlarni is_current=False qilamiz (prompt 3.3)
        # (async'da lazy-load relationship ishlatmaymiz — to'g'ridan-to'g'ri UPDATE)
        await session.execute(
            update(IgAccount).where(IgAccount.user_id == user.id).values(is_current=False)
        )
        account = IgAccount(
            user_id=user.id,
            ig_username=username,
            enc_password=encrypt(password) if password else None,
            enc_session=encrypt(session_json) if session_json else None,
            status=AccountStatus.active,
            is_current=True,
        )
        session.add(account)
        await session.flush()
        user_id = user.id

    # tayyor fetcher'ni keshga qo'yamiz
    fetcher = manager.pending_logins.get(tg_id)
    if fetcher is not None:
        manager.set_active(user_id, fetcher)


async def _fail(message: Message, state: FSMContext, reason: str | None, text: str | None = None) -> None:
    manager.pending_logins.pop(message.from_user.id, None)
    await state.clear()
    await message.answer(text or f"❌ {reason}", parse_mode="HTML", reply_markup=keyboards.main_menu())
