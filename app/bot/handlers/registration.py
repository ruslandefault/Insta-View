"""Ro'yxatdan o'tish: /start + kontakt (prompt 3.1)."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot import keyboards, texts
from app.bot.handlers.ig_account import start_ig_add
from app.bot.states import Registration
from app.config import settings
from app.db.base import session_scope
from app.db.models import User
from app.services.users import current_account, ensure_settings, get_user_by_tg

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    async with session_scope() as session:
        user = await get_user_by_tg(session, message.from_user.id)
        if user is not None:
            account = await current_account(session, user.id)
            has_account = account is not None

    if user is not None:
        await message.answer("🏠 Asosiy menyu", reply_markup=keyboards.main_menu())
        if not has_account:
            await start_ig_add(message, state)
        return

    await state.set_state(Registration.waiting_contact)
    await message.answer(texts.WELCOME, reply_markup=keyboards.contact_kb())


@router.message(Registration.waiting_contact, F.contact)
async def got_contact(message: Message, state: FSMContext) -> None:
    contact = message.contact
    # faqat o'z kontakti (prompt 3.1)
    if contact.user_id != message.from_user.id:
        await message.answer(texts.CONTACT_ONLY_OWN)
        return

    async with session_scope() as session:
        user = await get_user_by_tg(session, message.from_user.id)
        if user is None:
            user = User(
                telegram_id=message.from_user.id,
                phone_number=contact.phone_number,
                tz=settings.default_tz,
            )
            session.add(user)
            await session.flush()
        await ensure_settings(session, user.id)

    await state.clear()
    await message.answer(texts.REGISTERED, reply_markup=keyboards.main_menu())
    # darhol Instagram akkaunt qo'shishga o'tamiz (prompt 3.1)
    await start_ig_add(message, state)


@router.message(Registration.waiting_contact)
async def contact_fallback(message: Message) -> None:
    await message.answer(texts.CONTACT_ONLY_OWN, reply_markup=keyboards.contact_kb())
