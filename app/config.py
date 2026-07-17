"""Ilova sozlamalari — environment variables (.env) dan o'qiladi."""
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Telegram
    bot_token: str
    # Ixtiyoriy: shared akkaunt bloklansa xabar boradigan admin
    admin_telegram_id: int | None = None

    # DB
    database_url: str = "postgresql+asyncpg://insta:insta@db:5432/instaview"

    # Shifrlash
    fernet_key: str

    # === Shared Instagram akkaunt (barcha fetch shu orqali) ===
    # Foydalanuvchilar akkaunt kiritmaydi; markazda bitta akkaunt ishlatiladi.
    ig_username: str = ""
    ig_password: str = ""
    # Ixtiyoriy: parol o'rniga brauzer sessionid (login challenge bo'lmaydi)
    ig_sessionid: str = ""
    # Sessiya diskka saqlanadi — restartda qayta login bo'lmaydi
    shared_session_file: str = "shared_session.json"

    # Umumiy
    default_tz: str = "Asia/Tashkent"
    scheduler_interval_minutes: int = 30
    throttle_min_sec: float = 3.0
    throttle_max_sec: float = 8.0
    refresh_cooldown_minutes: int = 5
    max_telegram_file_mb: int = 50
    target_file_mb: int = 45
    log_level: str = "INFO"

    # Tavsiya etilgan maksimal kunlik so'rov (ban xavfi)
    max_polls_per_day: int = 4

    @field_validator("admin_telegram_id", mode="before")
    @classmethod
    def _empty_to_none(cls, v):
        # .env dagi bo'sh qiymat ("") None sifatida qabul qilinsin
        if v is None or (isinstance(v, str) and v.strip() == ""):
            return None
        return v

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()  # type: ignore[call-arg]
