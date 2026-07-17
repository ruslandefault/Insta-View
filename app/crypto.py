"""Credential va session shifrlash — Fernet (AES-128-CBC + HMAC).

Kalit .env dagi FERNET_KEY dan olinadi. Parol va instagrapi session
JSON'i bazaga faqat shifrlangan holda yoziladi.
"""
from cryptography.fernet import Fernet

from app.config import settings

_fernet = Fernet(settings.fernet_key.encode())


def encrypt(plaintext: str) -> str:
    return _fernet.encrypt(plaintext.encode()).decode()


def decrypt(token: str) -> str:
    return _fernet.decrypt(token.encode()).decode()
