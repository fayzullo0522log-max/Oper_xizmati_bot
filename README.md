# Guruh Boshqaruv va Spam Filtri Boti (Pro)

Telegram guruhlarini avtomatik boshqarish uchun professional darajadagi bot:
flood/spam aniqlash, havola filtri, taqiqlangan so'zlar, captcha, warn/ban tizimi
va to'liq admin buyruqlari.

## Imkoniyatlar

- 🛡 **Flood filtri** — bir foydalanuvchi qisqa vaqtda ko'p xabar yozsa avtomatik mute
- 🔗 **Havola filtri** — ruxsatsiz havolalarni avtomatik o'chirish (whitelist bilan)
- 🚫 **Taqiqlangan so'zlar** — moslashuvchan, har bir guruh uchun alohida ro'yxat
- ✅ **Captcha** — botlar/avtomatik akkauntlarni ushlab qolish (tugma bosish orqali)
- ⚠️ **Warn tizimi** — 3 marta buzilishdan keyin avtomatik ban
- 👮 **Admin buyruqlari** — ban, mute, kick, warn va h.k.
- ⚙️ **Har bir guruh uchun alohida sozlamalar** (SQLite bazada saqlanadi)

## O'rnatish

1. Repozitoriyani yuklab oling va papkaga kiring:
```bash
cd spam_guard_bot
```

2. Virtual muhit yarating va kutubxonalarni o'rnating:
```bash
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. `.env.example` faylini `.env` nomiga nusxalab, tokeningizni kiriting:
```bash
cp .env.example .env
```
`.env` faylini oching va quyidagilarni to'ldiring:
- `BOT_TOKEN` — @BotFather orqali olingan token
- `SUPER_ADMINS` — sizning telegram_id raqamingiz (ixtiyoriy, kengaytirish uchun)

4. Botni ishga tushiring:
```bash
python main.py
```

## Botni guruhga qo'shish

1. Botni guruhga a'zo qiling
2. Botga **Administrator** huquqini bering, quyidagilarni yoqing:
   - Delete messages (xabarlarni o'chirish)
   - Ban users (bloklash)
   - Restrict members (cheklash/mute)
3. Guruhda `/help` yozib buyruqlar ro'yxatini ko'ring

## Buyruqlar ro'yxati

| Buyruq | Tavsif |
|---|---|
| `/ban` | (reply) foydalanuvchini bloklaydi |
| `/unban` | (reply) blokni bekor qiladi |
| `/kick` | (reply) guruhdan chiqaradi |
| `/mute [daqiqa]` | (reply) jim qiladi (standart 60 daqiqa) |
| `/unmute` | (reply) jimlikni bekor qiladi |
| `/warn` | (reply) ogohlantirish beradi |
| `/resetwarn` | (reply) ogohlantirishlarni tozalaydi |
| `/addword so'z` | taqiqlangan so'z qo'shadi |
| `/removeword so'z` | ro'yxatdan olib tashlaydi |
| `/wordlist` | taqiqlangan so'zlar ro'yxati |
| `/setrules matn` | guruh qoidasini o'rnatadi |
| `/rules` | qoidani ko'rsatadi |
| `/captcha_on` `/captcha_off` | captchani yoqish/o'chirish |
| `/linkfilter_on` `/linkfilter_off` | havola filtrini boshqarish |
| `/floodfilter_on` `/floodfilter_off` | flood filtrini boshqarish |
| `/settings` | joriy sozlamalarni ko'rsatadi |

## Loyiha tuzilishi

```
spam_guard_bot/
├── main.py                  # Botni ishga tushirish
├── config.py                 # Sozlamalar (.env dan o'qiydi)
├── database.py                # SQLite baza bilan ishlash
├── requirements.txt
├── .env.example
├── filters/
│   ├── flood_filter.py       # Flood (tez xabar yozish) aniqlash
│   └── spam_filter.py        # Havola/so'z aniqlash
└── handlers/
    ├── admin.py               # Admin buyruqlari
    ├── members.py             # Yangi a'zo + captcha
    └── moderation.py          # Har bir xabarni avtomatik tekshirish
```

## Keyingi bosqichlar (kengaytirish uchun g'oyalar)

- **Statistika**: har kunlik faollik hisobotlari (`message_log` jadvali allaqachon tayyor)
- **Multi-til**: rus/ingliz tillarini ham qo'shish
- **Web panel**: FastAPI orqali guruh sozlamalarini brauzerdan boshqarish
- **Redis**: juda katta guruhlar uchun flood tekshiruvni tezlashtirish
- **AI-filtr**: spamni aniqlash uchun tashqi AI API bilan integratsiya

## Bepul serverda test qilish (Render.com)

Render karta talab qilmaydigan, chindan ham bepul variant (2026 holatiga ko'ra).
Bot "polling" rejimida ishlagani uchun, Render uni "web service" deb qabul qilishi
uchun kichik keep-alive server allaqachon `main.py` ga qo'shilgan.

**1-qadam — GitHub'ga yuklash**
```bash
git init
git add .
git commit -m "Spam guard bot"
```
`.env` faylini **hech qachon** commit qilmang (`.gitignore` allaqachon uni chetlab o'tadi).
GitHub'da yangi repo yarating va push qiling:
```bash
git remote add origin https://github.com/FOYDALANUVCHI/spam-guard-bot.git
git push -u origin main
```

**2-qadam — Render'da xizmat yaratish**
1. https://render.com ga kiring, GitHub akkauntingiz bilan ro'yxatdan o'ting
2. **New +** -> **Web Service** -> repongizni tanlang
3. Sozlamalar:
   - Runtime: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python main.py`
   - Plan: **Free**
4. **Environment** bo'limida qo'shing:
   - `BOT_TOKEN` = sizning tokeningiz
5. **Create Web Service** tugmasini bosing — 2-3 daqiqada bot ishga tushadi

**Muhim cheklov:** Render bepul rejasi 15 daqiqa so'rovsiz qolsa xizmatni "uxlatadi".
Bot polling qilayotgani uchun odatda muammo bo'lmaydi, lekin agar uxlab qolsa —
https://uptimerobot.com (bepul) orqali har 10 daqiqada bot manzilingizga so'rov
yuboring, bu uni doim uyg'oq tutadi.

**Muqobil variantlar:**
- **PythonAnywhere** (pythonanywhere.com) — karta kerak emas, brauzer konsolida
  `python main.py` ishga tushirasiz, qisqa testlar uchun qulay
- **Railway** (railway.com) — GitHub tasdiqlash bilan oyiga bepul kredit beradi,
  bir necha soatlik test uchun yetadi

## Muhim eslatma

Bot ishlashi uchun guruhda **administrator** huquqiga ega bo'lishi va
"Restrict members", "Delete messages", "Ban users" ruxsatlari yoqilgan bo'lishi shart.
