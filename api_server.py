"""
Mini-app uchun kichik API server.

Nima uchun kerak: mini-app (webapp/index.html) oddiy statik HTML bo'lib,
Telegram profilini (ism, rasm) faqat BOT TOKENI orqali so'rash mumkin.
Bot tokenini hech qachon frontendga (brauzerga) qo'yib bo'lmaydi — shuning
uchun bu alohida, kichik HTTP server bot bilan bir jarayonda ishlaydi va
mini-app undan "shu @username kim ekan?" deb so'raydi.

Ikki endpoint:
  GET /api/lookup?username=someuser
      -> {"found": true, "name": "...", "username": "...", "photo": true/false}
  GET /api/photo/<username>
      -> profil rasmi (JPEG bytes), agar bo'lmasa 404

CORS hammaga ochiq (*), chunki mini-app boshqa domenda (masalan GitHub Pages)
joylashgan bo'lishi mumkin.
"""

import logging
from aiohttp import web
from aiogram import Bot

logger = logging.getLogger(__name__)


def _cors(response: web.StreamResponse) -> web.StreamResponse:
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response


async def _lookup_profile(bot: Bot, username: str):
    uname = username if username.startswith("@") else f"@{username}"
    try:
        chat = await bot.get_chat(uname)
    except Exception:
        return None

    name = getattr(chat, "full_name", None) or chat.first_name or uname
    has_photo = False
    try:
        photos = await bot.get_user_profile_photos(chat.id, limit=1)
        has_photo = photos.total_count > 0
    except Exception:
        pass

    return {
        "found": True,
        "id": chat.id,
        "name": name,
        "username": chat.username or uname.lstrip("@"),
        "photo": has_photo,
    }


def create_app(bot: Bot) -> web.Application:
    app = web.Application()

    async def handle_options(request: web.Request) -> web.Response:
        return _cors(web.Response())

    async def handle_lookup(request: web.Request) -> web.Response:
        username = request.query.get("username", "").strip()
        if not username:
            return _cors(web.json_response({"found": False, "error": "username kerak"}, status=400))

        profile = await _lookup_profile(bot, username)
        if not profile:
            return _cors(web.json_response({"found": False}))
        return _cors(web.json_response(profile))

    async def handle_photo(request: web.Request) -> web.Response:
        username = request.match_info.get("username", "").strip()
        uname = username if username.startswith("@") else f"@{username}"
        try:
            chat = await bot.get_chat(uname)
            photos = await bot.get_user_profile_photos(chat.id, limit=1)
            if photos.total_count == 0:
                return _cors(web.Response(status=404))
            file_id = photos.photos[0][-1].file_id
            file = await bot.get_file(file_id)
            buf = await bot.download_file(file.file_path)
            return _cors(web.Response(body=buf.read(), content_type="image/jpeg"))
        except Exception:
            return _cors(web.Response(status=404))

    async def handle_root(request: web.Request) -> web.Response:
        # UptimeRobot (yoki shunga o'xshash pinger) shu manzilga har necha
        # daqiqada so'rov yuborib turadi, shunda Render'ning bepul tarifi
        # botni "uyquga" ketkazmaydi — 24/7 ishlashi shu orqali ta'minlanadi.
        return _cors(web.json_response({"status": "ok", "service": "stars_bot"}))

    app.router.add_get("/", handle_root)
    app.router.add_get("/api/lookup", handle_lookup)
    app.router.add_route("OPTIONS", "/api/lookup", handle_options)
    app.router.add_get("/api/photo/{username}", handle_photo)
    app.router.add_route("OPTIONS", "/api/photo/{username}", handle_options)
    return app


async def run_api_server(bot: Bot, host: str = "0.0.0.0", port: int = 8080):
    app = create_app(bot)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    logger.info(f"API server {host}:{port} da ishga tushdi (mini-app profil qidiruvi uchun)")
