import asyncio
import logging
import os
from aiohttp import web

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import BOT_TOKEN
from database import init_db
from handlers import admin, members, moderation

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def _start_keepalive_server():
    """Render/Railway kabi platformalar 'web service' uchun ochiq port kutadi.
    Bu funksiya botni tirik ko'rsatish uchun juda oddiy HTTP server ochadi.
    Faqat PORT muhit o'zgaruvchisi mavjud bo'lsa ishga tushadi (masalan Render'da)."""
    async def health(request):
        return web.Response(text="Bot ishlayapti ✅")

    app = web.Application()
    app.router.add_get("/", health)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"Keep-alive server {port}-portda ishga tushdi.")


async def main():
    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN topilmadi. .env faylida BOT_TOKEN=... ni to'ldiring "
            "(namuna: .env.example)."
        )

    await init_db()
    logger.info("Ma'lumotlar bazasi tayyor.")

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    # Buyruqlar (admin) alohida router, keyin a'zolar, keyin umumiy moderatsiya
    dp.include_router(admin.router)
    dp.include_router(members.router)
    dp.include_router(moderation.router)

    # Render kabi platformalarda PORT beriladi — u yerda keep-alive serverni ham ishga tushiramiz
    if os.getenv("PORT"):
        asyncio.create_task(_start_keepalive_server())

    logger.info("Bot ishga tushmoqda...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
