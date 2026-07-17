# 🤖 Telegram → Instagram Aggregator Bot — Loyiha Prompti (Texnik Topshiriq)

## 0. Loyiha parametrlari (aniqlangan)
- **Foydalanuvchilar:** ~20 ta (kichik masshtab)
- **Kanallar:** foydalanuvchi boshiga ~15 ta
- **Stories:** majburiy
- **Byudjet:** yo'q → faqat self-hosted, bepul yechim
- **Katta video:** 50MB dan katta bo'lsa ffmpeg bilan siqib yuboriladi
- **Instagram akkaunt:** ❗ **Har foydalanuvchi o'zining (yoki alohida) Instagram akkauntini kiritadi.** Bot fetch'ni aynan shu foydalanuvchi akkaunti orqali qiladi. Shu sabab ban xavfi ~20 akkauntga taqsimlanadi

## 1. Loyiha maqsadi
Telegram bot yaratish kerak. Foydalanuvchi botga o'z Instagram akkauntini va kuzatmoqchi bo'lgan Instagram kanallarini qo'shadi. Bot kuniga bir necha marta (foydalanuvchi belgilagan chastotada) shu kanallarning yangi kontentini (Reels / Stories / Post) **foydalanuvchining o'z akkaunti orqali** olib kelib, Telegram'da yetkazib beradi. Har bir yangilikda **kim joylagani, qachon joylangani va kontent turi** ko'rsatilishi shart.

