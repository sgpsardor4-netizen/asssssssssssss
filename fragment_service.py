"""
Fragment.com orqali avtomatik Stars yuborish.

⚠️ Bu norasmiy (unofficial) "pyfragment" kutubxonasidan foydalanadi
(https://github.com/bohd4nx/pyfragment). Fragment'ning rasmiy API'si yo'q.
Ishlashi uchun quyidagilar .env faylida sozlangan bo'lishi kerak:
  FRAGMENT_AUTO_SEND=true
  FRAGMENT_SEED="24 so'zli seed-phrase"
  FRAGMENT_API_KEY="tonconsole.com dan olingan kalit"
  FRAGMENT_COOKIES='{"stel_ssid":"...","stel_dt":"...","stel_token":"...","stel_ton_token":"..."}'

Cookie'larni olish: fragment.com saytiga kirib, TON hamyoningizni ulang,
so'ng brauzer Dev Tools > Application > Cookies bo'limidan
stel_ssid, stel_dt, stel_token, stel_ton_token qiymatlarini nusxalang.

Agar avtomatik yuborish o'chirilgan yoki xatolik yuz bersa, bot admin'ga
buni bildiradi va admin qo'lda yuborib, botda "Stars yuborildi" tugmasini
bosishi kerak bo'ladi (fallback rejimi) - shuning uchun pul yo'qolib qolmaydi.
"""
import json
import logging

import config

logger = logging.getLogger(__name__)


class FragmentError(Exception):
    """Fragment orqali yuborishda umumiy xatolik."""


class FragmentNotConfigured(FragmentError):
    """.env da kerakli sozlamalar to'liq kiritilmagan."""


def _load_cookies() -> dict:
    if not config.FRAGMENT_COOKIES:
        raise FragmentNotConfigured("FRAGMENT_COOKIES .env faylida sozlanmagan.")
    try:
        return json.loads(config.FRAGMENT_COOKIES)
    except json.JSONDecodeError as e:
        raise FragmentNotConfigured(f"FRAGMENT_COOKIES noto'g'ri JSON formatda: {e}")


async def send_stars_via_fragment(username: str, amount: int) -> str:
    """
    Fragment orqali `username` ga `amount` dona Stars sotib olib yuboradi.
    Muvaffaqiyatli bo'lsa tranzaksiya ID qaytaradi.
    Muvaffaqiyatsiz bo'lsa FragmentError (yoki subklassi) ko'taradi —
    chaqiruvchi kod buni ushlab, adminga qo'lda yuborishni so'rashi kerak.
    """
    if not config.FRAGMENT_AUTO_SEND:
        raise FragmentNotConfigured("Avtomatik yuborish o'chirilgan (FRAGMENT_AUTO_SEND=false).")
    if not config.FRAGMENT_SEED or not config.FRAGMENT_API_KEY:
        raise FragmentNotConfigured("FRAGMENT_SEED yoki FRAGMENT_API_KEY sozlanmagan.")
    if amount not in config.STAR_PACKAGES:
        raise FragmentError(
            f"{amount} — Fragment qo'llab-quvvatlaydigan miqdor emas. "
            f"Ruxsat etilgan: {config.STAR_PACKAGES}"
        )

    cookies = _load_cookies()
    target = username if username.startswith("@") else f"@{username}"

    try:
        # Import shu yerda, chunki paket o'rnatilmagan bo'lsa ham
        # bot fragment funksiyasisiz ishlayvera olsin.
        from pyfragment import FragmentClient
        from pyfragment.enums import PaymentMethod
    except ImportError:
        raise FragmentNotConfigured(
            "'pyfragment' o'rnatilmagan. O'rnatish: pip install pyfragment"
        )

    try:
        async with FragmentClient(
            seed=config.FRAGMENT_SEED,
            api_key=config.FRAGMENT_API_KEY,
            cookies=cookies,
        ) as client:
            result = await client.purchase_stars(
                target, amount=amount, payment_method=PaymentMethod.USDT_GRAM
            )
            logger.info(
                "Fragment: %s stars '%s' ga yuborildi, tx=%s",
                result.amount, result.username, result.transaction_id,
            )
            return result.transaction_id
    except Exception as e:
        logger.exception("Fragment orqali yuborishda xatolik: %s", e)
        raise FragmentError(str(e)) from e
