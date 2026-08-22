import os
from dotenv import load_dotenv

load_dotenv()

# .env faylidan o'qiladi (pastga qarang - .env.example)
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_ID = int(os.getenv("ADMIN_ID", "8083111569"))

# 1 ta Telegram Star narxi (so'mda). Admin /setprice buyrug'i bilan o'zgartira oladi.
# 300 so'm/⭐ = 100 ta stars uchun 30 000 so'm (TON/UZS konvertatsiya xarajati + foyda kiritilgan).
DEFAULT_PRICE_PER_STAR = 300

# To'lov qabul qilinadigan karta ma'lumotlari (admin /setcard bilan o'zgartira oladi)
DEFAULT_CARD_NUMBER = "4067 0700 2595 6058"
DEFAULT_CARD_OWNER = "S. O."

# Foydalanuvchi to'lovni amalga oshirishi uchun berilgan vaqt (daqiqada).
# Shu vaqt ichida chek yuborilmasa, buyurtma avtomatik "muddati tugagan" bo'ladi.
PAYMENT_TIMEOUT_MINUTES = 10

# Tayyor paketlar (stars soni). Fragment.com faqat shu belgilangan
# miqdorlarni qabul qiladi — ixtiyoriy son (masalan 67) sotib bo'lmaydi,
# shuning uchun foydalanuvchi faqat shu ro'yxatdan tanlaydi.
STAR_PACKAGES = [50, 75, 100, 150, 250, 350, 500, 750, 1000, 1500, 2500, 5000]

# Mini-app manzili (WebApp). O'zingizning hosting/GitHub Pages manzilingizni qo'ying.
# Masalan: https://username.github.io/stars-webapp/
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://example.com/webapp/")

# ---------------------------------------------------------------------------
# MINI-APP UCHUN PROFIL QIDIRUV API'SI (api_server.py)
# ---------------------------------------------------------------------------
# Mini-app "Qabul qiluvchi (@username)" maydonida yozilayotganda, profil
# rasmi/nomini jonli ko'rsatish uchun shu portda kichik API server ishga tushadi.
# Serverni tashqi internetdan ochish uchun (mini-app boshqa domenda joylashgan
# bo'lsa) shu portni ochiq qiling va HTTPS orqali (masalan Nginx + Certbot yoki
# Cloudflare Tunnel bilan) ulang — Telegram mini-app faqat https manzillarga
# so'rov yubora oladi, http'ga emas.
# Render.com kabi platformalarda PORT environment o'zgaruvchisi avtomatik
# beriladi — shu bo'lsa o'shani, bo'lmasa API_PORT yoki 8080 ni ishlatadi.
API_PORT = int(os.getenv("PORT", os.getenv("API_PORT", "8080")))
# Mini-app'dagi API_BASE_URL konstantasi (webapp/index.html) shu bilan bir xil
# bo'lishi kerak, masalan: https://sizning-domeningiz.com
API_BASE_URL = os.getenv("API_BASE_URL", "https://example.com")

DB_PATH = "stars_bot.db"

# ---------------------------------------------------------------------------
# FRAGMENT.COM - AVTOMATIK STARS YUBORISH (ixtiyoriy, xavfli qism!)
# ---------------------------------------------------------------------------
# Fragment'ning rasmiy ochiq API'si yo'q. Bu yerda "pyfragment" nomli
# NORASMIY (unofficial, uchinchi tomon) kutubxona ishlatiladi. U ishlashi
# uchun TON hamyoningizning 24 so'zli SEED-PHRASE'i kerak bo'ladi.
#
# ⚠️ XAVFSIZLIK BO'YICHA QAT'IY TAVSIYALAR:
#   1. Faqat shu bot uchun ALOHIDA, kichik miqdordagi mablag' bilan
#      to'ldirilgan hamyon yarating. Asosiy/katta hamyoningizning
#      seed-phrase'ini HECH QACHON bu yerga qo'ymang.
#   2. Seed-phrase'ni faqat .env faylida saqlang, kodga yozmang,
#      Git'ga yuklamang.
#   3. Avval juda kichik summada (masalan 50 stars) sinab ko'ring.
#   4. Balansni muntazam tekshirib turing.
FRAGMENT_AUTO_SEND = os.getenv("FRAGMENT_AUTO_SEND", "false").lower() == "true"
FRAGMENT_SEED = os.getenv("FRAGMENT_SEED", "")            # 24 so'zli seed-phrase
FRAGMENT_API_KEY = os.getenv("FRAGMENT_API_KEY", "")      # tonconsole.com dan olinadi
FRAGMENT_COOKIES = os.getenv("FRAGMENT_COOKIES", "")      # JSON: {"stel_ssid":"...","stel_dt":"...","stel_token":"...","stel_ton_token":"..."}
