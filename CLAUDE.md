# Insta View — Claude Code yo'riqnomasi

## Loyiha haqida
Telegram bot: foydalanuvchi kuzatgan Instagram kanallarining yangi kontentini
(Reels/Stories/Post) olib kelib Telegram'da yetkazadi.
To'liq texnik topshiriq: `instagram_bot_prompt.md`.

> ⚠️ ARXITEKTURA O'ZGARDI: dastlab prompt "har foydalanuvchi o'z IG akkauntini
> kiritadi" degan edi. Amalda Instagram programmatik login'ni throttle/challenge
> qildi va UX og'ir bo'ldi. Endi **bitta markaziy (shared) IG akkaunt** ishlatiladi
> (`app/instagram/shared.py`, `.env` dagi IG_USERNAME/IG_PASSWORD yoki IG_SESSIONID).
> Foydalanuvchilar faqat telefon bilan ro'yxatdan o'tadi va kanal qo'shadi.
> `ig_accounts` jadvali qoldi (backward-compat), lekin ishlatilmaydi.

## Texnologiyalar
- Python 3.12, **aiogram 3.x** (async), **instagrapi** (private API, per-user)
- **PostgreSQL 16** + SQLAlchemy 2.0 async (asyncpg)
- APScheduler (AsyncIOScheduler), ffmpeg (video siqish)
- cryptography (Fernet) — parol/session shifrlash
- Docker + docker-compose

## Buyruqlar
```bash
docker compose up --build -d     # ishga tushirish
docker compose logs -f bot       # loglar
python -m app.main               # lokal (venv + ffmpeg + DB kerak)
```

## Arxitektura qoidalari
- Barcha instagrapi (sinxron) chaqiruvlari `asyncio.to_thread` orqali — event loop bloklanmasin.
- IG bilan ishlash faqat `InstagramFetcher` protokoli (`app/instagram/base.py`) orqali —
  implementatsiyani almashtirish mumkin bo'lsin (SOLID).
- Markaziy sessiya `shared_session.json` ga saqlanadi — restartda qayta login yo'q
  (`app/instagram/shared.py`). Bu throttle sababini (takroriy login) yo'qotadi.
- DB migratsiyasi yo'q — `init_db()` `create_all` qiladi (20 foydalanuvchi uchun yetarli).
- Yetkazish idempotent: `deliveries(user_id, content_item_id)` UNIQUE.
- Kontent dedup: `content_items(channel_id, ig_media_id)` UNIQUE.

## Xavfsizlik (MUHIM)
- Parol/session bazaga faqat **shifrlangan** (Fernet) yoziladi.
- Parolli Telegram xabari qabul qilingach **darhol o'chiriladi** (`message.delete()`).
- Credential HECH QACHON log qilinmaydi.
- `.env` ni commit qilmang. `FERNET_KEY` va `BOT_TOKEN` majburiy.

## Uslub
- Foydalanuvchiga chiqadigan barcha matnlar o'zbek tilida (`app/bot/texts.py`).
- Kod izohlari o'zbekcha bo'lishi mumkin. Prompt bo'lim raqamlariga havola qiling (masalan "prompt 3.8").
- instagrapi xatolari `app/instagram/base.py`dagi `FetchError`/`FetchErrorKind` ga map qilinadi.
