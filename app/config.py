"""Ilova sozlamalari — environment variables (.env) dan o'qiladi."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Telegram
    bot_token: str

    # DB
    database_url: str = "postgresql+asyncpg://insta:insta@db:5432/instaview"

    # Shifrlash
    fernet_key: str

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

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()  # type: ignore[call-arg]
