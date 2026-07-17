"""FSM holatlari (aiogram)."""
from aiogram.fsm.state import State, StatesGroup


class Registration(StatesGroup):
    waiting_contact = State()


class AddChannel(StatesGroup):
    waiting_link = State()
