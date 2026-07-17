# Insta View 🤖

Telegram bot — foydalanuvchi kuzatgan Instagram kanallarining yangi kontentini
(**Reels / Stories / Post**) uning **o'z Instagram akkaunti** orqali olib kelib,
Telegram'da yetkazib beradi.

## Texnik stek
- **Bot:** Python 3.12 + aiogram 3.x (async)
- **Instagram:** instagrapi (per-user session)
- **DB:** PostgreSQL 16 + SQLAlchemy 2.0 (async/asyncpg)
- **Scheduler:** APScheduler
- **Video:** ffmpeg (two-pass siqish)
- **Shifrlash:** cryptography (Fernet) — parol/session
- **Deploy:** Docker + docker-compose

## Tuzilishi
```
app/
├── main.py              # kirish nuqtasi (bot + scheduler)
├── config.py            # .env sozlamalari
├── crypto.py            # Fernet shifrlash
├── scheduler.py         # avtomatik fetch (APScheduler)
├── db/
│   ├── models.py        # SQLAlchemy modellari
│   └── base.py          # engine / session / init
├── instagram/
│   ├── base.py          # InstagramFetcher protokoli + DTO
│   ├── instagrapi_fetcher.py
│   └── manager.py       # per-user sessiya keshi
├── services/
│   ├── fetch_service.py # fetch + dedup orkestratsiya
│   ├── delivery.py      # formatlash + yuborish (idempotent)
│   ├── video.py         # ffmpeg siqish
│   ├── links.py         # IG link parse
│   └── users.py         # DB yordamchilari
└── bot/
    ├── texts.py, keyboards.py, states.py, notify.py
    └── handlers/        # registration, ig_account, channels, refresh, settings
```

## Ishga tushirish (Docker)
```bash
cp .env.example .env
# .env ni to'ldiring: BOT_TOKEN va FERNET_KEY majburiy
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"  # FERNET_KEY

docker compose up --build -d
docker compose logs -f bot
```

## Lokal (Docker'siz)
```bash
python -m venv .venv && .venv\Scripts\Activate.ps1   # Windows
pip install -r requirements.txt
# ffmpeg tizimda o'rnatilgan bo'lsin
# DATABASE_URL ni lokal postgres yoki sqlite'ga moslang
python -m app.main
```

## Xavfsizlik eslatmasi ❗
- Foydalanuvchi **alohida (ikkilamchi)** Instagram akkaunt kiritishi tavsiya etiladi.
- Parol/session bazada **shifrlangan** holda saqlanadi, parolli xabar darhol o'chiriladi.
- instagrapi (private API) Instagram ToS ni buzadi — akkaunt ban xavfi mavjud
  (`instagram_bot_prompt.md`, 9-bo'lim).
