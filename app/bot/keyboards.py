"""Klaviaturalar (Reply + Inline)."""
from __future__ import annotations

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

# --- Reply ---

BTN_ADD = "➕ Kanal qo'shish"
BTN_LIST = "📋 Kanallar"
BTN_REFRESH = "🔄 Yangilash"
BTN_SETTINGS = "⚙️ Sozlamalar"


def contact_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_ADD), KeyboardButton(text=BTN_LIST)],
            [KeyboardButton(text=BTN_REFRESH), KeyboardButton(text=BTN_SETTINGS)],
        ],
        resize_keyboard=True,
    )


# --- Inline ---


def channels_kb(channels: list[tuple[int, str]]) -> InlineKeyboardMarkup:
    """channels: [(channel_id, ig_username), ...]"""
    rows = [
        [
            InlineKeyboardButton(text=f"@{username}", url=f"https://instagram.com/{username}"),
            InlineKeyboardButton(text="🗑", callback_data=f"unsub:{cid}"),
        ]
        for cid, username in channels
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def add_account_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🔐 Yangi akkaunt qo'shish", callback_data="ig_add")]]
    )


def settings_kb(polls: int, reels: bool, stories: bool, posts: bool) -> InlineKeyboardMarkup:
    def mark(on: bool) -> str:
        return "✅" if on else "☐"

    poll_row = [
        InlineKeyboardButton(text=("🔘 " if polls == n else "") + str(n), callback_data=f"set_polls:{n}")
        for n in (1, 2, 3, 4)
    ]
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📅 Kunlik so'rovlar soni:", callback_data="noop")],
            poll_row,
            [InlineKeyboardButton(text=f"{mark(reels)} Reels", callback_data="toggle:reels")],
            [InlineKeyboardButton(text=f"{mark(stories)} Stories", callback_data="toggle:stories")],
            [InlineKeyboardButton(text=f"{mark(posts)} Posts", callback_data="toggle:posts")],
            [InlineKeyboardButton(text="🔐 Instagram akkauntni almashtirish", callback_data="ig_add")],
        ]
    )
