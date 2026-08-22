import asyncio
import logging
import json
from typing import Optional

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

import config
import database as db
import keyboards as kb
import fragment_service
import api_server

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


# ---------- STATE'lar ----------
class BuyStars(StatesGroup):
    waiting_target_username = State()
    confirming_target = State()
    waiting_receipt = State()


class AdminSettings(StatesGroup):
    waiting_price = State()
    waiting_card = State()
    waiting_reject_reason = State()


# =========================================================
#                    FOYDALANUVCHI QISMI
# =========================================================

@dp.message(CommandStart())
async def cmd_start(message: Message):
    await db.upsert_user(message.from_user.id, message.from_user.username or "",
                          message.from_user.full_name)
    await message.answer(
        "Assalomu alaykum! ⭐️\n\n"
        "Bu bot orqali <b>Telegram Stars</b>ni so'mda (UZS) sotib olishingiz mumkin.\n\n"
        "1️⃣ Paket tanlaysiz\n"
        "2️⃣ Ko'rsatilgan kartaga to'lov qilasiz\n"
        "3️⃣ To'lov chekini (screenshot) yuborasiz\n"
        "4️⃣ Admin tasdiqlagach, stars hisobingizga yuboriladi\n\n"
        "Quyidagi menyudan foydalaning:",
        reply_markup=kb.main_menu_kb(),
        parse_mode="HTML",
    )


@dp.message(F.text == "⭐ Stars sotib olish")
async def buy_stars_menu(message: Message):
    price = int(await db.get_setting("price_per_star"))
    await message.answer(
        f"💵 Hozirgi narx: <b>{price:,} so'm</b> / 1 ⭐\n\nPaket tanlang:".replace(",", " "),
        reply_markup=kb.packages_kb(price),
        parse_mode="HTML",
    )


@dp.callback_query(F.data.startswith("buy:"))
async def process_package(callback: CallbackQuery, state: FSMContext):
    amount = int(callback.data.split(":")[1])
    if amount not in config.STAR_PACKAGES:
        await callback.answer("Bu miqdor mavjud emas, menyudan tanlang.", show_alert=True)
        return

    await state.update_data(stars_amount=amount)
    await callback.message.answer(
        "Stars kimning hisobiga yuborilsin? Telegram <b>@username</b>ini kiriting "
        "(agar o'zingizga bo'lsa, o'z username'ingizni yozing):",
        parse_mode="HTML",
    )
    await state.set_state(BuyStars.waiting_target_username)
    await callback.answer()


async def lookup_profile(username: str) -> Optional[dict]:
    """
    Berilgan @username bo'yicha Telegram profilini (ism, username, rasm) topishga urinadi.
    Bot API cheklovlari sababli har doim ham topib bo'lmaydi (masalan, foydalanuvchi
    hech qachon botga yozmagan va maxfiylik sozlamalari qattiq bo'lsa) — shu holatda
    None qaytaradi va oddiy matnli tasdiqlashga o'tiladi.
    """
    uname = username if username.startswith("@") else f"@{username}"
    try:
        chat = await bot.get_chat(uname)
    except Exception:
        return None

    name = getattr(chat, "full_name", None) or chat.first_name or uname
    photo_file_id = None
    try:
        photos = await bot.get_user_profile_photos(chat.id, limit=1)
        if photos.total_count > 0:
            photo_file_id = photos.photos[0][-1].file_id
    except Exception:
        pass

    return {
        "id": chat.id,
        "name": name,
        "username": chat.username,
        "photo": photo_file_id,
    }


def confirm_target_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Ha, to'g'ri", callback_data="confirm_target:yes"),
            InlineKeyboardButton(text="✏️ Qayta kiritish", callback_data="confirm_target:no"),
        ]
    ])