## 2. Texnik stek
- **Bot framework:** Python 3.12 + `aiogram` 3.x (async)
- **Instagram fetcher:** `instagrapi` (private API, har foydalanuvchi o'z akkaunti bilan login) — 5-bo'limga qarang
- **Ma'lumotlar bazasi:** PostgreSQL 16 + SQLAlchemy 2.0 (async, `asyncpg`). *20 foydalanuvchi uchun SQLite ham yetarli*
- **Scheduler:** APScheduler (`AsyncIOScheduler`) — bu masshtab uchun to'liq yetarli
- **Video siqish:** `ffmpeg` (Docker image ichida bo'lishi shart)
- **Shifrlash:** `cryptography` (Fernet / AES-256) — credential va session uchun
- **Konfiguratsiya:** environment variables (`.env`), CLI argumentlarsiz
- **Deploy:** Docker + docker-compose (bitta VM/container yetarli)

## 3. Funksional talablar

### 3.1 Ro'yxatdan o'tish
1. `/start` → `KeyboardButton(request_contact=True)` bilan telefon raqam so'raladi. Faqat o'z kontakti qabul qilinadi (`contact.user_id == message.from_user.id`)
2. Raqam va `telegram_id` `users` ga saqlanadi (timezone default `Asia/Tashkent`)
3. **Darhol Instagram akkaunt qo'shish so'raladi** (3.3) — akkaunt qo'shilmaguncha fetch ishlamaydi

### 3.2 Asosiy menyu (ReplyKeyboard)
- ➕ Kanal qo'shish
- 📋 Kanallar
- 🔄 Yangilash
- ⚙️ Sozlamalar (Instagram akkauntni boshqarish shu yerda)

### 3.3 Instagram akkaunt qo'shish ❗ (yangi, markaziy)
- **Xavfsizlik ogohlantirishi ko'rsatiladi:** "Asosiy akkauntingizni EMAS, alohida (ikkilamchi) akkaunt kiriting. Instagram avtomatlashtirish uchun akkauntni vaqtincha yoki butunlay bloklashi mumkin."
- Bot **username** so'raydi → keyin **parol**
- ⚠️ Parol yuborilgach, bot o'sha xabarni **darhol o'chiradi** (`bot.delete_message`)
- `instagrapi` orqali login urinishi:
  - **2FA / challenge kerak bo'lsa** (`TwoFactorRequired` / `ChallengeRequired`) → bot koddan so'raydi (FSM state) → foydalanuvchi SMS/email/authenticator kodini kiritadi → login yakunlanadi (`verification_code` / `challenge_resolve`)
- Muvaffaqiyat: **session** (va re-login uchun parol) **shifrlangan** holda saqlanadi, akkaunt `active` + `is_current=true`
- Xato: `BadPassword` va h.k. — tushunarli xabar bilan qaytariladi
- Bir foydalanuvchida bir vaqtda **bitta joriy akkaunt**; yangi qo'shilsa eskisi o'rnini egallaydi

### 3.4 Kanal qo'shish
- Foydalanuvchi Instagram **profil linki** yoki **istalgan post/reel linki** yuboradi
- Parse: `instagram.com/{username}` → username; `.../p/{shortcode}` yoki `.../reel/{shortcode}` → media fetch qilinib **muallif (author username)** aniqlanadi va o'sha kanal qo'shiladi
- Akkaunt mavjud/public ekani tekshiriladi (foydalanuvchining o'z IG akkaunti sessiyasi orqali)
- `channels` ga (agar yo'q bo'lsa) qo'shiladi + `subscriptions` yoziladi. Takror qo'shishning oldi olinadi

### 3.5 Kanallar ro'yxati
- Obuna bo'lingan barcha kanallar `InlineKeyboard` bilan chiqadi
- Har biri yonida 🗑 tugma → obuna o'chiriladi (callback query). Bo'sh bo'lsa tegishli xabar

### 3.6 Yangilash (on-demand)
- Foydalanuvchining barcha kanallariga darhol so'rov (uning IG akkaunti orqali). Faqat oxirgi yetkazilgandan keyingi yangi kontent (dedup)
- ⚠️ 5 daqiqalik cooldown (ketma-ket bosishning oldini olish, ban xavfi uchun)

### 3.7 Sozlamalar
- **Kunlik so'rovlar soni:** 1 / 2 / 3 / 4 (max 4 tavsiya, ban xavfi)
- **Kontent turlari:** Reels / Stories / Post — toggle (✅ / ☐)
- **Instagram akkaunt:** joriy akkaunt holati (@username, status) + yangisini qo'shish/almashtirish

### 3.8 Ban / challenge holati ❗ (yangi)
- Login yoki fetch paytida quyidagi `instagrapi` xatolari tutiladi: `ChallengeRequired`, `LoginRequired`, `PleaseWaitFewMinutes`, `RateLimitError`, `FeedbackRequired`, `ClientForbiddenError`
- Akkaunt statusi `banned` / `challenge_required` ga o'tadi, **o'sha foydalanuvchi uchun fetch pauza** qilinadi
- Foydalanuvchiga xabar yuboriladi:
  > ⚠️ @{username} akkauntingiz bloklandi yoki tekshiruv talab qilmoqda. Videolar olib kelish to'xtatildi. Yangi akkaunt qo'shing.
  
  + inline tugma **🔐 Yangi akkaunt qo'shish**
- Yangi ishlaydigan akkaunt qo'shilgach → status `active` → **keyingi cycle'da videolar olib kelish avtomatik davom etadi**

### 3.9 Kontent yetkazib berish formati
Har bir yangi element alohida xabar. Majburiy:
- 👤 **Muallif:** kanal username (+ profil link)
- 🕐 **Joylangan vaqti:** `posted_at`, foydalanuvchi timezone'ida (Asia/Tashkent)
- 🏷 **Kontent turi:** Reel / Story / Post
- 📝 Caption (qisqartirilgan)
- 🎬 Media bevosita yuboriladi
- 🔗 Originalga havola

**Katta video (>50MB) ni siqish (ffmpeg):**
1. `ffprobe` bilan duration/o'lcham aniqlanadi
2. Maqsad ~45MB: `target_video_bitrate = (45 * 8 * 1024) / duration_sec - 128` kbit/s
3. Eni 1080px dan katta bo'lsa → `scale=-2:1080`
4. H.264 two-pass:
   ```
   ffmpeg -y -i in.mp4 -c:v libx264 -b:v {vbitrate}k -pass 1 -an -f mp4 /dev/null
   ffmpeg -i in.mp4 -c:v libx264 -b:v {vbitrate}k -pass 2 -c:a aac -b:a 128k out.mp4
   ```
5. Reels (≤90s) / Stories (≤60s) uchun deyarli har doim <50MB. Baribir katta bo'lsa — permalink (fallback)

## 4. Ma'lumotlar modeli (PostgreSQL)

```
users(id, telegram_id UNIQUE, phone_number, tz DEFAULT 'Asia/Tashkent', created_at)

ig_accounts(id, user_id -> users, ig_username,
            enc_password TEXT,          -- shifrlangan (re-login uchun)
            enc_session TEXT,           -- shifrlangan instagrapi settings JSON
            status ENUM('active','challenge_required','banned','invalid') DEFAULT 'active',
            is_current BOOL DEFAULT true,
            last_login_at, last_error, created_at)   -- fetch shu akkaunt sessiyasi orqali

user_settings(user_id PK -> users, polls_per_day INT DEFAULT 3,
              fetch_reels BOOL DEFAULT true, fetch_stories BOOL DEFAULT true,
              fetch_posts BOOL DEFAULT true, last_poll_at TIMESTAMPTZ)

channels(id, ig_username UNIQUE, ig_user_id, display_name, is_private BOOL, last_fetched_at)

subscriptions(user_id -> users, channel_id -> channels, created_at,
              PRIMARY KEY(user_id, channel_id))

content_items(id, channel_id -> channels, ig_media_id, shortcode,
              media_type ENUM('reel','story','post'), caption,
              author_username, posted_at TIMESTAMPTZ, media_url, permalink,
              thumbnail_url, fetched_at,
              UNIQUE(channel_id, ig_media_id))    -- storage dedup (bir necha akkaunt fetch qilsa ham)

deliveries(id, user_id -> users, content_item_id -> content_items, sent_at,
           UNIQUE(user_id, content_item_id))       -- takroran yubormaslik kafolati
```

> Eslatma: fetch har foydalanuvchi akkaunti orqali bo'lgani uchun umumiy kanal bir necha akkaunt tomonidan alohida fetch qilinishi mumkin. Bu masshtabda (20×15) muammo emas; `content_items` va `deliveries` dublikatlarni bartaraf etadi.

## 5. Instagram fetcher — `instagrapi` (per-user akkaunt)

Stories majburiy va byudjet yo'q → yagona yo'l `instagrapi`. Endi **har foydalanuvchi o'z akkaunti** bilan login qiladi, shuning uchun:

**Yuk taqsimoti (asosiy afzallik):** har akkaunt faqat o'z egasining ~15 kanalini fetch qiladi → cycle'da ~30 so'rov/akkaunt (media + story). Bitta akkauntga 300 emas — **ban ehtimoli ancha past**.

**Qoidalar:**
- `InstagramFetcher` protokoli (interface) + `instagrapi` implementatsiyasi (SOLID / `Protocol`) — kelajakda almashtirish uchun
- **Har akkaunt uchun alohida session** saqlanadi (`dump_settings`/`load_settings`) va shifrlanadi. Qayta login'ni minimallashtirish — har login challenge chaqirishi mumkin (ayniqsa datacenter IP'dan birinchi login)
- Stories `user_stories(user_id)`, media/reels alohida
- **2FA / challenge oqimi** (3.3) qo'llab-quvvatlanadi
- So'rovlar orasida **random sleep 3–8s** (throttling, majburiy)

> Agar kelajakda kichik byudjet paydo bo'lsa — har akkaunt uchun alohida (residential) proxy ban xavfini yanada kamaytiradi.

## 6. Xavfsizlik (credential handling) ❗

Foydalanuvchilar botga Instagram parolini beradi — bu jiddiy mas'uliyat:
- **Parol va session shifrlanadi** (Fernet / AES-256), kalit `.env`/secret'dan (imkon bo'lsa bazadan alohida)
- **Parolli xabar darhol o'chiriladi** (`bot.delete_message`)
- Credential **hech qachon log qilinmaydi**
- Foydalanuvchiga ochiq tavsiya: **alohida ikkilamchi akkaunt** ishlating — asosiy akkaunt ban bo'lishi mumkin
- 2FA to'liq qo'llab-quvvatlanadi
- Baribir akkaunt bloklanishi mumkinligi foydalanuvchiga aniq aytiladi (3.3 ogohlantirish)

## 7. Rejalashtirilgan so'rovlar (scheduling)
- `AsyncIOScheduler` har ~30 daqiqada "tick"
- Har tick'da: har aktiv foydalanuvchi (`is_current` akkaunti `active`) uchun `now - last_poll_at >= 24h / polls_per_day` tekshiriladi
- Shart bajarilsa → foydalanuvchi kanallari **uning akkaunti orqali** fetch → dedup → yetkazib berish → `last_poll_at` yangilanadi
- Akkaunt `banned`/`challenge_required` bo'lsa fetch **pauza** (3.8)
- So'rovlarni kun bo'yi tekis taqsimlash; per-akkaunt yuk yengil (~30 so'rov/cycle)

## 8. Non-functional talablar
- `instagrapi` uchun rate-limiting + exponential backoff + circuit breaker
- Session persistence (har akkaunt) + proxy support (keyinchalik qo'shishga tayyor)
- Xatoliklar tushunarli xabar bilan qaytariladi (private/o'chirilgan akkaunt, media yo'q, login challenge, rate-limit)
- Strukturaviy logging (credential'siz), Sentry ixtiyoriy
- Idempotent yetkazib berish (`deliveries`)
- ffmpeg bilan Docker'da to'liq ishga tushadi

## 9. Huquqiy / ToS eslatmasi
`instagrapi` (private API) Instagram ToS ni buzadi va akkaunt/IP ban xavfini o'z ichiga oladi (endi foydalanuvchining o'z akkaunti). Bu texnik cheklov sifatida qabul qilingan; ishlab chiqarishga chiqarishdan oldin yuridik jihatlarni baholang.

## 10. MVP bosqichlari
1. Ro'yxatdan o'tish (telefon) + asosiy menyu + DB sxema
2. **Instagram akkaunt qo'shish** oqimi (login + 2FA/challenge + shifrlangan session + parolli xabarni o'chirish)
3. Kanal qo'shish (link parse) + kanallar ro'yxati + o'chirish
4. `InstagramFetcher` (`instagrapi`, per-user session) + Reels/Post/Stories + dedup
5. Qo'lda "Yangilash" (cooldown) + kontent yetkazib berish formati
6. ffmpeg video siqish
7. **Ban/challenge detektsiyasi + foydalanuvchiga xabar + yangi akkauntdan keyin davom etish**
8. Sozlamalar (chastota + turlari + akkaunt boshqaruvi) + throttling
9. Scheduler orqali avtomatik yetkazib berish + kun bo'yi taqsimlash
