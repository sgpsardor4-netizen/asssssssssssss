# ⭐ Telegram Stars Savdo Boti (UZS)

Bu bot orqali foydalanuvchilar Telegram Stars'ni so'mda (UZS) sotib olishlari mumkin:
karta orqali to'lov qiladi → chek yuklaydi → **admin tasdiqlaydi** → keyin siz
(admin) Fragment (fragment.com) yoki boshqa usul orqali stars'ni foydalanuvchiga
qo'lda yuborasiz va botda "Stars yuborildi" tugmasini bosasiz.

> ⚠️ **Muhim:** Telegram Bot API orqali botning o'zi ixtiyoriy foydalanuvchiga
> avtomatik "stars sovg'a qilish" imkoniyati yo'q — bu ish odatda **Fragment**
> platformasi orqali qo'lda amalga oshiriladi. Shu sabab tizim "admin tasdiqlaydi
> va qo'lda yuboradi" tartibida qurilgan.

## 1. O'rnatish

```bash
cd stars_bot
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Sozlash

1. `.env.example` faylini nusxalab `.env` deb nomlang.
2. **Yangi bot token oling!** Chatda yuborgan tokeningiz endi ochiq bo'lib qoldi —
   @BotFather ga boring → `/mybots` → botingiz → **API Token** → **Revoke current token**,
   yangisini `.env` ga qo'ying.
3. `ADMIN_ID=8083111569` — o'zingiznikini tekshirib qo'ying.
4. `WEBAPP_URL` — mini-app (`webapp/index.html`) ni biror hostingga (masalan GitHub Pages,
   Netlify, yoki o'z serveringiz, albatta **https** bo'lishi shart) joylab, shu manzilni yozing.

## 3. Ishga tushirish

```bash
python3 bot.py
```

## 4. Admin buyruqlari

| Buyruq | Vazifasi |
|---|---|
| `/pending` | Kutilayotgan barcha buyurtmalarni ko'rsatadi |
| `/setprice` | 1 stars narxini (so'mda) o'zgartirish |
| `/setcard` | To'lov qabul qilinadigan karta raqamini o'zgartirish |
| `/stats` | Qisqacha statistika |

Har bir yangi buyurtma kelganda admin'ga avtomatik xabar va ✅ Tasdiqlash / ❌ Rad etish
tugmalari bilan chek rasmi yuboriladi.

## 5. Foydalanuvchi jarayoni

1. `/start`
2. "⭐ Stars sotib olish" → paket tanlaydi
3. Stars kimga yuborilishini (@username) kiritadi
4. **Bot profilni tekshiradi** — topilsa, ism va profil rasmini ko'rsatib
   "To'g'rimi?" deb so'raydi (✅ Ha / ✏️ Qayta kiritish). Bu noto'g'ri
   username kiritishning oldini oladi. Agar profil topilmasa (foydalanuvchi
   hech qachon botga yozmagan yoki maxfiylik sozlamalari cheklangan bo'lsa),
   bot buni ogohlantiradi, lekin baribir davom etish imkonini beradi.
5. Tasdiqlagach, bot karta raqamini ko'rsatadi
6. Foydalanuvchi to'lov chekini (screenshot) yuboradi
7. Admin tasdiqlaydi → foydalanuvchiga xabar boradi
8. Admin Fragment orqali stars yuboradi (yoki avtomatik yuboriladi) → yakuniy xabar boradi

> **Eslatma:** Profilni aniqlash Telegram Bot API orqali ishlaydi va faqat
> foydalanuvchi botingiz bilan avval bog'liq bo'lgan taqdirda (masalan,
> botga yozgan, umumiy guruhda bo'lgan) yoki ochiq profilga ega bo'lsa
> ishonchli natija beradi. Har doim 100% ishlashiga kafolat yo'q — shu
> sabab "topilmasa ham davom etish" imkoniyati saqlab qolingan.

## 5.1. Fragment orqali AVTOMATIK yuborish (ixtiyoriy, xavfli!)

Standart holatda admin tasdiqlagach, stars'ni **siz Fragment.com'da qo'lda**
yuborasiz (yuqoridagi jarayon). Agar buni avtomatlashtirmoqchi bo'lsangiz:

### Qanday ishlaydi
- Fragment.com'ning **rasmiy ochiq API'si yo'q**. `fragment_service.py`
  norasmiy (uchinchi tomon, jamoat tomonidan yozilgan) `pyfragment`
  kutubxonasidan foydalanadi.
- Bu kutubxona ishlashi uchun sizning **TON hamyoningizning 24 so'zli
  seed-phrase'i**, Fragment sessiya cookie'lari va tonconsole.com API
  kaliti kerak bo'ladi — chunki xarid TON blokcheyn tranzaksiyasi orqali
  amalga oshadi.

### ⚠️ Xavfsizlik bo'yicha JIDDIY ogohlantirish
- Bu **norasmiy** kutubxona — men uni sizning nomingizdan sinovdan
  o'tkazmadim va Fragment/Telegram tomonidan tasdiqlanmagan. Seed-phrase —
  bu hamyoningiz ustidan **to'liq nazorat** demakdir. Uni serverga qo'yish
  har doim tavakkal hisoblanadi.
- **Hech qachon** asosiy/katta mablag'li hamyoningizning seed-phrase'ini
  ishlatmang. Faqat shu bot uchun alohida, kunlik aylanma uchun yetarli
  (masalan bir necha kunlik savdo hajmiga mos) mablag'li hamyon yarating.
- Kodni ishlatishdan oldin `pyfragment` manba kodini
  (https://github.com/bohd4nx/pyfragment) o'zingiz yoki ishonchli
  hamkasbingiz ko'rib chiqishini tavsiya qilamiz.
- Avval juda kichik summa (masalan 50 stars, o'zingizning username'ingizga)
  bilan sinab ko'ring.
- Balansni muntazam kuzatib boring, muddatidan oshib qolgan cookie'larni
  yangilab turing.

### Sozlash
1. `.env` faylida:
   ```
   FRAGMENT_AUTO_SEND=true
   FRAGMENT_SEED="word1 word2 ... word24"
   FRAGMENT_API_KEY=tonconsole_dan_olingan_kalit
   FRAGMENT_COOKIES={"stel_ssid":"...","stel_dt":"...","stel_token":"...","stel_ton_token":"..."}
   ```
2. Cookie'larni olish: fragment.com saytiga TON hamyoningizni ulab kiring →
   brauzer **Dev Tools → Application → Cookies** bo'limidan
   `stel_ssid`, `stel_dt`, `stel_token`, `stel_ton_token` qiymatlarini
   nusxalang.
3. `pip install pyfragment`

### Ishlash tartibi (avtomatik yoqilganda)
1. Admin "✅ Tasdiqlash" tugmasini bosadi
2. Bot avtomatik ravishda Fragment orqali stars sotib olib, foydalanuvchiga
   yuboradi
3. Muvaffaqiyatli bo'lsa — buyurtma "sent" holatiga o'tadi, foydalanuvchiga
   xabar boradi
4. **Xatolik bo'lsa** (masalan, balans yetarli emas, cookie eskirgan) — bot
   xatolikni sizga yozadi va **qo'lda yuborish rejimiga** qaytadi (pul
   yo'qolib qolmaydi, faqat avtomatlashtirish ishlamay qoladi)

Agar bunga ishonchingiz komil bo'lmasa, `FRAGMENT_AUTO_SEND=false` qoldiring
— tizim xavfsiz "admin qo'lda yuboradi" rejimida to'liq ishlayveradi.

## 6. Mini-App (ixtiyoriy)

`webapp/index.html` — Telegram WebApp orqali ochiladigan chiroyli interfeys.
Uni ochish uchun `keyboards.py` dagi `webapp_kb()` klaviaturasini biror
handler'ga ulang (masalan, asosiy menyuga qo'shing), masalan:

```python
@dp.message(F.text == "🛒 Mini-App orqali xarid")
async def open_webapp(message: Message):
    await message.answer("Mini-app orqali buyurtma bering:", reply_markup=kb.webapp_kb())
```

**Diqqat:** `webapp/index.html` ichidagi `PRICE_PER_STAR` qiymati bot bazasidagi
narx bilan bir xil bo'lishi kerak — narxni o'zgartirsangiz ikkalasini ham yangilang
(yoki keyinroq buni backend API orqali dinamik qilib qo'yish mumkin).

## 7. Xavfsizlik bo'yicha eslatmalar

- `.env` faylini **hech qachon** GitHub'ga yuklamang (`.gitignore` ga qo'shing).
- Chatga yuborilgan eski tokenni albatta **revoke** qiling.
- Adminlar ro'yxatini kengaytirish kerak bo'lsa, `config.py` dagi `ADMIN_ID`
  ni ro'yxatga (list) aylantirib, `is_admin()` funksiyasini shunga moslang.
- Ishlab chiqarishga chiqarishdan oldin bazani SQLite'dan PostgreSQL'ga
  o'tkazishni yoki muntazam backup olishni tavsiya qilamiz.