@dp.message(BuyStars.waiting_target_username)
async def process_target_username(message: Message, state: FSMContext):
    target = message.text.strip()
    if not target.startswith("@"):
        target = "@" + target

    await state.update_data(stars_target=target)

    profile = await lookup_profile(target)
    if profile:
        caption = (
            f"👤 <b>{profile['name']}</b>\n"
            f"🔗 @{profile['username'] or target.lstrip('@')}\n\n"
            f"Stars shu foydalanuvchiga yuboriladi. To'g'rimi?"
        )
        if profile["photo"]:
            await message.answer_photo(
                photo=profile["photo"], caption=caption,
                parse_mode="HTML", reply_markup=confirm_target_kb(),
            )
        else:
            await message.answer(
                caption + "\n\n(Profil rasmi topilmadi)",
                parse_mode="HTML", reply_markup=confirm_target_kb(),
            )
    else:
        await message.answer(
            f"⚠️ <b>{target}</b> profilini topib bo'lmadi (foydalanuvchi hali botga yozmagan "
            f"bo'lishi yoki maxfiylik sozlamalari cheklangan bo'lishi mumkin).\n\n"
            f"Baribir shu username'ga davom etamizmi?",
            parse_mode="HTML", reply_markup=confirm_target_kb(),
        )
    await state.set_state(BuyStars.confirming_target)


@dp.callback_query(BuyStars.confirming_target, F.data == "confirm_target:no")
async def confirm_target_no(callback: CallbackQuery, state: FSMContext):
    await state.set_state(BuyStars.waiting_target_username)
    await callback.message.answer("Yaxshi, @username'ni qaytadan kiriting:")
    await callback.answer()


