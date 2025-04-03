import asyncio
import logging
import os
from aiohttp import web
from aiohttp_middlewares import cors_middleware
from aiogram import Bot, Dispatcher, types
from aiogram.types import WebAppInfo, Message
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import CommandStart

BOT_TOKEN = os.getenv("BOT_TOKEN", "your_bot_token_here")
WEB_URL = os.getenv("WEB_URL", "https://your-web-url.com/")
HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", 8080))

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

@dp.message(CommandStart())
async def send_welcome(message: Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True).add(
        types.KeyboardButton(
            text="🚖 Заказать авто",
            web_app=WebAppInfo(url=WEB_URL)
        )
    )
    await message.answer("Добро пожаловать в NexaRide!", reply_markup=keyboard)

async def handle_ride(request):
    try:
        data = await request.json()
        destination = data.get("destination")
        latitude = data.get("latitude")
        longitude = data.get("longitude")

        if not destination or latitude is None or longitude is None:
            return web.json_response({"status": "error", "message": "Некорректные данные"}, status=400)

        text = f"🚖 Новая заявка:\n📍 Адрес: {destination}\n🌍 Координаты: {latitude}, {longitude}"
        await bot.send_message(chat_id=5778010807, text=text)

        return web.json_response({"status": "ok", "message": "✅ Заявка получена"})
    except Exception as e:
        logging.error(f"Ошибка обработки /ride: {e}")
        return web.json_response({"status": "error", "message": "Ошибка сервера"}, status=500)

async def handle_home(request):
    with open("web/index.html", encoding="utf-8") as f:
        return web.Response(text=f.read(), content_type="text/html")

async def main():
    logging.basicConfig(level=logging.INFO)

    cors = cors_middleware(allow_all=True)
    app = web.Application(middlewares=[cors])

    app.router.add_get("/", handle_home)
    app.router.add_post("/ride", handle_ride)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, HOST, PORT)
    await site.start()

    logging.info(f"Сервер запущен на http://{HOST}:{PORT}")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Выход...")
