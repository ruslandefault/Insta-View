"""Bot xabar shablonlari (o'zbek tilida)."""

WELCOME = (
    "👋 Assalomu alaykum!\n\n"
    "Bu bot siz kuzatmoqchi bo'lgan Instagram kanallarining yangi "
    "kontentini (Reels / Stories / Post) to'plab, shu yerda yetkazib beradi.\n\n"
    "Boshlash uchun telefon raqamingizni yuboring 👇"
)

CONTACT_ONLY_OWN = "❗ Iltimos, faqat o'zingizning kontaktingizni yuboring."

REGISTERED = "✅ Ro'yxatdan o'tdingiz!"

# --- Instagram akkaunt ---
IG_WARNING = (
    "🔐 <b>Instagram akkaunt qo'shish</b>\n\n"
    "⚠️ <b>Diqqat:</b> asosiy akkauntingizni EMAS, <b>alohida (ikkilamchi)</b> "
    "akkaunt kiriting. Instagram avtomatlashtirish uchun akkauntni vaqtincha "
    "yoki butunlay bloklashi mumkin.\n\n"
    "Instagram <b>username</b> ingizni yuboring:"
)
IG_ASK_PASSWORD = "🔑 Endi shu akkaunt <b>parolini</b> yuboring.\n\n<i>(Xabaringiz darhol o'chiriladi)</i>"
IG_ASK_2FA = "📲 Akkauntda 2FA yoqilgan. Ilova/SMS'dagi <b>6 xonali kodni</b> yuboring:"
IG_ASK_CHALLENGE = (
    "🛡 Instagram xavfsizlik tekshiruvini talab qilmoqda. "
    "Email yoki SMS orqali kelgan <b>kodni</b> yuboring:"
)
IG_LOGIN_OK = "✅ Instagram akkaunt (@{username}) muvaffaqiyatli ulandi!"
IG_BAD_PASSWORD = "❌ Login yoki parol xato. Qaytadan urinib ko'ring: /start → ⚙️ Sozlamalar"
IG_LOGIN_ERROR = "❌ Login amalga oshmadi: {reason}"

NEED_IG_FIRST = "❗ Avval Instagram akkauntingizni qo'shing (⚙️ Sozlamalar)."

# --- Kanallar ---
ADD_CHANNEL_ASK = (
    "🔗 Instagram <b>profil linki</b> yoki istalgan <b>post/reel linkini</b> yuboring.\n\n"
    "Masalan: <code>https://instagram.com/nasa</code>"
)
CHANNEL_ADDED = "✅ Kanal qo'shildi: @{username}"
CHANNEL_EXISTS = "ℹ️ Bu kanalga allaqachon obuna bo'lgansiz: @{username}"
CHANNEL_PARSE_FAIL = "❌ Linkdan kanalni aniqlab bo'lmadi. To'g'ri Instagram linki yuboring."
CHANNELS_EMPTY = "📭 Hali birorta kanalga obuna bo'lmagansiz. ➕ Kanal qo'shish tugmasini bosing."
CHANNELS_HEADER = "📋 <b>Obuna bo'lgan kanallaringiz:</b>"
CHANNEL_REMOVED = "🗑 Obuna bekor qilindi."

# --- Yangilash ---
REFRESH_COOLDOWN = "⏳ Yangilash {minutes} daqiqada bir marta mumkin. Yana {left} daqiqa kuting."
REFRESH_START = "🔄 Yangi kontent qidirilmoqda... (bu biroz vaqt olishi mumkin)"
REFRESH_DONE = "✅ Tayyor! {count} ta yangi element yuborildi."
REFRESH_NOTHING = "✅ Yangi kontent topilmadi."

# --- Ban/challenge (3.8) ---
ACCOUNT_BLOCKED = (
    "⚠️ <b>@{username}</b> akkauntingiz bloklandi yoki tekshiruv talab qilmoqda. "
    "Videolar olib kelish to'xtatildi. Yangi akkaunt qo'shing."
)
RATE_LIMITED = "⏳ Instagram so'rovlarni cheklab qo'ydi. Keyingi cycle'da avtomatik qayta urinamiz."

# --- Sozlamalar ---
SETTINGS_HEADER = "⚙️ <b>Sozlamalar</b>"
SETTINGS_ACCOUNT = "📱 Instagram akkaunt: {status}"
SETTINGS_NO_ACCOUNT = "📱 Instagram akkaunt: ulanmagan"
