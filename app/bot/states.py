"""FSM holatlari (aiogram)."""
from aiogram.fsm.state import State, StatesGroup


class Registration(StatesGroup):
    waiting_contact = State()


class IgLogin(StatesGroup):
    waiting_username = State()
    waiting_password = State()
    waiting_2fa = State()
    waiting_challenge = State()


class AddChannel(StatesGroup):
    waiting_link = State()
