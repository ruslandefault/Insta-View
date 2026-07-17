"""Barcha routerlarni bitta joyda yig'ish."""
from aiogram import Router

from app.bot.handlers import channels, refresh, registration, settings


def build_router() -> Router:
    root = Router()
    # tartib muhim: registration eng oldin
    root.include_router(registration.router)
    root.include_router(channels.router)
    root.include_router(refresh.router)
    root.include_router(settings.router)
    return root