@dp.callback_query(BuyStars.confirming_target, F.data == "confirm_target:yes")
async def confirm_target_yes(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    amount = data["stars_amount"]
    target = data["stars_target"]

    price_per_star = int(await db.get_setting("price_per_star"))
    total_price = amount * price_per_star

    order_id = await db.create_order(callback.from_user.id, amount, total_price, target)
    await state.update_data(order_id=order_id)

    card_number = await db.get_setting("card_number")
    card_owner = await db.get_setting("card_owner")

    await callback.message.answer(
        f"🧾 <b>Buyurtma #{order_id}</b>\n"
        f"⭐ Miqdor: {amount}\n"
        f"🎯 Kimga: {target}\n"
        f"💵 To'lov summasi: <b>{total_price:,} so'm</b>\n\n"
        f"💳 To'lovni quyidagi kartaga o'tkazing (bosib nusxalang):\n"
        f"<code>{card_number}</code>\n"
        f"Karta egasi: {card_owner}\n\n"
        f"⏰ To'lov uchun vaqtingiz: <b>{config.PAYMENT_TIMEOUT_MINUTES} daqiqa</b>. "
        f"Shu vaqt ichida chek yuborilmasa, buyurtma avtomatik bekor qilinadi.\n\n"
        f"To'lovni amalga oshirgach, chek (screenshot) rasmini shu yerga yuboring 👇"
        .replace(",", " "),
        parse_mode="HTML",
    )
    await state.set_state(BuyStars.waiting_receipt)
    asyncio.create_task(schedule_order_expiry(order_id, callback.from_user.id))
    await callback.answer()


async def schedule_order_expiry(order_id: int, user_id: int):
    """PAYMENT_TIMEOUT_MINUTES daqiqadan so'ng, agar buyurtma hali 'pending' bo'lsa,
    uni 'expired' deb belgilaydi va foydalanuvchiga xabar beradi."""
    await asyncio.sleep(config.PAYMENT_TIMEOUT_MINUTES * 60)
    order = await db.get_order(order_id)
    if order and order["status"] == "pending":
        await db.update_order_status(order_id, "expired")
        try:
            await bot.send_message(
                user_id,
                f"⏰ Buyurtma #{order_id} uchun to'lov vaqti tugadi "
                f"({config.PAYMENT_TIMEOUT_MINUTES} daqiqa).\n"
                f"Agar hali ham stars sotib olmoqchi bo'lsangiz, iltimos qaytadan boshlang: /start",
            )
        except Exception:
            pass


@dp.message(BuyStars.waiting_receipt, F.photo)
async def process_receipt(message: Message, state: FSMContext):
    data = await state.get_data()
    order_id = data["order_id"]
    order = await db.get_order(order_id)

    if not order or order["status"] != "pending":
        await message.answer(
            "⏰ Bu buyurtmaning to'lov muddati tugagan. Iltimos, qaytadan boshlang: /start",
            reply_markup=kb.main_menu_kb(),
        )
        await state.clear()
        return

    file_id = message.photo[-1].file_id
    await db.attach_receipt(order_id, file_id)

    await message.answer(
        "✅ Chekingiz qabul qilindi! Admin tekshirib, tasdiqlagach sizga xabar beramiz.\n"
        "Odatda bu tez orada amalga oshiriladi. Iltimos, kuting 🙏",
        reply_markup=kb.main_menu_kb(),
    )

    # Adminga yuborish
    caption = (
        f"🆕 <b>Yangi buyurtma #{order_id}</b>\n"
        f"👤 Foydalanuvchi: {message.from_user.full_name} "
        f"(@{message.from_user.username or 'yoq'}, id: {message.from_user.id})\n"
        f"⭐ Miqdor: {order['stars_amount']}\n"
        f"🎯 Kimga yuboriladi: {order['stars_target']}\n"
        f"💵 Summa: {order['price_uzs']:,} so'm".replace(",", " ")
    )
    await bot.send_photo(
        chat_id=config.ADMIN_ID,
        photo=file_id,
        caption=caption,
        parse_mode="HTML",
        reply_markup=kb.admin_order_kb(order_id),
    )
    await state.clear()


@dp.message(BuyStars.waiting_receipt)
async def process_receipt_wrong(message: Message):
    await message.answer("Iltimos, to'lov chekining rasmini (screenshot) yuboring 📷")


@dp.message(F.text == "🧾 Buyurtmalarim")
async def my_orders(message: Message):
    orders = await db.get_user_orders(message.from_user.id)
    if not orders:
        await message.answer("Sizda hali buyurtmalar yo'q.")
        return
    status_map = {
        "pending": "⏳ Kutilmoqda",
        "paid": "✅ Tasdiqlangan",
        "rejected": "❌ Rad etilgan",
        "sent": "⭐ Stars yuborildi",
        "expired": "⏰ Muddati tugagan",
    }
    lines = []
    for o in orders:
        lines.append(
            f"#{o['order_id']} — {o['stars_amount']}⭐ — {o['price_uzs']:,} so'm — "
            f"{status_map.get(o['status'], o['status'])}".replace(",", " ")
        )
    await message.answer("\n".join(lines))


@dp.message(F.text == "ℹ️ Yordam")
async def help_msg(message: Message):
    await message.answer(
        "Savol yoki muammo bo'lsa, admin bilan bog'laning.\n"
        "Buyurtma berish: ⭐ Stars sotib olish tugmasini bosing."
    )


# WebApp orqali kelgan ma'lumot (mini-app'dan).
# Mini-app'ning o'zida "Qabul qiluvchi" maydonida profil rasmi/nomi
# allaqachon ko'rsatilgan (jonli qidiruv orqali), shuning uchun bu yerda
# qayta "Shu odamga to'g'rimi?" deb so'ralmaydi — to'g'ridan-to'g'ri
# buyurtma yaratiladi.
@dp.message(F.web_app_data)
async def webapp_data_handler(message: Message, state: FSMContext):
    try:
        data = json.loads(message.web_app_data.data)
        amount = int(data["stars_amount"])
        target = data.get("target", "@" + (message.from_user.username or str(message.from_user.id)))
    except Exception:
        await message.answer("Ma'lumotni o'qib bo'lmadi, qaytadan urinib ko'ring.")
        return

    if amount not in config.STAR_PACKAGES:
        await message.answer("Bu miqdor mavjud emas. Iltimos, mini-app menyusidan tanlang.")
        return

    if not target.startswith("@"):
        target = "@" + target

    price_per_star = int(await db.get_setting("price_per_star"))
    total_price = amount * price_per_star

    order_id = await db.create_order(message.from_user.id, amount, total_price, target)
    await state.update_data(order_id=order_id)

    card_number = await db.get_setting("card_number")
    card_owner = await db.get_setting("card_owner")

    await message.answer(
        f"🧾 <b>Buyurtma #{order_id}</b>\n"
        f"⭐ Miqdor: {amount}\n"
        f"🎯 Kimga: {target}\n"
        f"💵 To'lov summasi: <b>{total_price:,} so'm</b>\n\n"
        f"💳 To'lovni quyidagi kartaga o'tkazing (bosib nusxalang):\n"
        f"<code>{card_number}</code>\n"
        f"Karta egasi: {card_owner}\n\n"
        f"⏰ To'lov uchun vaqtingiz: <b>{config.PAYMENT_TIMEOUT_MINUTES} daqiqa</b>. "
        f"Shu vaqt ichida chek yuborilmasa, buyurtma avtomatik bekor qilinadi.\n\n"
        f"To'lovni amalga oshirgach, chek (screenshot) rasmini shu yerga yuboring 👇"
        .replace(",", " "),
        parse_mode="HTML",
    )
    await state.set_state(BuyStars.waiting_receipt)
    asyncio.create_task(schedule_order_expiry(order_id, message.from_user.id))


# =========================================================
#                       ADMIN QISMI
# =========================================================

def is_admin(user_id: int) -> bool:
    return user_id == config.ADMIN_ID


@dp.callback_query(F.data.startswith("approve:"))
async def admin_approve(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q", show_alert=True)
        return
    order_id = int(callback.data.split(":")[1])
    order = await db.get_order(order_id)
    if not order or order["status"] != "pending":
        await callback.answer("Bu buyurtma allaqachon ko'rib chiqilgan.", show_alert=True)
        return

    await db.update_order_status(order_id, "paid")
    await callback.message.edit_caption(
        caption=callback.message.caption + "\n\n✅ <b>TASDIQLANDI</b>",
        parse_mode="HTML",
        reply_markup=kb.admin_sent_kb(order_id),
    )
    await bot.send_message(
        order["user_id"],
        f"✅ Buyurtma #{order_id} to'lovi tasdiqlandi!\n"
        f"⭐ {order['stars_amount']} stars tez orada '{order['stars_target']}' hisobiga yuboriladi."
    )
    await callback.answer("Tasdiqlandi ✅")

    # ---- Fragment orqali avtomatik yuborishga urinish (agar yoqilgan bo'lsa) ----
    if config.FRAGMENT_AUTO_SEND:
        await callback.message.answer(f"⏳ #{order_id}: Fragment orqali avtomatik yuborilmoqda...")
        try:
            tx_id = await fragment_service.send_stars_via_fragment(
                order["stars_target"], order["stars_amount"]
            )
            await db.update_order_status(order_id, "sent")
            await callback.message.answer(
                f"✅ #{order_id}: {order['stars_amount']} ⭐ avtomatik yuborildi.\n"
                f"Tranzaksiya: <code>{tx_id}</code>",
                parse_mode="HTML",
            )
            await bot.send_message(
                order["user_id"],
                f"⭐ Buyurtma #{order_id}: {order['stars_amount']} stars "
                f"'{order['stars_target']}' hisobiga yuborildi. Xaridingiz uchun rahmat!"
            )
        except fragment_service.FragmentError as e:
            await callback.message.answer(
                f"⚠️ #{order_id}: Fragment orqali avtomatik yuborib bo'lmadi:\n"
                f"<code>{e}</code>\n\n"
                f"Iltimos, stars'ni qo'lda yuboring va pastdagi \"⭐ Stars yuborildi\" tugmasini bosing.",
                parse_mode="HTML",
            )


@dp.callback_query(F.data.startswith("sent:"))
async def admin_mark_sent(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q", show_alert=True)
        return
    order_id = int(callback.data.split(":")[1])
    order = await db.get_order(order_id)
    await db.update_order_status(order_id, "sent")
    await callback.message.edit_caption(
        caption=callback.message.caption.split("\n\n✅")[0] + "\n\n⭐ <b>STARS YUBORILDI</b>",
        parse_mode="HTML",
    )
    await bot.send_message(
        order["user_id"],
        f"⭐ Buyurtma #{order_id}: {order['stars_amount']} stars '{order['stars_target']}' hisobiga yuborildi. "
        f"Xaridingiz uchun rahmat!"
    )
    await callback.answer("Belgilandi")


@dp.callback_query(F.data.startswith("reject:"))
async def admin_reject_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q", show_alert=True)
        return
    order_id = int(callback.data.split(":")[1])
    await state.update_data(reject_order_id=order_id)
    await state.set_state(AdminSettings.waiting_reject_reason)
    await callback.message.answer(f"Buyurtma #{order_id} uchun rad etish sababini yozing:")
    await callback.answer()


@dp.message(AdminSettings.waiting_reject_reason)
async def admin_reject_reason(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    data = await state.get_data()
    order_id = data["reject_order_id"]
    order = await db.get_order(order_id)

    await db.update_order_status(order_id, "rejected")
    await bot.send_message(
        order["user_id"],
        f"❌ Buyurtma #{order_id} rad etildi.\nSabab: {message.text}\n"
        f"Savol bo'lsa, admin bilan bog'laning."
    )
    await message.answer(f"Buyurtma #{order_id} rad etildi va foydalanuvchiga xabar berildi.")
    await state.clear()


@dp.message(Command("pending"))
async def admin_pending(message: Message):
    if not is_admin(message.from_user.id):
        return
    orders = await db.get_pending_orders()
    if not orders:
        await message.answer("Kutilayotgan buyurtmalar yo'q.")
        return
    for o in orders:
        await message.answer(
            f"#{o['order_id']} — user {o['user_id']} — {o['stars_amount']}⭐ — "
            f"{o['price_uzs']:,} so'm — {o['stars_target']}".replace(",", " "),
            reply_markup=kb.admin_order_kb(o["order_id"]),
        )


@dp.message(Command("setprice"))
async def admin_setprice_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    current = await db.get_setting("price_per_star")
    await message.answer(f"Hozirgi narx: {current} so'm/⭐\nYangi narxni kiriting (faqat raqam):")
    await state.set_state(AdminSettings.waiting_price)


@dp.message(AdminSettings.waiting_price)
async def admin_setprice_finish(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Faqat raqam kiriting.")
        return
    await db.set_setting("price_per_star", message.text)
    await message.answer(f"✅ Yangi narx o'rnatildi: {message.text} so'm/⭐")
    await state.clear()


@dp.message(Command("setcard"))
async def admin_setcard_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await message.answer(
        "Yangi karta ma'lumotini quyidagi formatda yuboring:\n"
        "<code>8600 0000 0000 0000 | F.I.SH.</code>",
        parse_mode="HTML",
    )
    await state.set_state(AdminSettings.waiting_card)


@dp.message(AdminSettings.waiting_card)
async def admin_setcard_finish(message: Message, state: FSMContext):
    if "|" not in message.text:
        await message.answer("Format noto'g'ri. Masalan: 8600 0000 0000 0000 | F.I.SH.")
        return
    number, owner = [p.strip() for p in message.text.split("|", 1)]
    await db.set_setting("card_number", number)
    await db.set_setting("card_owner", owner)
    await message.answer("✅ Karta ma'lumotlari yangilandi.")
    await state.clear()


@dp.message(Command("stats"))
async def admin_stats(message: Message):
    if not is_admin(message.from_user.id):
        return
    orders = await db.get_pending_orders()
    await message.answer(f"⏳ Kutilayotgan buyurtmalar: {len(orders)}")


# =========================================================

async def main():
    await db.init_db()
    asyncio.create_task(api_server.run_api_server(bot, port=config.API_PORT))
    logger.info("Bot ishga tushdi...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
