from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Ilova sozlamalari (.env faylidan o'qiladi)."""

    app_name: str = "Insta View API"
    debug: bool = True
    # React frontend manzili (CORS uchun)
    frontend_origin: str = "http://localhost:5173"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
