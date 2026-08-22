from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
)
from config import STAR_PACKAGES, WEBAPP_URL


def main_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⭐ Stars sotib olish")],
            [KeyboardButton(text="🧾 Buyurtmalarim"), KeyboardButton(text="ℹ️ Yordam")],
        ],
        resize_keyboard=True,
    )


def webapp_kb() -> ReplyKeyboardMarkup:
    """Mini-app orqali xarid qilish tugmasi (WEBAPP_URL ni config.py da sozlang)."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛒 Mini-App orqali xarid", web_app=WebAppInfo(url=WEBAPP_URL))],
            [KeyboardButton(text="⬅️ Orqaga")],
        ],
        resize_keyboard=True,
    )


def packages_kb(price_per_star: int) -> InlineKeyboardMarkup:
    """
    Fragment.com faqat belgilangan miqdorlarni qabul qiladi (config.STAR_PACKAGES),
    shuning uchun bu yerda "ixtiyoriy son kiritish" tugmasi YO'Q — faqat menyudan tanlanadi.
    """
    rows = []
    row = []
    for i, amount in enumerate(STAR_PACKAGES, 1):
        price = amount * price_per_star
        row.append(InlineKeyboardButton(
            text=f"{amount} ⭐ — {price:,} so'm".replace(",", " "),
            callback_data=f"buy:{amount}"
        ))
        if i % 2 == 0:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def confirm_payment_kb(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ To'lov qildim, chek yubordim", callback_data=f"paid:{order_id}")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"cancel:{order_id}")],
    ])


def admin_order_kb(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"approve:{order_id}"),
            InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject:{order_id}"),
        ]
    ])


def admin_sent_kb(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐ Stars yuborildi (belgilash)", callback_data=f"sent:{order_id}")]
    ])
